"""Transpile Angis IR instructions to Python code."""

from __future__ import annotations

import re

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
    AppSpec,
    AppStart,
    AppText,
    AssertTrue,
    BinaryOp,
    Break,
    CallExpr,
    Comprehension,
    Condition,
    Continue,
    CreateFromBlueprint,
    CreateList,
    CreateMap,
    CreateObject,
    DebugBreakpoint,
    DebugState,
    DefineBlueprint,
    Divide,
    EventBlock,
    ExecuteSql,
    ExportApp,
    Expression,
    FetchUrl,
    FileAttach,
    FilterItems,
    ForEachBlock,
    FunctionCall,
    FunctionDef,
    GameRule,
    GameStart,
    GetArgs,
    GetEnv,
    HttpRequest,
    IfBlock,
    ImportModule,
    Lambda,
    LengthOf,
    LoadState,
    LogicalCondition,
    MapOver,
    MoveObject,
    Multiply,
    ObjectMethodCall,
    ObjectMethodDef,
    OpenDatabase,
    PackageApp,
    PlaceObject,
    PlaySound,
    PlayVideo,
    Print,
    RaiseError,
    RangeExpr,
    ReadInput,
    ReduceItems,
    Reference,
    RemoveFromList,
    RemoveProperty,
    RepeatBlock,
    ResizeObject,
    ReturnValue,
    RotateObject,
    RunFile,
    SaveState,
    SetAccess,
    SetCamera,
    SetCameraMode,
    SetProperty,
    SetSoundVolume,
    SetVar,
    ShowText,
    SliceOf,
    Sleep,
    StopSound,
    Subtract,
    SwitchBlock,
    TryBlock,
    UnaryOp,
    WithBlock,
    YieldValue,
    ErrorDef,
    UpdateVar,
    UseStdLibAction,
    Value,
    WhileBlock,
)


def transpile(instructions: list[object]) -> str:
    lines: list[str] = []
    for instr in instructions:
        _emit(instr, lines, 0)
    return "\n".join(lines) + "\n"


def _emit(instr: object, lines: list[str], indent: int) -> None:
    prefix = "    " * indent

    if isinstance(instr, Print):
        val = _format_expr(instr.value)
        lines.append(f"{prefix}print({val})")

    elif isinstance(instr, SetVar):
        val = _format_expr(instr.value)
        lines.append(f"{prefix}{instr.name} = {val}")

    elif isinstance(instr, SetAccess):
        target = _format_expr(instr.target)
        val = _format_expr(instr.value)
        lines.append(f"{prefix}{target} = {val}")

    elif isinstance(instr, AddToVar):
        val = _format_expr(instr.value)
        lines.append(f"{prefix}{instr.name} = {instr.name} + {val}")

    elif isinstance(instr, UpdateVar):
        val = _format_expr(instr.value)
        op = instr.op
        lines.append(f"{prefix}{instr.name} {op}= {val}")

    elif isinstance(instr, Add):
        left = _format_expr(instr.left)
        right = _format_expr(instr.right)
        lines.append(f"{prefix}print({left} + {right})")

    elif isinstance(instr, Subtract):
        left = _format_expr(instr.left)
        right = _format_expr(instr.right)
        lines.append(f"{prefix}print({left} - {right})")

    elif isinstance(instr, Multiply):
        left = _format_expr(instr.left)
        right = _format_expr(instr.right)
        lines.append(f"{prefix}print({left} * {right})")

    elif isinstance(instr, Divide):
        left = _format_expr(instr.left)
        right = _format_expr(instr.right)
        lines.append(f"{prefix}print({left} / {right})")

    elif isinstance(instr, IfBlock):
        cond = _format_condition(instr.condition)
        lines.append(f"{prefix}if {cond}:")
        for child in instr.body:
            _emit(child, lines, indent + 1)
        if instr.else_body:
            lines.append(f"{prefix}else:")
            for child in instr.else_body:
                _emit(child, lines, indent + 1)

    elif isinstance(instr, RepeatBlock):
        count = _format_expr(instr.count)
        lines.append(f"{prefix}for _ in range({count}):")
        for child in instr.body:
            _emit(child, lines, indent + 1)

    elif isinstance(instr, WhileBlock):
        cond = _format_condition(instr.condition)
        lines.append(f"{prefix}while {cond}:")
        for child in instr.body:
            _emit(child, lines, indent + 1)

    elif isinstance(instr, ForEachBlock):
        item = instr.item_name
        coll = _format_expr(instr.collection)
        lines.append(f"{prefix}for {item} in {coll}:")
        for child in instr.body:
            _emit(child, lines, indent + 1)

    elif isinstance(instr, Break):
        lines.append(f"{prefix}break")

    elif isinstance(instr, Continue):
        lines.append(f"{prefix}continue")

    elif isinstance(instr, FunctionDef):
        params = ", ".join(instr.params or [])
        name = instr.name.replace("command_", "")
        lines.append(f"{prefix}def {name}({params}):")
        for child in instr.body:
            _emit(child, lines, indent + 1)

    elif isinstance(instr, FunctionCall):
        name = instr.name.replace("command_", "")
        args = ", ".join(_format_expr(a) for a in (instr.args or []))
        if instr.result_name:
            lines.append(f"{prefix}{instr.result_name} = {name}({args})")
        else:
            lines.append(f"{prefix}{name}({args})")

    elif isinstance(instr, ReturnValue):
        val = _format_expr(instr.value)
        lines.append(f"{prefix}return {val}")

    elif isinstance(instr, ImportModule):
        lines.append(f"{prefix}# import {instr.name}")

    elif isinstance(instr, UseStdLibAction):
        lines.append(f"{prefix}{instr.name} = _stdlib_{instr.module}_{instr.action}({_format_stdlib_args(instr.args)})")

    elif isinstance(instr, CreateList):
        items = ", ".join(_format_expr(i) for i in instr.items)
        lines.append(f"{prefix}{instr.name} = [{items}]")

    elif isinstance(instr, CreateMap):
        items = ", ".join(f"{_format_expr_key(k)}: {_format_expr(v)}" for k, v in instr.items.items())
        lines.append(f"{prefix}{instr.name} = {{{items}}}")

    elif isinstance(instr, AddToList):
        item = _format_expr(instr.item)
        lines.append(f"{prefix}{instr.name}.append({item})")

    elif isinstance(instr, RemoveFromList):
        item = _format_expr(instr.item)
        lines.append(f"{prefix}{instr.name}.remove({item})")

    elif isinstance(instr, RemoveProperty):
        lines.append(f"{prefix}del {instr.object_name}['{instr.property_name}']")

    elif isinstance(instr, DebugState):
        lines.append(f"{prefix}print('DEBUG {instr.target}:', {_debug_expr(instr.target)})")

    elif isinstance(instr, ExportApp):
        lines.append(f"{prefix}# export app to {instr.path}")

    elif isinstance(instr, PackageApp):
        lines.append(f"{prefix}# package app to {instr.path}")

    elif isinstance(instr, EventBlock):
        key = f"{instr.kind}:{instr.name.lower()}"
        func_name = "_event_" + re.sub(r"\W+", "_", key).strip("_")
        lines.append(f"{prefix}# event {key}")
        lines.append(f"{prefix}def {func_name}():")
        if instr.body:
            for child in instr.body:
                _emit(child, lines, indent + 1)
        else:
            lines.append(f"{prefix}    pass")

    elif isinstance(instr, FileAttach):
        path = _format_expr(instr.path)
        lines.append(f"{prefix}print(f'Attached file: {{path}}')")

    elif isinstance(instr, Sleep):
        lines.append(f"{prefix}import time; time.sleep({instr.milliseconds / 1000})")

    elif isinstance(instr, FetchUrl):
        url = _format_expr(instr.url)
        lines.append(f"{prefix}{instr.name} = {url}")

    elif isinstance(instr, HttpRequest):
        lines.append(f"{prefix}# HTTP {instr.method} {instr.url}")

    elif isinstance(instr, ReadInput):
        prompt = _format_expr(instr.prompt) if instr.prompt else "''"
        if instr.result_name:
            lines.append(f"{prefix}{instr.result_name} = input({prompt})")
        else:
            lines.append(f"{prefix}input({prompt})")

    elif isinstance(instr, OpenDatabase):
        lines.append(f"{prefix}# open database {instr.path} as {instr.name}")

    elif isinstance(instr, ExecuteSql):
        sql = _format_expr(instr.sql)
        if instr.name:
            lines.append(f"{prefix}{instr.name} = _execute_sql({instr.database!r}, {sql})")
        else:
            lines.append(f"{prefix}_execute_sql({instr.database!r}, {sql})")

    elif isinstance(instr, PlayVideo):
        lines.append(f"{prefix}# play video {instr.path} at x {instr.x} y {instr.y}")

    elif isinstance(instr, PlaySound):
        lines.append(f"{prefix}# play sound {instr.name}")

    elif isinstance(instr, StopSound):
        lines.append(f"{prefix}# stop sound")

    elif isinstance(instr, SetSoundVolume):
        lines.append(f"{prefix}# set volume to {instr.volume}")

    elif isinstance(instr, RaiseError):
        msg = _format_expr(instr.message)
        if instr.error_type:
            lines.append(f"{prefix}raise Exception(f\"{instr.error_type}: {{{msg}}}\")")
        else:
            lines.append(f"{prefix}raise Exception({msg})")

    elif isinstance(instr, ErrorDef):
        lines.append(f"{prefix}# defined error: {instr.name}")

    elif isinstance(instr, YieldValue):
        val = _format_expr(instr.value)
        lines.append(f"{prefix}yield {val}")

    elif isinstance(instr, AssertTrue):
        lines.append(f"{prefix}assert {instr.condition_text}, {_format_expr(instr.message)}")

    elif isinstance(instr, GetArgs):
        if instr.result_name:
            lines.append(f"{prefix}{instr.result_name} = sys.argv[1:]")
        else:
            lines.append(f"{prefix}print(sys.argv[1:])")

    elif isinstance(instr, GetEnv):
        lines.append(f"{prefix}{instr.result_name} = os.environ.get({instr.var_name!r}, '')")

    elif isinstance(instr, DebugBreakpoint):
        lines.append(f"{prefix}breakpoint()  # {instr.label}")

    elif isinstance(instr, SwitchBlock):
        val = _format_expr(instr.condition)
        lines.append(f"{prefix}match {val}:")
        for patterns, body in instr.cases:
            for pat in patterns:
                pat_val = _format_expr(pat)
                lines.append(f"{prefix}    case {pat_val}:")
                for child in body:
                    _emit(child, lines, indent + 2)
        if instr.default_body:
            lines.append(f"{prefix}    case _:")
            for child in instr.default_body:
                _emit(child, lines, indent + 2)

    elif isinstance(instr, TryBlock):
        lines.append(f"{prefix}try:")
        for child in instr.body:
            _emit(child, lines, indent + 1)
        if instr.except_body:
            var_part = f" as {instr.variable_name}" if instr.variable_name else ""
            lines.append(f"{prefix}except{var_part}:")
            for child in instr.except_body:
                _emit(child, lines, indent + 1)
        if instr.finally_body:
            lines.append(f"{prefix}finally:")
            for child in instr.finally_body:
                _emit(child, lines, indent + 1)

    elif isinstance(instr, WithBlock):
        res = _format_expr(instr.resource)
        var_part = f" as {instr.variable_name}" if instr.variable_name else ""
        lines.append(f"{prefix}with {res}{var_part}:")
        for child in instr.body:
            _emit(child, lines, indent + 1)

    elif isinstance(instr, MapOver):
        coll = _format_expr(instr.collection)
        exp = _format_expr(instr.expr)
        lines.append(f"{prefix}{instr.result_name} = [{exp} for it in {coll}]")

    elif isinstance(instr, FilterItems):
        coll = _format_expr(instr.collection)
        cond = _format_expr(instr.condition)
        lines.append(f"{prefix}{instr.result_name} = [it for it in {coll} if {cond}]")

    elif isinstance(instr, ReduceItems):
        coll = _format_expr(instr.collection)
        expr = _format_expr(instr.expr)
        init = _format_expr(instr.initial)
        lines.append(f"{prefix}acc = {init}")
        lines.append(f"{prefix}for it in {coll}:")
        lines.append(f"{prefix}    acc = {expr}")
        lines.append(f"{prefix}{instr.result_name} = acc")

    elif isinstance(instr, ShowText):
        lines.append(f"{prefix}print({instr.text!r})")

    elif isinstance(instr, SaveState):
        lines.append(f"{prefix}# save state to {instr.path}")

    elif isinstance(instr, LoadState):
        lines.append(f"{prefix}# load state from {instr.path}")

    elif isinstance(instr, AppStart):
        lines.append(f"{prefix}# App: {_format_expr(instr.title)}")

    elif isinstance(instr, AppText):
        lines.append(f"{prefix}# Text: {_format_expr(instr.value)}")

    elif isinstance(instr, AppButton):
        lines.append(f"{prefix}# Button: {_format_expr(instr.label)}")

    elif isinstance(instr, AppScene):
        lines.append(f"{prefix}# Scene: {_format_expr(instr.name)}")

    elif isinstance(instr, AppLayout):
        lines.append(f"{prefix}# Layout: {instr.kind}")

    elif isinstance(instr, AppSize):
        lines.append(f"{prefix}# Window size: {instr.width}x{instr.height}")

    elif isinstance(instr, AppLoadingScreen):
        lines.append(f"{prefix}# Loading screen")

    elif isinstance(instr, AppFileAttach):
        path = _format_expr(instr.path)
        lines.append(f"{prefix}# Attach file {path}")

    elif isinstance(instr, CreateObject):
        name = instr.name
        kind = instr.kind
        x, y, z = instr.x, instr.y, instr.z
        lines.append(f"{prefix}{name} = CreatorObject(kind={kind!r}, name={name!r}, x={x}, y={y}, z={z})")

    elif isinstance(instr, MoveObject):
        lines.append(f"{prefix}# move {instr.name} {instr.direction} {instr.amount}")

    elif isinstance(instr, PlaceObject):
        lines.append(f"{prefix}# place {instr.name} at x {instr.x} y {instr.y} z {instr.z}")

    elif isinstance(instr, ResizeObject):
        lines.append(f"{prefix}# resize {instr.name} to {instr.width}x{instr.height}")

    elif isinstance(instr, SetProperty):
        val = _format_expr(instr.value)
        lines.append(f"{prefix}{instr.object_name}.{instr.property_name} = {val}")

    elif isinstance(instr, GameStart):
        lines.append(f"{prefix}# Game: {_format_expr(instr.name)}")

    elif isinstance(instr, GameRule):
        lines.append(f"{prefix}# Game rule: {_format_expr(instr.text)}")

    elif isinstance(instr, RunFile):
        lines.append(f"{prefix}# run file {instr.path}")

    elif isinstance(instr, ObjectMethodDef):
        params = ", ".join(instr.params or [])
        sep = ", " if params else ""
        lines.append(f"{prefix}def {instr.method_name}(self{sep}{params}):")
        for child in instr.body:
            _emit(child, lines, indent + 1)

    elif isinstance(instr, ObjectMethodCall):
        args = ", ".join(_format_expr(a) for a in (instr.args or []))
        if instr.result_name:
            lines.append(f"{prefix}{instr.result_name} = {instr.object_name}.{instr.method_name}({args})")
        else:
            lines.append(f"{prefix}{instr.object_name}.{instr.method_name}({args})")

    elif isinstance(instr, DefineBlueprint):
        items = ", ".join(f"{k!r}: {_format_expr(v)}" for k, v in instr.items.items())
        lines.append(f"{prefix}Blueprint_{instr.name} = {{{items}}}")

    elif isinstance(instr, CreateFromBlueprint):
        items = ", ".join(f"{k!r}: {_format_expr(v)}" for k, v in instr.items.items())
        lines.append(f"{prefix}{instr.name} = _create_from_blueprint({instr.blueprint_name!r}, {{}}, {{{items}}})")

    elif isinstance(instr, AppBackground):
        lines.append(f"{prefix}# background color: {instr.color}")

    elif isinstance(instr, RotateObject):
        lines.append(f"{prefix}# rotate {instr.name} by {instr.angle} on {instr.axis}")

    elif isinstance(instr, SetCamera):
        lines.append(f"{prefix}# camera at {instr.x}, {instr.y}, {instr.z}")

    elif isinstance(instr, SetCameraMode):
        lines.append(f"{prefix}# camera mode: {instr.mode}")

    elif isinstance(instr, AnimateObject):
        lines.append(f"{prefix}# animate {instr.name} {instr.direction} {instr.amount} every {instr.milliseconds}ms")


def _format_expr(expr: Expression) -> str:
    if isinstance(expr, Reference):
        return expr.name
    if isinstance(expr, BinaryOp):
        left = _format_expr(expr.left)
        right = _format_expr(expr.right)
        return f"({left} {expr.op} {right})"
    if isinstance(expr, UnaryOp):
        right = _format_expr(expr.right)
        return f"{expr.op}({right})"
    if isinstance(expr, Access):
        target = _format_expr(expr.target)
        key = _format_expr(expr.key)
        if isinstance(expr.key, Reference) or isinstance(expr.key, str):
            key_str = _format_expr(expr.key)
            if key_str.isidentifier():
                return f"{target}.{key_str}"
        return f"{target}[{key}]"
    if isinstance(expr, SliceOf):
        target = _format_expr(expr.target)
        start = _format_expr(expr.start)
        end = _format_expr(expr.end)
        return f"{target}[{start}:{end}]"
    if isinstance(expr, LengthOf):
        val = _format_expr(expr.value)
        return f"len({val})"
    if isinstance(expr, CallExpr):
        args = ", ".join(_format_expr(arg) for arg in expr.args)
        return f"{expr.name}({args})"
    if isinstance(expr, RangeExpr):
        start = _format_expr(expr.start)
        end = _format_expr(expr.end)
        return f"range({start}, {end} + 1)"
    if isinstance(expr, Lambda):
        params = ", ".join(expr.params)
        body = _format_expr(expr.body)
        return f"lambda {params}: {body}"
    if isinstance(expr, Comprehension):
        var = expr.item_var
        coll = _format_expr(expr.collection)
        ex = _format_expr(expr.expr)
        filt = f" if {_format_expr(expr.filter_expr)}" if expr.filter_expr else ""
        if expr.is_dict and expr.key_expr is not None:
            key = _format_expr(expr.key_expr)
            return f"{{{key}: {ex} for {var} in {coll}{filt}}}"
        return f"[{ex} for {var} in {coll}{filt}]"
    if isinstance(expr, list):
        items = ", ".join(_format_expr(item) for item in expr)
        return f"[{items}]"
    if isinstance(expr, dict):
        items = ", ".join(f"{_format_expr_key(k)}: {_format_expr(v)}" for k, v in expr.items())
        return f"{{{items}}}"
    if isinstance(expr, Condition):
        return _format_condition(expr)
    if isinstance(expr, str):
        return repr(expr)
    if isinstance(expr, bool):
        return "True" if expr else "False"
    if isinstance(expr, (int, float)):
        return repr(expr)
    return repr(expr) if not isinstance(expr, str) else repr(expr)


def _format_expr_key(key: str) -> str:
    if key.isidentifier():
        return repr(key)
    return repr(key)


def _format_condition(cond: object) -> str:
    if isinstance(cond, LogicalCondition):
        if cond.operator == "not":
            return f"not ({_format_condition(cond.left)})"
        left = _format_condition(cond.left)
        right = _format_condition(cond.right)
        return f"({left} {cond.operator} {right})"
    if isinstance(cond, Condition):
        left = _format_expr(cond.left)
        if cond.operator == "truthy":
            return f"bool({left})"
        if cond.operator == "empty":
            return f"len({left}) == 0"
        if cond.operator == "not empty":
            return f"len({left}) != 0"
        if cond.operator in {"contains", "not contains"}:
            right = _format_expr(cond.right)
            op = "in" if cond.operator == "contains" else "not in"
            return f"{right} {op} {left}"
        right = _format_expr(cond.right)
        op_map = {
            "==": "==", "!=": "!=", ">": ">", "<": "<",
            ">=": ">=", "<=": "<=",
            "starts with": "startswith",
            "not starts with": "not startswith",
            "ends with": "endswith",
            "not ends with": "not endswith",
        }
        py_op = op_map.get(cond.operator, cond.operator)
        if py_op in {"startswith", "not startswith", "endswith", "not endswith"}:
            neg = "not " if py_op.startswith("not ") else ""
            method = "startswith" if "start" in py_op else "endswith"
            return f"{neg}{left}.{method}({right})"
        return f"({left} {py_op} {right})"
    return _format_expr(cond)


def _format_stdlib_args(args: dict[str, Expression]) -> str:
    parts = ", ".join(f"{k}={_format_expr(v)}" for k, v in args.items())
    return parts


def _debug_expr(target: str) -> str:
    if target == "variables":
        return "vars()"
    if target == "all":
        return "globals()"
    return repr(target)
