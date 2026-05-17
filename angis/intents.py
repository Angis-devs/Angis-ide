"""Intent matching for human-like Angis phrases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable, Iterable

from .errors import AmbiguityError, AngisSyntaxError
from .ir import (
    Access,
    Add,
    AddToList,
    AddToVar,
    AnimateObject,
    AppBackground,
    AppButton,
    AppFileAttach,
    AppLayout,
    AppLoadingScreen,
    AppScene,
    AppSize,
    AppStart,
    AppText,
    AssertTrue,
    BinaryOp,
    Comprehension,
    CreateFromBlueprint,
    CreateObject,
    CreateList,
    CreateMap,
    DefineBlueprint,
    DebugState,
    DebugBreakpoint,
    Divide,
    ExecuteSql,
    Expression,
    ExportApp,
    FileAttach,
    FetchUrl,
    GameRule,
    GameStart,
    GetArgs,
    GetEnv,
    HttpRequest,
    ImportModule,
    Lambda,
    LengthOf,
    Multiply,
    MoveObject,
    OpenDatabase,
    PackageApp,
    PlaceObject,
    PlayVideo,
    PlaySound,
    Print,
    PythonEval,
    RaiseError,
    ReadInput,
    ResizeObject,
    RotateObject,
    RunFile,
    SetCamera,
    SetCameraMode,
    RemoveFromList,
    RemoveProperty,
    SaveState,
    SetAccess,
    SetVar,
    SetProperty,
    SetSoundVolume,
    SetLiteral,
    ShowText,
    SliceOf,
    Sleep,
    LoadState,
    StopSound,
    Subtract,
    TernaryExpr,
    TupleLiteral,
    UnaryOp,
    UpdateVar,
    UseStdLibAction,
    WalrusExpr,
)


from .lang import ENGLISH, SPANISH, FRENCH, GERMAN, get_language, set_language as _set_lang

def PRINT_WORDS():
    return get_language()._p
def SET_WORDS():
    return get_language()._s
def MATH_WORDS():
    return get_language()._m
def APP_WORDS():
    return get_language()._a
def GAME_WORDS():
    return get_language()._g
def FILE_WORDS():
    return get_language()._f


InstructionFactory = Callable[[re.Match[str], str, float], object]


@dataclass(frozen=True)
class IntentPattern:
    name: str
    regex: re.Pattern[str]
    confidence: float
    factory: InstructionFactory

    def try_match(self, phrase: str) -> object | None:
        match = self.regex.fullmatch(phrase)
        if not match:
            return None
        return self.factory(match, phrase, self.confidence)


def parse_atom(text: str) -> Expression:
    value = text.strip()
    if not value:
        raise AngisSyntaxError("Expected a value.")
    if value.startswith("(") and value.endswith(")"):
        depth = 0
        for i, c in enumerate(value):
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            if depth == 0 and i < len(value) - 1:
                break
        else:
            return parse_expression(value[1:-1])
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        inner = value[1:-1]
        interpolated = _interpolate_string(inner)
        return interpolated
    if value.startswith("[") and value.endswith("]"):
        comp = _try_parse_comprehension(value)
        if comp is not None:
            return comp
        return _parse_list_literal(value)
    if value.startswith("{") and value.endswith("}"):
        comp = _try_parse_dict_comprehension(value)
        if comp is not None:
            return comp
        lam = _try_parse_lambda(value)
        if lam is not None:
            return lam
        return _parse_dict_literal(value)
    lowered = value.lower()

    set_match = re.fullmatch(r"set\s+of\s+(?P<items>.+)", value, re.I)
    if set_match:
        items = [item.strip() for item in _split_items(set_match.group("items"))]
        return SetLiteral(values=[parse_expression(item) for item in items])

    tuple_match = re.fullmatch(r"tuple\s+of\s+(?P<items>.+)", value, re.I)
    if tuple_match:
        items = [item.strip() for item in _split_items(tuple_match.group("items"))]
        return TupleLiteral(values=[parse_expression(item) for item in items])

    comp = _try_parse_natural_comprehension(value)
    if comp is not None:
        return comp

    lam = _try_parse_natural_lambda(value)
    if lam is not None:
        return lam

    py_match = re.fullmatch(r"(?:python|py)\((?P<code>.+)\)", value, re.I)
    if py_match:
        return PythonEval(expression=py_match.group("code"))

    py_inline = re.fullmatch(r"\{\{(?:py|python):(?P<code>.+)\}\}", value)
    if py_inline:
        return PythonEval(expression=py_inline.group("code"))

    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    if re.fullmatch(r"[+-]?\d+\.\d+", value):
        return float(value)
    length_match = re.fullmatch(
        r"(?:len|length|count|size)\s+of\s+(?P<value>.+)|number\s+of\s+(?:items|things|entries|letters)\s+in\s+(?P<items>.+)",
        value,
        re.I,
    )
    if length_match:
        return LengthOf(parse_expression(length_match.group("value") or length_match.group("items")))
    natural_slice = _split_natural_slice(value)
    if natural_slice is not None:
        return natural_slice
    natural_access = _split_natural_access(value)
    if natural_access is not None:
        target, key = natural_access
        return Access(parse_atom(target), key)
    dot_access = _split_dot_access(value)
    if dot_access is not None:
        target, key = dot_access
        return Access(parse_atom(target), key)
    index_access = _split_index_access(value)
    if index_access is not None:
        target, key = index_access
        return Access(parse_atom(target), parse_expression(key))
    if re.fullmatch(r"[^\W\d]\w*", value):
        from .ir import Reference

        return Reference(value)
    if lowered.startswith("not ") and len(value) > 4:
        rest = value[4:].strip()
        if rest:
            return UnaryOp("not", parse_atom(rest))
    if value.startswith("-") and len(value) > 1 and not re.fullmatch(r"[+-]?\d+(\.\d+)?", value):
        rest = value[1:].strip()
        if rest:
            return UnaryOp("-", parse_atom(rest))
    raise AngisSyntaxError(f"Could not understand value {value!r}.")


def parse_expression(text: str) -> Expression:
    value = text.strip()
    if not value:
        raise AngisSyntaxError("Expected a value.")
    lowered = value.lower()
    if lowered.startswith("for each ") and re.search(r"\b(collect|get)\b", lowered, re.I):
        comp = _try_parse_natural_comprehension(value)
        if comp is not None:
            return comp
    if lowered.startswith(("lambda ", "arrow ", "fn ")):
        lam = _try_parse_natural_lambda(value)
        if lam is not None:
            return lam
    ternary_match = re.fullmatch(
        r"(?P<true>.+?)\s+if\s+(?P<condition>.+?)\s+else\s+(?P<false>.+)",
        value, re.I,
    )
    if ternary_match:
        return TernaryExpr(
            condition=parse_expression(ternary_match.group("condition")),
            true_expr=parse_expression(ternary_match.group("true")),
            false_expr=parse_expression(ternary_match.group("false")),
        )

    walrus_match = re.fullmatch(r"\((?P<name>[^\W\d]\w*)\s*:=\s*(?P<value>.+)\)", value)
    if walrus_match:
        return WalrusExpr(
            name=walrus_match.group("name"),
            value=parse_expression(walrus_match.group("value")),
        )

    py_inline = re.fullmatch(r"\{\{(?:py|python):(?P<code>.+)\}\}", value)
    if py_inline:
        return PythonEval(expression=py_inline.group("code"))

    py_fn_match = re.fullmatch(r"(?:python|py)\((?P<code>.+)\)", value, re.I)
    if py_fn_match:
        return PythonEval(expression=py_fn_match.group("code"))

    for operators, word_operators in (
        (("==", "!=", ">=", "<=", ">", "<"), (("is", "=="), ("equals", "=="), ("equal to", "=="), ("same as", "=="), ("is not", "!="), ("not equal to", "!="), ("greater than or equal", ">="), ("at least", ">="), ("less than or equal", "<="), ("at most", "<="), ("greater than", ">"), ("bigger than", ">"), ("more than", ">"), ("less than", "<"), ("smaller than", "<"), ("under", "<"))),
        (("+", "-"), (("plus", "+"), ("added to", "+"), ("minus", "-"))),
        (("*", "/", "%"), (("times", "*"), ("multiplied by", "*"), ("divided by", "/"), ("over", "/"), ("mod", "%"), ("modulo", "%"), ("remainder", "%"))),
        ((), (("to the power of", "**"), ("raised to", "**"), ("to the power", "**"))),
    ):
        split = _split_expression(value, operators) or _split_word_expression(value, word_operators)
        if split is not None:
            left, operator, right = split
            return BinaryOp(operator, parse_expression(left), parse_expression(right))
    return parse_atom(value)


def parse_text_value(text: str) -> Expression:
    """Parse values where plain human text should become a string."""
    value = text.strip()
    lowered = value.lower()
    if lowered.startswith(("set of ", "tuple of ", "for each ", "lambda ", "arrow ", "fn ")):
        return parse_expression(value)
    if " if " in lowered and " else " in lowered:
        return parse_expression(value)
    if value.startswith("(") and ":=" in value:
        return parse_expression(value)
    if re.fullmatch(r"(?:python|py)\(.*\)", value, re.I):
        return parse_expression(value)
    if re.fullmatch(r"\{\{py(?:thon)?:.+\}\}", value):
        return parse_expression(value)
    if _is_quoted(value):
        return parse_atom(value)
    if (value.startswith("[") and value.endswith("]")) or (value.startswith("{") and value.endswith("}")):
        return parse_atom(value)
    if _looks_like_access(value) or _looks_like_expression(value):
        return parse_expression(value)
    if lowered in {"true", "false", "yes", "no", "on", "off"} or re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
        return parse_atom(value)
    if re.fullmatch(r"[^\W\d]\w*", value):
        if value[0].isupper():
            return value
        return parse_atom(value)
    return value


def parse_output_value(text: str, source: str) -> Expression:
    value = text.strip()
    source_lower = normalize_phrase(source).lower()
    if source_lower.startswith(("say ", "print ", "display ")):
        if _is_quoted(value) or re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
            return parse_text_value(value)
        if re.search(r'[+\-*/%]', value) or re.search(r'(?:plus|minus|times|divided|over|mod)', value, re.I):
            try:
                return parse_expression(value)
            except AngisSyntaxError:
                pass
        return value
    result = parse_text_value(value)
    if isinstance(result, str) and re.search(r'[+\-*/%]', result):
        try:
            return parse_expression(value)
        except AngisSyntaxError:
            pass
    return result


def _looks_like_expression(value: str) -> bool:
    if _is_quoted(value):
        return False
    stripped = value.strip()
    if re.fullmatch(r"(?:python|py)\(.*\)", stripped, re.I):
        return True
    if re.fullmatch(r"\{\{py(?:thon)?:.+\}\}", stripped):
        return True
    if re.fullmatch(r"(?:length|count|size)\s+of\s+.+|number\s+of\s+(?:items|things|entries|letters)\s+in\s+.+", stripped, re.I):
        return True
    if stripped.startswith("(") or stripped.startswith("-(") or stripped.startswith("not "):
        try:
            parse_expression(stripped)
            return True
        except AngisSyntaxError:
            return False
    if stripped.startswith("-") and not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", stripped):
        try:
            parse_atom(stripped)
            return True
        except AngisSyntaxError:
            pass
    if stripped.lower().startswith("not ") and len(stripped) > 4:
        rest = stripped[4:].strip()
        if rest and not rest.lower() in {"true", "false", "yes", "no", "on", "off"}:
            try:
                parse_atom(stripped)
                return True
            except AngisSyntaxError:
                pass
    named_access = r"[^\W\d]\w*\s+of\s+[^\W\d]\w*(?:\.[^\W\d]\w*)?(?:\[[^\]]+\])?"
    indexed_access = r"(?:(?:item|index)\s+[+-]?\d+|first|second|third|fourth|fifth|last)\s+(?:item|letter|character|entry)?\s*of\s+[^\W\d]\w*(?:\.[^\W\d]\w*)?(?:\[[^\]]+\])?"
    slice_access = r"(?:first\s+\d+\s+(?:items|letters|characters|entries)|(?:items|letters|characters|entries)\s+[+-]?\d+\s+(?:to|through)\s+[+-]?\d+)\s+of\s+[^\W\d]\w*(?:\.[^\W\d]\w*)?(?:\[[^\]]+\])?"
    paren_atom = r"\([^()]+\)"
    unary_atom = r"-[^\W\d]\w*|not\s+[^\W\d]\w*"
    atom = rf"(?:{slice_access}|{indexed_access}|{named_access}|{paren_atom}|{unary_atom}|[^\W\d]\w*(?:\.[^\W\d]\w*)?(?:\[[^\]]+\])?|[+-]?\d+(?:\.\d+)?)"
    if re.search(r"[+\-*/%]", stripped):
        if re.fullmatch(r"[^\W\d]\w*(?:-[^\W\d]\w*)+", stripped):
            return False
        if re.fullmatch(r"\d{4}-\d{1,2}(?:-\d{1,2})?", stripped):
            return False
        return bool(re.fullmatch(rf"\s*{atom}(?:\s*[+\-*/%]\s*{atom})+\s*", stripped))
    word_operator = r"(?:plus|added\s+to|minus|times|multiplied\s+by|divided\s+by|over|mod|modulo|remainder|to\s+the\s+power\s+(?:of)?|raised\s+to)"
    if re.search(r"(?:plus|minus|times|divided|over|mod|modulo|remainder|power|raised)", stripped, re.I):
        return bool(re.fullmatch(rf"\s*{atom}(?:\s+{word_operator}\s+{atom})+\s*", stripped, re.I))
    return False


def _looks_like_access(value: str) -> bool:
    if re.fullmatch(r"(?:python|py)\(.*\)", value.strip(), re.I):
        return True
    if re.fullmatch(r"\{\{py(?:thon)?:.+\}\}", value.strip()):
        return True
    return (
        _split_dot_access(value) is not None
        or _split_index_access(value) is not None
        or _split_natural_access(value) is not None
        or _split_natural_slice(value) is not None
    )


def _split_natural_access(value: str) -> tuple[str, Expression] | None:
    target = r"[^\W\d]\w*(?:\.[^\W\d]\w*)?(?:\[[^\]]+\])?"
    slice_match = _split_natural_slice(value)
    if slice_match is not None:
        return None
    nested_target = (
        rf"(?:(?:item|index)\s+[+-]?\d+|first|second|third|fourth|fifth|last)\s+"
        rf"(?:item|letter|character|entry)\s+of\s+{target}"
    )
    nested_match = re.fullmatch(rf"(?P<key>[^\W\d]\w*)\s+of\s+(?P<target>{nested_target})", value, re.I)
    if nested_match:
        return nested_match.group("target"), nested_match.group("key")
    index_match = re.fullmatch(rf"(?:item|index)\s+(?P<key>[+-]?\d+)\s+of\s+(?P<target>{target})", value, re.I)
    if index_match:
        return index_match.group("target"), int(index_match.group("key"))
    ordinal_match = re.fullmatch(
        rf"(?P<key>first|second|third|fourth|fifth|last)\s+(?:item|letter|character|entry)\s+of\s+(?P<target>{target})",
        value,
        re.I,
    )
    if ordinal_match:
        return ordinal_match.group("target"), _ordinal_index(ordinal_match.group("key"))
    field_match = re.fullmatch(rf"(?P<key>[^\W\d]\w*)\s+of\s+(?P<target>{target})", value, re.I)
    if field_match:
        return field_match.group("target"), field_match.group("key")
    return None


def _split_natural_slice(value: str) -> SliceOf | None:
    target = r"[^\W\d]\w*(?:\.[^\W\d]\w*)?(?:\[[^\]]+\])?"
    first_match = re.fullmatch(rf"first\s+(?P<count>\d+)\s+(?:items|letters|characters|entries)\s+of\s+(?P<target>{target})", value, re.I)
    if first_match:
        return SliceOf(parse_atom(first_match.group("target")), 0, int(first_match.group("count")))
    range_match = re.fullmatch(
        rf"(?:items|letters|characters|entries)\s+(?P<start>[+-]?\d+)\s+(?P<kind>to|through)\s+(?P<end>[+-]?\d+)\s+of\s+(?P<target>{target})",
        value,
        re.I,
    )
    if range_match:
        end = int(range_match.group("end"))
        if range_match.group("kind").lower() == "through":
            end += 1
        return SliceOf(parse_atom(range_match.group("target")), int(range_match.group("start")), end)
    return None


def _ordinal_index(value: str) -> int:
    indexes = {"first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4, "last": -1}
    return indexes[value.lower()]


def _split_dot_access(value: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"(?P<target>.+)\.(?P<key>[^\W\d]\w*)", value)
    if not match:
        return None
    target = match.group("target").strip()
    if not re.match(r"[^\W\d]", target):
        return None
    return target, match.group("key")


def _split_index_access(value: str) -> tuple[str, str] | None:
    if not value.endswith("]"):
        return None
    depth = 0
    quote: str | None = None
    for index in range(len(value) - 1, -1, -1):
        char = value[index]
        if char in {"'", '"'}:
            quote = None if quote == char else char
            continue
        if quote is not None:
            continue
        if char == "]":
            depth += 1
            continue
        if char == "[":
            depth -= 1
            if depth == 0:
                target = value[:index].strip()
                key = value[index + 1 : -1].strip()
                if target and key and re.match(r"[^\W\d]", target):
                    return target, key
    return None


def _split_expression(value: str, operators: tuple[str, ...]) -> tuple[str, str, str] | None:
    quote: str | None = None
    depth = 0
    for index in range(len(value) - 1, -1, -1):
        char = value[index]
        if char in {"'", '"'}:
            quote = None if quote == char else char
            continue
        if quote is not None:
            continue
        if char == ")":
            depth += 1
            continue
        if char == "(":
            depth -= 1
            continue
        if depth > 0 or char not in operators:
            continue
        if char in {"+", "-"} and index == 0:
            continue
        left = value[:index].strip()
        right = value[index + 1 :].strip()
        if left and right:
            return left, char, right
    return None


def _split_word_expression(value: str, operators: tuple[tuple[str, str], ...]) -> tuple[str, str, str] | None:
    phrases = sorted((phrase for phrase, _operator in operators), key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(phrase).replace(r"\ ", r"\s+") for phrase in phrases) + r")\b", re.I)
    quote: str | None = None
    matches = list(pattern.finditer(value))
    for match in reversed(matches):
        quote = None
        depth = 0
        for char in value[: match.start()]:
            if char in {"'", '"'}:
                quote = None if quote == char else char
            if quote is not None:
                continue
            if char == ")":
                depth += 1
            elif char == "(":
                depth -= 1
        if quote is not None or depth != 0:
            continue
        left = value[: match.start()].strip()
        right = value[match.end() :].strip()
        if not left or not right:
            continue
        phrase = re.sub(r"\s+", " ", match.group(1).lower())
        for candidate, operator in operators:
            if phrase == candidate:
                return left, operator, right
    return None


def _print(match: re.Match[str], source: str, confidence: float) -> Print:
    return Print(value=parse_output_value(match.group("value"), source), source=source, confidence=confidence)


def _set(match: re.Match[str], source: str, confidence: float) -> SetVar:
    return SetVar(
        name=_parse_name(match.group("name")),
        value=parse_text_value(match.group("value")),
        source=source,
        confidence=confidence,
    )


def _parse_list_literal(value: str) -> list[Expression]:
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [_parse_property_value(item) for item in _split_items(inner)]


def _parse_dict_literal(value: str) -> dict[str, Expression]:
    inner = value[1:-1].strip()
    if not inner:
        return {}
    return _parse_map_items(inner)


def _try_parse_natural_comprehension(value: str) -> Comprehension | None:
    match = re.fullmatch(
        r"for\s+each\s+(?P<var>[^\W\d]\w*)\s+in\s+(?P<collection>.+?)\s+(?:collect|get)\s+(?P<expr>.+?)(?:\s+if\s+(?P<filter>.+))?",
        value, re.I,
    )
    if not match:
        return None
    filter_expr = parse_expression(match.group("filter")) if match.group("filter") else None
    return Comprehension(
        expr=parse_expression(match.group("expr")),
        item_var=match.group("var"),
        collection=parse_expression(match.group("collection")),
        filter_expr=filter_expr,
    )


def _try_parse_natural_lambda(value: str) -> Lambda | None:
    match = re.fullmatch(
        r"(?:lambda|arrow|fn)\s+(?P<params>[^\W\d]\w*(?:\s*,\s*[^\W\d]\w*)*)\s+(?:into|to|=>)\s+(?P<body>.+)",
        value, re.I,
    )
    if not match:
        return None
    params = [p.strip() for p in match.group("params").split(",")]
    return Lambda(params=params, body=parse_expression(match.group("body")))


def _interpolate_string(text: str) -> Expression:
    if not text:
        return text
    parts: list[Expression | str] = []
    last_end = 0
    for match in re.finditer(r"\{([^{}]+)\}", text):
        if match.start() > last_end:
            parts.append(text[last_end:match.start()])
        try:
            parts.append(parse_expression(match.group(1)))
        except AngisSyntaxError:
            parts.append(match.group(0))
        last_end = match.end()
    if last_end < len(text):
        parts.append(text[last_end:])
    if len(parts) == 1:
        return parts[0]
    result: Expression = parts[0] if isinstance(parts[0], str) else parts[0]
    for part in parts[1:]:
        if isinstance(part, str):
            result = BinaryOp("+", result, part)
        else:
            result = BinaryOp("+", result, part)
    return result


def _try_parse_comprehension(value: str) -> Comprehension | None:
    inner = value[1:-1].strip()
    match = re.fullmatch(r"(?P<expr>.+?)\s+for\s+(?P<var>[^\W\d]\w*)\s+in\s+(?P<collection>.+?)(?:\s+if\s+(?P<filter>.+))?", inner, re.I)
    if not match:
        return None
    filter_expr = parse_expression(match.group("filter")) if match.group("filter") else None
    return Comprehension(
        expr=parse_expression(match.group("expr")),
        item_var=match.group("var"),
        collection=parse_expression(match.group("collection")),
        filter_expr=filter_expr,
    )


def _try_parse_dict_comprehension(value: str) -> Comprehension | None:
    inner = value[1:-1].strip()
    match = re.fullmatch(r"(?P<key>.+?)\s*:\s*(?P<val>.+?)\s+for\s+(?P<var>[^\W\d]\w*)\s+in\s+(?P<collection>.+?)(?:\s+if\s+(?P<filter>.+))?", inner, re.I)
    if not match:
        return None
    filter_expr = parse_expression(match.group("filter")) if match.group("filter") else None
    return Comprehension(
        expr=parse_expression(match.group("val")),
        item_var=match.group("var"),
        collection=parse_expression(match.group("collection")),
        filter_expr=filter_expr,
        is_dict=True,
        key_expr=parse_expression(match.group("key")),
    )


def _try_parse_lambda(value: str) -> Lambda | None:
    inner = value[1:-1].strip()
    arrow = re.search(r"\s*->\s*", inner)
    if not arrow:
        return None
    params_text = inner[:arrow.start()].strip()
    body_text = inner[arrow.end():].strip()
    params = [p.strip() for p in params_text.split(",") if p.strip()] if params_text else []
    for p in params:
        if not re.fullmatch(r"[^\W\d]\w*", p):
            return None
    return Lambda(params=params, body=parse_expression(body_text))


def _set_access(match: re.Match[str], source: str, confidence: float) -> SetAccess:
    target = parse_expression(match.group("target"))
    if not isinstance(target, Access):
        raise AngisSyntaxError("Expected a data field or list index target.")
    return SetAccess(target=target, value=parse_text_value(match.group("value")), source=source, confidence=confidence)


def _set_item_of(match: re.Match[str], source: str, confidence: float) -> SetAccess:
    target = Access(parse_atom(match.group("name")), int(match.group("index")))
    return SetAccess(target=target, value=parse_text_value(match.group("value")), source=source, confidence=confidence)


def _change_property(op: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> SetProperty:
        object_name = _parse_name(match.group("object"))
        property_name = _parse_name(match.group("property"))
        current = Access(parse_atom(object_name), property_name)
        value = BinaryOp(op, current, parse_text_value(match.group("value")))
        return SetProperty(object_name=object_name, property_name=property_name, value=value, source=source, confidence=confidence)

    return factory


def _change_item(op: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> SetAccess:
        target = Access(parse_atom(match.group("name")), int(match.group("index")))
        value = BinaryOp(op, target, parse_text_value(match.group("value")))
        return SetAccess(target=target, value=value, source=source, confidence=confidence)

    return factory


def _add_to_var(match: re.Match[str], source: str, confidence: float) -> AddToVar:
    return AddToVar(
        name=_parse_name(match.group("name")),
        value=parse_atom(match.group("value")),
        source=source,
        confidence=confidence,
    )


def _update_var(op: str, default_value: Expression | None = None) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UpdateVar:
        raw_value = match.groupdict().get("value")
        value = default_value if raw_value is None else parse_text_value(raw_value)
        if value is None:
            raise AngisSyntaxError("Expected a value.")
        return UpdateVar(name=_parse_name(match.group("name")), op=op, value=value, source=source, confidence=confidence)

    return factory


def _math(cls: type[Add] | type[Subtract] | type[Multiply] | type[Divide]) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> object:
        return cls(
            left=parse_expression(match.group("left")),
            right=parse_expression(match.group("right")),
            source=source,
            confidence=confidence,
        )

    return factory


def _app_start(match: re.Match[str], source: str, confidence: float) -> AppStart:
    return AppStart(title=parse_text_value(match.group("value")), source=source, confidence=confidence)


def _app_text(match: re.Match[str], source: str, confidence: float) -> AppText:
    return AppText(value=parse_text_value(match.group("value")), source=source, confidence=confidence)


def _app_button(match: re.Match[str], source: str, confidence: float) -> AppButton:
    return AppButton(label=parse_text_value(match.group("value")), source=source, confidence=confidence)


def _app_scene(match: re.Match[str], source: str, confidence: float) -> AppScene:
    return AppScene(name=match.group("value").strip(), source=source, confidence=confidence)


def _app_layout(match: re.Match[str], source: str, confidence: float) -> AppLayout:
    kind = match.group("kind").strip().lower()
    columns = int(match.groupdict().get("columns") or 1)
    if kind in {"horizontal", "row", "rows"}:
        kind = "row"
    elif kind in {"vertical", "column", "columns"}:
        kind = "column"
    return AppLayout(kind=kind, columns=columns, source=source, confidence=confidence)


def _app_size(match: re.Match[str], source: str, confidence: float) -> AppSize:
    return AppSize(width=int(match.group("width")), height=int(match.group("height")), source=source, confidence=confidence)


def _app_file_attach(match: re.Match[str], source: str, confidence: float) -> AppFileAttach:
    return AppFileAttach(
        path=parse_text_value(match.group("path")),
        x=parse_text_value(match.group("x")),
        y=parse_text_value(match.group("y")),
        z=parse_text_value(match.group("z")),
        source=source,
        confidence=confidence,
    )

def _named_file_attach(match: re.Match[str], source: str, confidence: float) -> AppFileAttach:
    return AppFileAttach(
        file_name=match.group("name").strip(),
        path=_strip_optional_quotes(match.group("path")),
        x=0,
        y=0,
        z=0,
        source=source,
        confidence=confidence,
    )


def _attach_file_at_position(match: re.Match[str], source: str, confidence: float) -> CreateObject:
    path = _strip_optional_quotes(match.group("path").strip())
    name = Path(path).stem
    return CreateObject(
        kind="image",
        name=name,
        x=int(match.group("x")),
        y=int(match.group("y")),
        z=int(match.group("z")),
        path=path,
        source=source,
        confidence=confidence,
    )


def _app_loading_screen(match: re.Match[str], source: str, confidence: float) -> AppLoadingScreen:
    return AppLoadingScreen(
        image_path=_strip_optional_quotes(match.group("image")),
        audio_path=_strip_optional_quotes(match.group("audio")),
        source=source,
        confidence=confidence,
    )


def _default_app_loading_screen(match: re.Match[str], source: str, confidence: float) -> AppLoadingScreen:
    return AppLoadingScreen(image_path="", audio_path="", source=source, confidence=confidence)


def _create_image(match: re.Match[str], source: str, confidence: float) -> CreateObject:
    return CreateObject(
        kind="image",
        name=_parse_name(match.group("name")),
        x=int(match.group("x")),
        y=int(match.group("y")),
        z=int(match.group("z")),
        path=_strip_optional_quotes(match.group("path")),
        source=source,
        confidence=confidence,
    )


def _create_player(match: re.Match[str], source: str, confidence: float) -> CreateObject:
    return CreateObject(
        kind="player",
        name=_parse_name(match.group("name")),
        x=int(match.group("x")),
        y=int(match.group("y")),
        z=int(match.group("z")),
        source=source,
        confidence=confidence,
    )


def _create_button(match: re.Match[str], source: str, confidence: float) -> CreateObject:
    return CreateObject(
        kind="button",
        name=_parse_name(match.group("name")),
        x=int(match.groupdict().get("x") or 0),
        y=int(match.groupdict().get("y") or 0),
        z=int(match.groupdict().get("z") or 0),
        text=match.group("text").strip(),
        source=source,
        confidence=confidence,
    )


def _create_text_object(match: re.Match[str], source: str, confidence: float) -> CreateObject:
    return CreateObject(
        kind="text",
        name=_parse_name(match.group("name")),
        x=int(match.group("x")),
        y=int(match.group("y")),
        z=int(match.group("z") or 0),
        text=match.group("text").strip(),
        source=source,
        confidence=confidence,
    )


def _create_generic_object(match: re.Match[str], source: str, confidence: float) -> CreateObject:
    return CreateObject(
        kind=match.group("kind").strip().lower(),
        name=_parse_name(match.group("name")),
        x=int(match.group("x")),
        y=int(match.group("y")),
        z=int(match.group("z") or 0),
        source=source,
        confidence=confidence,
    )


def _create_described_object(match: re.Match[str], source: str, confidence: float) -> CreateObject:
    properties: dict[str, Expression] = {}
    color = match.groupdict().get("color")
    if color:
        properties["color"] = color.strip().lower()
    width = match.groupdict().get("width")
    height = match.groupdict().get("height")
    if width and height:
        properties["width"] = int(width)
        properties["height"] = int(height)
    return CreateObject(
        kind=match.group("kind").strip().lower(),
        name=_parse_name(match.group("name")),
        x=int(match.groupdict().get("x") or match.groupdict().get("x2") or 0),
        y=int(match.groupdict().get("y") or match.groupdict().get("y2") or 0),
        z=int(match.groupdict().get("z") or match.groupdict().get("z2") or 0),
        properties=properties,
        source=source,
        confidence=confidence,
    )


def _move_object(match: re.Match[str], source: str, confidence: float) -> MoveObject:
    return MoveObject(
        name=_parse_name(match.group("name")),
        direction=match.group("direction").lower(),
        amount=int(match.group("amount")),
        source=source,
        confidence=confidence,
    )


def _place_object(match: re.Match[str], source: str, confidence: float) -> PlaceObject:
    return PlaceObject(
        name=_parse_name(match.group("name")),
        x=int(match.group("x")),
        y=int(match.group("y")),
        z=int(match.groupdict().get("z") or 0),
        source=source,
        confidence=confidence,
    )


def _resize_object(match: re.Match[str], source: str, confidence: float) -> ResizeObject:
    return ResizeObject(
        name=_parse_name(match.group("name")),
        width=int(match.group("width")),
        height=int(match.group("height")),
        source=source,
        confidence=confidence,
    )


def _show_text(match: re.Match[str], source: str, confidence: float) -> ShowText:
    return ShowText(text=match.group("value").strip(), source=source, confidence=confidence)


def _set_property(match: re.Match[str], source: str, confidence: float) -> SetProperty:
    return SetProperty(
        object_name=_parse_name(match.group("object")),
        property_name=_parse_name(match.group("property")),
        value=_parse_property_value(match.group("value")),
        source=source,
        confidence=confidence,
    )


def _parse_property_value(text: str) -> Expression:
    value = text.strip()
    if (value.startswith("[") and value.endswith("]")) or (value.startswith("{") and value.endswith("}")):
        return parse_atom(value)
    if _looks_like_expression(value):
        return parse_expression(value)
    if _is_quoted(value) or _looks_like_access(value) or value.lower() in {"true", "false", "yes", "no", "off", "on"} or re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
        return parse_atom(value)
    return value


def _animate_object(match: re.Match[str], source: str, confidence: float) -> AnimateObject:
    return AnimateObject(
        name=_parse_name(match.group("name")),
        direction=match.group("direction").lower(),
        amount=int(match.group("amount")),
        milliseconds=int(match.group("milliseconds")),
        source=source,
        confidence=confidence,
    )


def _play_sound(match: re.Match[str], source: str, confidence: float) -> PlaySound:
    return PlaySound(name=match.group("value").strip(), source=source, confidence=confidence)


def _stop_sound(_match: re.Match[str], source: str, confidence: float) -> StopSound:
    return StopSound(source=source, confidence=confidence)


def _sound_volume(match: re.Match[str], source: str, confidence: float) -> SetSoundVolume:
    volume = max(0, min(100, int(match.group("volume"))))
    return SetSoundVolume(volume=volume, source=source, confidence=confidence)


def _create_list(match: re.Match[str], source: str, confidence: float) -> CreateList:
    raw_items = match.group("items").strip()
    items = [_parse_property_value(item.strip()) for item in _split_items(raw_items) if item.strip()] if raw_items else []
    return CreateList(name=_parse_name(match.group("name")), items=items, source=source, confidence=confidence)


def _create_map(match: re.Match[str], source: str, confidence: float) -> CreateMap:
    return CreateMap(name=_parse_name(match.group("name")), items=_parse_map_items(match.group("items")), source=source, confidence=confidence)


def _define_blueprint(match: re.Match[str], source: str, confidence: float) -> DefineBlueprint:
    parent = (match.group("parent") or "").strip()
    return DefineBlueprint(
        name=_parse_name(match.group("name")),
        items=_parse_map_items(match.group("items")),
        inherits=parent,
        source=source,
        confidence=confidence,
    )


def _create_from_blueprint(match: re.Match[str], source: str, confidence: float) -> CreateFromBlueprint:
    return CreateFromBlueprint(
        blueprint_name=_parse_name(match.group("blueprint")),
        name=_parse_name(match.group("name")),
        items=_parse_map_items(match.group("items") or ""),
        source=source,
        confidence=confidence,
    )


def _parse_map_items(raw: str | None) -> dict[str, Expression]:
    raw_items = (raw or "").strip()
    items: dict[str, Expression] = {}
    if raw_items:
        for item in _split_items(raw_items):
            key, separator, value = item.partition(":")
            if not separator:
                key, separator, value = item.partition("=")
            if not separator:
                raise AngisSyntaxError("Dictionary items must look like key: value.")
            items[_parse_map_key(key.strip())] = _parse_property_value(value.strip())
    return items


def _parse_map_key(key: str) -> str:
    if _is_quoted(key):
        return key[1:-1]
    return _parse_name(key)


def _add_to_list(match: re.Match[str], source: str, confidence: float) -> AddToList:
    return AddToList(
        name=_parse_name(match.group("name")),
        item=_parse_property_value(match.group("item")),
        source=source,
        confidence=confidence,
    )


def _remove_from_list(match: re.Match[str], source: str, confidence: float) -> RemoveFromList:
    return RemoveFromList(
        name=_parse_name(match.group("name")),
        item=_parse_property_value(match.group("item")),
        source=source,
        confidence=confidence,
    )


def _remove_property(match: re.Match[str], source: str, confidence: float) -> RemoveProperty:
    return RemoveProperty(
        object_name=_parse_name(match.group("object")),
        property_name=_parse_name(match.group("property")),
        source=source,
        confidence=confidence,
    )


def _save_state(match: re.Match[str], source: str, confidence: float) -> SaveState:
    return SaveState(path=match.group("path").strip(), source=source, confidence=confidence)


def _load_state(match: re.Match[str], source: str, confidence: float) -> LoadState:
    return LoadState(path=match.group("path").strip(), source=source, confidence=confidence)


def _fetch_url(match: re.Match[str], source: str, confidence: float) -> FetchUrl:
    return FetchUrl(
        url=match.group("url").strip(),
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _http_request(match: re.Match[str], source: str, confidence: float) -> HttpRequest:
    return HttpRequest(
        method=match.group("method").upper(),
        url=match.group("url").strip(),
        body=_strip_optional_quotes(match.group("body")) if match.groupdict().get("body") else "",
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _debug_state(match: re.Match[str], source: str, confidence: float) -> DebugState:
    return DebugState(target=match.group("target").strip().lower(), source=source, confidence=confidence)


def _export_app(match: re.Match[str], source: str, confidence: float) -> ExportApp:
    return ExportApp(path=match.group("path").strip(), source=source, confidence=confidence)


def _package_app(match: re.Match[str], source: str, confidence: float) -> PackageApp:
    return PackageApp(path=match.group("path").strip(), source=source, confidence=confidence)


def _breakpoint(match: re.Match[str], source: str, confidence: float) -> DebugBreakpoint:
    return DebugBreakpoint(label=(match.group("label") or "breakpoint").strip(), source=source, confidence=confidence)


def _open_database(match: re.Match[str], source: str, confidence: float) -> OpenDatabase:
    return OpenDatabase(path=match.group("path").strip(), name=_parse_name(match.group("name")), source=source, confidence=confidence)


def _execute_sql(match: re.Match[str], source: str, confidence: float) -> ExecuteSql:
    return ExecuteSql(
        database=_parse_name(match.group("database")),
        sql=_strip_optional_quotes(match.group("sql")),
        name=_parse_name(match.group("name")) if match.groupdict().get("name") else "",
        source=source,
        confidence=confidence,
    )


def _play_video(match: re.Match[str], source: str, confidence: float) -> PlayVideo:
    return PlayVideo(
        path=match.group("path").strip(),
        x=int(match.group("x")),
        y=int(match.group("y")),
        width=int(match.groupdict().get("width") or 320),
        height=int(match.groupdict().get("height") or 180),
        source=source,
        confidence=confidence,
    )


def _flappy_start(_match: re.Match[str], source: str, confidence: float) -> GameStart:
    return GameStart(name="Flappy Bird", source=source, confidence=confidence)


def _game_rule(match: re.Match[str], source: str, confidence: float) -> GameRule:
    return GameRule(text=parse_text_value(match.group("value")), source=source, confidence=confidence)


def _file_attach(match: re.Match[str], source: str, confidence: float) -> FileAttach:
    return FileAttach(path=parse_text_value(match.group("value")), source=source, confidence=confidence)


def _run_file(match: re.Match[str], source: str, confidence: float) -> RunFile:
    return RunFile(path=parse_text_value(match.group("value")).strip('"').strip("'"), source=source, confidence=confidence)


def _import_module(match: re.Match[str], source: str, confidence: float) -> ImportModule:
    return ImportModule(name=match.group("name").strip().lower(), source=source, confidence=confidence)


def _use_stdlib_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    raw_args = match.groupdict().get("args") or ""
    module = match.group("module").strip().lower()
    action = match.group("action").strip().lower().replace(" ", "_")
    args: dict[str, Expression] = {}
    if raw_args:
        for item in _split_items(raw_args):
            key, separator, value = item.partition(":")
            if not separator:
                key, separator, value = item.partition("=")
            if not separator:
                raise AngisSyntaxError("Standard library arguments must look like key: value.")
            arg_name = _parse_name(key.strip())
            if module == "json" and action == "parse" and arg_name == "text":
                args[arg_name] = _strip_optional_quotes(value.strip())
            else:
                args[arg_name] = parse_text_value(value.strip())
    return UseStdLibAction(
        module=module,
        action=action,
        args=args,
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _natural_stdlib_action(module: str, action: str, arg_name: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module=module,
            action=action,
            args={arg_name: parse_text_value(match.group("value"))},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _stdlib_simple_action(module: str, action: str, key: str = "value") -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        grp = key if match.groupdict().get(key) is not None else next(v for v in ("value", "values", "text", "path") if match.groupdict().get(v))
        return UseStdLibAction(
            module=module,
            action=action,
            args={key: parse_text_value(match.group(grp))},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _split_text_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="text",
        action="split",
        args={"text": parse_text_value(match.group("text")), "by": parse_text_value(match.group("by"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _join_text_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="text",
        action="join",
        args={"values": parse_text_value(match.group("values")), "by": parse_text_value(match.group("by"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _replace_text_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="text",
        action="replace",
        args={
            "text": parse_text_value(match.group("text")),
            "old": parse_text_value(match.group("old")),
            "new": parse_text_value(match.group("new")),
        },
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _list_values_action(action: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module="list",
            action=action,
            args={"values": parse_text_value(match.group("values"))},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _random_choice_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="random",
        action="choice",
        args={"from": parse_text_value(match.group("values"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _map_get_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="map",
        action="get",
        args={"value": parse_text_value(match.group("value")), "key": parse_text_value(match.group("key"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _map_values_action(action: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module="map",
            action=action,
            args={"value": parse_text_value(match.group("value"))},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _map_merge_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="map",
        action="merge",
        args={"value": parse_text_value(match.group("value")), "other": parse_text_value(match.group("other"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _file_read_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="file",
        action="read",
        args={"path": _strip_optional_quotes(match.group("path"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _file_write_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="file",
        action="write",
        args={"path": _strip_optional_quotes(match.group("path")), "text": parse_text_value(match.group("text"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _file_info_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="file",
        action="info",
        args={"path": _strip_optional_quotes(match.group("path"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _csv_read_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="csv",
        action="read",
        args={"path": _strip_optional_quotes(match.group("path"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _data_count_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="data",
        action="count",
        args={"rows": parse_text_value(match.group("rows"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _data_column_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="data",
        action="column",
        args={"rows": parse_text_value(match.group("rows")), "column": parse_text_value(match.group("column"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _data_filter_equals_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="data",
        action="filter_equals",
        args={
            "rows": parse_text_value(match.group("rows")),
            "column": parse_text_value(match.group("column")),
            "value": parse_text_value(match.group("value")),
        },
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _read_input(match: re.Match[str], source: str, confidence: float) -> ReadInput:
    prompt_text = match.groupdict().get("prompt", "").strip()
    return ReadInput(prompt=prompt_text if prompt_text else "", source=source, confidence=confidence)


def _raise_error(match: re.Match[str], source: str, confidence: float) -> RaiseError:
    return RaiseError(message=parse_text_value(match.group("message")), source=source, confidence=confidence)


def _assert_true(match: re.Match[str], source: str, confidence: float) -> AssertTrue:
    return AssertTrue(
        condition_text=match.group("condition").strip(),
        message=parse_text_value(match.group("message")),
        source=source, confidence=confidence,
    )


def _json_parse_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="json",
        action="parse",
        args={"text": _strip_optional_quotes(match.group("text"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _json_stringify_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="json",
        action="stringify",
        args={"value": parse_text_value(match.group("value"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _math_one_arg_action(action: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module="math",
            action=action,
            args={"value": parse_text_value(match.group("value"))},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _math_power_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="math",
        action="power",
        args={"base": parse_text_value(match.group("base")), "exponent": parse_text_value(match.group("exponent"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _math_clamp_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="math",
        action="clamp",
        args={
            "value": parse_text_value(match.group("value")),
            "min": parse_text_value(match.group("min")),
            "max": parse_text_value(match.group("max")),
        },
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _random_integer_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="random",
        action="integer",
        args={"min": parse_text_value(match.group("min")), "max": parse_text_value(match.group("max"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _path_one_arg_action(action: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module="path",
            action=action,
            args={"path": _strip_optional_quotes(match.group("path"))},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _path_join_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="path",
        action="join",
        args={"left": _strip_optional_quotes(match.group("left")), "right": _strip_optional_quotes(match.group("right"))},
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _math_two_arg_action(action: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module="math",
            action=action,
            args={
                "left": parse_text_value(match.group("left")),
                "right": parse_text_value(match.group("right")),
            },
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )
    return factory


def _list_at_action(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
    return UseStdLibAction(
        module="list",
        action="at",
        args={
            "values": parse_text_value(match.group("values")),
            "index": parse_text_value(match.group("index")),
        },
        name=_parse_name(match.group("name")),
        source=source,
        confidence=confidence,
    )


def _time_action(action: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module="time",
            action=action,
            args={},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _time_days_action(action: str) -> InstructionFactory:
    def factory(match: re.Match[str], source: str, confidence: float) -> UseStdLibAction:
        return UseStdLibAction(
            module="time",
            action=action,
            args={"days": parse_text_value(match.group("days"))},
            name=_parse_name(match.group("name")),
            source=source,
            confidence=confidence,
        )

    return factory


def _parse_name(text: str) -> str:
    name = text.strip()
    if not re.fullmatch(r"[^\W\d][\w ]*", name):
        raise AngisSyntaxError(f"Invalid variable name {name!r}.")
    return name


def _is_quoted(value: str) -> bool:
    return (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))


def _strip_optional_quotes(value: str) -> str:
    text = value.strip()
    if _is_quoted(text):
        return text[1:-1]
    return text


def _split_items(text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    depth = 0
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = set(pairs.values())
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            current.append(char)
            quote = char
            continue
        if char in pairs:
            depth += 1
            current.append(char)
            continue
        if char in closers and depth > 0:
            depth -= 1
            current.append(char)
            continue
        if char == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
            continue
        current.append(char)
    item = "".join(current).strip()
    if item:
        items.append(item)
    return items


VALUE = r"(?P<value>.+?)"
NAME = r"(?P<name>[^\W\d]\w*)"
ASSIGN_NAME = r"(?:set|make|let)\s+(?P<name>[^\W\d]\w*)\s+(?:to|equal|=)\s+"
LEFT = r"(?P<left>.+?)"
RIGHT = r"(?P<right>.+?)"


PATTERNS: tuple[IntentPattern, ...] = (
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:current\s+)?(?:time|now|date\s+and\s+time)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        _time_action("now"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:timestamp|seconds\s+since\s+epoch)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        _time_action("timestamp"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:today|today's\s+date|todays\s+date|current\s+date)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        _time_action("today"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:add|put)\s+(?P<days>[+-]?\d+)\s+days?\s+to\s+today\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        _time_days_action("add_days"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:what\s+is\s+)?(?P<days>[+-]?\d+)\s+days?\s+from\s+today\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        _time_days_action("add_days"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:subtract|take)\s+(?P<days>[+-]?\d+)\s+days?\s+from\s+today\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        _time_days_action("subtract_days"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"join\s+path\s+(?P<left>.+?)\s+with\s+(?P<right>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        _path_join_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"split\s+(?P<text>.+?)\s+by\s+(?P<by>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _split_text_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"join\s+(?P<values>.+?)\s+with\s+(?P<by>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _join_text_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"replace\s+(?P<old>.+?)\s+in\s+(?P<text>.+?)\s+with\s+(?P<new>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _replace_text_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"sort\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _list_values_action("sort"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"reverse\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _list_values_action("reverse"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:unique|dedupe|remove\s+duplicates\s+from)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _list_values_action("unique"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:pick|choose|get)\s+(?:a\s+)?random\s+(?:item\s+)?from\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _random_choice_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?P<key>(?!keys\b|values\b|name\b|extension\b|folder\b|parent\b|directory\b|stem\b)[^\W\d]\w*)\s+from\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _map_get_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+keys\s+from\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _map_values_action("keys"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+values\s+from\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _map_values_action("values"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"merge\s+(?P<value>.+?)\s+with\s+(?P<other>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _map_merge_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"read\s+file\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _file_read_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"write\s+(?P<text>.+?)\s+to\s+file\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _file_write_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:info|information)\s+(?:for|about)\s+file\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _file_info_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"read\s+csv\s+file\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _csv_read_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"count\s+rows\s+(?:in\s+)?(?P<rows>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _data_count_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+column\s+(?P<column>[^\W\d]\w*)\s+from\s+(?P<rows>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _data_column_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:keep|filter)\s+(?P<rows>.+?)\s+where\s+(?P<column>[^\W\d]\w*)\s+is\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _data_filter_equals_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:parse|read)\s+json\s+(?P<text>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _json_parse_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:turn|convert|stringify)\s+(?P<value>.+?)\s+(?:into|to|as)\s+json\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _json_stringify_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"round\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.98,
        _math_one_arg_action("round"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"floor\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _math_one_arg_action("floor"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"ceil\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _math_one_arg_action("ceil"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"absolute\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _math_one_arg_action("absolute"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:raise|power)\s+(?P<base>[^\W\d]\w*|[+-]?\d+(?:\.\d+)?)\s+to\s+power\s+(?P<exponent>[^\W\d]\w*|[+-]?\d+(?:\.\d+)?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _math_power_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"clamp\s+(?P<value>.+?)\s+between\s+(?P<min>.+?)\s+and\s+(?P<max>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _math_clamp_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:pick|get|choose)\s+random\s+(?:number|integer)\s+between\s+(?P<min>.+?)\s+and\s+(?P<max>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _random_integer_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:file\s+)?name\s+from\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _path_one_arg_action("name"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:file\s+)?extension\s+from\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _path_one_arg_action("extension"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:folder|parent|directory)\s+from\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _path_one_arg_action("parent"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"get\s+(?:stem|file\s+stem)\s+from\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _path_one_arg_action("stem"),
    ),
    IntentPattern(
        "SET",
        re.compile(rf"{ASSIGN_NAME}(?P<value>.+(?:\+|\-|\*|/|\bplus\b|\badded\s+to\b|\bminus\b|\btimes\b|\bmultiplied\s+by\b|\bdivided\s+by\b|\bover\b).+)", re.I),
        1.0,
        _set,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?uppercase\s+of\s+(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("text", "uppercase", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?lowercase\s+of\s+(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("text", "lowercase", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?trimmed\s+text\s+of\s+(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("text", "trim", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?square\s+root\s+of\s+(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("math", "sqrt", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?absolute\s+(?:value\s+)?of\s+(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("math", "absolute", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?(?:length|count)\s+of\s+(?P<value>(?!.*(?:\+|\-|\*|/|\bplus\b|\badded\s+to\b|\bminus\b|\btimes\b|\bmultiplied\s+by\b|\bdivided\s+by\b|\bover\b)).+)", re.I),
        1.0,
        _natural_stdlib_action("list", "length", "values"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?file\s+name\s+of\s+(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("path", "name", "path"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}(?:the\s+)?file\s+extension\s+of\s+(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("path", "extension", "path"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(rf"{ASSIGN_NAME}file\s+exists\s+(?:at\s+)?(?P<value>.+)", re.I),
        1.0,
        _natural_stdlib_action("file", "exists", "path"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(
            rf"{ASSIGN_NAME}(?P<module>math|random|time|json|file|text|csv|data|list|map|path|capabilities|convert|bitwise|statistics|ai)\s+"
            r"(?P<action>[^\W\d]\w[\w\s]*?)(?:\s+with\s+(?P<args>.+))?",
            re.I,
        ),
        1.0,
        _use_stdlib_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make|turn)\s+(?:the\s+)?uppercase\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "uppercase", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make|turn)\s+(?:the\s+)?lowercase\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "lowercase", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|trim)\s+(?:the\s+)?trimmed\s+text\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "trim", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?square\s+root\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "sqrt", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?absolute\s+(?:value\s+)?of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "absolute", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|count)\s+(?:the\s+)?(?:length|count)\s+of\s+(?P<value>(?!.*(?:\+|\-|\*|/|\bplus\b|\badded\s+to\b|\bminus\b|\btimes\b|\bmultiplied\s+by\b|\bdivided\s+by\b|\bover\b)).+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("list", "length", "values"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|find)\s+(?:the\s+)?file\s+name\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("path", "name", "path"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|find)\s+(?:the\s+)?file\s+extension\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("path", "extension", "path"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check|see)\s+(?:if\s+)?file\s+exists\s+(?:at\s+)?(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("file", "exists", "path"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(
            r"use\s+(?P<module>math|random|time|json|file|text|csv|data|list|map|path|capabilities|convert|bitwise|statistics|socket|ai)\s+(?P<action>[^\W\d]\w[\w\s]*?)"
            r"(?:\s+with\s+(?P<args>.+?))?\s+as\s+(?P<name>[^\W\d]\w*)",
            re.I,
        ),
        1.0,
        _use_stdlib_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(
            r"(?:ask|tell)\s+(?P<module>math|random|time|json|file|text|csv|data|list|map|path|capabilities|convert|bitwise|statistics|socket|ai)\s+to\s+"
            r"(?P<action>[^\W\d]\w[\w\s]*?)(?:\s+with\s+(?P<args>.+?))?\s+as\s+(?P<name>[^\W\d]\w*)",
            re.I,
        ),
        0.99,
        _use_stdlib_action,
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(
            r"(?:get|run)\s+(?P<module>math|random|time|json|file|text|csv|data|list|map|path|capabilities|convert|bitwise|statistics|socket|ai)\s+"
            r"(?P<action>[^\W\d]\w[\w\s]*?)(?:\s+with\s+(?P<args>.+?))?\s+as\s+(?P<name>[^\W\d]\w*)",
            re.I,
        ),
        0.98,
        _use_stdlib_action,
    ),
    IntentPattern("IMPORT", re.compile(r"(?:import|use)\s+(?P<name>[^\W\d]\w[\w.]*)", re.I), 1.0, _import_module),
    IntentPattern(
        "LOADING",
        re.compile(
            r"(?:loading|loding)\s+screen\s+(?:from\s+)?(?:picture|image|pickter)\s+(?P<image>.+?)\s+"
            r"with\s+(?:audio|adieo|sound)\s+(?P<audio>.+?)(?:\s+then\s+open\s+app)?",
            re.I,
        ),
        1.0,
        _app_loading_screen,
    ),
    IntentPattern(
        "LOADING",
        re.compile(r"(?:loading|loding)\s+screen(?:\s+then\s+open\s+app)?", re.I),
        1.0,
        _default_app_loading_screen,
    ),
    IntentPattern(
        "APP_FILE",
        re.compile(
            r"(?:set\s+)?file\s+attach\s+to\s+window\s+at\s+"
            r"(?:\(?\s*)?x\s+(?P<x>[^\W\d]\w*(?:\[[^\]]+\])?|-?\d+)\s+y\s+(?P<y>[^\W\d]\w*(?:\[[^\]]+\])?|-?\d+)\s+z\s+(?P<z>[^\W\d]\w*(?:\[[^\]]+\])?|-?\d+)(?:\s*\))?"
            r"\s+(?:from|using|with)\s+(?:the\s+|a\s+)?file\s+(?:called\s|named\s|at\s)?(?P<path>.+)",
            re.I,
        ),
        1.0,
        _app_file_attach,
    ),
    IntentPattern(
        "CREATE",
        re.compile(
            r"create\s+image\s+named\s+(?P<name>[^\W\d]\w[\w ]*?)\s+at\s+"
            r"x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)\s+z\s+(?P<z>-?\d+)\s+from\s+file\s+(?P<path>.+)",
            re.I,
        ),
        0.99,
        _create_image,
    ),
    IntentPattern(
        "CREATE",
        re.compile(
            r"create\s+image\s+named\s+(?P<name>[^\W\d]\w[\w ]*?)\s+at\s+"
            r"x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)\s+z\s+(?P<z>-?\d+)\s+"
            r"(?:from|using|with)\s+(?:the\s+|a\s+)?file\s+(?:called\s|named\s|at\s)?(?P<path>.+)",
            re.I,
        ),
        0.98,
        _create_image,
    ),
    IntentPattern(
        "CREATE",
        re.compile(
            r"create\s+player\s+named\s+(?P<name>[^\W\d]\w[\w ]*?)\s+at\s+"
            r"x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)\s+z\s+(?P<z>-?\d+)",
            re.I,
        ),
        0.99,
        _create_player,
    ),
    IntentPattern(
        "CREATE",
        re.compile(
            r"create\s+button\s+named\s+(?P<name>[^\W\d]\w[\w ]*?)\s+at\s+"
            r"x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)(?:\s+z\s+(?P<z>-?\d+))?\s+with\s+text\s+(?P<text>.+)",
            re.I,
        ),
        1.0,
        _create_button,
    ),
    IntentPattern(
        "CREATE",
        re.compile(r"create\s+button\s+named\s+(?P<name>[^\W\d]\w[\w ]*?)\s+with\s+text\s+(?P<text>.+)", re.I),
        0.99,
        _create_button,
    ),
    IntentPattern(
        "CREATE",
        re.compile(
            r"create\s+text\s+named\s+(?P<name>[^\W\d]\w[\w ]*?)\s+at\s+"
            r"x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)(?:\s+z\s+(?P<z>-?\d+))?\s+(?:saying|with\s+text)\s+(?P<text>.+)",
            re.I,
        ),
        0.99,
        _create_text_object,
    ),
    IntentPattern(
        "CREATE",
        re.compile(
            r"(?:create|make|draw|put)\s+(?:(?P<color>[^\W\d#][\w#-]*)\s+)?"
            r"(?P<kind>rectangle|rect|box|block|circle|ball|player|enemy|platform|sprite|cube|pyramid|sphere|cylinder|torus|panel)\s+"
            r"named\s+(?P<name>[^\W\d]\w[\w ]*?)\s+(?:at|to)\s+"
            r"(?:\(\s*(?P<x>-?\d+)\s*,\s*(?P<y>-?\d+)(?:\s*,\s*(?P<z>-?\d+))?\s*\)|x\s+(?P<x2>-?\d+)\s+y\s+(?P<y2>-?\d+)(?:\s+z\s+(?P<z2>-?\d+))?)"
            r"(?:\s+size\s+(?P<width>\d+)\s*(?:by|x)\s*(?P<height>\d+))?",
            re.I,
        ),
        1.0,
        _create_described_object,
    ),
    IntentPattern(
        "CREATE",
        re.compile(
            r"create\s+(?P<kind>rectangle|rect|box|block|circle|ball|player|enemy|platform|sprite|cube|pyramid|sphere|cylinder|torus|input|textbox|slider|checkbox|toggle|panel|text|label)\s+named\s+"
            r"(?P<name>[^\W\d]\w[\w ]*?)\s+at\s+x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)(?:\s+z\s+(?P<z>-?\d+))?",
            re.I,
        ),
        0.98,
        _create_generic_object,
    ),
    IntentPattern(
        "MOVE",
        re.compile(r"move\s+(?P<name>[^\W\d]\w[\w ]*?)\s+(?P<direction>forward|backward|left|right|up|down)\s+by\s+(?P<amount>\d+)", re.I),
        0.99,
        _move_object,
    ),
    IntentPattern(
        "PLACE",
        re.compile(
            r"(?:put|place|move|set)\s+(?P<name>[^\W\d]\w[\w ]*?)\s+(?:at|to)\s+"
            r"(?:\(?\s*)?x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)(?:\s+z\s+(?P<z>-?\d+))?(?:\s*\))?",
            re.I,
        ),
        1.0,
        _place_object,
    ),
    IntentPattern(
        "PLACE",
        re.compile(
            r"(?:put|place|move|set)\s+(?P<name>[^\W\d]\w[\w ]*?)\s+(?:at|to)\s+"
            r"\(\s*(?P<x>-?\d+)\s*,\s*(?P<y>-?\d+)(?:\s*,\s*(?P<z>-?\d+))?\s*\)",
            re.I,
        ),
        1.0,
        _place_object,
    ),
    IntentPattern(
        "RESIZE",
        re.compile(
            r"(?:resize|size)\s+(?P<name>[^\W\d]\w[\w ]*?)\s+(?:to\s+)?(?P<width>\d+)\s*(?:by|x)\s*(?P<height>\d+)",
            re.I,
        ),
        1.0,
        _resize_object,
    ),
    IntentPattern(
        "RESIZE",
        re.compile(
            r"set\s+(?P<name>[^\W\d]\w[\w ]*?)\s+size\s+to\s+(?P<width>\d+)\s*(?:by|x)\s*(?P<height>\d+)",
            re.I,
        ),
        1.0,
        _resize_object,
    ),
    IntentPattern("SHOW_TEXT", re.compile(rf"show\s+text\s+{VALUE}", re.I), 1.0, _show_text),
    IntentPattern(
        "PROPERTY",
        re.compile(r"set\s+(?P<object>[^\W\d]\w[\w ]*?)\s+(?P<property>[^\W\d]\w*)\s+to\s+(?P<value>.+)", re.I),
        0.99,
        _set_property,
    ),
    IntentPattern(
        "ANIMATE",
        re.compile(
            r"animate\s+(?P<name>[^\W\d]\w[\w ]*?)\s+(?P<direction>forward|backward|left|right|up|down)\s+by\s+"
            r"(?P<amount>\d+)\s+every\s+(?P<milliseconds>\d+)\s+milliseconds",
            re.I,
        ),
        0.99,
        _animate_object,
    ),
    IntentPattern("SOUND", re.compile(rf"play\s+sound\s+{VALUE}", re.I), 0.99, _play_sound),
    IntentPattern("SOUND", re.compile(r"stop\s+(?:sound|audio|music)", re.I), 0.99, _stop_sound),
    IntentPattern("SOUND", re.compile(r"set\s+(?:sound|audio|music)\s+volume\s+to\s+(?P<volume>\d{1,3})", re.I), 1.0, _sound_volume),
    IntentPattern(
        "LIST",
        re.compile(r"create\s+list\s+named\s+(?P<name>[^\W\d]\w*)(?:\s+with\s+(?P<items>.*))?", re.I),
        0.99,
        _create_list,
    ),
    IntentPattern(
        "MAP",
        re.compile(r"create\s+(?:dictionary|map)\s+named\s+(?P<name>[^\W\d]\w*)(?:\s+with\s+(?P<items>.*))?", re.I),
        0.99,
        _create_map,
    ),
    IntentPattern(
        "BLUEPRINT",
        re.compile(r"(?:define\s+)?(?:blueprint|type|class)\s+(?P<name>[^\W\d]\w*)(?:\s+(?:inherits|extends|is\s+a)\s+(?P<parent>[^\W\d]\w*))?(?:\s+with\s+(?P<items>.*))?", re.I),
        0.99,
        _define_blueprint,
    ),
    IntentPattern(
        "CREATE_FROM_BLUEPRINT",
        re.compile(
            r"create\s+(?P<blueprint>(?!dictionary\b|map\b|list\b)[^\W\d]\w*)\s+named\s+(?P<name>[^\W\d]\w*)(?:\s+with\s+(?P<items>.*))?",
            re.I,
        ),
        0.99,
        _create_from_blueprint,
    ),
    IntentPattern(
        "LIST_ADD",
        re.compile(r"add\s+(?P<item>.+)\s+to\s+list\s+(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        _add_to_list,
    ),
    IntentPattern(
        "LIST_ADD",
        re.compile(r"(?:put|place|store)\s+(?P<item>.+)\s+(?:in|inside|into)\s+(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        _add_to_list,
    ),
    IntentPattern(
        "LIST_REMOVE",
        re.compile(r"(?:remove|delete)\s+(?!field\b|property\b)(?P<item>.+)\s+from\s+(?:list\s+)?(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        _remove_from_list,
    ),
    IntentPattern(
        "LIST_REMOVE",
        re.compile(r"(?:take|pull)\s+(?P<item>.+)\s+out\s+of\s+(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        _remove_from_list,
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"add\s+(?P<value>.+?)\s+to\s+(?P<property>[^\W\d]\w*)\s+(?:of|on|for)\s+(?P<object>[^\W\d]\w[\w ]*?)", re.I),
        1.0,
        _change_property("+"),
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"(?:increase|raise)\s+(?P<property>[^\W\d]\w*)\s+(?:of|on|for)\s+(?P<object>[^\W\d]\w[\w ]*?)\s+by\s+(?P<value>.+)", re.I),
        1.0,
        _change_property("+"),
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"(?:subtract|take)\s+(?P<value>.+?)\s+from\s+(?P<property>[^\W\d]\w*)\s+(?:of|on|for)\s+(?P<object>[^\W\d]\w[\w ]*?)", re.I),
        1.0,
        _change_property("-"),
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"(?:decrease|lower|reduce)\s+(?P<property>[^\W\d]\w*)\s+(?:of|on|for)\s+(?P<object>[^\W\d]\w[\w ]*?)\s+by\s+(?P<value>.+)", re.I),
        1.0,
        _change_property("-"),
    ),
    IntentPattern(
        "SET_ACCESS",
        re.compile(r"add\s+(?P<value>.+?)\s+to\s+(?:item|index)\s+(?P<index>[+-]?\d+)\s+of\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _change_item("+"),
    ),
    IntentPattern(
        "SET_ACCESS",
        re.compile(r"(?:subtract|take)\s+(?P<value>.+?)\s+from\s+(?:item|index)\s+(?P<index>[+-]?\d+)\s+of\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _change_item("-"),
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"make\s+(?P<object>[^\W\d]\w[\w ]*?)\s+have\s+(?P<property>[^\W\d]\w*)\s+(?P<value>.+)", re.I),
        0.98,
        _set_property,
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"give\s+(?P<object>[^\W\d]\w[\w ]*?)\s+(?P<property>(?!with\b|to\b|of\b|on\b|for\b)[^\W\d]\w*)\s+(?P<value>(?!to\b)[^,]+)", re.I),
        0.98,
        _set_property,
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"set\s+(?P<property>[^\W\d]\w*)\s+(?:of|on|for)\s+(?P<object>[^\W\d]\w[\w ]*?)\s+to\s+(?P<value>.+)", re.I),
        1.0,
        _set_property,
    ),
    IntentPattern(
        "PROPERTY_REMOVE",
        re.compile(r"(?:remove|delete)\s+(?:property|field)\s+(?P<property>[^\W\d]\w*)\s+from\s+(?P<object>[^\W\d]\w[\w ]*?)", re.I),
        0.99,
        _remove_property,
    ),
    IntentPattern(
        "PROPERTY_REMOVE",
        re.compile(r"(?:clear|erase)\s+(?P<object>[^\W\d]\w[\w ]*?)\s+(?P<property>[^\W\d]\w*)", re.I),
        0.98,
        _remove_property,
    ),
    IntentPattern("DEBUG", re.compile(r"debug\s+(?P<target>variables|lists|maps|app|imports|capabilities|all)", re.I), 0.99, _debug_state),
    IntentPattern("BREAKPOINT", re.compile(r"breakpoint(?:\s+(?P<label>.+))?", re.I), 0.99, _breakpoint),
    IntentPattern("EXPORT", re.compile(r"export\s+app\s+to\s+file\s+(?P<path>.+)", re.I), 0.99, _export_app),
    IntentPattern("PACKAGE", re.compile(r"package\s+app\s+to\s+folder\s+(?P<path>.+)", re.I), 0.99, _package_app),
    IntentPattern("DATABASE", re.compile(r"open\s+database\s+file\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I), 0.99, _open_database),
    IntentPattern(
        "SQL",
        re.compile(r"(?:run|execute)\s+sql\s+(?P<sql>.+?)\s+on\s+(?P<database>[^\W\d]\w*)(?:\s+as\s+(?P<name>[^\W\d]\w*))?", re.I),
        0.99,
        _execute_sql,
    ),
    IntentPattern(
        "VIDEO",
        re.compile(
            r"play\s+video\s+(?P<path>.+?)\s+at\s+x\s+(?P<x>-?\d+)\s+y\s+(?P<y>-?\d+)"
            r"(?:\s+size\s+(?P<width>\d+)\s*(?:by|x)\s*(?P<height>\d+))?",
            re.I,
        ),
        0.99,
        _play_video,
    ),
    IntentPattern("SAVE_STATE", re.compile(r"save\s+state\s+to\s+file\s+(?P<path>.+)", re.I), 0.99, _save_state),
    IntentPattern("LOAD_STATE", re.compile(r"load\s+state\s+from\s+file\s+(?P<path>.+)", re.I), 0.99, _load_state),
    IntentPattern(
        "FETCH",
        re.compile(r"fetch\s+(?P<url>https?://\S+)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        _fetch_url,
    ),
    IntentPattern(
        "HTTP",
        re.compile(
            r"http\s+(?P<method>get|post|put|delete)\s+(?P<url>https?://\S+)"
            r"(?:\s+with\s+body\s+(?P<body>.+?))?\s+as\s+(?P<name>[^\W\d]\w*)",
            re.I,
        ),
        0.99,
        _http_request,
    ),
    IntentPattern(
        "APP_FILE",
        re.compile(
            r"attach\s+file\s+(?P<path>.+?)\s+to\s+window\s+at\s+"
            r"(?:\(?\s*)?x\s+(?P<x>[^\W\d]\w*(?:\[[^\]]+\])?|-?\d+)\s+y\s+(?P<y>[^\W\d]\w*(?:\[[^\]]+\])?|-?\d+)\s+z\s+(?P<z>[^\W\d]\w*(?:\[[^\]]+\])?|-?\d+)(?:\s*\))?",
            re.I,
        ),
        1.0,
        _app_file_attach,
    ),
    IntentPattern(
        "APP_FILE",
        re.compile(
            r"(?:attach\s+(?:file\s+)?|add\s+file\s+)(?P<path>.+?)\s+(?:named|as|called)\s+(?P<name>[^\W\d]\w*)",
            re.I,
        ),
        0.995,
        _named_file_attach,
    ),
    IntentPattern("FILE", re.compile(rf"(?:attach\s+file|locate\s+file|find\s+file)\s+(?:at\s+)?{VALUE}", re.I), 0.99, _file_attach),
    IntentPattern("FILE", re.compile(rf"file\s+(?:at|is)\s+{VALUE}", re.I), 0.96, _file_attach),
    IntentPattern(
        "APP_FILE",
        re.compile(
            r"(?:attach\s+file|locate\s+file|find\s+file)\s+(?:at\s+)?(?P<path>.+?)\s+"
            r"(?:at\s+)?(?:position|pos|coordinits|coordinates|location|loc)\s*"
            r"\(?\s*(?P<x>-?\d+)\s*[-,\s]\s*(?P<y>-?\d+)\s*[-,\s]\s*(?P<z>-?\d+)\s*\)?",
            re.I,
        ),
        0.995,
        _attach_file_at_position,
    ),
    IntentPattern("RUN_FILE", re.compile(rf"(?:call|run)\s+(?:file\s+)?(?P<value>[\"'].+?[\"']|[^\s]+\.\w+)", re.I), 0.99, _run_file),
    IntentPattern("GAME", re.compile(r"(?:make|create|build)\s+(?:a\s+)?(?:flappy\s+)?bird(?:\s+game)?", re.I), 0.98, _flappy_start),
    IntentPattern("GAME", re.compile(r"(?:put\s+)?bird\s+on\s+screen", re.I), 0.97, _flappy_start),
    IntentPattern("GAME_RULE", re.compile(r"(?P<value>when\s+(?:the\s+)?(?:screen\s+is\s+)?click(?:ed)?\s*,?\s+(?:the\s+)?bird\s+(?:goes|moves)\s+up)", re.I), 0.95, _game_rule),
    IntentPattern("GAME_RULE", re.compile(r"(?P<value>(?:the\s+)?bird\s+falls\s+down)", re.I), 0.95, _game_rule),
    IntentPattern("GAME_RULE", re.compile(r"(?P<value>add\s+obstacles)", re.I), 0.95, _game_rule),
    IntentPattern("GAME_RULE", re.compile(r"(?P<value>if\s+(?:the\s+)?bird\s+hits\s+(?:an\s+)?obstacle\s*,?\s+(?:end|stop)\s+(?:the\s+)?game)", re.I), 0.94, _game_rule),
    IntentPattern("APP", re.compile(rf"(?:app|window)\s+{VALUE}", re.I), 0.99, _app_start),
    IntentPattern(
        "APP_SIZE",
        re.compile(r"(?:set\s+)?window\s+size\s+(?:to\s+)?(?P<width>\d+)\s*(?:by|x)\s*(?P<height>\d+)", re.I),
        1.0,
        _app_size,
    ),
    IntentPattern("APP_SCENE", re.compile(rf"scene\s+{VALUE}", re.I), 0.99, _app_scene),
    IntentPattern("APP_SCENE", re.compile(rf"(?:make\s+)?(?:it\s+)?(?:a\s+)?(?P<value>lobby|canvas|2d\s+screen|2d\s+world|true\s+3d|3d\s+render|3d\s+world|three\s+d\s+world)", re.I), 0.96, _app_scene),
    IntentPattern(
        "APP_LAYOUT",
        re.compile(r"(?:layout|set\s+layout\s+to|use)\s+(?P<kind>grid)(?:\s+(?:with\s+)?(?P<columns>\d+)\s+columns?)?", re.I),
        0.99,
        _app_layout,
    ),
    IntentPattern(
        "APP_LAYOUT",
        re.compile(r"(?:layout|set\s+layout\s+to|use)\s+(?P<kind>vertical|horizontal|row|column|rows|columns)", re.I),
        0.98,
        _app_layout,
    ),
    IntentPattern("APP_TEXT", re.compile(rf"(?:text|label)\s+{VALUE}", re.I), 0.98, _app_text),
    IntentPattern("APP_BUTTON", re.compile(rf"button\s+{VALUE}", re.I), 0.98, _app_button),
    IntentPattern("PRINT", re.compile(rf"(?:say|print|show|display)\s+{VALUE}", re.I), 0.99, _print),
    IntentPattern("PRINT", re.compile(rf"tell\s+me\s+{VALUE}", re.I), 0.96, _print),
    IntentPattern(
        "SET_ACCESS",
        re.compile(r"set\s+(?:item|index)\s+(?P<index>[+-]?\d+)\s+of\s+(?P<name>[^\W\d]\w*)\s+to\s+(?P<value>.+)", re.I),
        1.0,
        _set_item_of,
    ),
    IntentPattern("SET_ACCESS", re.compile(r"set\s+(?P<target>[^\W\d]\w*[.\[][\w.\[\]]*)\s+to\s+(?P<value>.+)", re.I), 1.0, _set_access),
    IntentPattern("SET", re.compile(rf"set\s+{NAME}\s+to\s+{VALUE}", re.I), 0.99, _set),
    IntentPattern("SET", re.compile(rf"make\s+{NAME}\s+equal\s+{VALUE}", re.I), 0.97, _set),
    IntentPattern("SET", re.compile(rf"{NAME}\s+is\s+{VALUE}", re.I), 0.93, _set),
    IntentPattern("SET", re.compile(rf"let\s+{NAME}\s*=\s*{VALUE}", re.I), 0.99, _set),
    IntentPattern("SET", re.compile(rf"store\s+{VALUE}\s+as\s+{NAME}", re.I), 0.98, _set),
    IntentPattern("ADD_TO", re.compile(rf"add\s+{VALUE}\s+to\s+{NAME}", re.I), 0.99, _add_to_var),
    IntentPattern("ADD_TO", re.compile(rf"increase\s+{NAME}\s+by\s+{VALUE}", re.I), 0.98, _add_to_var),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:subtract|take)\s+(?P<value>.+?)\s+from\s+{NAME}", re.I), 1.0, _update_var("-")),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:decrease|lower|reduce)\s+{NAME}\s+by\s+(?P<value>.+)", re.I), 1.0, _update_var("-")),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:multiply|times)\s+{NAME}\s+by\s+(?P<value>.+)", re.I), 1.0, _update_var("*")),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:double)\s+{NAME}", re.I), 1.0, _update_var("*", 2)),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:divide)\s+{NAME}\s+by\s+(?P<value>.+)", re.I), 1.0, _update_var("/")),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:halve|cut)\s+{NAME}\s+(?:in\s+half|by\s+half)", re.I), 1.0, _update_var("/", 2)),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:increment|inc)\s+{NAME}(?:\s+by\s+1)?", re.I), 1.0, _update_var("+", 1)),
    IntentPattern("UPDATE_VAR", re.compile(rf"(?:decrement|dec)\s+{NAME}(?:\s+by\s+1)?", re.I), 1.0, _update_var("-", 1)),
    IntentPattern("ADD", re.compile(rf"add\s+{LEFT}\s+and\s+{RIGHT}", re.I), 0.99, _math(Add)),
    IntentPattern("ADD", re.compile(rf"what\s+is\s+{LEFT}\s+plus\s+{RIGHT}", re.I), 0.97, _math(Add)),
    IntentPattern("ADD", re.compile(rf"calculate\s+{LEFT}\s*\+\s*{RIGHT}", re.I), 0.98, _math(Add)),
    IntentPattern("ADD", re.compile(rf"give\s+me\s+{LEFT}\s+added\s+to\s+{RIGHT}", re.I), 0.95, _math(Add)),
    IntentPattern("SUBTRACT", re.compile(rf"subtract\s+{RIGHT}\s+from\s+{LEFT}", re.I), 0.98, _math(Subtract)),
    IntentPattern("SUBTRACT", re.compile(rf"what\s+is\s+{LEFT}\s+minus\s+{RIGHT}", re.I), 0.97, _math(Subtract)),
    IntentPattern("SUBTRACT", re.compile(rf"calculate\s+{LEFT}\s*-\s*{RIGHT}", re.I), 0.98, _math(Subtract)),
    IntentPattern("MULTIPLY", re.compile(rf"multiply\s+{LEFT}\s+and\s+{RIGHT}", re.I), 0.99, _math(Multiply)),
    IntentPattern("MULTIPLY", re.compile(rf"what\s+is\s+{LEFT}\s+times\s+{RIGHT}", re.I), 0.97, _math(Multiply)),
    IntentPattern("MULTIPLY", re.compile(rf"calculate\s+{LEFT}\s*\*\s*{RIGHT}", re.I), 0.98, _math(Multiply)),
    IntentPattern("MULTIPLY", re.compile(rf"calculate\s+{LEFT}\s*=\s*{RIGHT}", re.I), 0.80, _math(Multiply)),
    IntentPattern("DIVIDE", re.compile(rf"divide\s+{LEFT}\s+by\s+{RIGHT}", re.I), 0.99, _math(Divide)),
    IntentPattern("DIVIDE", re.compile(rf"what\s+is\s+{LEFT}\s+divided\s+by\s+{RIGHT}", re.I), 0.97, _math(Divide)),
    IntentPattern("DIVIDE", re.compile(rf"calculate\s+{LEFT}\s*/\s*{RIGHT}", re.I), 0.98, _math(Divide)),
    # --- User input ---
    IntentPattern(
        "READ_INPUT",
        re.compile(r"(?:ask|read|get|prompt)\s+(?:input|user\s+input|answer)\s*(?:with\s+prompt\s+(?P<prompt>.+?))?\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        lambda m, s, c: ReadInput(prompt=m.group("prompt") if m.group("prompt") else "", result_name=m.group("name"), source=s, confidence=c),
    ),
    IntentPattern(
        "READ_INPUT",
        re.compile(r"(?:ask|prompt)\s+(?P<prompt>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.98,
        lambda m, s, c: ReadInput(prompt=m.group("prompt"), result_name=m.group("name"), source=s, confidence=c),
    ),
    # --- Raise error ---
    IntentPattern(
        "RAISE_ERROR",
        re.compile(r"(?:raise|throw)\s+(?:error|exception)\s+(?P<message>.+)", re.I),
        0.99,
        _raise_error,
    ),
    IntentPattern(
        "RAISE_CUSTOM_ERROR",
        re.compile(r"(?:raise|throw)\s+(?P<type>(?!error|exception)[^\W\d]\w*)\s+(?P<message>.+)", re.I),
        0.99,
        lambda m, s, c: RaiseError(
            message=parse_text_value(m.group("message")),
            error_type=m.group("type"),
            source=s,
            confidence=c,
        ),
    ),
    # --- Assert ---
    IntentPattern(
        "ASSERT",
        re.compile(r"assert\s+(?P<condition>.+?)\s+else\s+(?P<message>.+)", re.I),
        0.99,
        _assert_true,
    ),
    # --- Command-line args ---
    IntentPattern(
        "GET_ARGS",
        re.compile(r"get\s+(?:command\s+line\s+)?arguments?\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        lambda m, s, c: GetArgs(result_name=m.group("name"), source=s, confidence=c),
    ),
    IntentPattern(
        "GET_ARGS",
        re.compile(r"(?:args|arguments)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.97,
        lambda m, s, c: GetArgs(result_name=m.group("name"), source=s, confidence=c),
    ),
    # --- Environment variables ---
    IntentPattern(
        "GET_ENV",
        re.compile(r"get\s+(?:environment\s+)?variable\s+(?P<name>[^\W\d]\w*)\s+as\s+(?P<result>[^\W\d]\w*)", re.I),
        0.99,
        lambda m, s, c: GetEnv(var_name=m.group("name"), result_name=m.group("result"), source=s, confidence=c),
    ),
    IntentPattern(
        "GET_ENV",
        re.compile(r"(?:env|environment)\s+(?P<name>[^\W\d]\w*)\s+as\s+(?P<result>[^\W\d]\w*)", re.I),
        0.97,
        lambda m, s, c: GetEnv(var_name=m.group("name"), result_name=m.group("result"), source=s, confidence=c),
    ),
    # --- Natural math action forms ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?sine\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "sin", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?cosine\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "cos", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?tangent\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "tan", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:natural\s+)?log(?:arithm)?\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "log", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:base-?\s*10\s+)?log10\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "log10", "value"),
    ),
    # --- Natural type conversion forms ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:turn|convert)\s+(?P<value>.+?)\s+(?:into|to)\s+(?:text|string)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("convert", "to_string", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:turn|convert)\s+(?P<value>.+?)\s+(?:into|to)\s+(?:number|integer|int)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("convert", "to_number", "value"),
    ),
    # --- Natural file system forms ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"make\s+director(?:y|ies)\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="file", action="mkdir",
            args={"path": m.group("path").strip()},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:list|show)\s+(?:directory|folder|dir)\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="file", action="list_dir",
            args={"path": m.group("path").strip()},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"copy\s+file\s+(?P<source>.+?)\s+to\s+(?P<dest>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="file", action="copy",
            args={"source": _strip_optional_quotes(m.group("source")), "destination": _strip_optional_quotes(m.group("dest"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"move\s+file\s+(?P<source>.+?)\s+to\s+(?P<dest>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="file", action="move",
            args={"source": _strip_optional_quotes(m.group("source")), "destination": _strip_optional_quotes(m.group("dest"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"delete\s+file\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="file", action="delete",
            args={"path": m.group("path").strip()},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Natural bitwise forms ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"bitwise\s+and\s+of\s+(?P<left>.+?)\s+and\s+(?P<right>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="bitwise", action="and",
            args={"left": parse_text_value(m.group("left")), "right": parse_text_value(m.group("right"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"bitwise\s+or\s+of\s+(?P<left>.+?)\s+and\s+(?P<right>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="bitwise", action="or",
            args={"left": parse_text_value(m.group("left")), "right": parse_text_value(m.group("right"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"bitwise\s+xor\s+of\s+(?P<left>.+?)\s+and\s+(?P<right>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="bitwise", action="xor",
            args={"left": parse_text_value(m.group("left")), "right": parse_text_value(m.group("right"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"bitwise\s+not\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("bitwise", "not", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"bitwise\s+(?:shift\s+)?left\s+(?P<value>.+?)\s+by\s+(?P<amount>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="bitwise", action="shift_left",
            args={"value": parse_text_value(m.group("value")), "amount": parse_text_value(m.group("amount"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"bitwise\s+(?:shift\s+)?right\s+(?P<value>.+?)\s+by\s+(?P<amount>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="bitwise", action="shift_right",
            args={"value": parse_text_value(m.group("value")), "amount": parse_text_value(m.group("amount"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Natural string forms ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:character|char|letter)\s+at\s+(?:index\s+)?(?P<index>.+?)\s+of\s+(?P<text>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="char_at",
            args={"text": parse_text_value(m.group("text")), "index": parse_text_value(m.group("index"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:character\s+)?code\s+at\s+(?:index\s+)?(?P<index>.+?)\s+of\s+(?P<text>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="char_code_at",
            args={"text": parse_text_value(m.group("text")), "index": parse_text_value(m.group("index"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|take)\s+(?:a\s+)?substring\s+of\s+(?P<text>.+?)\s+(?:from|start)\s+(?P<start>.+?)\s+to\s+(?P<end>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="substring",
            args={"text": parse_text_value(m.group("text")), "start": parse_text_value(m.group("start")), "end": parse_text_value(m.group("end"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"pad\s+(?P<text>.+?)\s+(?:(?:start|left)\s+with\s+(?P<char>.+?))?\s+to\s+(?P<length>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="pad_start",
            args={"text": parse_text_value(m.group("text")), "length": parse_text_value(m.group("length")), "char": m.group("char") or " "},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"pad\s+(?P<text>.+?)\s+(?:end|right)\s+with\s+(?P<char>.+?)\s+to\s+(?P<length>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="pad_end",
            args={"text": parse_text_value(m.group("text")), "length": parse_text_value(m.group("length")), "char": m.group("char") or " "},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"repeat\s+(?P<text>.+?)\s+(?P<times>.+?)\s+times?\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="repeat",
            args={"text": parse_text_value(m.group("text")), "times": parse_text_value(m.group("times"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"regex\s+match\s+(?P<pattern>.+?)\s+in\s+(?P<text>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="regex_match",
            args={"text": parse_text_value(m.group("text")), "pattern": _strip_optional_quotes(m.group("pattern"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"regex\s+search\s+(?P<pattern>.+?)\s+in\s+(?P<text>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="regex_search",
            args={"text": parse_text_value(m.group("text")), "pattern": _strip_optional_quotes(m.group("pattern"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"regex\s+replace\s+(?P<pattern>.+?)\s+in\s+(?P<text>.+?)\s+with\s+(?P<replacement>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="regex_replace",
            args={"text": parse_text_value(m.group("text")), "pattern": _strip_optional_quotes(m.group("pattern")), "replacement": parse_text_value(m.group("replacement"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Text checks (isalpha, isdigit, etc.) ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check|see|test)\s+(?:if\s+)?(?P<text>.+?)\s+(?:is\s+)?(?:alpha|letter|alphabetic)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="isalpha",
            args={"text": parse_text_value(m.group("text"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check|see|test)\s+(?:if\s+)?(?P<text>.+?)\s+(?:is\s+)?(?:digit|numeric|number)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="isdigit",
            args={"text": parse_text_value(m.group("text"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check|see|test)\s+(?:if\s+)?(?P<text>.+?)\s+(?:is\s+)?(?:alnum|alphanumeric|letter_or_number)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="isalnum",
            args={"text": parse_text_value(m.group("text"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check|see|test)\s+(?:if\s+)?(?P<text>.+?)\s+(?:is\s+)?(?:space|whitespace|blank)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="isspace",
            args={"text": parse_text_value(m.group("text"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Text partition ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"partition\s+(?P<text>.+?)\s+(?:by|with|on)\s+(?P<separator>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="text", action="partition",
            args={"text": parse_text_value(m.group("text")), "separator": parse_text_value(m.group("separator"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Text capitalize / title / swapcase / lstrip / rstrip ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make|turn)\s+(?:the\s+)?capitalize\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "capitalize", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make|turn)\s+(?:the\s+)?title\s+(?:case\s+)?of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "title", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make|turn)\s+(?:the\s+)?swapcase\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "swapcase", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make)\s+(?:the\s+)?left\s+strip\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "lstrip", "text"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make)\s+(?:the\s+)?right\s+strip\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("text", "rstrip", "text"),
    ),
    # --- Natural date/time forms ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:format|convert)\s+(?:date\s+)?(?P<value>.+?)\s+(?:as|using)\s+(?:format\s+)?(?P<format>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="time", action="format",
            args={"value": parse_text_value(m.group("value")), "format": _strip_optional_quotes(m.group("format"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Math min / max ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|find|take)\s+(?:the\s+)?minimum\s+of\s+(?P<left>.+?)\s+and\s+(?P<right>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _math_two_arg_action("min"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|find|take)\s+(?:the\s+)?maximum\s+of\s+(?P<left>.+?)\s+and\s+(?P<right>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _math_two_arg_action("max"),
    ),
    # --- Math constants ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:value\s+of\s+)?pi\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="math", action="pi", args={},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:value\s+of\s+)?euler(?:'s)?\s+number\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="math", action="e", args={},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Math: factorial ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?factorial\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "factorial", "value"),
    ),
    # --- Math: gcd ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:gcd|greatest\s+common\s+divisor)\s+of\s+(?P<a>.+?)\s+and\s+(?P<b>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="math", action="gcd",
            args={"a": parse_text_value(m.group("a")), "b": parse_text_value(m.group("b"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Math: exp (e^x) ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?exp\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "exp", "value"),
    ),
    # --- Math: atan / arctan ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:atan|arctan|arc\s+tangent)\s+of\s+(?P<value>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "atan", "value"),
    ),
    # --- Math: hypot / hypotenuse ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:hypot|hypotenuse|distance)\s+of\s+(?P<a>.+?)\s+and\s+(?P<b>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="math", action="hypot",
            args={"a": parse_text_value(m.group("a")), "b": parse_text_value(m.group("b"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Math: degrees / radians ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:convert|turn)\s+(?P<value>.+?)\s+to\s+degrees\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "degrees", "value"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:convert|turn)\s+(?P<value>.+?)\s+to\s+radians\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "radians", "value"),
    ),
    # --- Math: isnan ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check|test)\s+(?:if\s+)?(?P<value>.+?)\s+(?:is\s+)?(?:nan|not\s+a\s+number)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _natural_stdlib_action("math", "isnan", "value"),
    ),
    # --- Statistics: median, mode, stdev ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?median\s+of\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="statistics", action="median",
            args={"values": parse_text_value(m.group("values"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?mode\s+of\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="statistics", action="mode",
            args={"values": parse_text_value(m.group("values"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?(?:stdev|standard\s+deviation)\s+of\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        lambda m, s, c: UseStdLibAction(
            module="statistics", action="stdev",
            args={"values": parse_text_value(m.group("values"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- List first / last ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|take)\s+(?:the\s+)?first\s+(?:item\s+)?(?:of|from|in)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _list_values_action("first"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|take)\s+(?:the\s+)?last\s+(?:item\s+)?(?:of|from|in)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _list_values_action("last"),
    ),
    # --- List item at index ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|take)\s+(?:the\s+)?(?:item|element)\s+at\s+(?:index\s+)?(?P<index>.+?)\s+(?:of|from|in)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.0,
        _list_at_action,
    ),
    # --- Text contains / starts with / ends with ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check\s+)?(?:if\s+)?(?P<text>.+?)\s+contains\s+(?P<needle>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="text", action="contains",
            args={"text": parse_text_value(m.group("text")), "needle": parse_text_value(m.group("needle"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check\s+)?(?:if\s+)?(?P<text>.+?)\s+(?:starts?\s+with)\s+(?P<prefix>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="text", action="starts_with",
            args={"text": parse_text_value(m.group("text")), "prefix": parse_text_value(m.group("prefix"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check\s+)?(?:if\s+)?(?P<text>.+?)\s+(?:ends?\s+with)\s+(?P<suffix>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="text", action="ends_with",
            args={"text": parse_text_value(m.group("text")), "suffix": parse_text_value(m.group("suffix"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- General contains (value in list / text / map) ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check\s+)?(?:if\s+)?(?P<value>.+?)\s+is\s+in\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="list", action="contains",
            args={"values": parse_text_value(m.group("values")), "value": parse_text_value(m.group("value"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- File glob ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:glob|find|search)\s+(?:files?\s+)?(?:matching\s+)?(?P<pattern>.+?)\s+(?:in\s+(?P<root>.+?))?\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="file", action="glob",
            args={"pattern": _strip_optional_quotes(m.group("pattern")), **({"root": _strip_optional_quotes(m.group("root"))} if m.group("root") else {})},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Map has key ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check\s+)?(?:if\s+)?map\s+(?P<value>.+?)\s+(?:has|contains)\s+key\s+(?P<key>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="map", action="has",
            args={"value": parse_text_value(m.group("value")), "key": parse_text_value(m.group("key"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- File append ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"append\s+(?P<text>.+?)\s+to\s+file\s+(?P<path>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="file", action="append",
            args={"path": _strip_optional_quotes(m.group("path")), "text": parse_text_value(m.group("text"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Range generation ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|make|create)\s+(?:a\s+)?range\s+(?:from\s+)?(?P<start>.+?)\s+to\s+(?P<end>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        lambda m, s, c: UseStdLibAction(
            module="list", action="range",
            args={"start": parse_text_value(m.group("start")), "end": parse_text_value(m.group("end"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- List sum / average ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?sum\s+of\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        _list_values_action("sum"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?average\s+of\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        _list_values_action("average"),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|calculate)\s+(?:the\s+)?mean\s+of\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        _list_values_action("average"),
    ),
    # --- Natural window/screen background color ---
    IntentPattern(
        "APP_BG",
        re.compile(r"(?P<color>blue|red|green|yellow|purple|orange|pink|brown|gray|grey|black|white|cyan|teal|indigo|violet|dark|light|amber|lime|emerald|navy|maroon|coral|crimson|gold|silver|transparent|clear)\s+(?:screen|window|background)", re.I),
        0.95,
        lambda m, s, c: AppBackground(color=m.group("color").lower(), source=s, confidence=c),
    ),
    # --- Natural motion: NAME goes/go up/down/left/right by N ---
    IntentPattern(
        "MOVE",
        re.compile(r"(?P<name>[^\W\d]\w*)\s+go(?:es)?\s+(?P<direction>up|down|left|right|forward|backward)\s+by\s+(?P<amount>\d+)", re.I),
        0.95,
        _move_object,
    ),
    # --- Natural motion: NAME falls/fell down by N ---
    IntentPattern(
        "MOVE",
        re.compile(r"(?P<name>[^\W\d]\w*)\s+fall(?:s|ing)?\s+down\s+by\s+(?P<amount>\d+)", re.I),
        0.95,
        lambda m, s, c: MoveObject(
            name=_parse_name(m.group("name")),
            direction="down",
            amount=int(m.group("amount")),
            source=s, confidence=c,
        ),
    ),
    # --- Sleep / Wait ---
    IntentPattern(
        "SLEEP",
        re.compile(r"(?:sleep|wait)\s+(?P<ms>\d+)\s*(?:milliseconds?|ms)", re.I),
        0.99,
        lambda m, s, c: Sleep(milliseconds=int(m.group("ms")), source=s, confidence=c),
    ),
    IntentPattern(
        "SLEEP",
        re.compile(r"(?:sleep|wait)\s+(?P<seconds>\d+(?:\.\d+)?)\s*seconds?", re.I),
        0.99,
        lambda m, s, c: Sleep(milliseconds=int(float(m.group("seconds")) * 1000), source=s, confidence=c),
    ),
    # --- Random between ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:pick|choose|get)\s+(?:a\s+)?random\s+(?:number|integer)\s+between\s+(?P<min>.+?)\s+and\s+(?P<max>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="random", action="integer",
            args={"min": parse_text_value(m.group("min")), "max": parse_text_value(m.group("max"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Power ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:raise|power)\s+(?P<base>.+?)\s+to\s+(?:the\s+)?power\s+of\s+(?P<exp>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="math", action="power",
            args={"base": parse_text_value(m.group("base")), "exponent": parse_text_value(m.group("exp"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:raise|power)\s+(?P<base>.+?)\s+to\s+(?P<exp>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.90,
        lambda m, s, c: UseStdLibAction(
            module="math", action="power",
            args={"base": parse_text_value(m.group("base")), "exponent": parse_text_value(m.group("exp"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Rounding ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:round)\s+(?P<value>.+?)\s+to\s+(?P<places>\d+)\s+(?:decimal\s+)?places?\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.99,
        lambda m, s, c: UseStdLibAction(
            module="math", action="round",
            args={"value": parse_text_value(m.group("value")), "places": int(m.group("places"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Natural property: increase/set/decrease OBJECT's PROP ---
    IntentPattern(
        "PROPERTY",
        re.compile(r"(?:increase|raise)\s+(?P<object>[^\W\d]\w*)'s?\s+(?P<property>[^\W\d]\w*)\s+by\s+(?P<value>.+)", re.I),
        0.95,
        lambda m, s, c: SetProperty(
            object_name=_parse_name(m.group("object")),
            property_name=_parse_name(m.group("property")),
            value=_parse_property_value(m.group("value")),
            source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"(?:decrease|lower|reduce)\s+(?P<object>[^\W\d]\w*)'s?\s+(?P<property>[^\W\d]\w*)\s+by\s+(?P<value>.+)", re.I),
        0.95,
        lambda m, s, c: SetProperty(
            object_name=_parse_name(m.group("object")),
            property_name=_parse_name(m.group("property")),
            value=_parse_property_value(m.group("value")),
            source=s, confidence=c,
        ),
    ),
    # --- Natural property without apostrophe: OBJECT PROP by VALUE ---
    IntentPattern(
        "PROPERTY",
        re.compile(r"(?:increase|raise)\s+(?P<object>[^\W\d]\w*)\s+(?P<property>[^\W\d]\w*)\s+by\s+(?P<value>.+)", re.I),
        0.90,
        lambda m, s, c: SetProperty(
            object_name=_parse_name(m.group("object")),
            property_name=_parse_name(m.group("property")),
            value=_parse_property_value(m.group("value")),
            source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "PROPERTY",
        re.compile(r"(?:decrease|lower|reduce)\s+(?P<object>[^\W\d]\w*)\s+(?P<property>[^\W\d]\w*)\s+by\s+(?P<value>.+)", re.I),
        0.90,
        lambda m, s, c: SetProperty(
            object_name=_parse_name(m.group("object")),
            property_name=_parse_name(m.group("property")),
            value=_parse_property_value(m.group("value")),
            source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "ROTATE",
        re.compile(r"rotate\s+(?P<name>[^\W\d]\w*)\s+by\s+(?P<angle>[+-]?\d+(?:\.\d+)?)\s+degrees?\s*(?:around|on)\s+(?P<axis>[xyz])\s*axis?", re.I),
        0.99,
        lambda m, s, c: RotateObject(
            name=_parse_name(m.group("name")),
            angle=float(m.group("angle")),
            axis=m.group("axis").lower(),
            source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "ROTATE",
        re.compile(r"spin\s+(?P<name>[^\W\d]\w*)\s+by\s+(?P<angle>[+-]?\d+(?:\.\d+)?)\s*(?:degrees?\s*)?on\s+(?P<axis>[xyz])\s*axis?", re.I),
        0.95,
        lambda m, s, c: RotateObject(
            name=_parse_name(m.group("name")),
            angle=float(m.group("angle")),
            axis=m.group("axis").lower(),
            source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "CAMERA",
        re.compile(r"camera\s+(?:at|position|to)\s+x\s+(?P<x>[+-]?\d+(?:\.\d+)?)\s+y\s+(?P<y>[+-]?\d+(?:\.\d+)?)\s+z\s+(?P<z>[+-]?\d+(?:\.\d+)?)", re.I),
        0.99,
        lambda m, s, c: SetCamera(
            x=float(m.group("x")),
            y=float(m.group("y")),
            z=float(m.group("z")),
            source=s, confidence=c,
        ),
    ),
    IntentPattern(
        "CAMERA_MODE",
        re.compile(r"(?:camera\s+)?mode\s+(?P<mode>first\s*person|1st\s*person|third\s*person|3rd\s*person|fixed|follow)", re.I),
        0.95,
        lambda m, s, c: SetCameraMode(
            mode=m.group("mode").strip().lower().replace(" ", "_").replace("1st", "first").replace("3rd", "third"),
            source=s, confidence=c,
        ),
    ),
    # --- List slice from start to end ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:get|take)\s+(?:items|elements|values)\s+(?P<start>.+?)\s+(?:to|through)\s+(?P<end>.+?)\s+(?:from|of|in)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="list", action="slice",
            args={"values": parse_text_value(m.group("values")), "start": parse_text_value(m.group("start")), "end": parse_text_value(m.group("end"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Count items / length of list ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:count|how\s+many)\s+(?:items|elements|entries)\s+(?:are|do\s+we\s+have)?\s+(?:in|inside|of)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.90,
        _list_values_action("length"),
    ),
    # --- Set variable to empty list ---
    IntentPattern(
        "SET",
        re.compile(rf"{ASSIGN_NAME}(?:empty|new)\s+list", re.I),
        0.90,
        lambda m, s, c: SetVar(
            name=_parse_name(m.group("name")),
            value=[],
            source=s, confidence=c,
        ),
    ),
    # --- Set variable to empty map ---
    IntentPattern(
        "SET",
        re.compile(rf"{ASSIGN_NAME}(?:empty|new)\s+(?:dictionary|map)", re.I),
        0.90,
        lambda m, s, c: SetVar(
            name=_parse_name(m.group("name")),
            value={},
            source=s, confidence=c,
        ),
    ),
    # --- List append at end ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:put|add|place)\s+(?P<value>.+?)\s+at\s+(?:the\s+)?end\s+of\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="list", action="append",
            args={"values": parse_text_value(m.group("values")), "value": parse_text_value(m.group("value"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Map has key ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:check\s+)?(?:if\s+)?(?P<value>.+?)\s+(?:has\s+key|contains\s+key)\s+(?P<key>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="map", action="has",
            args={"value": parse_text_value(m.group("value")), "key": parse_text_value(m.group("key"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Not / isn't condition expressions ---
    IntentPattern(
        "PRINT",
        re.compile(r"(?:show|print|display|say)\s+(?P<value>not\s+.+)", re.I),
        0.95,
        _print,
    ),
    # --- Natural append with just "add X to list named Y" ---
    IntentPattern(
        "LIST_ADD",
        re.compile(r"add\s+(?P<item>.+?)\s+to\s+(?:the\s+)?(?:list\s+)?named\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        _add_to_list,
    ),
    # --- Insert into list ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"insert\s+(?P<value>.+?)\s+at\s+(?:index\s+)?(?P<index>.+?)\s+(?:into|in)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        lambda m, s, c: UseStdLibAction(
            module="list", action="insert",
            args={"values": parse_text_value(m.group("values")), "index": parse_text_value(m.group("index")), "value": parse_text_value(m.group("value"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Extend / concatenate lists ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:extend|concat|concatenate|merge)\s+(?P<values>.+?)\s+(?:with|and)\s+(?P<other>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="list", action="extend",
            args={"values": parse_text_value(m.group("values")), "values": parse_text_value(m.group("other"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Count occurrences in list ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:count|find)\s+occurrences\s+of\s+(?P<value>.+?)\s+(?:in|inside)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        lambda m, s, c: UseStdLibAction(
            module="list", action="count_value",
            args={"values": parse_text_value(m.group("values")), "value": parse_text_value(m.group("value"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Find index in list ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:find|get)\s+(?:the\s+)?(?:index|position)\s+of\s+(?P<value>.+?)\s+(?:in|inside)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        1.01,
        lambda m, s, c: UseStdLibAction(
            module="list", action="index_of",
            args={"values": parse_text_value(m.group("values")), "value": parse_text_value(m.group("value"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Pop / remove last item ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:pop|remove\s+last)\s+(?:item\s+)?(?:from|of)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.95,
        lambda m, s, c: UseStdLibAction(
            module="list", action="pop",
            args={"values": parse_text_value(m.group("values"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Clear list ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:clear|empty|erase)\s+(?:the\s+)?(?:contents\s+of\s+)?(?:list\s+)?(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.90,
        lambda m, s, c: UseStdLibAction(
            module="list", action="clear",
            args={"values": parse_text_value(m.group("values"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
    # --- Shuffle list ---
    IntentPattern(
        "USE_STDLIB",
        re.compile(r"(?:shuffle|randomize)\s+(?P<values>.+?)\s+as\s+(?P<name>[^\W\d]\w*)", re.I),
        0.90,
        lambda m, s, c: UseStdLibAction(
            module="list", action="shuffle",
            args={"values": parse_text_value(m.group("values"))},
            name=_parse_name(m.group("name")), source=s, confidence=c,
        ),
    ),
)


def _to_english(phrase: str) -> str:
    lang = get_language()
    if lang.code == "en":
        return phrase
    result = phrase
    eng = ENGLISH
    mappings = [
        (lang._p, eng._p),
        (lang._s, eng._s),
        (lang._m, eng._m),
        (lang._a, eng._a),
        (lang._g, eng._g),
        (lang._f, eng._f),
        (lang.to, eng.to),
        (lang.equal, eng.equal),
        (lang.for_p, eng.for_p),
        (lang.in_p, eng.in_p),
        (lang.as_p, eng.as_p),
        (lang.true, eng.true),
        (lang.false, eng.false),
        (lang.yes, eng.yes),
        (lang.no, eng.no),
        (lang.for_each, eng.for_each),
        (lang.teaching, eng.teaching),
        ({lang.if_w}, {eng.if_w}),
        ({lang.else_w}, {eng.else_w}),
        ({lang.and_w}, {eng.and_w}),
        ({lang.or_w}, {eng.or_w}),
        ({lang.not_w}, {eng.not_w}),
        ({lang.switch}, {eng.switch}),
        ({lang.match}, {eng.match}),
        ({lang.case, lang.when}, {eng.case, eng.when}),
        ({lang.default, lang.otherwise}, {eng.default, eng.otherwise}),
        ({lang.define}, {eng.define}),
        ({lang.function}, {eng.function}),
        ({lang.return_w}, {eng.return_w}),
        ({lang.call}, {eng.call}),
        ({lang.blueprint}, {eng.blueprint}),
        ({lang.create}, {eng.create}),
        ({lang.named}, {eng.named}),
        ({lang.method}, {eng.method}),
        ({lang.phrase}, {eng.phrase}),
        ({lang.command}, {eng.command}),
        ({lang.means}, {eng.means}),
        ({lang.repeat}, {eng.repeat}),
        ({lang.times}, {eng.times}),
        ({lang.while_w}, {eng.while_w}),
        ({lang.lambda_w}, {eng.lambda_w}),
        ({lang.arrow}, {eng.arrow}),
        ({lang.fn}, {eng.fn}),
        ({lang.into}, {eng.into}),
        ({lang.try_w}, {eng.try_w}),
        ({lang.except_w, lang.catch}, {eng.except_w, eng.catch}),
        ({lang.finally_w}, {eng.finally_w}),
        ({lang.with_w}, {eng.with_w}),
        ({lang.async_w}, {eng.async_w}),
        ({lang.spawn, lang.background}, {eng.spawn, eng.background}),
        ({lang.await_w}, {eng.await_w}),
        ({lang.import_w}, {eng.import_w}),
        ({lang.python}, {eng.python}),
        ({lang.include}, {eng.include}),
        ({lang.library}, {eng.library}),
        ({lang.pack}, {eng.pack}),
        ({lang.use}, {eng.use}),
        ({lang.show, lang.say, lang.display, lang.tell}, {eng.show, eng.say, eng.display, eng.tell}),
        ({lang.ask}, {eng.ask}),
        ({lang.input, lang.prompt, lang.read}, {eng.input, eng.prompt, eng.read}),
        ({lang.raise_w, lang.error_w}, {eng.raise_w, eng.error_w}),
        ({lang.assert_w}, {eng.assert_w}),
        ({lang.debug}, {eng.debug}),
        ({lang.all_w}, {eng.all_w}),
        ({lang.language}, {eng.language}),
        ({lang.true_word}, {eng.true_word}),
        ({lang.false_word}, {eng.false_word}),
    ]
    for from_set, to_set in mappings:
        for fw in sorted(from_set, key=len, reverse=True):
            for tw in to_set:
                result = re.sub(
                    rf"(?<!\w){re.escape(fw)}(?!\w)",
                    tw,
                    result,
                    flags=re.I,
                )
    return result


def match_intent(phrase: str, patterns: Iterable[IntentPattern] = PATTERNS) -> object:
    phrase = _to_english(phrase)
    normalized = normalize_phrase(phrase)
    matches = []
    extraction_errors: list[AngisSyntaxError] = []
    for pattern in patterns:
        try:
            result = pattern.try_match(normalized)
        except AngisSyntaxError as exc:
            extraction_errors.append(exc)
            continue
        if result is not None:
            matches.append(result)
    if not matches:
        if extraction_errors:
            raise extraction_errors[0]
        hint = _hint(normalized)
        raise AngisSyntaxError(f"Could not understand phrase {phrase!r}.{hint}")
    matches.sort(key=lambda item: item.confidence, reverse=True)
    if len(matches) > 1 and matches[0].confidence - matches[1].confidence < 0.005:
        raise AmbiguityError(phrase, [type(item).__name__.upper() for item in matches[:3]])
    return matches[0]


def normalize_phrase(phrase: str) -> str:
    normalized = _strip_sentence_period(phrase.strip())
    normalized = re.sub(
        r"^\s*(say|print|show|display|set|make|store|add|subtract|multiply|divide|calculate)\s*,\s*",
        r"\1 ",
        normalized,
        flags=re.I,
    )
    normalized = re.sub(
        r"^\s*(app|window|text|label|button|scene|layout|game|attach file|locate file|find file|file)\s*,\s*",
        r"\1 ",
        normalized,
        flags=re.I,
    )
    normalized = re.sub(r"\bwhat\s+is\s*,\s*", "what is ", normalized, flags=re.I)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _strip_sentence_period(phrase: str) -> str:
    if not phrase.endswith("."):
        return phrase
    in_quote: str | None = None
    escaped = False
    prev_char = ""
    for char in phrase[:-1]:
        if escaped:
            escaped = False
            prev_char = char
            continue
        if char == "\\":
            escaped = True
            prev_char = char
            continue
        if char == '"':
            if in_quote == '"':
                in_quote = None
            elif in_quote is None:
                in_quote = '"'
        elif char == "'" and not prev_char.isalpha():
            if in_quote == "'":
                in_quote = None
            elif in_quote is None:
                in_quote = "'"
        prev_char = char
    if in_quote is None:
        return phrase[:-1].rstrip()
    return phrase


def _hint(phrase: str) -> str:
    words = set(re.findall(r"[^\W\d]+", phrase.lower()))
    lang = get_language()
    if words & lang._p:
        return f' For output, try: {next(iter(lang._p))} "hello".'
    if words & lang._s or re.search(r"\bis\b|=", phrase):
        return f" For variables, try: {next(iter(lang._s))} x to 5."
    if words & lang._m or re.search(r"[+\-*/]", phrase):
        return f" For math, try: {next(iter(lang._m))} 5 and 3."
    if words & lang._a:
        return f" For apps, try: {next(iter(lang._a))}, My App."
    if words & lang._g:
        return " For games, try: Bird on screen."
    if words & lang._f:
        return " For files, try: Attach file at /path/to/file.txt."
    return " Try a language print, variable, or math phrase."
