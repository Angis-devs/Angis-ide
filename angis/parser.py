"""Parser that converts Angis source into IR instructions."""

from __future__ import annotations

import re
from pathlib import Path
import textwrap

from .errors import AngisError, AngisSyntaxError
from .intents import match_intent, parse_atom, parse_expression, parse_text_value
from .ir import (
    Break,
    Condition,
    Continue,
    Comprehension,
    EventBlock,
    FilterItems,
    ForEachBlock,
    FunctionCall,
    FunctionDef,
    IfBlock,
    Lambda,
    LogicalCondition,
    MapOver,
    ObjectMethodCall,
    ObjectMethodDef,
    RangeExpr,
    ReduceItems,
    RepeatBlock,
    ReturnValue,
    SwitchBlock,
    TryBlock,
    Spawn,
    Await,
    AsyncFunctionDef,
    AwaitExpr,
    PythonImport,
    WatchFile,
    NativeGUI,
    WhileBlock,
    WithBlock,
    YieldValue,
    ErrorDef,
)


class _CaseBlock:
    """Internal marker for Case: inside a SwitchBlock."""
    def __init__(self, patterns: list[object], body: list[object] | None = None) -> None:
        self.patterns = patterns
        self.body = body or []


class _DefaultBlock:
    """Internal marker for Default: inside a SwitchBlock."""
    def __init__(self, body: list[object] | None = None) -> None:
        self.body = body or []
from .lexer import SourceLine, lex


SlotSpec = tuple[str, str]
CommandTemplate = tuple[re.Pattern[str], str, list[SlotSpec]]


def parse(source: str) -> list[object]:
    return parse_source(source)


def parse_source(source: str, base_path: Path | None = None, seen: set[Path] | None = None) -> list[object]:
    if base_path is not None:
        source = _expand_includes(source, base_path, seen or set())
    lines = lex(source)
    if not lines:
        return []
    base_indent = min(line.indent for line in lines)
    command_templates = _collect_command_templates(lines)
    instructions, index = _parse_block(lines, start=0, indent=base_indent, command_templates=command_templates)
    if index != len(lines):
        line = lines[index]
        raise AngisSyntaxError(f"Line {line.number}: Unexpected indentation.")
    return instructions


def parse_file(path: Path) -> list[object]:
    resolved = path.expanduser().resolve()
    if resolved.suffix != ".angis":
        raise AngisSyntaxError("Angis only imports files ending in .angis.")
    return parse_source(resolved.read_text(encoding="utf-8"), resolved.parent, {resolved})


def _expand_includes(source: str, base_path: Path, seen: set[Path]) -> str:
    expanded: list[str] = []
    for line in textwrap.dedent(source).splitlines():
        stripped = line.strip()
        match = re.fullmatch(r"(?:include|import\s+file|use\s+phrase\s+(?:library|pack))\s+(.+)", stripped, re.I)
        if not match:
            expanded.append(line)
            continue
        raw_path = match.group(1).strip().strip('"').strip("'")
        include_path = (base_path / raw_path).expanduser().resolve()
        if include_path.is_dir():
            expanded.extend(_expand_include_directory(include_path, seen))
            continue
        if include_path.suffix != ".angis":
            raise AngisSyntaxError("Included files must end in .angis.")
        if include_path in seen:
            raise AngisSyntaxError(f"Recursive include blocked for {include_path}.")
        seen.add(include_path)
        expanded.append(_expand_includes(include_path.read_text(encoding="utf-8"), include_path.parent, seen))
        seen.remove(include_path)
    return "\n".join(expanded)


def _expand_include_directory(directory: Path, seen: set[Path]) -> list[str]:
    expanded: list[str] = []
    for include_path in sorted(directory.rglob("*.angis")):
        resolved = include_path.resolve()
        if resolved in seen:
            raise AngisSyntaxError(f"Recursive include blocked for {resolved}.")
        seen.add(resolved)
        expanded.append(_expand_includes(resolved.read_text(encoding="utf-8"), resolved.parent, seen))
        seen.remove(resolved)
    return expanded


def _parse_block(lines: list[SourceLine], start: int, indent: int, command_templates: list[CommandTemplate]) -> tuple[list[object], int]:
    instructions: list[object] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line.indent < indent:
            break
        if line.indent > indent:
            raise AngisSyntaxError(f"Line {line.number}: Unexpected indentation.")
        try:
            if _is_block_header(line.text):
                child_indent = _next_indent(lines, index, indent)
                body, next_index = _parse_block(lines, index + 1, child_indent, command_templates)
                instruction = _parse_block_header(line, body)
                _register_command_template(line.text, instruction, command_templates)
                if isinstance(instruction, IfBlock) and next_index < len(lines):
                    maybe_else = lines[next_index]
                    if maybe_else.indent == indent and _is_else_header(maybe_else.text):
                        else_indent = _next_indent(lines, next_index, indent)
                        else_body, next_index = _parse_block(lines, next_index + 1, else_indent, command_templates)
                        instruction = IfBlock(
                            condition=instruction.condition,
                            body=instruction.body,
                            else_body=else_body,
                            source=instruction.source,
                            confidence=instruction.confidence,
                        )
                if isinstance(instruction, SwitchBlock):
                    cases, default_body = _extract_switch_cases(body)
                    instruction = SwitchBlock(
                        condition=instruction.condition,
                        cases=cases,
                        default_body=default_body,
                        source=instruction.source,
                        confidence=instruction.confidence,
                    )
                if isinstance(instruction, TryBlock) and next_index < len(lines):
                    maybe_except = lines[next_index]
                    if maybe_except.indent == indent and _is_except_header(maybe_except.text):
                        except_indent = _next_indent(lines, next_index, indent)
                        except_body, next_index = _parse_block(lines, next_index + 1, except_indent, command_templates)
                        variable_name = _parse_except_variable(maybe_except.text)
                        instruction = TryBlock(
                            body=instruction.body,
                            except_body=except_body,
                            variable_name=variable_name,
                            source=instruction.source,
                            confidence=instruction.confidence,
                        )
                    if isinstance(instruction, TryBlock) and next_index < len(lines):
                        maybe_finally = lines[next_index]
                        if maybe_finally.indent == indent and _is_finally_header(maybe_finally.text):
                            finally_indent = _next_indent(lines, next_index, indent)
                            finally_body, next_index = _parse_block(lines, next_index + 1, finally_indent, command_templates)
                            instruction = TryBlock(
                                body=instruction.body,
                                except_body=getattr(instruction, "except_body", []),
                                finally_body=finally_body,
                                variable_name=getattr(instruction, "variable_name", ""),
                                source=instruction.source,
                                confidence=instruction.confidence,
                            )
                instructions.append(instruction)
                index = next_index
            else:
                instructions.append(_parse_simple(line, command_templates))
                index += 1
        except AngisError as exc:
            raise AngisSyntaxError(f"Line {line.number}: {exc}") from exc
    return instructions, index


def _is_block_header(text: str) -> bool:
    return text.endswith(":")


def _is_else_header(text: str) -> bool:
    return bool(re.fullmatch(r"(?:else|otherwise)\s*:?", text.strip(), re.I))


def _collect_command_templates(lines: list[SourceLine]) -> list[CommandTemplate]:
    templates: list[CommandTemplate] = []
    for line in lines:
        phrase_text = _phrase_definition_text(line.text)
        if phrase_text is None:
            continue
        name, _params = _parse_phrase_definition(phrase_text)
        regex, slots = _phrase_regex(phrase_text)
        templates.append((regex, name, slots))
    return templates


def _phrase_definition_text(text: str) -> str | None:
    if _is_block_header(text):
        header = _strip_trailing_period(text[:-1].strip())
        phrase_match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<body>.+)", header, re.I)
        if phrase_match:
            return phrase_match.group("body")
        phrase_match = re.fullmatch(r"when\s+i\s+say\s+(?P<body>.+)", header, re.I)
        if not phrase_match:
            return None
        return phrase_match.group("body")
    phrase_match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<body>.+?)\s+means\s+.+", _strip_trailing_period(text), re.I)
    if phrase_match:
        return phrase_match.group("body")
    phrase_match = re.fullmatch(r"when\s+i\s+say\s+(?P<body>.+?),?\s+it\s+means\s+.+", _strip_trailing_period(text), re.I)
    if phrase_match:
        return phrase_match.group("body")
    phrase_match = re.fullmatch(r"teach\s+angis\s+(?P<body>.+?)\s+to\s+mean\s+.+", _strip_trailing_period(text), re.I)
    if not phrase_match:
        return None
    return phrase_match.group("body")


def _next_indent(lines: list[SourceLine], index: int, parent_indent: int) -> int:
    if index + 1 >= len(lines) or lines[index + 1].indent <= parent_indent:
        raise AngisSyntaxError(f"Line {lines[index].number}: Expected an indented block.")
    return lines[index + 1].indent


def _parse_simple(line: SourceLine, command_templates: list[CommandTemplate]) -> object:
    normalized = _strip_trailing_period(line.text)
    inline_phrase = _parse_inline_phrase_definition(normalized, line, command_templates)
    if inline_phrase is not None:
        return inline_phrase
    bare_return_match = re.fullmatch(r"return\.?\s*", normalized, re.I)
    if bare_return_match:
        return ReturnValue(value=None, source=line.text, confidence=0.99)
    return_match = re.fullmatch(r"return\s*,?\s*(?P<value>.+)", normalized, re.I)
    if return_match:
        raw = return_match.group("value")
        from .intents import _split_items, parse_text_value
        parts = _split_items(raw)
        if len(parts) > 1:
            return ReturnValue(
                values=[parse_text_value(p) for p in parts],
                source=line.text,
                confidence=0.99,
            )
        return ReturnValue(value=parse_text_value(raw), source=line.text, confidence=0.99)
    break_match = re.fullmatch(r"break\.?", normalized, re.I)
    if break_match:
        return Break(source=line.text, confidence=0.99)
    continue_match = re.fullmatch(r"continue\.?", normalized, re.I)
    if continue_match:
        return Continue(source=line.text, confidence=0.99)
    map_over_match = re.fullmatch(
        r"(?:map|transform)\s+(?P<expr>.+?)\s+(?:over|across)\s+(?P<collection>.+?)\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*)",
        normalized, re.I,
    )
    if map_over_match:
        return MapOver(
            expr=parse_expression(map_over_match.group("expr")),
            collection=parse_expression(map_over_match.group("collection")),
            result_name=map_over_match.group("result"),
            source=line.text, confidence=0.99,
        )
    filter_match = re.fullmatch(
        r"(?:filter|keep)\s+(?P<condition>.+?)\s+(?:from|in)\s+(?P<collection>.+?)\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*)",
        normalized, re.I,
    )
    if filter_match:
        return FilterItems(
            condition=parse_expression(filter_match.group("condition")),
            collection=parse_expression(filter_match.group("collection")),
            result_name=filter_match.group("result"),
            source=line.text, confidence=0.99,
        )
    reduce_match = re.fullmatch(
        r"(?:reduce|fold)\s+(?P<expr>.+?)\s+(?:over|across)\s+(?P<collection>.+?)\s+(?:starting|with\s+initial)\s+(?P<initial>.+?)\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*)",
        normalized, re.I,
    )
    if reduce_match:
        return ReduceItems(
            expr=parse_expression(reduce_match.group("expr")),
            collection=parse_expression(reduce_match.group("collection")),
            initial=parse_expression(reduce_match.group("initial")),
            result_name=reduce_match.group("result"),
            source=line.text, confidence=0.99,
        )
    command_call = _parse_command_call(normalized, line.text)
    if command_call is not None:
        return command_call
    method_call_match = re.fullmatch(
        r"(?:call|run)\s*,?\s*(?P<object>[A-Za-z_][A-Za-z0-9_]*)\.(?P<method>[A-Za-z_][A-Za-z0-9_.]*)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*))?",
        normalized,
        re.I,
    )
    if method_call_match:
        args = _parse_call_args(method_call_match.group("args") or "")
        result_raw = (method_call_match.group("result") or "").strip()
        result_names: list[str] = [r.strip() for r in result_raw.split(",")] if result_raw else []
        return ObjectMethodCall(
            object_name=method_call_match.group("object"),
            method_name=method_call_match.group("method"),
            args=args,
            result_name=result_names[0] if result_names else "",
            result_names=result_names if len(result_names) > 1 else None,
            source=line.text,
            confidence=0.99,
        )
    call_match = re.fullmatch(
        r"(?:call|run)\s*,?\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*))?",
        normalized,
        re.I,
    )
    if call_match:
        args = _parse_call_args(call_match.group("args") or "")
        result_raw = (call_match.group("result") or "").strip()
        result_names = [r.strip() for r in result_raw.split(",")] if result_raw else []
        return FunctionCall(
            name=call_match.group("name"),
            args=args,
            result_name=result_names[0] if result_names else "",
            result_names=result_names if len(result_names) > 1 else None,
            source=line.text,
            confidence=0.99,
        )
    template_command_call = _parse_template_command_call(normalized, line.text, command_templates)
    if template_command_call is not None:
        return template_command_call
    yield_match = re.fullmatch(r"yield\s*,?\s*(?P<value>.+?)(?:\s+as\s+(?P<send_var>[A-Za-z_][A-Za-z0-9_]*))?", normalized, re.I)
    if yield_match:
        return YieldValue(
            value=parse_text_value(yield_match.group("value")),
            send_var=yield_match.group("send_var") or "",
            source=line.text,
            confidence=0.99,
        )

    spawn_match = re.fullmatch(
        r"(?:spawn|background|async)\s+(?:call\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*))?",
        normalized,
        re.I,
    )
    if spawn_match:
        return Spawn(
            name=spawn_match.group("name"),
            args=_parse_call_args(spawn_match.group("args") or ""),
            result_name=spawn_match.group("result") or "",
            source=line.text,
            confidence=0.99,
        )

    await_match = re.fullmatch(
        r"(?:await|wait\s+for)\s+(?P<target>[A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*))?",
        normalized,
        re.I,
    )
    if await_match:
        return Await(
            target=await_match.group("target"),
            result_name=await_match.group("result") or "",
            source=line.text,
            confidence=0.99,
        )

    py_import_match = re.fullmatch(
        r"(?:import|use)\s+python\s+(?P<module>[A-Za-z_][A-Za-z0-9_.]*)(?:\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*))?(?:\s+with\s+names\s+(?P<names>.+))?",
        normalized,
        re.I,
    )
    if py_import_match:
        names_text = py_import_match.group("names") or ""
        names = [n.strip() for n in names_text.split(",") if n.strip()] if names_text else None
        return PythonImport(
            module=py_import_match.group("module"),
            result_name=py_import_match.group("result") or "",
            names=names,
            source=line.text,
            confidence=0.99,
        )

    await_expr_match = re.fullmatch(r"await\s+(?P<value>.+?)\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*)", normalized, re.I)
    if await_expr_match:
        return AwaitExpr(
            value=parse_text_value(await_expr_match.group("value")),
            result_name=await_expr_match.group("result"),
            source=line.text,
            confidence=0.99,
        )

    watch_match = re.fullmatch(r"watch\s+file\s+(?P<path>.+)", normalized, re.I)
    if watch_match:
        return WatchFile(path=watch_match.group("path").strip(), source=line.text, confidence=0.99)

    native_gui_match = re.fullmatch(
        r"(?:use|create|open)\s+(?:native\s+)?gui\s+(?P<action>[A-Za-z_]+)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*))?",
        normalized,
        re.I,
    )
    if native_gui_match:
        args_text = native_gui_match.group("args") or ""
        args: dict[str, Expression] = {}
        if args_text:
            for item in args_text.split(","):
                kv = item.strip().split(":", 1)
                if len(kv) == 2:
                    key = kv[0].strip()
                    args[key] = parse_text_value(kv[1].strip())
        return NativeGUI(
            action=native_gui_match.group("action").lower(),
            args=args,
            result_name=native_gui_match.group("result") or "",
            source=line.text,
            confidence=0.99,
        )

    error_def_match = re.fullmatch(r"(?:define\s+error|error)\s*,?\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)", normalized, re.I)
    if error_def_match:
        return ErrorDef(name=error_def_match.group("name"), source=line.text, confidence=0.99)

    try:
        return match_intent(line.text)
    except AngisError:
        direct_command_call = _parse_direct_command_call(normalized, line.text)
        if direct_command_call is not None:
            return direct_command_call
        raise


def _parse_block_header(line: SourceLine, body: list[object]) -> object:
    header = _strip_trailing_period(line.text[:-1].strip())
    if _is_else_header(line.text):
        raise AngisSyntaxError("Else must come directly after an If block.")

    if_match = re.fullmatch(r"if\s*,?\s*(?P<condition>.+?)(?:\s+then)?", header, re.I)
    if if_match:
        return IfBlock(
            condition=_parse_condition(if_match.group("condition")),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    unless_match = re.fullmatch(r"unless\s*,?\s*(?P<condition>.+)", header, re.I)
    if unless_match:
        return IfBlock(
            condition=_parse_condition(f"not {unless_match.group('condition')}"),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    repeat_match = re.fullmatch(r"(?:repeat|do\s+this|run\s+this)\s*,?\s*(?P<count>.+?)\s+times", header, re.I)
    if repeat_match:
        return RepeatBlock(
            count=parse_atom(repeat_match.group("count")),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    while_match = re.fullmatch(r"(?:while|as\s+long\s+as|keep\s+going\s+while)\s*,?\s*(?P<condition>.+)", header, re.I)
    if while_match:
        return WhileBlock(
            condition=_parse_condition(while_match.group("condition")),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    until_match = re.fullmatch(r"until\s*,?\s*(?P<condition>.+)", header, re.I)
    if until_match:
        return WhileBlock(
            condition=_parse_condition(f"not {until_match.group('condition')}"),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    range_for_match = re.fullmatch(
        r"(?:for\s+each|foreach|for\s+every|for)\s*,?\s*(?P<item>[A-Za-z_][A-Za-z0-9_]*)\s+in\s+range\s+(?:from\s+)?(?P<start>.+?)\s+to\s+(?P<end>.+)",
        header,
        re.I,
    )
    if range_for_match:
        return ForEachBlock(
            item_name=range_for_match.group("item"),
            collection=RangeExpr(
                start=parse_expression(range_for_match.group("start")),
                end=parse_expression(range_for_match.group("end")),
            ),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    for_each_match = re.fullmatch(
        r"(?:for\s+each|foreach|for\s+every|for\s+each\s+one|for\s+every\s+one)\s*,?\s*(?P<item>[A-Za-z_][A-Za-z0-9_]*)\s+(?:in|inside|from)\s+(?P<collection>.+)",
        header,
        re.I,
    )
    if for_each_match:
        return ForEachBlock(
            item_name=for_each_match.group("item"),
            collection=parse_expression(for_each_match.group("collection")),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    plain_for_match = re.fullmatch(
        r"for\s*,?\s*(?P<item>[A-Za-z_][A-Za-z0-9_]*)\s+in\s+(?P<collection>.+)",
        header,
        re.I,
    )
    if plain_for_match:
        return ForEachBlock(
            item_name=plain_for_match.group("item"),
            collection=parse_expression(plain_for_match.group("collection")),
            body=body,
            source=line.text,
            confidence=0.95,
        )

    command_match = re.fullmatch(r"(?:define\s+command|command)\s*,?\s*(?P<body>.+)", header, re.I)
    if command_match:
        name, params, param_types = _parse_command_definition(command_match.group("body"))
        return FunctionDef(
            name=name,
            params=params,
            param_types=param_types,
            body=body,
            source=line.text,
            confidence=0.99,
        )

    phrase_match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<body>.+)", header, re.I)
    if not phrase_match:
        phrase_match = re.fullmatch(r"when\s+i\s+say\s+(?P<body>.+)", header, re.I)
    if phrase_match:
        name, params = _parse_phrase_definition(phrase_match.group("body"))
        return FunctionDef(
            name=name,
            params=params,
            body=body,
            source=line.text,
            confidence=0.99,
        )

    async_match = re.fullmatch(
        r"(?:define\s+)?async\s+(?:function\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
        r"(?:\s+with\s+(?P<params>.+?))?"
        r"(?:\s*->\s*(?P<return_type>text|string|number|int|decimal|float|bool|boolean|list|map|dict|any))?",
        header,
        re.I,
    )
    if async_match:
        params, param_types = _parse_param_names(async_match.group("params") or "")
        return AsyncFunctionDef(
            name=async_match.group("name"),
            params=params,
            param_types=param_types,
            return_type=(async_match.group("return_type") or "").lower(),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    function_match = re.fullmatch(
        r"(?:define|function)\s*,?\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
        r"(?:\s+with\s+(?P<params>.+?))?"
        r"(?:\s*->\s*(?P<return_type>text|string|number|int|decimal|float|bool|boolean|list|map|dict|any))?",
        header,
        re.I,
    )
    if function_match:
        params, param_types = _parse_param_names(function_match.group("params") or "")
        return FunctionDef(
            name=function_match.group("name"),
            params=params,
            param_types=param_types,
            return_type=(function_match.group("return_type") or "").lower(),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    method_match = re.fullmatch(
        r"(?:define\s+method|method)\s*,?\s*(?P<method>[A-Za-z_][A-Za-z0-9_]*)(?:\s+for\s+(?P<object>[A-Za-z_][A-Za-z0-9_]*))"
        r"(?:\s+with\s+(?P<params>.+?))?"
        r"(?:\s*->\s*(?P<return_type>text|string|number|int|decimal|float|bool|boolean|list|map|dict|any))?",
        header,
        re.I,
    )
    if method_match:
        params, param_types = _parse_param_names(method_match.group("params") or "")
        return ObjectMethodDef(
            object_name=method_match.group("object"),
            method_name=method_match.group("method"),
            params=params,
            param_types=param_types,
            return_type=(method_match.group("return_type") or "").lower(),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    key_match = re.fullmatch(r"(?:when|on|if)\s+(?:(?:key\s+)?(?P<name>[A-Za-z0-9_]+)\s+(?:is\s+)?(?:pressed|hit|typed|released)|(?P<named>space|enter|up|down|left|right|w|a|s|d|escape|shift|ctrl|alt)\s+(?:key\s+)?(?:pressed|hit|typed|released))", header, re.I)
    if key_match:
        key_name = (key_match.group("named") or key_match.group("name")).lower()
        kind = "key"
        for part in ("pressed", "hit", "typed"):
            if part in key_match.group(0).lower():
                kind = "key"
                break
        if "released" in key_match.group(0).lower():
            kind = "key_release"
        return EventBlock(kind=kind, name=key_name, body=body, source=line.text, confidence=0.99)

    mouse_match = re.fullmatch(r"(?:when|on|if)\s+(?:(?:the\s+)?mouse\s+)?(?P<name>clicked|clicks|click|tap|tapped|moved|moves|pressed|presses)", header, re.I)
    if mouse_match:
        name = mouse_match.group("name").lower()
        normalized_name = {"clicks": "clicked", "click": "clicked", "tap": "clicked", "tapped": "clicked", "moves": "moved", "presses": "pressed"}.get(name, name)
        return EventBlock(kind="mouse", name=normalized_name, body=body, source=line.text, confidence=0.99)

    button_match = re.fullmatch(r"when\s+(?:button\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+(?:is\s+)?(?:clicked|pressed|tapped)", header, re.I)
    if button_match:
        return EventBlock(kind="button", name=button_match.group("name"), body=body, source=line.text, confidence=0.99)

    every_match = re.fullmatch(r"(?:every|each)\s+(?P<name>\d+)\s*(?:milliseconds|millisecond|ms)", header, re.I)
    if every_match:
        return EventBlock(kind="timer", name=every_match.group("name"), body=body, source=line.text, confidence=0.99)

    collision_match = re.fullmatch(
        r"(?:when|on|if)\s+(?P<left>[A-Za-z_][A-Za-z0-9_]*)\s+(?:touches|hits|collides\s+with|runs\s+into|bumps\s+into|hits\s+against)\s+(?P<right>[A-Za-z_][A-Za-z0-9_ ]+)",
        header,
        re.I,
    )
    if collision_match:
        return EventBlock(
            kind="collision",
            name=f"{collision_match.group('left')}:{collision_match.group('right')}",
            body=body,
            source=line.text,
            confidence=0.99,
        )

    switch_match = re.fullmatch(r"(?:switch|match)\s*,?\s*(?P<condition>.+)", header, re.I)
    if switch_match:
        return SwitchBlock(
            condition=parse_expression(switch_match.group("condition")),
            cases=[],
            source=line.text,
            confidence=0.99,
        )

    with_match = re.fullmatch(r"with\s+,?\s*(?P<resource>.+)", header, re.I)
    if with_match:
        resource_text = with_match.group("resource").strip()
        var_name = ""
        as_match = re.fullmatch(r"(?P<expr>.+?)\s+as\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)", resource_text, re.I)
        if as_match:
            resource_text = as_match.group("expr").strip()
            var_name = as_match.group("var")
        try:
            resource_expr = parse_expression(resource_text)
        except AngisSyntaxError:
            resource_expr = parse_text_value(resource_text)
        return WithBlock(
            body=body,
            resource=resource_expr,
            variable_name=var_name,
            source=line.text,
            confidence=0.99,
        )

    try_match = re.fullmatch(r"(?:try|attempt)", header, re.I)
    if try_match:
        return TryBlock(
            body=body,
            except_body=[],
            source=line.text,
            confidence=0.99,
        )

    case_match = re.fullmatch(r"(?:case|when)\s*,?\s*(?P<patterns>.+)", header, re.I)
    if case_match:
        return _CaseBlock(patterns=_parse_case_patterns(case_match.group("patterns")), body=body)

    default_match = re.fullmatch(r"(?:default|else|otherwise)", header, re.I)
    if default_match:
        return _DefaultBlock(body=body)

    raise AngisSyntaxError("Unknown block header. Try If, While, Repeat, For each, Define, or When.")


def _parse_case_patterns(text: str) -> list[object]:
    from .intents import _split_items, parse_text_value
    raw = text.strip()
    parts = _split_items(raw) if "," in raw else [raw]
    return [parse_text_value(p.strip()) for p in parts if p.strip()]


def _parse_command_call(text: str, source: str) -> FunctionCall | None:
    match = re.fullmatch(r"(?:run|call|use)\s+command\s*,?\s*(?P<body>.+)", text, re.I)
    if not match:
        return None
    body = match.group("body").strip()
    result_name = ""
    result_match = re.fullmatch(r"(?P<body>.+?)\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*)", body, re.I)
    if result_match:
        body = result_match.group("body").strip()
        result_name = result_match.group("result")
    name_text, args_text = _split_command_with(body)
    return FunctionCall(
        name=_command_name(name_text),
        args=_parse_call_args(args_text),
        result_name=result_name,
        source=source,
        confidence=0.99,
    )


def _parse_direct_command_call(text: str, source: str) -> FunctionCall | None:
    result_name = ""
    result_match = re.fullmatch(r"(?P<body>.+?)\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*)", text, re.I)
    if result_match:
        text = result_match.group("body").strip()
        result_name = result_match.group("result")
    name_text, args_text = _split_command_with(text)
    if not args_text:
        return None
    return FunctionCall(
        name=_command_name(name_text),
        args=_parse_call_args(args_text),
        result_name=result_name,
        source=source,
        confidence=0.88,
    )


def _parse_template_command_call(text: str, source: str, command_templates: list[CommandTemplate]) -> FunctionCall | None:
    result_name = ""
    result_match = re.fullmatch(r"(?P<body>.+?)\s+as\s+(?P<result>[A-Za-z_][A-Za-z0-9_]*)", text, re.I)
    if result_match:
        text = result_match.group("body").strip()
        result_name = result_match.group("result")
    text = _normalize_phrase_call(text)
    for regex, name, slots in reversed(command_templates):
        match = regex.fullmatch(text)
        if not match:
            continue
        return FunctionCall(
            name=name,
            args=[_parse_slot_value(match.group(slot_name).strip(), slot_type) for slot_name, slot_type in slots],
            result_name=result_name,
            source=source,
            confidence=0.91,
        )
    return None


def _parse_command_definition(text: str) -> tuple[str, list[str], dict[str, str]]:
    name_text, params_text = _split_command_with(text.strip())
    params, param_types = _parse_param_names(params_text)
    return _command_name(name_text), params, param_types


def _parse_inline_phrase_definition(normalized: str, line: SourceLine, command_templates: list[CommandTemplate]) -> FunctionDef | None:
    match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<phrase>.+?)\s+means\s+(?P<body>.+)", normalized, re.I)
    if not match:
        match = re.fullmatch(r"when\s+i\s+say\s+(?P<phrase>.+?),?\s+it\s+means\s+(?P<body>.+)", normalized, re.I)
    if not match:
        match = re.fullmatch(r"teach\s+angis\s+(?P<phrase>.+?)\s+to\s+mean\s+(?P<body>.+)", normalized, re.I)
    if not match:
        return None
    name, params = _parse_phrase_definition(match.group("phrase"))
    body: list[object] = []
    available_templates = [template for template in command_templates if template[1] != name]
    for step in _split_inline_phrase_steps(match.group("body")):
        body_line = SourceLine(number=line.number, text=step, tokens=[], indent=line.indent)
        body.append(_parse_simple(body_line, available_templates))
    return FunctionDef(name=name, params=params, body=body, source=line.text, confidence=0.99)


def _split_inline_phrase_steps(text: str) -> list[str]:
    steps: list[str] = []
    start = 0
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if char in {"'", '"'}:
            quote = None if quote == char else char
            index += 1
            continue
        separator_length = _inline_step_separator_length(text, index) if quote is None else 0
        if separator_length:
            step = text[start:index].strip()
            if step:
                steps.append(step)
            start = index + separator_length
            index = start
            continue
        index += 1
    final_step = text[start:].strip()
    if final_step:
        steps.append(final_step)
    if not steps:
        raise AngisSyntaxError("Phrase definition needs an action after means.")
    return steps


def _inline_step_separator_length(text: str, index: int) -> int:
    for separator in (" and then ", " then ", ";"):
        if text[index : index + len(separator)].lower() == separator:
            return len(separator)
    return 0


def _parse_phrase_definition(text: str) -> tuple[str, list[str]]:
    template = text.strip()
    slots = _phrase_slots(template)
    params = [name for name, _slot_type in slots]
    if len(params) != len(set(params)):
        raise AngisSyntaxError("Phrase command slots must have unique names.")
    literal_name = re.sub(r"\{[A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)?\}", " ", template)
    literal_name = re.sub(r"\(([^()]+)\)", lambda match: match.group(1).split("|", 1)[0], literal_name)
    literal_name = literal_name.replace("[", " ").replace("]", " ")
    return _command_name(literal_name), params


def _register_command_template(text: str, instruction: object, command_templates: list[CommandTemplate]) -> None:
    if not isinstance(instruction, FunctionDef):
        return
    header = _strip_trailing_period(text[:-1].strip())
    phrase_match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<body>.+)", header, re.I)
    if not phrase_match:
        phrase_match = re.fullmatch(r"when\s+i\s+say\s+(?P<body>.+)", header, re.I)
    if not phrase_match:
        return
    regex, slots = _phrase_regex(phrase_match.group("body"))
    command_templates.append((regex, instruction.name, slots))


def _phrase_regex(template: str) -> tuple[re.Pattern[str], list[SlotSpec]]:
    slots: list[SlotSpec] = []
    parts: list[str] = []
    cursor = 0
    template = _normalize_phrase_template(template)
    while cursor < len(template):
        slot = re.search(r"[\{\[\(]", template[cursor:])
        if slot is None:
            parts.append(_phrase_literal_regex(template[cursor:]))
            break
        start = cursor + slot.start()
        parts.append(_phrase_literal_regex(template[cursor:start]))
        opener = template[start]
        if opener == "{":
            end = template.find("}", start + 1)
            if end == -1:
                raise AngisSyntaxError("Phrase slot is missing a closing }.")
            slot_name, slot_type = _parse_slot_spec(template[start + 1 : end].strip())
            slots.append((slot_name, slot_type))
            parts.append(rf"(?P<{slot_name}>{_slot_regex(slot_type)})")
        elif opener == "[":
            end = template.find("]", start + 1)
            if end == -1:
                raise AngisSyntaxError("Optional phrase text is missing a closing ].")
            optional = template[start + 1 : end].strip()
            if not optional:
                raise AngisSyntaxError("Optional phrase text cannot be empty.")
            if any(char in optional for char in "{}[]()|"):
                raise AngisSyntaxError("Optional phrase text cannot contain slots, groups, or alternatives.")
            parts.append(rf"(?:\s*{_phrase_literal_regex(optional)}\s*)?")
        else:
            end = template.find(")", start + 1)
            if end == -1:
                raise AngisSyntaxError("Phrase alternatives are missing a closing ).")
            raw_choices = template[start + 1 : end].strip()
            choices = [choice.strip() for choice in raw_choices.split("|") if choice.strip()]
            if len(choices) < 2:
                raise AngisSyntaxError("Phrase alternatives must look like (word|other word).")
            if any(any(char in choice for char in "{}[]()") for choice in choices):
                raise AngisSyntaxError("Phrase alternatives cannot contain slots or nested groups.")
            parts.append(r"(?:\s*(?:" + "|".join(_phrase_literal_regex(choice) for choice in choices) + r")\s*)")
        cursor = end + 1
    return re.compile(r"\s*" + "".join(parts) + r"\s*", re.I), slots


def _phrase_slots(template: str) -> list[SlotSpec]:
    return [_parse_slot_spec(match.group(1).strip()) for match in re.finditer(r"\{([^{}]+)\}", template)]


def _parse_slot_spec(text: str) -> SlotSpec:
    name, separator, raw_type = text.partition(":")
    slot_name = name.strip()
    slot_type = raw_type.strip().lower() if separator else "value"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", slot_name):
        raise AngisSyntaxError(f"Invalid phrase slot {slot_name!r}.")
    if slot_type not in {"value", "number", "text", "name", "key", "path", "point", "expr", "condition"}:
        raise AngisSyntaxError("Phrase slot types must be value, number, text, name, key, path, point, expr, or condition.")
    return slot_name, slot_type


def _parse_slot_value(text: str, slot_type: str) -> object:
    if slot_type in {"text", "key", "path"}:
        return text
    if slot_type == "name":
        return parse_atom(text)
    if slot_type == "number":
        value = parse_atom(text)
        if not isinstance(value, (int, float)):
            raise AngisSyntaxError(f"Expected a number for phrase slot, got {text!r}.")
        return value
    if slot_type == "point":
        return _parse_point_value(text)
    if slot_type == "expr":
        return parse_expression(text)
    if slot_type == "condition":
        return _parse_condition(text)
    return parse_text_value(text)


def _slot_regex(slot_type: str) -> str:
    if slot_type == "number":
        return r"[+-]?\d+(?:\.\d+)?"
    if slot_type in {"name", "key"}:
        return r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?(?:\[[^\]]+\])?"
    if slot_type == "path":
        return r"(?:[A-Za-z0-9_./~:@%+=,-]|\s)+?"
    if slot_type == "point":
        number = r"[+-]?\d+(?:\.\d+)?"
        separator = r"(?:\s*,\s*|\s+)"
        return rf"\(?\s*{number}{separator}{number}{separator}{number}\s*\)?"
    if slot_type in {"expr", "condition"}:
        return r".+"
    return r".+?"


def _parse_point_value(text: str) -> list[int | float]:
    cleaned = text.strip().strip("()")
    parts = [part for part in re.split(r"(?:\s*,\s*|\s+)", cleaned) if part]
    if len(parts) != 3:
        raise AngisSyntaxError("Point slots need three numbers.")
    point: list[int | float] = []
    for part in parts:
        value = parse_atom(part)
        if not isinstance(value, (int, float)):
            raise AngisSyntaxError(f"Expected a number in point slot, got {part!r}.")
        point.append(value)
    return point


def _phrase_literal_regex(text: str) -> str:
    escaped = re.escape(text)
    escaped = re.sub(
        r"(?<=[A-Za-z0-9])\\\.(?=[A-Za-z0-9])",
        lambda _match: r"(?:\.|\s+)",
        escaped,
    )
    return re.sub(r"\\\s+", r"\\s*", escaped)


def _normalize_phrase_call(text: str) -> str:
    normalized = re.sub(r"[,:;!?]+", " ", text.strip())
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _normalize_phrase_template(text: str) -> str:
    normalized = re.sub(r"[,;!?]+", " ", text.strip())
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _split_command_with(text: str) -> tuple[str, str]:
    match = re.fullmatch(r"(?P<name>.+?)\s+with\s+(?P<values>.+)", text, re.I)
    if match:
        return match.group("name").strip(), match.group("values").strip()
    return text.strip(), ""


def _command_name(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", text.strip().lower()).strip("_")
    if not cleaned or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", cleaned):
        raise AngisSyntaxError(f"Invalid command name {text!r}.")
    return f"command_{cleaned}"


def _parse_condition(text: str) -> object:
    normalized = text.strip()
    not_between_match = re.fullmatch(
        r"(?P<left>.+?)\s+(?:is\s+)?(?:not\s+between|outside)\s+(?P<low>.+?)\s+and\s+(?P<high>.+)",
        normalized,
        re.I,
    )
    if not_between_match:
        return LogicalCondition(
            "or",
            Condition(
                left=parse_expression(not_between_match.group("left")),
                operator="<",
                right=parse_expression(not_between_match.group("low")),
            ),
            Condition(
                left=parse_expression(not_between_match.group("left")),
                operator=">",
                right=parse_expression(not_between_match.group("high")),
            ),
        )
    between_match = re.fullmatch(
        r"(?P<left>.+?)\s+(?:is\s+)?between\s+(?P<low>.+?)\s+and\s+(?P<high>.+)",
        normalized,
        re.I,
    )
    if between_match:
        return LogicalCondition(
            "and",
            Condition(
                left=parse_expression(between_match.group("left")),
                operator=">=",
                right=parse_expression(between_match.group("low")),
            ),
            Condition(
                left=parse_expression(between_match.group("left")),
                operator="<=",
                right=parse_expression(between_match.group("high")),
            ),
        )
    split = _split_condition(normalized, "or")
    if split is not None:
        left, right = split
        return LogicalCondition("or", _parse_condition(left), _parse_condition(right))
    split = _split_condition(normalized, "and")
    if split is not None:
        left, right = split
        return LogicalCondition("and", _parse_condition(left), _parse_condition(right))
    not_match = re.fullmatch(r"(?:not|it\s+is\s+not\s+true\s+that)\s+(?P<condition>.+)", normalized, re.I)
    if not_match:
        return LogicalCondition("not", _parse_condition(not_match.group("condition")))
    empty_match = re.fullmatch(
        r"(?P<left>.+?)\s+(?:is\s+)?(?P<operator>empty|not\s+empty|blank|not\s+blank)",
        normalized,
        re.I,
    )
    if empty_match:
        raw_operator = re.sub(r"\s+", " ", empty_match.group("operator").lower())
        operator = "not empty" if raw_operator in {"not empty", "not blank"} else "empty"
        return Condition(
            left=parse_expression(empty_match.group("left")),
            operator=operator,
            right=True,
        )
    text_match = re.fullmatch(
        r"(?P<left>.+?)\s+(?P<operator>does\s+not\s+start\s+with|doesn't\s+start\s+with|does\s+not\s+begin\s+with|doesn't\s+begin\s+with|does\s+not\s+end\s+with|doesn't\s+end\s+with|starts\s+with|begins\s+with|ends\s+with)\s+(?P<right>.+?)(?P<ignore_case>\s+ignoring\s+case)?",
        normalized,
        re.I,
    )
    if text_match:
        raw_operator = re.sub(r"\s+", " ", text_match.group("operator").lower())
        negative = "not" in raw_operator or "doesn't" in raw_operator
        if "start" in raw_operator or "begin" in raw_operator:
            operator = "not starts with" if negative else "starts with"
        else:
            operator = "not ends with" if negative else "ends with"
        if text_match.group("ignore_case"):
            operator = f"{operator} ignoring case"
        return Condition(
            left=parse_expression(text_match.group("left")),
            operator=operator,
            right=parse_expression(text_match.group("right")),
        )
    contains_patterns = (
        (
            r"(?P<left>.+?)\s+(?:does\s+not\s+contain|doesn't\s+contain|does\s+not\s+include|doesn't\s+include|has\s+no)\s+(?P<right>.+)",
            "not contains",
        ),
        (
            r"(?P<right>.+?)\s+(?:is\s+not\s+in|isn't\s+in)\s+(?P<left>.+)",
            "not contains",
        ),
        (
            r"(?P<left>.+?)\s+(?:contains|includes|has)\s+(?P<right>.+)",
            "contains",
        ),
        (
            r"(?P<right>.+?)\s+is\s+in\s+(?P<left>.+)",
            "contains",
        ),
    )
    for pattern, operator in contains_patterns:
        match = re.fullmatch(pattern, normalized, re.I)
        if match:
            return Condition(
                left=parse_expression(match.group("left")),
                operator=operator,
                right=parse_expression(match.group("right")),
            )
    patterns = (
        (r"(?P<left>.+?)\s+(?:is\s+not|does\s+not\s+equal|is\s+not\s+same\s+as|is\s+different\s+from)\s+(?P<right>.+)", "!="),
        (r"(?P<left>.+?)\s+(?:is\s+at\s+least|at\s+least|is\s+greater\s+than\s+or\s+equal\s+to|greater\s+than\s+or\s+equal\s+to|is\s+bigger\s+than\s+or\s+equal\s+to|bigger\s+than\s+or\s+equal\s+to|>=)\s+(?P<right>.+)", ">="),
        (r"(?P<left>.+?)\s+(?:is\s+at\s+most|at\s+most|is\s+less\s+than\s+or\s+equal\s+to|less\s+than\s+or\s+equal\s+to|is\s+smaller\s+than\s+or\s+equal\s+to|smaller\s+than\s+or\s+equal\s+to|<=)\s+(?P<right>.+)", "<="),
        (r"(?P<left>.+?)\s+(?:is\s+greater\s+than|greater\s+than|is\s+bigger\s+than|bigger\s+than|is\s+more\s+than|more\s+than|is\s+over|over|>)\s+(?P<right>.+)", ">"),
        (r"(?P<left>.+?)\s+(?:is\s+less\s+than|less\s+than|is\s+smaller\s+than|smaller\s+than|is\s+under|under|<)\s+(?P<right>.+)", "<"),
        (r"(?P<left>.+?)\s+(?:is\s+same\s+as|same\s+as|equals|equal\s+to|matches|is)\s+(?P<right>.+)", "=="),
    )
    for pattern, operator in patterns:
        match = re.fullmatch(pattern, normalized, re.I)
        if match:
            return Condition(
                left=parse_expression(match.group("left")),
                operator=operator,
                right=parse_expression(match.group("right")),
            )
    try:
        return Condition(left=parse_expression(normalized), operator="truthy", right=True)
    except AngisSyntaxError as exc:
        raise AngisSyntaxError(f"Could not understand condition {text!r}.") from exc


def _split_condition(text: str, operator: str) -> tuple[str, str] | None:
    pattern = re.compile(rf"\s+{operator}\s+", re.I)
    quote: str | None = None
    matches = list(pattern.finditer(text))
    for match in reversed(matches):
        prefix = text[: match.start()]
        quote = None
        for char in prefix:
            if char in {"'", '"'}:
                quote = None if quote == char else char
        if quote is None:
            left = text[: match.start()].strip()
            right = text[match.end() :].strip()
            if left and right:
                return left, right
    return None


def _parse_param_names(text: str) -> tuple[list[str], dict[str, str]]:
    if not text.strip():
        return [], {}
    cleaned = re.sub(r"\s+and\s+", ",", text.strip(), flags=re.I)
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    params: list[str] = []
    param_types: dict[str, str] = {}
    for part in parts:
        type_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(text|string|number|int|decimal|float|bool|boolean|list|map|dict|any)", part, re.I)
        if type_match:
            name = type_match.group(1)
            ptype = type_match.group(2).lower()
            params.append(name)
            param_types[name] = ptype
        else:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part):
                raise AngisSyntaxError(f"Invalid function parameter {part!r}.")
            params.append(part)
    return params, param_types


def _parse_call_args(text: str) -> list[object]:
    if not text.strip():
        return []
    from .intents import _split_items  # Local import keeps this parser helper private to intents.

    return [parse_text_value(item) for item in _split_items(text)]


def _extract_switch_cases(body: list[object]) -> tuple[list[tuple[list[object], list[object]]], list[object] | None]:
    cases: list[tuple[list[object], list[object]]] = []
    default_body: list[object] | None = None
    for item in body:
        if isinstance(item, _CaseBlock):
            cases.append((item.patterns, item.body))
        elif isinstance(item, _DefaultBlock):
            default_body = item.body
    return cases, default_body


def _is_except_header(text: str) -> bool:
    return bool(re.fullmatch(r"(?:except|catch|on\s+error)(?:\s+as\s+\w+)?\s*:?", text.strip(), re.I))


def _parse_except_variable(text: str) -> str:
    match = re.fullmatch(r"(?:except|catch|on\s+error)\s+as\s+(?P<var>\w+)\s*:?", text.strip(), re.I)
    return match.group("var") if match else ""


def _is_finally_header(text: str) -> bool:
    return bool(re.fullmatch(r"finally\s*:?", text.strip(), re.I))


def parse_condition(text: str) -> object:
    return _parse_condition(text)


def _strip_trailing_period(text: str) -> str:
    return text[:-1].strip() if text.endswith(".") else text.strip()
