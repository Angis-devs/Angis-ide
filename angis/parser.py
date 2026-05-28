"""Parser that converts Angis source into IR instructions."""

from __future__ import annotations

import re
from pathlib import Path
import textwrap

from .errors import AngisError, AngisSyntaxError
from .intents import match_intent, parse_atom, parse_expression, parse_text_value
import dataclasses

from .lang import ENGLISH, SPANISH, FRENCH, GERMAN, get_language, set_language as _set_lang

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
    MatchBlock,
    ObjectMethodCall,
    ObjectMethodDef,
    RangeExpr,
    ReduceItems,
    RepeatBlock,
    ReturnValue,
    SetVar,
    SwitchBlock,
    TryBlock,
    Spawn,
    Await,
    AsyncFunctionDef,
    AsyncForBlock,
    AsyncWithBlock,
    AwaitExpr,
    PythonEval,
    PythonExec,
    PythonImport,
    WatchFile,
    NativeGUI,
    BlueprintInitDef,
    WhileBlock,
    WithBlock,
    YieldValue,
    ErrorDef,
    OperatorOverloadDef,
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
        package_match = re.fullmatch(r"use\s+(?:package|module\s+folder)\s+(.+?)\s+as\s+([^\W\d]\w*)", stripped, re.I)
        if package_match:
            raw_path = package_match.group(1).strip().strip('"').strip("'")
            namespace = package_match.group(2)
            package_path = (base_path / raw_path).expanduser().resolve()
            expanded.extend(_expand_module_directory(package_path, namespace, seen))
            continue
        selected_function_match = re.fullmatch(r"use\s+functions?\s+(.+?)\s+from\s+module\s+(.+)", stripped, re.I)
        if selected_function_match:
            names = [name.strip() for name in selected_function_match.group(1).split(",") if name.strip()]
            raw_path = selected_function_match.group(2).strip().strip('"').strip("'")
            module_path = (base_path / raw_path).expanduser().resolve()
            expanded.append(_expand_selected_module_functions(module_path, names, seen))
            continue
        everything_module_match = re.fullmatch(r"use\s+(?:everything|all)\s+from\s+module\s+(.+?)\s+as\s+([^\W\d]\w*)", stripped, re.I)
        if everything_module_match:
            raw_path = everything_module_match.group(1).strip().strip('"').strip("'")
            namespace = everything_module_match.group(2)
            module_path = (base_path / raw_path).expanduser().resolve()
            expanded.append(_expand_module_file(module_path, namespace, seen))
            continue
        module_match = re.fullmatch(r"use\s+module\s+(.+?)\s+as\s+([^\W\d]\w*)", stripped, re.I)
        if module_match:
            raw_path = module_match.group(1).strip().strip('"').strip("'")
            namespace = module_match.group(2)
            module_path = (base_path / raw_path).expanduser().resolve()
            expanded.append(_expand_module_file(module_path, namespace, seen))
            continue
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


def _expand_module_file(module_path: Path, namespace: str, seen: set[Path]) -> str:
    if module_path.suffix != ".angis":
        raise AngisSyntaxError("Module files must end in .angis.")
    if module_path in seen:
        raise AngisSyntaxError(f"Recursive module import blocked for {module_path}.")
    seen.add(module_path)
    expanded_source = _expand_includes(module_path.read_text(encoding="utf-8"), module_path.parent, seen)
    seen.remove(module_path)
    return _namespace_module_source(expanded_source, namespace)


def _expand_selected_module_functions(module_path: Path, names: list[str], seen: set[Path]) -> str:
    if module_path.suffix != ".angis":
        raise AngisSyntaxError("Module files must end in .angis.")
    if module_path in seen:
        raise AngisSyntaxError(f"Recursive module import blocked for {module_path}.")
    wanted = {name.strip() for name in names if name.strip()}
    if not wanted:
        raise AngisSyntaxError("Use function from module needs at least one function name.")
    seen.add(module_path)
    expanded_source = _expand_includes(module_path.read_text(encoding="utf-8"), module_path.parent, seen)
    seen.remove(module_path)
    selected = _select_module_function_blocks(expanded_source, wanted)
    missing = wanted - _module_function_names(selected)
    if missing:
        raise AngisSyntaxError(f"Module {module_path.name} does not define function(s): {', '.join(sorted(missing))}.")
    return selected


def _select_module_function_blocks(source: str, names: set[str]) -> str:
    lines = source.splitlines()
    selected: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = _strip_trailing_period(line.strip().removesuffix(":").strip())
        function_match = re.fullmatch(
            r"(?:define|function)\s*,?\s*(?P<name>[^\W\d]\w*)"
            r"(?:\s+with\s+.+?)?"
            r"(?:\s*->\s*(?:text|string|number|int|decimal|float|bool|boolean|list|map|dict|any))?",
            stripped,
            re.I,
        )
        if not function_match or function_match.group("name") not in names:
            index += 1
            continue
        start = index
        index += 1
        while index < len(lines):
            next_line = lines[index]
            if next_line.strip() and len(next_line) - len(next_line.lstrip(" ")) == 0:
                break
            index += 1
        selected.extend(lines[start:index])
        selected.append("")
    return "\n".join(selected)


def _expand_module_directory(directory: Path, namespace: str, seen: set[Path]) -> list[str]:
    if not directory.is_dir():
        raise AngisSyntaxError("Package imports need a folder.")
    expanded: list[str] = []
    for module_path in sorted(directory.rglob("*.angis")):
        relative_namespace = "_".join([namespace, *module_path.relative_to(directory).with_suffix("").parts])
        expanded.append(_expand_module_file(module_path.resolve(), relative_namespace, seen))
    return expanded


def _namespace_module_source(source: str, namespace: str) -> str:
    names = _module_function_names(source)
    if not names:
        return source
    rewritten: list[str] = []
    for line in source.splitlines():
        rewritten.append(_namespace_module_line(line, namespace, names))
    return "\n".join(rewritten)


def _module_function_names(source: str) -> set[str]:
    names: set[str] = set()
    for line in source.splitlines():
        header = _strip_trailing_period(line.strip().removesuffix(":").strip())
        command_match = re.fullmatch(r"(?:define\s+command|command)\s*,?\s*(?P<body>.+)", header, re.I)
        if command_match:
            name, _params, _param_types = _parse_command_definition(command_match.group("body"))
            names.add(name)
            continue
        function_match = re.fullmatch(
            r"(?:define|function)\s*,?\s*(?P<name>[^\W\d]\w*)"
            r"(?:\s+with\s+.+?)?"
            r"(?:\s*->\s*(?:text|string|number|int|decimal|float|bool|boolean|list|map|dict|any))?",
            header,
            re.I,
        )
        if function_match:
            names.add(function_match.group("name"))
    return names


def _namespace_module_line(line: str, namespace: str, names: set[str]) -> str:
    for name in sorted(names, key=len, reverse=True):
        prefixed = f"{namespace}_{name}"
        line = re.sub(rf"(?i)(\b(?:define|function)\s*,?\s*){re.escape(name)}\b", rf"\1{prefixed}", line)
        line = re.sub(rf"(?i)(\b(?:call|run)\s*,?\s*){re.escape(name)}\b", rf"\1{prefixed}", line)
        line = re.sub(rf"(?i)(\b(?:spawn|background|async)\s+(?:call\s+)?)({re.escape(name)})\b", rf"\1{prefixed}", line)
    return line


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
    pending_decorators: list[str] = []
    while index < len(lines):
        line = lines[index]
        if line.indent < indent:
            break
        if line.indent > indent:
            raise AngisSyntaxError(f"Line {line.number}: Unexpected indentation.")
        text_stripped = line.text.strip()
        decorator_match = re.fullmatch(r"@(?P<name>[^\W\d]\w*)", text_stripped)
        if decorator_match:
            pending_decorators.append(decorator_match.group("name"))
            index += 1
            continue
        try:
            python_block_match = re.fullmatch(r"(?:run|exec|execute)\s+python\s*:", line.text, re.I)
            if python_block_match:
                child_indent = _next_indent(lines, index, indent)
                code_lines: list[str] = []
                next_index = index + 1
                while next_index < len(lines):
                    child_line = lines[next_index]
                    if child_line.indent <= indent:
                        break
                    relative_indent = max(0, child_line.indent - child_indent)
                    code_lines.append(" " * relative_indent + child_line.text)
                    next_index += 1
                if not code_lines:
                    raise AngisSyntaxError("Python block needs indented code.")
                instructions.append(PythonExec(code="\n".join(code_lines), source=line.text, confidence=0.99))
                index = next_index
            elif _is_block_header(line.text):
                child_indent = _next_indent(lines, index, indent)
                body, next_index = _parse_block(lines, index + 1, child_indent, command_templates)
                instruction = _parse_block_header(line, body)
                if pending_decorators and isinstance(instruction, (FunctionDef, AsyncFunctionDef)):
                    instruction = dataclasses.replace(instruction, decorators=list(pending_decorators))
                pending_decorators.clear()
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
                if isinstance(instruction, MatchBlock):
                    cases, default_body = _extract_switch_cases(body)
                    instruction = MatchBlock(
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
        return _phrase_body_from_block_header(_strip_trailing_period(text[:-1].strip()))
    phrase_match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<body>.+?)\s+(?:means|does|runs?|makes?)\s+.+", _strip_trailing_period(text), re.I)
    if phrase_match:
        return phrase_match.group("body")
    phrase_match = re.fullmatch(r"when\s+i\s+say\s+(?P<body>.+?),?\s+(?:it\s+)?(?:means|does|runs?|makes?)\s+.+", _strip_trailing_period(text), re.I)
    if phrase_match:
        return phrase_match.group("body")
    phrase_match = re.fullmatch(r"teach\s+angis\s+(?P<body>.+?)\s+to\s+(?:mean|do|run|make|understand)\s+.+", _strip_trailing_period(text), re.I)
    if not phrase_match:
        return None
    return phrase_match.group("body")


def _strip_phrase_action_suffix(text: str) -> str:
    return re.sub(r"\s*,?\s+(?:do|run|make|mean|understand)\s*$", "", text.strip(), flags=re.I)


def _phrase_body_from_block_header(header: str) -> str | None:
    phrase_match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<body>.+)", header, re.I)
    if phrase_match:
        return phrase_match.group("body")
    phrase_match = re.fullmatch(r"when\s+i\s+say\s+(?P<body>.+)", header, re.I)
    if phrase_match:
        return _strip_phrase_action_suffix(phrase_match.group("body"))
    phrase_match = re.fullmatch(r"teach\s+angis\s+(?P<body>.+?)\s+to(?:\s+(?:do|run|make|mean|understand))?", header, re.I)
    if phrase_match:
        return phrase_match.group("body")
    return None


def _next_indent(lines: list[SourceLine], index: int, parent_indent: int) -> int:
    if index + 1 >= len(lines) or lines[index + 1].indent <= parent_indent:
        raise AngisSyntaxError(f"Line {lines[index].number}: Expected an indented block.")
    return lines[index + 1].indent


def _translate(phrase: str) -> str:
    lang = get_language()
    if lang.code == "en":
        return phrase
    from .lang import ENGLISH as _ENG
    result = phrase
    mappings = [
        (lang._p, _ENG._p), (lang._s, _ENG._s), (lang._m, _ENG._m),
        (lang._a, _ENG._a), (lang._g, _ENG._g), (lang._f, _ENG._f),
        (lang.to, _ENG.to), (lang.equal, _ENG.equal),
        (lang.for_p, _ENG.for_p), (lang.in_p, _ENG.in_p), (lang.as_p, _ENG.as_p),
        (lang.true, _ENG.true), (lang.false, _ENG.false),
        (lang.yes, _ENG.yes), (lang.no, _ENG.no),
        (lang.for_each, _ENG.for_each), (lang.teaching, _ENG.teaching),
        ({lang.if_w}, {_ENG.if_w}), ({lang.else_w}, {_ENG.else_w}),
        ({lang.and_w}, {_ENG.and_w}), ({lang.or_w}, {_ENG.or_w}), ({lang.not_w}, {_ENG.not_w}),
        ({lang.switch}, {_ENG.switch}), ({lang.match}, {_ENG.match}),
        ({lang.case, lang.when}, {_ENG.case, _ENG.when}),
        ({lang.default, lang.otherwise}, {_ENG.default, _ENG.otherwise}),
        ({lang.define}, {_ENG.define}), ({lang.function}, {_ENG.function}),
        ({lang.return_w}, {_ENG.return_w}), ({lang.call}, {_ENG.call}),
        ({lang.blueprint}, {_ENG.blueprint}), ({lang.create}, {_ENG.create}),
        ({lang.named}, {_ENG.named}), ({lang.method}, {_ENG.method}),
        ({lang.phrase}, {_ENG.phrase}), ({lang.command}, {_ENG.command}),
        ({lang.means}, {_ENG.means}), ({lang.repeat}, {_ENG.repeat}),
        ({lang.times}, {_ENG.times}), ({lang.while_w}, {_ENG.while_w}),
        ({lang.lambda_w}, {_ENG.lambda_w}), ({lang.arrow}, {_ENG.arrow}),
        ({lang.fn}, {_ENG.fn}), ({lang.into}, {_ENG.into}),
        ({lang.try_w}, {_ENG.try_w}), ({lang.except_w, lang.catch}, {_ENG.except_w, _ENG.catch}),
        ({lang.finally_w}, {_ENG.finally_w}), ({lang.with_w}, {_ENG.with_w}),
        ({lang.async_w}, {_ENG.async_w}),
        ({lang.spawn, lang.background}, {_ENG.spawn, _ENG.background}),
        ({lang.await_w}, {_ENG.await_w}), ({lang.import_w}, {_ENG.import_w}),
        ({lang.python}, {_ENG.python}), ({lang.include}, {_ENG.include}),
        ({lang.library}, {_ENG.library}), ({lang.pack}, {_ENG.pack}),
        ({lang.use}, {_ENG.use}),
        ({lang.show, lang.say, lang.display, lang.tell}, {_ENG.show, _ENG.say, _ENG.display, _ENG.tell}),
        ({lang.ask}, {_ENG.ask}),
        ({lang.input, lang.prompt, lang.read}, {_ENG.input, _ENG.prompt, _ENG.read}),
        ({lang.raise_w, lang.error_w}, {_ENG.raise_w, _ENG.error_w}),
        ({lang.assert_w}, {_ENG.assert_w}), ({lang.debug}, {_ENG.debug}),
        ({lang.all_w}, {_ENG.all_w}), ({lang.language}, {_ENG.language}),
    ]
    for from_set, to_set in mappings:
        for fw in sorted(from_set, key=len, reverse=True):
            for tw in to_set:
                result = re.sub(rf"(?<!\w){re.escape(fw)}(?!\w)", tw, result, flags=re.I)
    return result


def _parse_simple(line: SourceLine, command_templates: list[CommandTemplate]) -> object:
    translated = _translate(line.text)
    normalized = _strip_trailing_period(translated)
    inline_phrase = _parse_inline_phrase_definition(normalized, line, command_templates)
    if inline_phrase is not None:
        return inline_phrase
    bare_return_match = re.fullmatch(r"return\.?\s*", normalized, re.I)
    if bare_return_match:
        return ReturnValue(value=None, source=line.text, confidence=0.99)
    return_match = re.fullmatch(r"return\s*,?\s*(?P<value>.+)", normalized, re.I)
    if return_match:
        raw = return_match.group("value")
        from .intents import _split_items
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
        r"(?:map|transform)\s+(?P<expr>.+?)\s+(?:over|across)\s+(?P<collection>.+?)\s+as\s+(?P<result>[^\W\d]\w*)",
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
        r"(?:filter|keep)\s+(?P<condition>.+?)\s+(?:from|in)\s+(?P<collection>.+?)\s+as\s+(?P<result>[^\W\d]\w*)",
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
        r"(?:reduce|fold)\s+(?P<expr>.+?)\s+(?:over|across)\s+(?P<collection>.+?)\s+(?:starting|with\s+initial)\s+(?P<initial>.+?)\s+as\s+(?P<result>[^\W\d]\w*)",
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
        r"(?:call|run)\s*,?\s*(?P<object>[^\W\d]\w*)\.(?P<method>[^\W\d]\w*(?:\.[^\W\d]\w*)*)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[^\W\d]\w*(?:\s*,\s*[^\W\d]\w*)*))?",
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
        r"(?:call|run)\s*,?\s*(?P<name>[^\W\d]\w*)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[^\W\d]\w*(?:\s*,\s*[^\W\d]\w*)*))?",
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
    yield_match = re.fullmatch(r"yield\s*,?\s*(?P<value>.+?)(?:\s+as\s+(?P<send_var>[^\W\d]\w*))?", normalized, re.I)
    if yield_match:
        return YieldValue(
            value=parse_text_value(yield_match.group("value")),
            send_var=yield_match.group("send_var") or "",
            source=line.text,
            confidence=0.99,
        )

    spawn_match = re.fullmatch(
        r"(?:(?:spawn|background|async)\s+(?:call\s+)?(?P<name>[^\W\d]\w*)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[^\W\d]\w*))?|(?:run|call)\s+(?P<run_name>[^\W\d]\w*)\s+in\s+background(?:\s+with\s+(?P<run_args>.+?))?(?:\s+as\s+(?P<run_result>[^\W\d]\w*))?)",
        normalized,
        re.I,
    )
    if spawn_match:
        return Spawn(
            name=spawn_match.group("name") or spawn_match.group("run_name"),
            args=_parse_call_args(spawn_match.group("args") or spawn_match.group("run_args") or ""),
            result_name=spawn_match.group("result") or spawn_match.group("run_result") or "",
            source=line.text,
            confidence=0.99,
        )

    await_match = re.fullmatch(
        r"(?:await|wait\s+for)\s+(?P<target>[^\W\d]\w*)(?:\s+as\s+(?P<result>[^\W\d]\w*))?",
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
        r"(?:import|use)\s+python\s+(?P<module>[^\W\d]\w*(?:\.[^\W\d]\w*)*)(?:\s+as\s+(?P<result>[^\W\d]\w*))?(?:\s+with\s+names\s+(?P<names>.+))?",
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

    py_exec_match = re.fullmatch(
        r"(?:run|exec|execute)\s+python\s*[::,]\s*(?P<code>.+)",
        normalized,
        re.I,
    )
    if py_exec_match:
        return PythonExec(
            code=py_exec_match.group("code"),
            source=line.text,
            confidence=0.99,
        )

    py_eval_match = re.fullmatch(
        r"(?:eval\s+python|python\s+eval)\s+(?P<expr>.+?)\s+as\s+(?P<result>[^\W\d]\w*)",
        normalized,
        re.I,
    )
    if py_eval_match:
        return SetVar(
            name=py_eval_match.group("result"),
            value=PythonEval(expression=py_eval_match.group("expr")),
            source=line.text,
            confidence=0.99,
        )

    await_expr_match = re.fullmatch(r"await\s+(?P<value>.+?)\s+as\s+(?P<result>[^\W\d]\w*)", normalized, re.I)
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
        r"(?:use|create|open)\s+(?:native\s+)?gui\s+(?P<action>[^\W\d]\w+)(?:\s+with\s+(?P<args>.+?))?(?:\s+as\s+(?P<result>[^\W\d]\w*))?",
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

    error_def_match = re.fullmatch(r"(?:define\s+error|error)\s*,?\s*(?P<name>[^\W\d]\w*)", normalized, re.I)
    if error_def_match:
        return ErrorDef(name=error_def_match.group("name"), source=line.text, confidence=0.99)

    lang_match = re.fullmatch(
        r"(?:set|use|change)\s+language\s+(?:to\s+)?(?P<lang>[^\W\d]\w+)",
        normalized, re.I,
    )
    if lang_match:
        from .lang import set_language as _sl, get_supported_languages
        lang_name = lang_match.group("lang").lower()
        for lp in get_supported_languages():
            if lang_name == lp["code"] or lang_name == lp["name"].lower():
                _sl(lp["code"])
                from .ir import Print
                return Print(value=f"Language set to {lp['name']}", source=line.text, confidence=0.99)
        raise AngisSyntaxError(f"Unsupported language: {lang_name!r}. Try: en, es, fr, de")

    try:
        return match_intent(translated)
    except AngisError:
        direct_command_call = _parse_direct_command_call(normalized, line.text)
        if direct_command_call is not None:
            return direct_command_call
        raise


def _parse_block_header(line: SourceLine, body: list[object]) -> object:
    header = _translate(_strip_trailing_period(line.text[:-1].strip()))
    if _is_else_header(header + ":"):
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
        r"(?:for\s+each|foreach|for\s+every|for)\s*,?\s*(?P<item>[^\W\d]\w*)\s+in\s+range\s+(?:from\s+)?(?P<start>.+?)\s+to\s+(?P<end>.+)",
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
        r"(?:for\s+each|foreach|for\s+every|for\s+each\s+one|for\s+every\s+one)\s*,?\s*(?P<item>[^\W\d]\w*)\s+(?:in|inside|from)\s+(?P<collection>.+)",
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
        r"for\s*,?\s*(?P<item>[^\W\d]\w*)\s+in\s+(?P<collection>.+)",
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

    phrase_body = _phrase_body_from_block_header(header)
    if phrase_body is not None:
        name, params = _parse_phrase_definition(phrase_body)
        return FunctionDef(
            name=name,
            params=params,
            body=body,
            source=line.text,
            confidence=0.99,
        )

    async_match = re.fullmatch(
        r"(?:define\s+)?async\s+(?:function\s+)?(?P<name>[^\W\d]\w*)"
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
        r"(?:define|function)\s*,?\s*(?P<name>[^\W\d]\w*)"
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
        r"(?:define\s+method|method)\s*,?\s*(?P<method>[^\W\d]\w*)(?:\s+for\s+(?P<object>[^\W\d]\w*))"
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

    overload_match = re.fullmatch(
        r"(?:define\s+)?(?P<operator>[+\-*/%]|==|!=|<=|>=|<>)\s+(?:for|on)\s+(?P<blueprint>[^\W\d]\w*)"
        r"(?:\s+(?:with|taking)\s+(?P<param1>[^\W\d]\w*)\s*,\s*(?P<param2>[^\W\d]\w*))?",
        header,
        re.I,
    )
    if overload_match:
        op_map = {"<>": "!="}
        operator = op_map.get(overload_match.group("operator"), overload_match.group("operator"))
        p1 = overload_match.group("param1") or "left"
        p2 = overload_match.group("param2") or "right"
        return OperatorOverloadDef(
            operator=operator,
            blueprint_name=overload_match.group("blueprint"),
            param1=p1,
            param2=p2,
            body=body,
            source=line.text,
            confidence=0.99,
        )

    key_match = re.fullmatch(r"(?:when|on|if)\s+(?:(?:key\s+)?(?P<name>\w+)\s+(?:is\s+)?(?:pressed|hit|typed|released)|(?P<named>space|enter|up|down|left|right|w|a|s|d|escape|shift|ctrl|alt)\s+(?:key\s+)?(?:pressed|hit|typed|released))", header, re.I)
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

    button_match = re.fullmatch(r"when\s+(?:button\s+)?(?P<name>[^\W\d]\w*)\s+(?:is\s+)?(?:clicked|pressed|tapped)", header, re.I)
    if button_match:
        return EventBlock(kind="button", name=button_match.group("name"), body=body, source=line.text, confidence=0.99)

    every_match = re.fullmatch(r"(?:every|each)\s+(?P<name>\d+)\s*(?:milliseconds|millisecond|ms)", header, re.I)
    if every_match:
        return EventBlock(kind="timer", name=every_match.group("name"), body=body, source=line.text, confidence=0.99)

    collision_match = re.fullmatch(
        r"(?:when|on|if)\s+(?P<left>[^\W\d]\w*)\s+(?:touches|hits|collides\s+with|runs\s+into|bumps\s+into|hits\s+against)\s+(?P<right>[^\W]\w[\w ]*)",
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

    match_match = re.fullmatch(r"match\s*,?\s*(?P<condition>.+)", header, re.I)
    if match_match:
        return MatchBlock(
            condition=parse_expression(match_match.group("condition")),
            cases=[],
            source=line.text,
            confidence=0.99,
        )

    switch_match = re.fullmatch(r"switch\s*,?\s*(?P<condition>.+)", header, re.I)
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
        as_match = re.fullmatch(r"(?P<expr>.+?)\s+as\s+(?P<var>[^\W\d]\w*)", resource_text, re.I)
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

    async_for_match = re.fullmatch(
        r"(?:async|non.blocking)\s+(?:for\s+each|foreach|for)\s*,?\s*(?P<item>[^\W\d]\w*)\s+(?:in|inside|from)\s+(?P<collection>.+)",
        header,
        re.I,
    )
    if async_for_match:
        return AsyncForBlock(
            item_name=async_for_match.group("item"),
            collection=parse_expression(async_for_match.group("collection")),
            body=body,
            source=line.text,
            confidence=0.99,
        )

    async_with_match = re.fullmatch(
        r"(?:async|non.blocking)\s+with\s+,?\s*(?P<resource>.+)",
        header,
        re.I,
    )
    if async_with_match:
        resource_text = async_with_match.group("resource").strip()
        var_name = ""
        as_match = re.fullmatch(r"(?P<expr>.+?)\s+as\s+(?P<var>[^\W\d]\w*)", resource_text, re.I)
        if as_match:
            resource_text = as_match.group("expr").strip()
            var_name = as_match.group("var")
        try:
            resource_expr = parse_expression(resource_text)
        except AngisSyntaxError:
            resource_expr = parse_text_value(resource_text)
        return AsyncWithBlock(
            body=body,
            resource=resource_expr,
            variable_name=var_name,
            source=line.text,
            confidence=0.99,
        )

    init_match = re.fullmatch(
        r"(?:on\s+create|init|constructor|when\s+creating)\s+(?:for\s+)?(?P<blueprint>[^\W\d]\w*)"
        r"(?:\s+with\s+(?P<params>.+))?",
        header,
        re.I,
    )
    if init_match:
        params, param_types = _parse_param_names(init_match.group("params") or "")
        return BlueprintInitDef(
            blueprint_name=init_match.group("blueprint"),
            params=params,
            param_types=param_types,
            body=body,
            source=line.text,
            confidence=0.99,
        )

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
    result_match = re.fullmatch(r"(?P<body>.+?)\s+as\s+(?P<result>[^\W\d]\w*)", body, re.I)
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
    result_match = re.fullmatch(r"(?P<body>.+?)\s+as\s+(?P<result>[^\W\d]\w*)", text, re.I)
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
    result_match = re.fullmatch(r"(?P<body>.+?)\s+as\s+(?P<result>[^\W\d]\w*)", text, re.I)
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
    match = re.fullmatch(r"(?:define\s+phrase|phrase)\s*,?\s*(?P<phrase>.+?)\s+(?:means|does|runs?|makes?)\s+(?P<body>.+)", normalized, re.I)
    if not match:
        match = re.fullmatch(r"when\s+i\s+say\s+(?P<phrase>.+?),?\s+(?:it\s+)?(?:means|does|runs?|makes?)\s+(?P<body>.+)", normalized, re.I)
    if not match:
        match = re.fullmatch(r"teach\s+angis\s+(?P<phrase>.+?)\s+to\s+(?:mean|do|run|make|understand)\s+(?P<body>.+)", normalized, re.I)
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
    literal_name = re.sub(r"\{[^\W\d]\w*(?::[^\W\d]\w*)?\}", " ", template)
    literal_name = re.sub(r"\(([^()]+)\)", lambda match: match.group(1).split("|", 1)[0], literal_name)
    literal_name = literal_name.replace("[", " ").replace("]", " ")
    return _command_name(literal_name), params


def _register_command_template(text: str, instruction: object, command_templates: list[CommandTemplate]) -> None:
    if not isinstance(instruction, FunctionDef):
        return
    header = _strip_trailing_period(text[:-1].strip())
    phrase_body = _phrase_body_from_block_header(header)
    if phrase_body is None:
        return
    regex, slots = _phrase_regex(phrase_body)
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
    if not re.fullmatch(r"[^\W\d]\w*", slot_name):
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
        return r"[^\W\d]\w*(?:\.[^\W\d]\w*)?(?:\[[^\]]+\])?"
    if slot_type == "path":
        return r"(?:(?!\s)[\w./~:@%+=-]|\s)+?"
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
        r"(?<=[\w])\\\.(?=[\w])",
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
    if not cleaned or not re.fullmatch(r"[^\W\d]\w*", cleaned):
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
    type_pattern = r"(text|string|number|int|decimal|float|bool|boolean|list|map|dict|any)(?:\[[^\W\d_,\s\[\]]+\])?"
    for part in parts:
        type_match = re.fullmatch(rf"([^\W\d]\w*)\s*:\s*{type_pattern}", part, re.I)
        if type_match:
            name = type_match.group(1)
            ptype = type_match.group(2).lower()
            params.append(name)
            param_types[name] = ptype
        else:
            name_match = re.fullmatch(r"[^\W\d]\w*", part)
            if name_match:
                params.append(part)
            else:
                raise AngisSyntaxError(f"Invalid function parameter {part!r}.")
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
    return bool(re.fullmatch(r"(?:except|catch|on\s+error)(?:\s+as\s+\w+)?\s*:?", _translate(text.strip()), re.I))


def _parse_except_variable(text: str) -> str:
    match = re.fullmatch(r"(?:except|catch|on\s+error)\s+as\s+(?P<var>\w+)\s*:?", _translate(text.strip()), re.I)
    return match.group("var") if match else ""


def _is_finally_header(text: str) -> bool:
    return bool(re.fullmatch(r"finally\s*:?", _translate(text.strip()), re.I))


def parse_condition(text: str) -> object:
    return _parse_condition(text)


def _strip_trailing_period(text: str) -> str:
    return text[:-1].strip() if text.endswith(".") else text.strip()
