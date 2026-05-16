"""Interpreter for Angis IR."""

from __future__ import annotations

import csv
import builtins
import re
import threading
import asyncio
import importlib
import os
from dataclasses import dataclass, field
import datetime as dt
import html
import json
import math
from pathlib import Path
import random
import re
import sqlite3
import time
from typing import Callable, TextIO
from urllib.error import URLError
from urllib.request import Request, urlopen

from .errors import AngisRuntimeError
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
    Sleep,
    BinaryOp,
    Break,
    Comprehension,
    Continue,
    CreateFromBlueprint,
    CreateList,
    CreateMap,
    CreateObject,
    CreatorObject,
    DefineBlueprint,
    DebugBreakpoint,
    DebugState,
    Divide,
    EventBlock,
    ExecuteSql,
    ExportApp,
    Expression,
    FetchUrl,
    FileAttach,
    FileInfo,
    FilterItems,
    ForEachBlock,
    FunctionCall,
    FunctionDef,
    GameRule,
    GameSpec,
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
    RotateObject,
    RunFile,
    SetCamera,
    SetCameraMode,
    ReturnValue,
    SaveState,
    SetAccess,
    SetProperty,
    SetSoundVolume,
    SetVar,
    ShowText,
    SliceOf,
    StopSound,
    Subtract,
    SwitchBlock,
    TryBlock,
    ErrorDef,
    Spawn,
    Await,
    AsyncFunctionDef,
    AwaitExpr,
    PythonImport,
    WatchFile,
    NativeGUI,
    WithBlock,
    YieldValue,
    UnaryOp,
    UpdateVar,
    UseStdLibAction,
    WhileBlock,
)


MAX_WHILE_ITERATIONS = 10000
MAX_FOR_EACH_ITEMS = 10000


class _FunctionReturn(Exception):
    def __init__(self, value: object) -> None:
        self.value = value


class _LoopControl(Exception):
    def __init__(self, kind: str) -> None:
        self.kind = kind  # "break" or "continue"


class _GeneratorYield(Exception):
    def __init__(self, value: object) -> None:
        self.value = value


def _has_yield(instructions: list[object]) -> bool:
    for instr in instructions:
        if isinstance(instr, YieldValue):
            return True
        if isinstance(instr, (ForEachBlock, WhileBlock, RepeatBlock, IfBlock, TryBlock, SwitchBlock, WithBlock)):
            children: list[object] = []
            if isinstance(instr, (ForEachBlock, WhileBlock, RepeatBlock, WithBlock)):
                children = instr.body
            elif isinstance(instr, IfBlock):
                children = instr.body + (instr.else_body or [])
            elif isinstance(instr, TryBlock):
                children = instr.body + instr.except_body + instr.finally_body
            elif isinstance(instr, SwitchBlock):
                for _, case_body in instr.cases:
                    children.extend(case_body)
                if instr.default_body:
                    children.extend(instr.default_body)
            if _has_yield(children):
                return True
    return False


@dataclass
class Interpreter:
    output: TextIO | None = None
    app_runner: Callable[[AppSpec], None] | None = None
    game_runner: Callable[[GameSpec], None] | None = None
    base_path: Path | None = None
    variables: dict[str, object] = field(default_factory=dict)
    functions: dict[str, FunctionDef] = field(default_factory=dict)
    object_methods: dict[tuple[str, str], ObjectMethodDef] = field(default_factory=dict)
    blueprints: dict[str, dict[str, object]] = field(default_factory=dict)
    lists: dict[str, list[object]] = field(default_factory=dict)
    maps: dict[str, dict[str, object]] = field(default_factory=dict)
    databases: dict[str, sqlite3.Connection] = field(default_factory=dict)
    imports: list[str] = field(default_factory=list)
    app: AppSpec | None = None
    game: GameSpec | None = None
    _pending_notifications: list[str] = field(default_factory=list)
    error_types: dict[str, bool] = field(default_factory=dict)
    _futures: dict[str, threading.Thread] = field(default_factory=dict)
    _future_results: dict[str, object] = field(default_factory=dict)
    _future_counter: int = 0
    python_modules: dict[str, object] = field(default_factory=dict)
    async_functions: dict[str, AsyncFunctionDef] = field(default_factory=dict)
    _async_loop: object = None
    _tk_root: object = None
    _tk_widgets: dict[str, object] = field(default_factory=dict)

    def run(self, instructions: list[object]) -> list[str]:
        captured: list[str] = []
        self._hoist_definitions(instructions)
        for instruction in instructions:
            self._run_instruction(instruction, captured)
        if self.app is not None:
            if self.app_runner:
                self.app_runner(self.app)
            else:
                message = f"App ready: {self.app.title}"
                captured.append(message)
                if self.output:
                    print(message, file=self.output)
        if self.game is not None:
            if self.game_runner:
                self.game_runner(self.game)
            else:
                message = f"Game ready: {self.game.name}"
                captured.append(message)
                if self.output:
                    print(message, file=self.output)
        return captured

    def _hoist_definitions(self, instructions: list[object]) -> None:
        for instruction in instructions:
            if isinstance(instruction, FunctionDef):
                self.functions[instruction.name] = instruction
            elif isinstance(instruction, ObjectMethodDef):
                self.object_methods[(instruction.object_name, instruction.method_name)] = instruction
            elif isinstance(instruction, ErrorDef):
                self.error_types[instruction.name] = True
            elif isinstance(instruction, AsyncFunctionDef):
                self.async_functions[instruction.name] = instruction

    def _run_instruction(self, instruction: object, captured: list[str]) -> None:
        if isinstance(instruction, IfBlock):
            if self._condition_is_true(instruction.condition):
                self._run_nested(instruction.body, captured)
            elif instruction.else_body:
                self._run_nested(instruction.else_body, captured)
            return
        if isinstance(instruction, RepeatBlock):
            count = self.evaluate(instruction.count)
            if not isinstance(count, int) or count < 0:
                raise AngisRuntimeError("Repeat count must be a non-negative whole number.")
            for _ in range(count):
                try:
                    self._run_nested(instruction.body, captured)
                except _LoopControl as ctrl:
                    if ctrl.kind == "break":
                        break
            return
        if isinstance(instruction, WhileBlock):
            iterations = 0
            while self._condition_is_true(instruction.condition):
                if iterations >= MAX_WHILE_ITERATIONS:
                    raise AngisRuntimeError("While loop stopped after 10000 runs. Check the condition.")
                try:
                    self._run_nested(instruction.body, captured)
                except _LoopControl as ctrl:
                    if ctrl.kind == "break":
                        break
                    if ctrl.kind == "continue":
                        iterations += 1
                        continue
                iterations += 1
            return
        if isinstance(instruction, ForEachBlock):
            values = self._iterable_values(instruction.collection)
            if len(values) > MAX_FOR_EACH_ITEMS:
                raise AngisRuntimeError("For each loop stopped because the collection is too large.")
            previous = self.variables.get(instruction.item_name)
            had_previous = instruction.item_name in self.variables
            try:
                for value in values:
                    self.variables[instruction.item_name] = value
                    try:
                        self._run_nested(instruction.body, captured)
                    except _LoopControl as ctrl:
                        if ctrl.kind == "break":
                            break
                        if ctrl.kind == "continue":
                            continue
            finally:
                if had_previous:
                    self.variables[instruction.item_name] = previous
                else:
                    self.variables.pop(instruction.item_name, None)
            return
        if isinstance(instruction, Break):
            raise _LoopControl("break")
        if isinstance(instruction, Continue):
            raise _LoopControl("continue")
        if isinstance(instruction, SwitchBlock):
            value = self.evaluate(instruction.condition)
            matched = False
            for patterns, case_body in instruction.cases:
                for pattern in patterns:
                    pattern_value = self.evaluate(pattern)
                    if value == pattern_value:
                        self._run_nested(case_body, captured)
                        matched = True
                        break
                if matched:
                    break
            if not matched and instruction.default_body:
                self._run_nested(instruction.default_body, captured)
            return
        if isinstance(instruction, TryBlock):
            try:
                self._run_nested(instruction.body, captured)
            except AngisRuntimeError as exc:
                if instruction.except_body:
                    if instruction.variable_name:
                        self.variables[instruction.variable_name] = str(exc)
                    self._run_nested(instruction.except_body, captured)
            finally:
                if instruction.finally_body:
                    self._run_nested(instruction.finally_body, captured)
            return
        if isinstance(instruction, WithBlock):
            resource = self.evaluate(instruction.resource)
            if isinstance(resource, str):
                res_text: str = resource
                file_match = re.fullmatch(r'file\s+"(.+)"', res_text.strip())
                if file_match:
                    res_path = file_match.group(1)
                else:
                    res_path = res_text
                res_file = None
                try:
                    res_file = builtins.open(res_path, "r")
                    if instruction.variable_name:
                        self.variables[instruction.variable_name] = res_file
                    self._run_nested(instruction.body, captured)
                finally:
                    if res_file:
                        res_file.close()
            elif isinstance(resource, dict):
                obj_name = instruction.variable_name
                enter = resource.get("__enter__")
                if enter is None and obj_name:
                    em = self.object_methods.get((obj_name, "__enter__"))
                    if em:
                        def _call_cm(captured_copy):
                            return self._call_object_method(em, obj_name, [], captured_copy)
                        enter = _call_cm
                if enter:
                    ctx = enter(captured) if callable(enter) else self._call_function(enter, [], captured)
                else:
                    ctx = resource
                if obj_name:
                    self.variables[obj_name] = ctx
                try:
                    self._run_nested(instruction.body, captured)
                finally:
                    exit_method = resource.get("__exit__")
                    if exit_method is None and obj_name:
                        em = self.object_methods.get((obj_name, "__exit__"))
                        if em:
                            exit_method = lambda captured_copy: self._call_object_method(em, obj_name, [], captured_copy)
                    if exit_method:
                        exit_method(captured) if callable(exit_method) else self._call_function(exit_method, [None, None, None], captured)
                    else:
                        close_method = resource.get(instruction.close_action)
                        if close_method is None and obj_name:
                            cm = self.object_methods.get((obj_name, instruction.close_action))
                            if cm:
                                close_method = lambda captured_copy: self._call_object_method(cm, obj_name, [], captured_copy)
                        if close_method:
                            close_method(captured) if callable(close_method) else self._call_function(close_method, [], captured)
            else:
                if instruction.variable_name:
                    self.variables[instruction.variable_name] = resource
                self._run_nested(instruction.body, captured)
            return
        if isinstance(instruction, YieldValue):
            raise AngisRuntimeError("Yield can only be used inside a function.")
        if isinstance(instruction, Spawn):
            name = instruction.name
            if name not in self.functions:
                raise AngisRuntimeError(f"Cannot spawn unknown function {name!r}.")
            function = self.functions[name]
            t_args = instruction.args
            t_captured = captured
            t_result_name = instruction.result_name
            self._future_counter += 1
            t_future_name = f"_future_{name}_{self._future_counter}"
            result_container: list[object] = [None]
            error_container: list[Exception | None] = [None]

            def _target():
                try:
                    val = self._call_function(function, t_args, t_captured)
                    result_container[0] = val
                except Exception as exc:
                    error_container[0] = exc

            t = threading.Thread(target=_target, daemon=True)
            t.start()
            self._futures[t_future_name] = t
            self._future_results[t_future_name] = result_container
            if t_result_name:
                self.variables[t_result_name] = t_future_name
            return
        if isinstance(instruction, Await):
            target = instruction.target
            resolved = str(self.variables.get(target, target))
            fut = self._futures.get(resolved)
            if fut is None:
                raise AngisRuntimeError(f"Cannot await unknown task {instruction.target!r}.")
            fut.join()
            result_container = self._future_results.get(resolved, [None])
            result = result_container[0] if result_container else None
            if instruction.result_name:
                self.variables[instruction.result_name] = result
            self._futures.pop(resolved, None)
            self._future_results.pop(resolved, None)
            return
        if isinstance(instruction, PythonImport):
            mod_name = instruction.module
            try:
                mod = importlib.import_module(mod_name)
            except ImportError as exc:
                raise AngisRuntimeError(f"Could not import Python module {mod_name!r}: {exc}")
            self.python_modules[mod_name] = mod
            if instruction.names:
                for n in instruction.names:
                    obj = getattr(mod, n, None)
                    if obj is not None:
                        self.variables[n] = obj
            if instruction.result_name:
                self.variables[instruction.result_name] = mod
                self.python_modules[instruction.result_name] = mod
            return
        if isinstance(instruction, AsyncFunctionDef):
            self.async_functions[instruction.name] = instruction
            return
        if isinstance(instruction, AwaitExpr):
            if self._async_loop is None:
                self._async_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._async_loop)
            coro_val = self.evaluate(instruction.value)
            if asyncio.iscoroutine(coro_val):
                result = self._async_loop.run_until_complete(coro_val)
            else:
                result = coro_val
            if instruction.result_name:
                self.variables[instruction.result_name] = result
            return
        if isinstance(instruction, WatchFile):
            path = instruction.path
            import subprocess, sys, time
            resolved = Path(path).expanduser().resolve() if self.base_path else Path(path).resolve()
            last_mtime = resolved.stat().st_mtime if resolved.is_file() else 0
            captured.append(f"Watching {resolved} for changes...")
            captured.append("Hit Ctrl+C to stop.")

            def _watcher():
                nonlocal last_mtime
                if not resolved.is_file():
                    return
                new_mtime = resolved.stat().st_mtime
                if new_mtime != last_mtime:
                    last_mtime = new_mtime
                    try:
                        new_source = resolved.read_text(encoding="utf-8")
                        from .parser import parse
                        new_instructions = parse(new_source)
                        self._hoist_definitions(new_instructions)
                        new_captured: list[str] = []
                        for instr in new_instructions:
                            self._run_instruction(instr, new_captured)
                        for msg in new_captured:
                            captured.append(msg)
                            if self.output:
                                print(msg, file=self.output)
                    except Exception as exc:
                        err = f"Reload error: {exc}"
                        captured.append(err)
                        if self.output:
                            print(err, file=self.output)

            import threading as _thr
            def _watch_loop():
                try:
                    while True:
                        _watcher()
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            t = _thr.Thread(target=_watch_loop, daemon=True)
            t.start()
            return
        if isinstance(instruction, NativeGUI):
            try:
                import tkinter as tk
                import tkinter.ttk as ttk
            except ImportError:
                raise AngisRuntimeError("Tkinter is not available on this system.")
            action = instruction.action
            args = {k: self.evaluate(v) for k, v in instruction.args.items()}
            if action == "window":
                title = args.get("title", "Angis App")
                width = int(args.get("width", 600))
                height = int(args.get("height", 400))
                root = tk.Tk()
                root.title(str(title))
                root.geometry(f"{width}x{height}")
                self._tk_root = root
                if instruction.result_name:
                    self.variables[instruction.result_name] = root
            elif action == "label":
                text = str(args.get("text", ""))
                parent = args.get("parent", self._tk_root)
                label = tk.Label(parent, text=text)
                label.pack()
                if instruction.result_name:
                    self._tk_widgets[instruction.result_name] = label
            elif action == "button":
                text = str(args.get("text", ""))
                parent = args.get("parent", self._tk_root)
                btn = tk.Button(parent, text=text)
                btn.pack()
                if instruction.result_name:
                    self._tk_widgets[instruction.result_name] = btn
            elif action == "entry":
                parent = args.get("parent", self._tk_root)
                entry = tk.Entry(parent)
                entry.pack()
                if instruction.result_name:
                    self._tk_widgets[instruction.result_name] = entry
            elif action == "run":
                if self._tk_root:
                    self._tk_root.mainloop()
            elif action == "get":
                widget_name = str(args.get("widget", ""))
                w = self._tk_widgets.get(widget_name) or self._tk_root
                if instruction.result_name:
                    self.variables[instruction.result_name] = w.get() if hasattr(w, "get") else w
            elif action == "set":
                widget_name = str(args.get("widget", ""))
                value = str(args.get("value", ""))
                w = self._tk_widgets.get(widget_name)
                if w and hasattr(w, "insert"):
                    w.delete(0, tk.END)
                    w.insert(0, value)
                elif w and hasattr(w, "config"):
                    w.config(text=value)
            elif action == "on_click":
                widget_name = str(args.get("widget", ""))
                command_name = str(args.get("command", ""))
                w = self._tk_widgets.get(widget_name)
                if w and command_name in self.functions:
                    w.config(command=lambda: self._call_function(self.functions[command_name], [], captured))
            return
        if isinstance(instruction, MapOver):
            collection = self.evaluate(instruction.collection)
            if not isinstance(collection, list):
                raise AngisRuntimeError("Map needs a list.")
            result = []
            for item in collection:
                self.variables["it"] = item
                result.append(self.evaluate(instruction.expr))
            self.variables.pop("it", None)
            self.variables[instruction.result_name] = result
            return
        if isinstance(instruction, FilterItems):
            collection = self.evaluate(instruction.collection)
            if not isinstance(collection, list):
                raise AngisRuntimeError("Filter needs a list.")
            result = []
            for item in collection:
                self.variables["it"] = item
                if self.evaluate(instruction.condition):
                    result.append(item)
            self.variables.pop("it", None)
            self.variables[instruction.result_name] = result
            return
        if isinstance(instruction, ReduceItems):
            collection = self.evaluate(instruction.collection)
            if not isinstance(collection, list) or not collection:
                raise AngisRuntimeError("Reduce needs a non-empty list.")
            initial = self.evaluate(instruction.initial)
            acc = initial
            for item in collection:
                self.variables["acc"] = acc
                self.variables["it"] = item
                acc = self.evaluate(instruction.expr)
            self.variables.pop("acc", None)
            self.variables.pop("it", None)
            self.variables[instruction.result_name] = acc
            return
        if isinstance(instruction, FunctionDef):
            self.functions[instruction.name] = instruction
            return
        if isinstance(instruction, ObjectMethodDef):
            self.object_methods[(instruction.object_name, instruction.method_name)] = instruction
            return
        if isinstance(instruction, ObjectMethodCall):
            key = (instruction.object_name, instruction.method_name)
            method = self.object_methods.get(key)
            if method is None:
                object_type = self._object_type(instruction.object_name)
                if object_type:
                    method = self.object_methods.get((object_type, instruction.method_name))
            if method is None:
                obj_name = instruction.object_name
                mod = self.python_modules.get(obj_name)
                if mod is None and obj_name in self.variables:
                    mod = self.variables[obj_name]
                if mod is not None:
                    py_method = getattr(mod, instruction.method_name, None)
                    if py_method is not None:
                        args = [self.evaluate(a) for a in (instruction.args or [])]
                        value = py_method(*args)
                        if instruction.result_name:
                            self.variables[instruction.result_name] = value
                        return
                raise AngisRuntimeError(f"Method {instruction.object_name}.{instruction.method_name} has not been defined.")
            value = self._call_object_method(method, instruction.object_name, instruction.args or [], captured)
            if instruction.result_name:
                self.variables[instruction.result_name] = value
            return
        if isinstance(instruction, FunctionCall):
            if instruction.name in self.variables and isinstance(self.variables[instruction.name], Lambda):
                value = self._call_lambda(self.variables[instruction.name], instruction.args or [], captured)
                if instruction.result_name:
                    self.variables[instruction.result_name] = value
                return
            if instruction.name in self.async_functions:
                async_fn = self.async_functions[instruction.name]
                async def _run_async():
                    return await self._run_async_function(async_fn, instruction.args or [], captured)
                if self._async_loop is None:
                    self._async_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._async_loop)
                value = self._async_loop.run_until_complete(_run_async())
                if instruction.result_name:
                    self.variables[instruction.result_name] = value
                return
            if instruction.name not in self.functions:
                raise AngisRuntimeError(f"Function {instruction.name!r} has not been defined.")
            value = self._call_function(self.functions[instruction.name], instruction.args or [], captured)
            if instruction.result_name:
                self.variables[instruction.result_name] = value
            return
        if isinstance(instruction, ReturnValue):
            raise _FunctionReturn(self.evaluate(instruction.value))
        if isinstance(instruction, ImportModule):
            self._import_module(instruction.name)
            return
        if isinstance(instruction, RunFile):
            self._run_angis_file(instruction.path)
            return
        if isinstance(instruction, ReadInput):
            prompt = _format_value(self.evaluate(instruction.prompt)) if instruction.prompt else ""
            if self.output and prompt:
                print(prompt, end="", file=self.output)
            try:
                value = input()
            except (EOFError, KeyboardInterrupt):
                value = ""
            if instruction.result_name:
                self.variables[instruction.result_name] = value
            captured.append(value)
            if self.output:
                print(value, file=self.output)
            return
        if isinstance(instruction, RaiseError):
            message = _format_value(self.evaluate(instruction.message))
            if instruction.error_type:
                if instruction.error_type not in self.error_types:
                    raise AngisRuntimeError(f"Unknown error type '{instruction.error_type}'. Define it with 'Define error {instruction.error_type}'.")
                raise AngisRuntimeError(f"{instruction.error_type}: {message}")
            raise AngisRuntimeError(message)
        if isinstance(instruction, AssertTrue):
            from .parser import parse_condition
            condition = parse_condition(instruction.condition_text)
            result = self._condition_is_true(condition)
            if not result:
                message = _format_value(self.evaluate(instruction.message))
                raise AngisRuntimeError(f"Assertion failed: {message}")
            return
        if isinstance(instruction, GetArgs):
            import sys
            value = sys.argv[1:]
            if instruction.result_name:
                self.variables[instruction.result_name] = value
            captured.append(str(value))
            if self.output:
                print(value, file=self.output)
            return
        if isinstance(instruction, GetEnv):
            import os
            value = os.environ.get(instruction.var_name, "")
            if instruction.result_name:
                self.variables[instruction.result_name] = value
            captured.append(value)
            if self.output:
                print(value, file=self.output)
            return
        if isinstance(instruction, EventBlock):
            app = self._require_app()
            if app.events is None:
                app.events = {}
            app.events[f"{instruction.kind}:{instruction.name.lower()}"] = instruction.body
            return

        result = self.execute(instruction)
        if isinstance(
            instruction,
            (Add, Subtract, Multiply, Divide, Print, FileAttach, ShowText, DebugState, ExportApp, PackageApp, OpenDatabase, ExecuteSql, DebugBreakpoint),
        ):
            captured.append(_format_value(result))
            if self.output:
                print(_format_value(result), file=self.output)

    def execute(self, instruction: object) -> object:
        if isinstance(instruction, Print):
            return self.evaluate(instruction.value)
        if isinstance(instruction, SetVar):
            value = self.evaluate(instruction.value)
            self.variables[instruction.name] = value
            return value
        if isinstance(instruction, SetAccess):
            try:
                value = self.evaluate(instruction.value)
            except AngisRuntimeError as exc:
                if isinstance(instruction.value, Reference) and "has not been set" in str(exc):
                    value = instruction.value.name
                else:
                    raise
            self._assign_access(instruction.target, value)
            return value
        if isinstance(instruction, AddToVar):
            current = _require_number(self.variables.get(instruction.name, 0))
            value = _require_number(self.evaluate(instruction.value))
            self.variables[instruction.name] = current + value
            return self.variables[instruction.name]
        if isinstance(instruction, UpdateVar):
            if instruction.name not in self.variables:
                raise AngisRuntimeError(f"Variable {instruction.name!r} has not been set.")
            current = _require_number(self.variables[instruction.name])
            value = _require_number(self.evaluate(instruction.value))
            if instruction.op == "+":
                self.variables[instruction.name] = current + value
            elif instruction.op == "-":
                self.variables[instruction.name] = current - value
            elif instruction.op == "*":
                self.variables[instruction.name] = current * value
            elif instruction.op == "/":
                if value == 0:
                    raise AngisRuntimeError("Cannot divide by zero.")
                self.variables[instruction.name] = current / value
            else:
                raise AngisRuntimeError(f"Unknown variable update {instruction.op!r}.")
            return self.variables[instruction.name]
        if isinstance(instruction, Add):
            return _require_number(self.evaluate(instruction.left)) + _require_number(self.evaluate(instruction.right))
        if isinstance(instruction, Subtract):
            return _require_number(self.evaluate(instruction.left)) - _require_number(self.evaluate(instruction.right))
        if isinstance(instruction, Multiply):
            return _require_number(self.evaluate(instruction.left)) * _require_number(self.evaluate(instruction.right))
        if isinstance(instruction, Divide):
            right = _require_number(self.evaluate(instruction.right))
            if right == 0:
                raise AngisRuntimeError("Cannot divide by zero.")
            return _require_number(self.evaluate(instruction.left)) / right
        if isinstance(instruction, AppStart):
            self.app = AppSpec(
                title=_format_value(self.evaluate(instruction.title)),
                texts=[],
                buttons=[],
                imports=list(self.imports),
                backend="pygame" if "pygame" in self.imports else "tk",
                files=[],
                objects=[],
                events={},
                lists={},
                maps={},
                layout={"kind": "free", "columns": 1},
                resources={},
            )
            return self.app
        if isinstance(instruction, AppLoadingScreen):
            app = self._require_app()
            image_path = instruction.image_path or str(_default_loading_asset("loading screen.png"))
            audio_path = instruction.audio_path or str(_default_loading_asset("loading-adieo.mp3"))
            image = self._file_info(image_path)
            audio = self._file_info(audio_path)
            app.loading_image = image.path
            app.loading_audio = audio.path
            return app
        if isinstance(instruction, AppScene):
            app = self._require_app()
            app.scene = _format_value(self.evaluate(instruction.name)).lower()
            return app
        if isinstance(instruction, AppLayout):
            app = self._require_app()
            app.layout = {"kind": instruction.kind, "columns": instruction.columns}
            return app
        if isinstance(instruction, AppSize):
            app = self._require_app()
            if instruction.width < 240 or instruction.height < 180:
                raise AngisRuntimeError("Window size must be at least 240 by 180.")
            app.width = min(instruction.width, 2400)
            app.height = min(instruction.height, 1600)
            return app
        if isinstance(instruction, AppBackground):
            app = self._require_app()
            app.bg = instruction.color
            return app
        if isinstance(instruction, AppText):
            app = self._require_app()
            app.texts.append(_format_value(self.evaluate(instruction.value)))
            return app
        if isinstance(instruction, AppButton):
            app = self._require_app()
            app.buttons.append(_format_value(self.evaluate(instruction.label)))
            return app
        if isinstance(instruction, AppFileAttach):
            app = self._require_app()
            raw_path = _format_value(self.evaluate(instruction.path))
            if instruction.file_name:
                app.resources = app.resources or {}
                app.resources[instruction.file_name] = raw_path
            if app.files is None:
                app.files = []
            app.files.append(
                self._file_info(
                    raw_path,
                    x=int(_require_number(self.evaluate(instruction.x))),
                    y=int(_require_number(self.evaluate(instruction.y))),
                    z=int(_require_number(self.evaluate(instruction.z))),
                )
            )
            return app
        if isinstance(instruction, CreateObject):
            app = self._require_app()
            if app.objects is None:
                app.objects = []
            app.objects.append(
                CreatorObject(
                    kind=instruction.kind,
                    name=instruction.name,
                    x=instruction.x,
                    y=instruction.y,
                    z=instruction.z,
                    text=instruction.text,
                    path=instruction.path,
                    properties=dict(instruction.properties or {}),
                )
            )
            if instruction.kind == "image":
                app.files = app.files or []
                app.files.append(self._file_info(instruction.path, x=instruction.x, y=instruction.y, z=instruction.z))
            if instruction.kind == "button":
                app.buttons.append(instruction.text)
            return app
        if isinstance(instruction, MoveObject):
            return instruction
        if isinstance(instruction, PlaceObject):
            app = self._require_app()
            target = _find_object(app, instruction.name)
            target.x = instruction.x
            target.y = instruction.y
            target.z = instruction.z
            return target
        if isinstance(instruction, ResizeObject):
            app = self._require_app()
            target = _find_object(app, instruction.name)
            target.properties = target.properties or {}
            target.properties["width"] = instruction.width
            target.properties["height"] = instruction.height
            return target
        if isinstance(instruction, SetProperty):
            raw = instruction.value
            if isinstance(raw, str) and raw in self.variables:
                value = self.variables[raw]
            elif isinstance(raw, str) and raw in self.lists:
                value = self.lists[raw]
            elif isinstance(raw, str) and raw in self.maps:
                value = self.maps[raw]
            else:
                value = self.evaluate(instruction.value)
            if instruction.object_name in self.maps:
                self.maps[instruction.object_name][instruction.property_name] = value
                if self.app is not None:
                    self.app.maps = self.app.maps or {}
                    self.app.maps[instruction.object_name] = dict(self.maps[instruction.object_name])
                return self.maps[instruction.object_name]
            app = self._require_app()
            target = _find_object(app, instruction.object_name)
            target.properties = target.properties or {}
            target.properties[instruction.property_name] = value
            return target
        if isinstance(instruction, RotateObject):
            app = self._require_app()
            target = _find_object(app, instruction.name)
            target.properties = target.properties or {}
            angle_key = f"rotation_{instruction.axis}"
            current = float(target.properties.get(angle_key, 0))
            target.properties[angle_key] = current + instruction.angle
            return target
        if isinstance(instruction, SetCamera):
            app = self._require_app()
            app.camera_init = {"x": instruction.x, "y": instruction.y, "z": instruction.z,
                               "rx": instruction.rotation_x, "ry": instruction.rotation_y}
            return instruction
        if isinstance(instruction, SetCameraMode):
            app = self._require_app()
            app.camera_mode = instruction.mode
            return instruction
        if isinstance(instruction, AnimateObject):
            return instruction
        if isinstance(instruction, ShowText):
            self._pending_notifications.append(instruction.text)
            return instruction.text
        if isinstance(instruction, Sleep):
            import time
            time.sleep(instruction.milliseconds / 1000)
            return instruction
        if isinstance(instruction, PlaySound):
            return instruction
        if isinstance(instruction, StopSound):
            return instruction
        if isinstance(instruction, SetSoundVolume):
            app = self._require_app()
            app.sound_volume = instruction.volume
            return instruction
        if isinstance(instruction, ErrorDef):
            return instruction
        if isinstance(instruction, AsyncFunctionDef):
            return instruction
        if isinstance(instruction, DefineBlueprint):
            bp = {key: self.evaluate(value) for key, value in instruction.items.items()}
            if instruction.inherits:
                bp["__parent__"] = instruction.inherits
            self.blueprints[instruction.name] = bp
            return self.blueprints[instruction.name]
        if isinstance(instruction, CreateFromBlueprint):
            if instruction.blueprint_name not in self.blueprints:
                raise AngisRuntimeError(f"Blueprint {instruction.blueprint_name!r} has not been defined.")
            parents = []
            bp_name = instruction.blueprint_name
            seen = set()
            while bp_name in self.blueprints and bp_name not in seen:
                seen.add(bp_name)
                parents.append(self.blueprints[bp_name])
                bp_name = self.blueprints[bp_name].get("__parent__", "")
            values: dict[str, object] = {}
            for parent_bp in reversed(parents):
                for k, v in parent_bp.items():
                    if k != "__parent__":
                        values[k] = v
            values.update({key: self.evaluate(value) for key, value in instruction.items.items()})
            values["__type__"] = instruction.blueprint_name
            self.maps[instruction.name] = values
            if self.app is not None:
                self.app.maps = self.app.maps or {}
                self.app.maps[instruction.name] = dict(values)
            return values
        if isinstance(instruction, CreateList):
            self.lists[instruction.name] = [self.evaluate(item) for item in instruction.items]
            if self.app is not None:
                self.app.lists = self.app.lists or {}
                self.app.lists[instruction.name] = list(self.lists[instruction.name])
            return self.lists[instruction.name]
        if isinstance(instruction, CreateMap):
            self.maps[instruction.name] = {key: self.evaluate(value) for key, value in instruction.items.items()}
            if self.app is not None:
                self.app.maps = self.app.maps or {}
                self.app.maps[instruction.name] = dict(self.maps[instruction.name])
            return self.maps[instruction.name]
        if isinstance(instruction, AddToList):
            self.lists.setdefault(instruction.name, []).append(self.evaluate(instruction.item))
            if self.app is not None:
                self.app.lists = self.app.lists or {}
                self.app.lists[instruction.name] = list(self.lists[instruction.name])
            return self.lists[instruction.name]
        if isinstance(instruction, RemoveFromList):
            if instruction.name not in self.lists:
                raise AngisRuntimeError(f"List {instruction.name!r} has not been created.")
            item = self.evaluate(instruction.item)
            try:
                self.lists[instruction.name].remove(item)
            except ValueError as exc:
                raise AngisRuntimeError(f"Item {item!r} is not in list {instruction.name!r}.") from exc
            if self.app is not None:
                self.app.lists = self.app.lists or {}
                self.app.lists[instruction.name] = list(self.lists[instruction.name])
            return self.lists[instruction.name]
        if isinstance(instruction, RemoveProperty):
            if instruction.object_name in self.maps:
                if instruction.property_name not in self.maps[instruction.object_name]:
                    raise AngisRuntimeError(f"Field {instruction.property_name!r} does not exist.")
                del self.maps[instruction.object_name][instruction.property_name]
                if self.app is not None:
                    self.app.maps = self.app.maps or {}
                    self.app.maps[instruction.object_name] = dict(self.maps[instruction.object_name])
                return self.maps[instruction.object_name]
            app = self._require_app()
            target = _find_object(app, instruction.object_name)
            target.properties = target.properties or {}
            if instruction.property_name not in target.properties:
                raise AngisRuntimeError(f"Property {instruction.property_name!r} does not exist.")
            del target.properties[instruction.property_name]
            return target
        if isinstance(instruction, SaveState):
            return self._save_state(instruction.path)
        if isinstance(instruction, LoadState):
            return self._load_state(instruction.path)
        if isinstance(instruction, FetchUrl):
            self.variables[instruction.name] = self._fetch_url(instruction.url)
            return self.variables[instruction.name]
        if isinstance(instruction, HttpRequest):
            self.variables[instruction.name] = self._http_request(instruction.method, instruction.url, instruction.body)
            return self.variables[instruction.name]
        if isinstance(instruction, UseStdLibAction):
            self.variables[instruction.name] = self._use_stdlib_action(instruction)
            return self.variables[instruction.name]
        if isinstance(instruction, DebugState):
            return self._debug_state(instruction.target)
        if isinstance(instruction, ExportApp):
            return self._export_app(instruction.path)
        if isinstance(instruction, PackageApp):
            return self._package_app(instruction.path)
        if isinstance(instruction, DebugBreakpoint):
            return self._debug_breakpoint(instruction.label)
        if isinstance(instruction, OpenDatabase):
            return self._open_database(instruction.path, instruction.name)
        if isinstance(instruction, ExecuteSql):
            return self._execute_sql(instruction.database, instruction.sql, instruction.name)
        if isinstance(instruction, PlayVideo):
            app = self._require_app()
            info = self._file_info(instruction.path, x=instruction.x, y=instruction.y)
            app.files = app.files or []
            app.files.append(info)
            app.objects = app.objects or []
            app.objects.append(
                CreatorObject(
                    kind="video",
                    name=f"video{len(app.objects) + 1}",
                    x=instruction.x,
                    y=instruction.y,
                    z=0,
                    path=info.path,
                    properties={"width": instruction.width, "height": instruction.height},
                )
            )
            return app
        if isinstance(instruction, GameStart):
            self.game = GameSpec(name=_format_value(self.evaluate(instruction.name)))
            return self.game
        if isinstance(instruction, GameRule):
            if self.game is None:
                self.game = GameSpec(name="Flappy Bird")
            return self.game
        if isinstance(instruction, FileAttach):
            info = self._file_info(_format_value(self.evaluate(instruction.path)))
            return self._format_file_info(info)
        raise AngisRuntimeError(f"Unknown instruction {type(instruction).__name__}.")

    def evaluate(self, expression: Expression) -> object:
        if isinstance(expression, Reference):
            if expression.name in self.variables:
                return self.variables[expression.name]
            if expression.name in self.lists:
                return self.lists[expression.name]
            if expression.name in self.maps:
                return self.maps[expression.name]
            raise AngisRuntimeError(f"Variable {expression.name!r} has not been set.")
        if isinstance(expression, Access):
            target = self.evaluate(expression.target)
            key = self.evaluate(expression.key)
            return _access_value(target, key)
        if isinstance(expression, SliceOf):
            target = self.evaluate(expression.target)
            start = self.evaluate(expression.start)
            end = self.evaluate(expression.end)
            return _slice_value(target, start, end)
        if isinstance(expression, LengthOf):
            value = self.evaluate(expression.value)
            if isinstance(value, (str, list, dict)):
                return len(value)
            raise AngisRuntimeError("Length needs text, a list, or a map.")
        if isinstance(expression, BinaryOp):
            left_val = self.evaluate(expression.left)
            right_val = self.evaluate(expression.right)
            if expression.op == "+":
                if isinstance(left_val, str) or isinstance(right_val, str):
                    return str(left_val) + str(right_val)
                return _require_number(left_val) + _require_number(right_val)
            if expression.op == "-":
                return _require_number(left_val) - _require_number(right_val)
            if expression.op == "*":
                return _require_number(left_val) * _require_number(right_val)
            if expression.op == "/":
                if _require_number(right_val) == 0:
                    raise AngisRuntimeError("Cannot divide by zero.")
                return _require_number(left_val) / _require_number(right_val)
            if expression.op == "%":
                right_num = _require_number(right_val)
                if right_num == 0:
                    raise AngisRuntimeError("Cannot modulo by zero.")
                return _require_number(left_val) % right_num
            if expression.op == "**":
                return _require_number(left_val) ** _require_number(right_val)
            if expression.op == "==":
                return left_val == right_val
            if expression.op == "!=":
                return left_val != right_val
            if expression.op == ">":
                return _require_number(left_val) > _require_number(right_val)
            if expression.op == "<":
                return _require_number(left_val) < _require_number(right_val)
            if expression.op == ">=":
                return _require_number(left_val) >= _require_number(right_val)
            if expression.op == "<=":
                return _require_number(left_val) <= _require_number(right_val)
            raise AngisRuntimeError(f"Unknown expression operator {expression.op!r}.")
        if isinstance(expression, UnaryOp):
            right_val = self.evaluate(expression.right)
            if expression.op == "-":
                return -_require_number(right_val)
            if expression.op == "not":
                return not right_val
            raise AngisRuntimeError(f"Unknown unary operator {expression.op!r}.")
        if isinstance(expression, Lambda):
            return expression
        if isinstance(expression, Comprehension):
            collection = self.evaluate(expression.collection)
            if not isinstance(collection, list):
                raise AngisRuntimeError("Comprehension needs a list.")
            previous = self.variables.get(expression.item_var)
            had_previous = expression.item_var in self.variables
            try:
                if expression.is_dict:
                    result: dict[object, object] = {}
                    for item in collection:
                        self.variables[expression.item_var] = item
                        if expression.filter_expr:
                            filter_result = self.evaluate(expression.filter_expr)
                            if not filter_result:
                                continue
                        key = self.evaluate(expression.key_expr)
                        value = self.evaluate(expression.expr)
                        result[key] = value
                else:
                    result = []
                    for item in collection:
                        self.variables[expression.item_var] = item
                        if expression.filter_expr:
                            filter_result = self.evaluate(expression.filter_expr)
                            if not filter_result:
                                continue
                        result.append(self.evaluate(expression.expr))
            finally:
                if had_previous:
                    self.variables[expression.item_var] = previous
                else:
                    self.variables.pop(expression.item_var, None)
            return result
        if isinstance(expression, RangeExpr):
            start = _require_number(self.evaluate(expression.start))
            end = _require_number(self.evaluate(expression.end))
            return list(range(int(start), int(end) + 1))
        if isinstance(expression, list):
            return [self.evaluate(item) for item in expression]
        if isinstance(expression, dict):
            return {key: self.evaluate(value) for key, value in expression.items()}
        return expression

    def _assign_access(self, target: Access, value: object) -> None:
        container = self.evaluate(target.target)
        key = self.evaluate(target.key)
        if isinstance(container, dict):
            if isinstance(key, str) and "." in key and key not in container:
                _assign_path(container, key, value)
                return
            container[str(key)] = value
            return
        if isinstance(container, list):
            if not isinstance(key, int):
                raise AngisRuntimeError("List indexes must be whole numbers.")
            if key < 0 or key >= len(container):
                raise AngisRuntimeError(f"List index {key} is out of range.")
            container[key] = value
            return
        raise AngisRuntimeError("Only maps, data rows, and lists can be changed with field or index access.")

    def _require_app(self) -> AppSpec:
        if self.app is None:
            raise AngisRuntimeError("Start an app first with: App, My App.")
        return self.app

    def _iterable_values(self, expression: Expression) -> list[object]:
        if isinstance(expression, Reference):
            if expression.name in self.lists:
                return list(self.lists[expression.name])
            if expression.name in self.maps:
                return list(self.maps[expression.name].keys())
        value = self.evaluate(expression)
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            return list(value.keys())
        if hasattr(value, "__next__"):
            return list(value)
        if hasattr(value, "__iter__"):
            return list(value)
        raise AngisRuntimeError("For each needs a list, data rows, or map.")

    def _run_angis_file(self, path: str) -> None:
        resolved = self.base_path / path if self.base_path else Path(path)
        resolved = resolved.expanduser().resolve()
        if not resolved.is_file():
            raise AngisRuntimeError(f"File not found: {path}")
        from .parser import parse_file
        instructions = parse_file(resolved)
        for instr in instructions:
            self._run_instruction(instr, [])

    def _import_module(self, name: str) -> None:
        allowed = {
            "pygame",
            "canvas",
            "physics",
            "sound",
            "network",
            "storage",
            "database",
            "sqlite3",
            "ui",
            "video",
            "packaging",
            "debug",
            "std",
            "math",
            "random",
            "time",
            "json",
            "file",
            "text",
            "csv",
            "data",
            "list",
            "map",
            "path",
            "capabilities",
        }
        if name not in allowed:
            raise AngisRuntimeError(f"Module {name!r} is not available in Angis.")
        if name not in self.imports:
            self.imports.append(name)
        if self.app is not None:
            self.app.imports = self.app.imports or []
            if name not in self.app.imports:
                self.app.imports.append(name)
            if name == "pygame":
                self.app.backend = "pygame"

    def _debug_state(self, target: str) -> str:
        data = {}
        if target in {"variables", "all"}:
            data["variables"] = self.variables
        if target in {"lists", "all"}:
            data["lists"] = self.lists
        if target in {"maps", "all"}:
            data["maps"] = self.maps
        if target in {"imports", "all"}:
            data["imports"] = self.imports
        if target in {"capabilities", "all"}:
            data["capabilities"] = _stdlib_capabilities()
        if target in {"app", "all"} and self.app is not None:
            data["app"] = {
                "title": self.app.title,
                "scene": self.app.scene,
                "backend": self.app.backend,
                "layout": self.app.layout or {"kind": "free", "columns": 1},
                "sound_volume": self.app.sound_volume,
                "objects": [obj.__dict__ for obj in self.app.objects or []],
            }
        return json.dumps(data, indent=2, sort_keys=True)

    def _export_app(self, raw_path: str) -> str:
        app = self._require_app()
        path = Path(raw_path).expanduser().resolve()
        if path.suffix.lower() != ".html":
            raise AngisRuntimeError("Export path must end with .html.")
        html = _app_to_html(app)
        path.write_text(html, encoding="utf-8")
        return f"Exported app to {path}"

    def _package_app(self, raw_path: str) -> str:
        app = self._require_app()
        folder = Path(raw_path).expanduser().resolve()
        if folder.suffix == ".app":
            contents = folder / "Contents"
            macos = contents / "MacOS"
            resources = contents / "Resources"
            macos.mkdir(parents=True, exist_ok=True)
            resources.mkdir(parents=True, exist_ok=True)
            (resources / "index.html").write_text(_app_to_html(app), encoding="utf-8")
            launcher = macos / "AngisApp"
            launcher.write_text("#!/bin/sh\nopen \"$0/../../Resources/index.html\"\n", encoding="utf-8")
            launcher.chmod(0o755)
            (contents / "Info.plist").write_text(_mac_app_plist(app.title), encoding="utf-8")
            return f"Packaged macOS app to {folder}"
        if folder.suffix.lower() == ".exe":
            package_dir = folder.with_suffix("")
            package_dir.mkdir(parents=True, exist_ok=True)
            (package_dir / "index.html").write_text(_app_to_html(app), encoding="utf-8")
            (package_dir / "README.txt").write_text(
                "Windows executable packaging needs a Windows build tool such as PyInstaller.\n"
                "This Angis package is a safe local scaffold containing the exported app HTML.\n",
                encoding="utf-8",
            )
            (package_dir / "angis-package.json").write_text(
                json.dumps({"title": app.title, "scene": app.scene, "target": "windows-exe-scaffold"}, indent=2),
                encoding="utf-8",
            )
            return f"Packaged Windows app scaffold to {package_dir}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(_app_to_html(app), encoding="utf-8")
        (folder / "angis-package.json").write_text(
            json.dumps({"title": app.title, "scene": app.scene, "imports": app.imports or [], "backend": app.backend, "layout": app.layout or {"kind": "free", "columns": 1}}, indent=2),
            encoding="utf-8",
        )
        return f"Packaged app to {folder}"

    def _debug_breakpoint(self, label: str) -> str:
        return f"Breakpoint: {label}\n{self._debug_state('all')}"

    def _open_database(self, raw_path: str, name: str) -> str:
        path = Path(raw_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.databases[name] = sqlite3.connect(path)
        return f"Opened database {name} at {path}"

    def _execute_sql(self, database: str, sql: str, name: str) -> str:
        if database not in self.databases:
            raise AngisRuntimeError(f"Database {database!r} has not been opened.")
        cursor = self.databases[database].execute(sql)
        rows = [dict(zip([column[0] for column in cursor.description or []], row)) for row in cursor.fetchall()]
        self.databases[database].commit()
        if name:
            self.variables[name] = rows
        return json.dumps(rows, indent=2) if rows else "SQL ok"

    def _run_nested(self, instructions: list[object], captured: list[str]) -> None:
        for instruction in instructions:
            self._run_instruction(instruction, captured)

    def _check_type(self, value: object, expected: str, param_name: str) -> None:
        mapping = {
            "text": str, "string": str,
            "number": (int, float), "int": int, "decimal": float, "float": float,
            "bool": bool, "boolean": bool,
            "list": list,
            "map": dict, "dict": dict,
            "any": object,
        }
        allowed = mapping.get(expected)
        if allowed is None:
            return
        if not isinstance(value, allowed):
            raise AngisRuntimeError(f"Parameter {param_name!r} expected {expected}, got {type(value).__name__}.")

    def _call_function(self, function: FunctionDef, args: list[Expression], captured: list[str]) -> object:
        params = function.params or []
        if len(args) != len(params):
            raise AngisRuntimeError(f"Function {function.name!r} expects {len(params)} argument(s), got {len(args)}.")
        if _has_yield(function.body):
            return self._make_generator(function, args, captured)
        previous = {name: self.variables.get(name) for name in params}
        had_previous = {name: name in self.variables for name in params}
        try:
            for name, value in zip(params, args):
                evaled = self.evaluate(value)
                if function.param_types and name in function.param_types:
                    self._check_type(evaled, function.param_types[name], name)
                self.variables[name] = evaled
            try:
                self._run_nested(function.body, captured)
            except _FunctionReturn as signal:
                if function.return_type:
                    self._check_type(signal.value, function.return_type, "return")
                return signal.value
            return None
        finally:
            for name in params:
                if had_previous[name]:
                    self.variables[name] = previous[name]
                else:
                    self.variables.pop(name, None)

    def _make_generator(self, function: FunctionDef, args: list[Expression], captured: list[str]):
        params = function.params or []
        previous = {name: self.variables.get(name) for name in params}
        had_previous = {name: name in self.variables for name in params}
        for name, value in zip(params, args):
            self.variables[name] = self.evaluate(value)

        def _run_gen_body(body: list[object]):
            for instr in body:
                if isinstance(instr, YieldValue):
                    sent = yield self.evaluate(instr.value)
                    if instr.send_var:
                        self.variables[instr.send_var] = sent if sent is not None else ""
                elif isinstance(instr, ReturnValue):
                    val = self.evaluate(instr.value) if instr.value is not None else None
                    raise _FunctionReturn(val)
                elif isinstance(instr, FunctionDef):
                    self.functions[instr.name] = instr
                elif isinstance(instr, ForEachBlock):
                    collection = self.evaluate(instr.collection)
                    if not isinstance(collection, (list, str)):
                        raise AngisRuntimeError("For each needs a list.")
                    for item in collection:
                        old_item = self.variables.get(instr.item_name)
                        had_item = instr.item_name in self.variables
                        self.variables[instr.item_name] = item
                        try:
                            yield from _run_gen_body(instr.body)
                        except _LoopControl as ctrl:
                            if ctrl.kind == "break":
                                break
                        finally:
                            if had_item:
                                self.variables[instr.item_name] = old_item
                            else:
                                self.variables.pop(instr.item_name, None)
                elif isinstance(instr, IfBlock):
                    if self._condition_is_true(instr.condition):
                        yield from _run_gen_body(instr.body)
                    elif instr.else_body:
                        yield from _run_gen_body(instr.else_body)
                elif isinstance(instr, WhileBlock):
                    iterations = 0
                    while self._condition_is_true(instr.condition):
                        if iterations >= MAX_WHILE_ITERATIONS:
                            raise AngisRuntimeError("While loop stopped after 10000 runs.")
                        try:
                            yield from _run_gen_body(instr.body)
                        except _LoopControl as ctrl:
                            if ctrl.kind == "break":
                                break
                        iterations += 1
                elif isinstance(instr, RepeatBlock):
                    count = self.evaluate(instr.count)
                    if isinstance(count, int) and count >= 0:
                        for _ in range(count):
                            try:
                                yield from _run_gen_body(instr.body)
                            except _LoopControl as ctrl:
                                if ctrl.kind == "break":
                                    break
                elif isinstance(instr, TryBlock):
                    try:
                        yield from _run_gen_body(instr.body)
                    except Exception as exc:
                        if instr.variable_name:
                            self.variables[instr.variable_name] = str(exc)
                        yield from _run_gen_body(instr.except_body)
                    finally:
                        if instr.finally_body:
                            yield from _run_gen_body(instr.finally_body)
                elif isinstance(instr, SwitchBlock):
                    yielded = False
                    for case_patterns, case_body in instr.cases:
                        for pattern in case_patterns:
                            if self._condition_is_true(self._make_eq_condition(instr.condition, pattern)):
                                yield from _run_gen_body(case_body)
                                yielded = True
                                break
                        if yielded:
                            break
                    if not yielded and instr.default_body:
                        yield from _run_gen_body(instr.default_body)
                else:
                    self._run_instruction(instr, captured)

        def generator():
            try:
                yield from _run_gen_body(function.body)
            except _FunctionReturn:
                pass
            finally:
                for name in params:
                    if had_previous[name]:
                        self.variables[name] = previous[name]
                    else:
                        self.variables.pop(name, None)

        return generator()

    def _call_lambda(self, function: Lambda, args: list[Expression], captured: list[str]) -> object:
        params = function.params
        if len(args) != len(params):
            raise AngisRuntimeError(f"Lambda expects {len(params)} argument(s), got {len(args)}.")
        previous = {name: self.variables.get(name) for name in params}
        had_previous = {name: name in self.variables for name in params}
        try:
            for name, value in zip(params, args):
                self.variables[name] = self.evaluate(value)
            return self.evaluate(function.body)
        finally:
            for name in params:
                if had_previous[name]:
                    self.variables[name] = previous[name]
                else:
                    self.variables.pop(name, None)

    def _call_object_method(self, method: ObjectMethodDef, object_name: str, args: list[Expression], captured: list[str]) -> object:
        params = method.params or []
        if len(args) != len(params):
            raise AngisRuntimeError(f"Method {method.object_name}.{method.method_name} expects {len(params)} argument(s), got {len(args)}.")
        target = self._method_target(object_name)
        bound_names = ["self", *params]
        previous = {name: self.variables.get(name) for name in bound_names}
        had_previous = {name: name in self.variables for name in bound_names}
        try:
            self.variables["self"] = target
            for name, value in zip(params, args):
                evaled = self.evaluate(value)
                if method.param_types and name in method.param_types:
                    self._check_type(evaled, method.param_types[name], name)
                self.variables[name] = evaled
            try:
                self._run_nested(method.body, captured)
            except _FunctionReturn as signal:
                if method.return_type:
                    self._check_type(signal.value, method.return_type, "return")
                return signal.value
            return None
        finally:
            for name in bound_names:
                if had_previous[name]:
                    self.variables[name] = previous[name]
                else:
                    self.variables.pop(name, None)

    async def _run_async_function(self, function: AsyncFunctionDef, args: list[Expression], captured: list[str]) -> object:
        params = function.params or []
        if len(args) != len(params):
            raise AngisRuntimeError(f"Async function {function.name!r} expects {len(params)} argument(s), got {len(args)}.")
        previous = {name: self.variables.get(name) for name in params}
        had_previous = {name: name in self.variables for name in params}
        try:
            for name, value in zip(params, args):
                evaled = self.evaluate(value)
                if function.param_types and name in function.param_types:
                    self._check_type(evaled, function.param_types[name], name)
                self.variables[name] = evaled
            try:
                for instr in function.body:
                    if isinstance(instr, AwaitExpr):
                        coro_val = self.evaluate(instr.value)
                        if asyncio.iscoroutine(coro_val):
                            result = await coro_val
                        else:
                            result = coro_val
                        if instr.result_name:
                            self.variables[instr.result_name] = result
                    elif isinstance(instr, ReturnValue):
                        val = self.evaluate(instr.value) if instr.value is not None else None
                        if function.return_type:
                            self._check_type(val, function.return_type, "return")
                        raise _FunctionReturn(val)
                    else:
                        self._run_instruction(instr, captured)
            except _FunctionReturn as signal:
                return signal.value
            return None
        finally:
            for name in params:
                if had_previous[name]:
                    self.variables[name] = previous[name]
                else:
                    self.variables.pop(name, None)

    def _method_target(self, object_name: str) -> object:
        if object_name in self.maps:
            return self.maps[object_name]
        if object_name in self.lists:
            return self.lists[object_name]
        if self.app is not None:
            app_object = _find_object(self.app, object_name)
            if app_object.properties is None:
                app_object.properties = {}
            return app_object.properties
        raise AngisRuntimeError(f"Object {object_name!r} has not been created.")

    def _object_type(self, object_name: str) -> str:
        if object_name in self.maps:
            value = self.maps[object_name].get("__type__", "")
            return str(value) if value else ""
        return ""

    def _condition_is_true(self, condition: object) -> bool:
        from .ir import Condition

        if isinstance(condition, LogicalCondition):
            if condition.operator == "and":
                return self._condition_is_true(condition.left) and self._condition_is_true(condition.right)
            if condition.operator == "or":
                return self._condition_is_true(condition.left) or self._condition_is_true(condition.right)
            if condition.operator == "not":
                return not self._condition_is_true(condition.left)
            raise AngisRuntimeError(f"Unknown logical operator {condition.operator!r}.")
        if not isinstance(condition, Condition):
            raise AngisRuntimeError("Invalid condition.")
        left = self.evaluate(condition.left)
        if condition.operator == "truthy":
            return bool(left)
        if condition.operator == "empty":
            return _is_empty_value(left)
        if condition.operator == "not empty":
            return not _is_empty_value(left)
        if condition.operator == "contains":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return _contains_value(left, right)
        if condition.operator == "not contains":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return not _contains_value(left, right)
        if condition.operator == "starts with":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return _string_condition(left, right, "starts with")
        if condition.operator == "not starts with":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return not _string_condition(left, right, "starts with")
        if condition.operator == "ends with":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return _string_condition(left, right, "ends with")
        if condition.operator == "not ends with":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return not _string_condition(left, right, "ends with")
        if condition.operator == "starts with ignoring case":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return _string_condition(left, right, "starts with", ignore_case=True)
        if condition.operator == "not starts with ignoring case":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return not _string_condition(left, right, "starts with", ignore_case=True)
        if condition.operator == "ends with ignoring case":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return _string_condition(left, right, "ends with", ignore_case=True)
        if condition.operator == "not ends with ignoring case":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return not _string_condition(left, right, "ends with", ignore_case=True)
        if condition.operator == "==":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return left == right
        if condition.operator == "!=":
            right = self._condition_value(condition.right, allow_bare_text=True)
            return left != right
        right = self.evaluate(condition.right)
        if condition.operator == ">":
            return _require_number(left) > _require_number(right)
        if condition.operator == "<":
            return _require_number(left) < _require_number(right)
        if condition.operator == ">=":
            return _require_number(left) >= _require_number(right)
        if condition.operator == "<=":
            return _require_number(left) <= _require_number(right)
        raise AngisRuntimeError(f"Unknown condition operator {condition.operator!r}.")

    def _condition_value(self, expression: Expression, *, allow_bare_text: bool = False) -> object:
        try:
            return self.evaluate(expression)
        except AngisRuntimeError as exc:
            if allow_bare_text and isinstance(expression, Reference) and "has not been set" in str(exc):
                return expression.name
            if (
                allow_bare_text
                and isinstance(expression, Access)
                and isinstance(expression.target, Reference)
                and isinstance(expression.key, str)
                and "has not been set" in str(exc)
            ):
                return f"{expression.target.name}.{expression.key}"
            raise

    def _attach_file(self, raw_path: str) -> str:
        return self._format_file_info(self._file_info(raw_path))

    def _file_info(self, raw_path: str, x: int = 0, y: int = 0, z: int = 0) -> FileInfo:
        if not raw_path.strip():
            raise AngisRuntimeError("File path cannot be empty.")
        path = Path(raw_path)
        if not path.is_absolute() and not raw_path.startswith("~") and self.base_path is not None:
            path = self.base_path / raw_path
        path = path.expanduser()
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise AngisRuntimeError(f"Could not locate file {raw_path!r}.") from exc
        if not resolved.is_file():
            raise AngisRuntimeError(f"Path is not a file: {raw_path!r}.")
        size = resolved.stat().st_size
        return FileInfo(
            name=resolved.name,
            size=size,
            path=str(resolved),
            x=x,
            y=y,
            z=z,
            kind=_file_kind(resolved),
            preview=_file_preview(resolved),
        )

    def _format_file_info(self, info: FileInfo) -> str:
        return f"Attached file: {info.name} ({info.size} bytes) at {info.path}"

    def _save_state(self, raw_path: str) -> str:
        path = Path(raw_path).expanduser().resolve()
        state = {"variables": self.variables, "lists": self.lists, "maps": self.maps, "imports": self.imports}
        if self.app is not None:
            state["app"] = {
                "title": self.app.title,
                "scene": self.app.scene,
                "layout": self.app.layout or {"kind": "free", "columns": 1},
                "objects": [obj.__dict__ for obj in self.app.objects or []],
            }
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return f"Saved state to {path}"

    def _load_state(self, raw_path: str) -> str:
        path = Path(raw_path).expanduser().resolve()
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AngisRuntimeError(f"Could not load state from {raw_path!r}.") from exc
        variables = state.get("variables", {})
        lists = state.get("lists", {})
        maps = state.get("maps", {})
        if isinstance(variables, dict):
            self.variables.update(variables)
        if isinstance(lists, dict):
            self.lists.update(lists)
        if isinstance(maps, dict):
            self.maps.update(maps)
        return f"Loaded state from {path}"

    def _fetch_url(self, url: str) -> str:
        try:
            with urlopen(url, timeout=5) as response:
                data = response.read(4096)
        except (OSError, URLError) as exc:
            raise AngisRuntimeError(f"Could not fetch {url!r}.") from exc
        return data.decode("utf-8", errors="replace")

    def _http_request(self, method: str, url: str, body: str) -> str:
        data = body.encode("utf-8") if body else None
        request = Request(url, data=data, method=method, headers={"User-Agent": "Angis/0.1"})
        try:
            with urlopen(request, timeout=5) as response:
                payload = response.read(8192)
        except (OSError, URLError) as exc:
            raise AngisRuntimeError(f"HTTP {method} failed for {url!r}.") from exc
        return payload.decode("utf-8", errors="replace")

    def _use_stdlib_action(self, instruction: UseStdLibAction) -> object:
        args = {key: self._evaluate_stdlib_arg(key, value) for key, value in instruction.args.items()}
        module = instruction.module
        action = instruction.action
        if module == "data":
            module = "csv" if action in {"csv_read", "read_csv"} else module
        if module not in _stdlib_capabilities():
            raise AngisRuntimeError(f"Standard library module {module!r} is not available.")
        try:
            if module == "math":
                return _run_math_action(action, args)
            if module == "random":
                return _run_random_action(action, args)
            if module == "time":
                return _run_time_action(action, args)
            if module == "json":
                return _run_json_action(action, args)
            if module == "file":
                return _run_file_action(action, args)
            if module == "text":
                return _run_text_action(action, args)
            if module == "csv":
                return _run_csv_action(action, args)
            if module == "data":
                return _run_data_action(action, args)
            if module == "list":
                return _run_list_action(action, args)
            if module == "map":
                return _run_map_action(action, args)
            if module == "path":
                return _run_path_action(action, args)
            if module == "convert":
                return _run_convert_action(action, args)
            if module == "bitwise":
                return _run_bitwise_action(action, args)
            if module == "statistics":
                return _run_statistics_action(action, args)
            if module == "socket":
                return _run_socket_action(action, args)
            if module == "capabilities":
                return _stdlib_capabilities()
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise AngisRuntimeError(f"Could not use {module} {action}.") from exc
        raise AngisRuntimeError(f"Standard library action {module} {action} is not available.")

    def _evaluate_stdlib_arg(self, key: str, value: Expression) -> object:
        if isinstance(value, Reference):
            if value.name in self.variables:
                return self.variables[value.name]
            if value.name in self.lists:
                return self.lists[value.name]
            if value.name in self.maps:
                return self.maps[value.name]
            if key in {
                "by",
                "column",
                "key",
                "needle",
                "new",
                "old",
                "path",
                "pattern",
                "prefix",
                "replacement",
                "right",
                "separator",
                "suffix",
                "text",
                "value",
            }:
                return value.name
        return self.evaluate(value)


def run_source(
    source: str,
    output: TextIO | None = None,
    app_runner: Callable[[AppSpec], None] | None = None,
    game_runner: Callable[[GameSpec], None] | None = None,
) -> list[str]:
    from .parser import parse

    return Interpreter(output=output, app_runner=app_runner, game_runner=game_runner).run(parse(source))


def _require_number(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AngisRuntimeError(f"Expected a number, got {value!r}.")
    return value


def _contains_value(container: object, item: object) -> bool:
    if isinstance(container, str):
        return str(item) in container
    if isinstance(container, list):
        return item in container
    if isinstance(container, dict):
        return item in container or str(item) in container
    raise AngisRuntimeError("Contains conditions need text, lists, or maps.")


def _is_empty_value(value: object) -> bool:
    if isinstance(value, (str, list, dict)):
        return len(value) == 0
    raise AngisRuntimeError("Empty conditions need text, a list, or a map.")


def _slice_value(target: object, start: object, end: object) -> object:
    if not isinstance(start, int) or not isinstance(end, int):
        raise AngisRuntimeError("Slice indexes must be whole numbers.")
    if isinstance(target, list):
        return target[start:end]
    if isinstance(target, str):
        return target[start:end]
    raise AngisRuntimeError("Slices need text or a list.")


def _string_condition(left: object, right: object, operator: str, *, ignore_case: bool = False) -> bool:
    if not isinstance(left, str):
        raise AngisRuntimeError("Text conditions need text on the left side.")
    text = left.lower() if ignore_case else left
    needle = str(right).lower() if ignore_case else str(right)
    if operator == "starts with":
        return text.startswith(needle)
    if operator == "ends with":
        return text.endswith(needle)
    raise AngisRuntimeError(f"Unknown text condition {operator!r}.")


def _access_value(target: object, key: object) -> object:
    if isinstance(target, dict):
        text_key = str(key)
        if "." in text_key and text_key not in target:
            return _access_path(target, text_key)
        if text_key not in target:
            raise AngisRuntimeError(f"Field {text_key!r} does not exist.")
        return target[text_key]
    if isinstance(target, list):
        if not isinstance(key, int):
            raise AngisRuntimeError("List indexes must be whole numbers.")
        try:
            return target[key]
        except IndexError as exc:
            raise AngisRuntimeError(f"List index {key} is out of range.") from exc
    if isinstance(target, str):
        if not isinstance(key, int):
            raise AngisRuntimeError("Text indexes must be whole numbers.")
        try:
            return target[key]
        except IndexError as exc:
            raise AngisRuntimeError(f"Text index {key} is out of range.") from exc
    raise AngisRuntimeError("Only maps, data rows, lists, and text support field or index access.")


def _access_path(target: object, path: str) -> object:
    current = target
    for part in path.split("."):
        current = _access_value(current, int(part) if isinstance(current, list) and part.isdigit() else part)
    return current


def _assign_path(target: dict[str, object], path: str, value: object) -> None:
    parts = path.split(".")
    current: object = target
    for part in parts[:-1]:
        if isinstance(current, dict):
            if part not in current:
                current[part] = {}
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index < 0 or index >= len(current):
                raise AngisRuntimeError(f"List index {index} is out of range.")
            current = current[index]
            continue
        raise AngisRuntimeError(f"Cannot assign through path {path!r}.")
    last = parts[-1]
    if isinstance(current, dict):
        current[last] = value
        return
    if isinstance(current, list) and last.isdigit():
        index = int(last)
        if index < 0 or index >= len(current):
            raise AngisRuntimeError(f"List index {index} is out of range.")
        current[index] = value
        return
    raise AngisRuntimeError(f"Cannot assign through path {path!r}.")


def _require_arg(args: dict[str, object], name: str) -> object:
    if name not in args:
        raise AngisRuntimeError(f"Missing standard library argument {name!r}.")
    return args[name]


def _stdlib_capabilities() -> dict[str, list[str]]:
    return {
        "bitwise": ["and", "not", "or", "shift_left", "shift_right", "xor"],
        "capabilities": ["list"],
        "convert": ["to_number", "to_string"],
        "csv": ["read", "write"],
        "data": ["column", "count", "filter_equals", "first"],
        "file": ["copy", "delete", "exists", "glob", "info", "list_dir", "mkdir", "move", "read", "write"],
        "json": ["parse", "stringify"],
        "list": ["append", "at", "clear", "contains", "count_value", "extend", "first", "index_of", "insert", "last", "length", "pop", "reverse", "shuffle", "slice", "sort", "unique"],
        "map": ["get", "has", "keys", "merge", "values"],
        "math": ["absolute", "atan", "ceil", "clamp", "cos", "degrees", "exp", "factorial", "floor", "gcd", "hypot", "isnan", "log", "log10", "maximum", "minimum", "pi", "power", "radians", "round", "sin", "sqrt", "tan"],
        "path": ["extension", "join", "name", "parent", "stem"],
        "random": ["choice", "integer"],
        "socket": ["accept", "bind", "close", "connect", "listen", "recv", "recvfrom", "send", "sendto", "udp_socket", "websocket_connect", "websocket_send", "websocket_recv", "websocket_close"],
        "statistics": ["median", "mode", "stdev"],
        "text": ["capitalize", "char_at", "char_code_at", "contains", "ends_with", "isalnum", "isalpha", "isdigit", "isspace", "join", "lowercase", "lstrip", "pad_end", "pad_start", "partition", "regex_match", "regex_replace", "regex_search", "repeat", "replace", "rstrip", "split", "starts_with", "substring", "swapcase", "title", "trim", "uppercase"],
        "time": ["add_days", "format", "now", "subtract_days", "timestamp", "today"],
    }


def _run_math_action(action: str, args: dict[str, object]) -> int | float:
    if action in {"round", "rounded"}:
        val = _require_number(_require_arg(args, "value"))
        if "places" in args:
            return round(val, int(_require_arg(args, "places")))
        return round(val)
    if action == "floor":
        return math.floor(_require_number(_require_arg(args, "value")))
    if action == "ceil":
        return math.ceil(_require_number(_require_arg(args, "value")))
    if action in {"sqrt", "square_root"}:
        return math.sqrt(_require_number(_require_arg(args, "value")))
    if action in {"power", "pow"}:
        return math.pow(_require_number(_require_arg(args, "base")), _require_number(_require_arg(args, "exponent")))
    if action == "absolute":
        return abs(_require_number(_require_arg(args, "value")))
    if action in {"minimum", "min"}:
        return min(_require_number(_require_arg(args, "left")), _require_number(_require_arg(args, "right")))
    if action in {"maximum", "max"}:
        return max(_require_number(_require_arg(args, "left")), _require_number(_require_arg(args, "right")))
    if action == "clamp":
        value = _require_number(_require_arg(args, "value"))
        low = _require_number(_require_arg(args, "min"))
        high = _require_number(_require_arg(args, "max"))
        return min(max(value, low), high)
    if action in {"sin", "sine"}:
        return math.sin(math.radians(_require_number(_require_arg(args, "value"))))
    if action in {"cos", "cosine"}:
        return math.cos(math.radians(_require_number(_require_arg(args, "value"))))
    if action in {"tan", "tangent"}:
        return math.tan(math.radians(_require_number(_require_arg(args, "value"))))
    if action in {"atan", "arctan", "atan2"}:
        y = _require_number(_require_arg(args, "y")) if "y" in args else _require_number(_require_arg(args, "value"))
        if "y" in args:
            x = _require_number(_require_arg(args, "x"))
            return math.degrees(math.atan2(y, x))
        return math.degrees(math.atan(y))
    if action in {"hypot", "hypotenuse", "distance"}:
        a = _require_number(_require_arg(args, "a"))
        b = _require_number(_require_arg(args, "b"))
        return math.hypot(a, b)
    if action == "degrees":
        return math.degrees(_require_number(_require_arg(args, "value")))
    if action == "radians":
        return math.radians(_require_number(_require_arg(args, "value")))
    if action == "exp":
        return math.exp(_require_number(_require_arg(args, "value")))
    if action in {"factorial", "fact"}:
        return math.factorial(int(_require_number(_require_arg(args, "value"))))
    if action == "gcd":
        a = int(_require_number(_require_arg(args, "a")))
        b = int(_require_number(_require_arg(args, "b")))
        return math.gcd(a, b)
    if action in {"isnan", "is_nan", "is_not_a_number"}:
        return math.isnan(_require_number(_require_arg(args, "value")))
    if action in {"log", "ln", "natural_log"}:
        return math.log(_require_number(_require_arg(args, "value")))
    if action == "log10":
        return math.log10(_require_number(_require_arg(args, "value")))
    if action == "pi":
        return math.pi
    if action == "e":
        return math.e
    raise AngisRuntimeError(f"Math action {action!r} is not available.")


def _run_random_action(action: str, args: dict[str, object]) -> object:
    if action in {"integer", "number"}:
        low = int(_require_number(_require_arg(args, "min")))
        high = int(_require_number(_require_arg(args, "max")))
        return random.randint(low, high)
    if action == "choice":
        values = _require_arg(args, "from")
        if not isinstance(values, list) or not values:
            raise AngisRuntimeError("Random choice needs a non-empty list.")
        return random.choice(values)
    raise AngisRuntimeError(f"Random action {action!r} is not available.")


def _run_time_action(action: str, args: dict[str, object]) -> object:
    if action == "now":
        return time.strftime("%Y-%m-%d %H:%M:%S")
    if action in {"today", "date"}:
        return dt.date.today().isoformat()
    if action in {"timestamp", "seconds"}:
        return int(time.time())
    if action in {"add_days", "subtract_days"}:
        days = int(_require_number(_require_arg(args, "days")))
        if action == "subtract_days":
            days = -days
        return (dt.date.today() + dt.timedelta(days=days)).isoformat()
    if action in {"format", "date_format"}:
        value = str(_require_arg(args, "value"))
        fmt = str(_require_arg(args, "format"))
        try:
            parsed = dt.datetime.strptime(value, "%Y-%m-%d")
            return parsed.strftime(fmt)
        except ValueError:
            try:
                parsed = dt.datetime.fromisoformat(value)
                return parsed.strftime(fmt)
            except (ValueError, TypeError):
                raise AngisRuntimeError(f"Could not parse date {value!r}. Use ISO format like 2024-01-15.")
    raise AngisRuntimeError(f"Time action {action!r} is not available.")


def _run_json_action(action: str, args: dict[str, object]) -> object:
    if action == "parse":
        text = str(_require_arg(args, "text"))
        return json.loads(text)
    if action in {"stringify", "dump"}:
        return json.dumps(_require_arg(args, "value"), sort_keys=True)
    raise AngisRuntimeError(f"JSON action {action!r} is not available.")


def _run_file_action(action: str, args: dict[str, object]) -> object:
    if action == "exists":
        path = Path(str(_require_arg(args, "path"))).expanduser()
        return path.exists()
    if action == "info":
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve(strict=True)
        if not path.is_file():
            raise AngisRuntimeError("File info needs a real file path.")
        return {"name": path.name, "size": path.stat().st_size, "suffix": path.suffix.lower(), "kind": _file_kind(path)}
    if action == "read":
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve(strict=True)
        if not path.is_file():
            raise AngisRuntimeError("File read needs a real file path.")
        return path.read_text(encoding="utf-8", errors="replace")
    if action == "write":
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(_require_arg(args, "text")), encoding="utf-8")
        return f"Wrote file {path.name}"
    if action in {"append", "append_file"}:
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(str(_require_arg(args, "text")))
            handle.write("\n")
        return f"Appended to file {path.name}"
    if action in {"glob", "match", "find_files"}:
        pattern = str(_require_arg(args, "pattern"))
        root = Path(str(args.get("root", "."))).expanduser()
        matches = []
        for p in sorted(root.glob(pattern)):
            matches.append({"name": p.name, "path": str(p), "is_dir": p.is_dir()})
        return matches
    if action in {"mkdir", "make_directory", "create_directory"}:
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return f"Created directory {path}"
    if action in {"list_dir", "listdir", "list_directory"}:
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve()
        if not path.is_dir():
            raise AngisRuntimeError("List directory needs a real directory path.")
        entries = []
        for entry in sorted(path.iterdir()):
            entries.append({"name": entry.name, "is_dir": entry.is_dir(), "size": entry.stat().st_size if entry.is_file() else 0})
        return entries
    if action == "copy":
        source = Path(str(_require_arg(args, "source"))).expanduser().resolve(strict=True)
        destination = Path(str(_require_arg(args, "destination"))).expanduser().resolve()
        if not source.is_file():
            raise AngisRuntimeError("Copy needs a real source file.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(source, destination)
        return f"Copied {source.name} to {destination}"
    if action == "move":
        source = Path(str(_require_arg(args, "source"))).expanduser().resolve(strict=True)
        destination = Path(str(_require_arg(args, "destination"))).expanduser().resolve()
        if not source.is_file():
            raise AngisRuntimeError("Move needs a real source file.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.move(str(source), str(destination))
        return f"Moved {source.name} to {destination}"
    if action == "delete":
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve()
        if path.is_file():
            path.unlink()
            return f"Deleted file {path}"
        if path.is_dir():
            import shutil
            shutil.rmtree(path)
            return f"Deleted directory {path}"
        raise AngisRuntimeError(f"Path does not exist: {path}")
    raise AngisRuntimeError(f"File action {action!r} is not available.")


def _run_text_action(action: str, args: dict[str, object]) -> object:
    if action == "uppercase":
        return str(_require_arg(args, "text")).upper()
    if action == "lowercase":
        return str(_require_arg(args, "text")).lower()
    if action in {"capitalize", "capitalised", "capitalized"}:
        return str(_require_arg(args, "text")).capitalize()
    if action in {"title", "titlecase", "title_case"}:
        return str(_require_arg(args, "text")).title()
    if action == "swapcase":
        return str(_require_arg(args, "text")).swapcase()
    if action in {"lstrip", "left_strip", "strip_left"}:
        return str(_require_arg(args, "text")).lstrip()
    if action in {"rstrip", "right_strip", "strip_right"}:
        return str(_require_arg(args, "text")).rstrip()
    if action == "trim":
        return str(_require_arg(args, "text")).strip()
    if action == "split":
        text = str(_require_arg(args, "text"))
        separator = _text_separator(args.get("by", args.get("separator", " ")))
        return text.split(separator)
    if action == "join":
        values = _require_arg(args, "values")
        separator = _text_separator(args.get("by", args.get("separator", "")))
        if not isinstance(values, list):
            raise AngisRuntimeError("Text join needs a list.")
        return separator.join(str(value) for value in values)
    if action == "replace":
        return str(_require_arg(args, "text")).replace(str(_require_arg(args, "old")), str(_require_arg(args, "new")))
    if action == "contains":
        return str(_require_arg(args, "needle")) in str(_require_arg(args, "text"))
    if action in {"starts_with", "starts"}:
        return str(_require_arg(args, "text")).startswith(str(_require_arg(args, "prefix")))
    if action in {"ends_with", "ends"}:
        return str(_require_arg(args, "text")).endswith(str(_require_arg(args, "suffix")))
    if action in {"isalpha", "is_alpha", "is_letter"}:
        return str(_require_arg(args, "text")).isalpha()
    if action in {"isdigit", "is_digit", "is_number"}:
        return str(_require_arg(args, "text")).isdigit()
    if action in {"isalnum", "is_alnum", "is_letter_or_number"}:
        return str(_require_arg(args, "text")).isalnum()
    if action in {"isspace", "is_space", "is_whitespace"}:
        return str(_require_arg(args, "text")).isspace()
    if action in {"partition", "split_first"}:
        text = str(_require_arg(args, "text"))
        sep = str(_require_arg(args, "separator"))
        return list(text.partition(sep))
    if action in {"char_at", "char_at_index", "character_at"}:
        text = str(_require_arg(args, "text"))
        index = int(_require_number(_require_arg(args, "index")))
        if index < 0 or index >= len(text):
            raise AngisRuntimeError(f"Character index {index} is out of range.")
        return text[index]
    if action in {"char_code_at", "char_code"}:
        text = str(_require_arg(args, "text"))
        index = int(_require_number(_require_arg(args, "index")))
        if index < 0 or index >= len(text):
            raise AngisRuntimeError(f"Character index {index} is out of range.")
        return ord(text[index])
    if action in {"substring", "substr"}:
        text = str(_require_arg(args, "text"))
        start = int(_require_number(_require_arg(args, "start")))
        end = int(_require_number(_require_arg(args, "end")))
        return text[start:end]
    if action in {"pad_start", "pad_left"}:
        text = str(_require_arg(args, "text"))
        length = int(_require_number(_require_arg(args, "length")))
        char = str(args.get("char", " "))
        return text.rjust(length, char[:1])
    if action in {"pad_end", "pad_right"}:
        text = str(_require_arg(args, "text"))
        length = int(_require_number(_require_arg(args, "length")))
        char = str(args.get("char", " "))
        return text.ljust(length, char[:1])
    if action == "repeat":
        text = str(_require_arg(args, "text"))
        times = int(_require_number(_require_arg(args, "times")))
        return text * max(0, times)
    if action == "regex_match":
        text = str(_require_arg(args, "text"))
        pattern = str(_require_arg(args, "pattern"))
        match = re.match(pattern, text)
        return match.group(0) if match else ""
    if action == "regex_search":
        text = str(_require_arg(args, "text"))
        pattern = str(_require_arg(args, "pattern"))
        match = re.search(pattern, text)
        return match.group(0) if match else ""
    if action == "regex_replace":
        text = str(_require_arg(args, "text"))
        pattern = str(_require_arg(args, "pattern"))
        replacement = str(_require_arg(args, "replacement"))
        return re.sub(pattern, replacement, text)
    raise AngisRuntimeError(f"Text action {action!r} is not available.")


def _text_separator(value: object) -> str:
    text = str(value)
    shortcuts = {"space": " ", "tab": "\t", "newline": "\n", "comma": ",", "dash": "-", "slash": "/"}
    return shortcuts.get(text.lower(), text)


def _run_csv_action(action: str, args: dict[str, object]) -> object:
    if action in {"read", "csv_read", "read_csv"}:
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve(strict=True)
        if not path.is_file():
            raise AngisRuntimeError("CSV read needs a real file path.")
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle))
    if action in {"write", "csv_write", "write_csv"}:
        path = Path(str(_require_arg(args, "path"))).expanduser().resolve()
        rows = _require_arg(args, "rows")
        if not isinstance(rows, list):
            raise AngisRuntimeError("CSV write needs rows as a list of dicts.")
        fieldnames = _require_arg(args, "columns") if "columns" in args else (list(rows[0]) if rows else [])
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return str(path)
    raise AngisRuntimeError(f"CSV action {action!r} is not available.")


def _run_data_action(action: str, args: dict[str, object]) -> object:
    rows = _require_arg(args, "rows")
    if not isinstance(rows, list):
        raise AngisRuntimeError("Data actions need rows as a list.")
    if action == "count":
        return len(rows)
    if action == "first":
        return rows[0] if rows else {}
    if action == "column":
        column = str(_require_arg(args, "column"))
        return [row.get(column, "") if isinstance(row, dict) else "" for row in rows]
    if action == "filter_equals":
        column = str(_require_arg(args, "column"))
        value = str(_require_arg(args, "value"))
        return [row for row in rows if isinstance(row, dict) and str(row.get(column, "")) == value]
    raise AngisRuntimeError(f"Data action {action!r} is not available.")


def _run_list_action(action: str, args: dict[str, object]) -> object:
    if action == "range":
        start = int(_require_number(_require_arg(args, "start")))
        end = int(_require_number(_require_arg(args, "end")))
        return list(range(start, end + 1))
    values = _require_arg(args, "values")
    if not isinstance(values, list):
        raise AngisRuntimeError("List actions need values as a list.")
    if action in {"length", "count"}:
        return len(values)
    if action in {"count_value", "count_occurrences", "occurrences"}:
        return values.count(_require_arg(args, "value"))
    if action in {"index_of", "find_index", "position"}:
        value = _require_arg(args, "value")
        try:
            return values.index(value)
        except ValueError as exc:
            raise AngisRuntimeError(f"Value {value!r} not found in list.") from exc
    if action in {"insert", "insert_at"}:
        index = int(_require_number(_require_arg(args, "index")))
        result = list(values)
        result.insert(index, _require_arg(args, "value"))
        return result
    if action in {"extend", "concat", "concatenate"}:
        other = _require_arg(args, "values")
        if not isinstance(other, list):
            raise AngisRuntimeError("List extend needs another list.")
        return [*values, *other]
    if action == "first":
        return values[0] if values else ""
    if action == "last":
        return values[-1] if values else ""
    if action in {"sum", "total"}:
        return sum(_require_number(v) for v in values)
    if action in {"average", "avg", "mean"}:
        if not values:
            return 0
        return sum(_require_number(v) for v in values) / len(values)
    if action == "at":
        index = int(_require_number(_require_arg(args, "index")))
        try:
            return values[index]
        except IndexError as exc:
            raise AngisRuntimeError(f"List index {index} is out of range.") from exc
    if action == "slice":
        start = int(_require_number(args.get("start", 0)))
        end = int(_require_number(args.get("end", len(values))))
        return values[start:end]
    if action == "sort":
        return sorted(values, key=lambda value: str(value))
    if action == "reverse":
        return list(reversed(values))
    if action == "unique":
        seen: set[str] = set()
        unique_values: list[object] = []
        for value in values:
            key = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
            if key not in seen:
                seen.add(key)
                unique_values.append(value)
        return unique_values
    if action == "contains":
        return _require_arg(args, "value") in values
    if action == "append":
        return [*values, _require_arg(args, "value")]
    if action == "pop":
        if not values:
            raise AngisRuntimeError("Cannot pop from an empty list.")
        return values.pop()
    if action == "clear":
        return []
    if action == "shuffle":
        shuffled = list(values)
        random.shuffle(shuffled)
        return shuffled
    raise AngisRuntimeError(f"List action {action!r} is not available.")


def _run_map_action(action: str, args: dict[str, object]) -> object:
    value = _require_arg(args, "value")
    if not isinstance(value, dict):
        raise AngisRuntimeError("Map actions need value as a dictionary.")
    if action == "keys":
        return list(value.keys())
    if action == "values":
        return list(value.values())
    if action == "get":
        return value.get(str(_require_arg(args, "key")), "")
    if action == "has":
        return str(_require_arg(args, "key")) in value
    if action == "merge":
        other = _require_arg(args, "other")
        if not isinstance(other, dict):
            raise AngisRuntimeError("Map merge needs other as a dictionary.")
        return {**value, **other}
    raise AngisRuntimeError(f"Map action {action!r} is not available.")


def _run_path_action(action: str, args: dict[str, object]) -> object:
    if action == "join":
        left = Path(str(_require_arg(args, "left"))).expanduser()
        right = str(_require_arg(args, "right"))
        return str((left / right).resolve())
    path = Path(str(_require_arg(args, "path"))).expanduser()
    if action == "name":
        return path.name
    if action == "extension":
        return path.suffix
    if action == "parent":
        return str(path.parent)
    if action == "stem":
        return path.stem
    raise AngisRuntimeError(f"Path action {action!r} is not available.")


def _run_convert_action(action: str, args: dict[str, object]) -> object:
    if action in {"to_string", "to_text", "str"}:
        return str(_require_arg(args, "value"))
    if action in {"to_number", "to_int", "to_integer", "int", "num"}:
        try:
            raw = _require_arg(args, "value")
            if isinstance(raw, str):
                if "." in raw:
                    return float(raw)
                return int(raw)
            if isinstance(raw, bool):
                return int(raw)
            if isinstance(raw, (int, float)):
                return raw
            return int(str(raw))
        except (ValueError, TypeError) as exc:
            raise AngisRuntimeError(f"Could not convert {raw!r} to a number.") from exc
    raise AngisRuntimeError(f"Convert action {action!r} is not available.")


def _run_bitwise_action(action: str, args: dict[str, object]) -> int:
    if action in {"and", "bitwise_and"}:
        return int(_require_number(_require_arg(args, "left"))) & int(_require_number(_require_arg(args, "right")))
    if action in {"or", "bitwise_or"}:
        return int(_require_number(_require_arg(args, "left"))) | int(_require_number(_require_arg(args, "right")))
    if action in {"xor", "bitwise_xor"}:
        return int(_require_number(_require_arg(args, "left"))) ^ int(_require_number(_require_arg(args, "right")))
    if action in {"not", "bitwise_not"}:
        return ~int(_require_number(_require_arg(args, "value")))
    if action in {"shift_left", "left_shift"}:
        return int(_require_number(_require_arg(args, "value"))) << int(_require_number(_require_arg(args, "amount")))
    if action in {"shift_right", "right_shift"}:
        return int(_require_number(_require_arg(args, "value"))) >> int(_require_number(_require_arg(args, "amount")))
    raise AngisRuntimeError(f"Bitwise action {action!r} is not available.")


def _run_statistics_action(action: str, args: dict[str, object]) -> object:
    values = _require_arg(args, "values")
    if not isinstance(values, list) or not values:
        raise AngisRuntimeError("Statistics actions need a non-empty list of numbers.")
    nums = [_require_number(v) for v in values]
    if action in {"median", "middle"}:
        s = sorted(nums)
        n = len(s)
        if n % 2 == 1:
            return s[n // 2]
        return (s[n // 2 - 1] + s[n // 2]) / 2
    if action in {"mode", "most_common"}:
        from collections import Counter
        counts = Counter(nums)
        return counts.most_common(1)[0][0]
    if action in {"stdev", "std", "standard_deviation"}:
        avg = sum(nums) / len(nums)
        variance = sum((x - avg) ** 2 for x in nums) / len(nums)
        return math.sqrt(variance)
    raise AngisRuntimeError(f"Statistics action {action!r} is not available.")


import socket as _socket


def _run_socket_action(action: str, args: dict[str, object]) -> object:
    sock = args.get("socket")
    if action == "connect":
        host = str(_require_arg(args, "host"))
        port = int(_require_number(_require_arg(args, "port")))
        family = args.get("family", _socket.AF_INET)
        s = _socket.socket(family, _socket.SOCK_STREAM)
        s.settimeout(30)
        s.connect((host, port))
        return s
    if action == "send":
        if sock is None:
            raise AngisRuntimeError("Socket send needs a 'socket' argument.")
        data = str(_require_arg(args, "data")).encode("utf-8")
        sock.sendall(data)
        return len(data)
    if action == "recv":
        if sock is None:
            raise AngisRuntimeError("Socket recv needs a 'socket' argument.")
        bufsize = int(_require_number(_require_arg(args, "size")))
        data = sock.recv(bufsize)
        return data.decode("utf-8")
    if action == "close":
        if sock is None:
            raise AngisRuntimeError("Socket close needs a 'socket' argument.")
        sock.close()
        return True
    if action == "bind":
        host = str(_require_arg(args, "host"))
        port = int(_require_number(_require_arg(args, "port")))
        s = sock if sock else _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        s.bind((host, port))
        return s
    if action == "listen":
        if sock is None:
            raise AngisRuntimeError("Socket listen needs a 'socket' argument.")
        backlog = int(_require_arg(args, "backlog")) if "backlog" in args else 5
        sock.listen(backlog)
        return True
    if action == "accept":
        if sock is None:
            raise AngisRuntimeError("Socket accept needs a 'socket' argument.")
        conn, addr = sock.accept()
        return {"connection": conn, "address": addr[0], "port": addr[1]}
    if action == "udp_socket":
        family = args.get("family", _socket.AF_INET)
        s = _socket.socket(family, _socket.SOCK_DGRAM)
        s.settimeout(30)
        return s
    if action == "sendto":
        if sock is None:
            raise AngisRuntimeError("Socket sendto needs a 'socket' argument.")
        data = str(_require_arg(args, "data")).encode("utf-8")
        host = str(_require_arg(args, "host"))
        port = int(_require_number(_require_arg(args, "port")))
        sock.sendto(data, (host, port))
        return len(data)
    if action == "recvfrom":
        if sock is None:
            raise AngisRuntimeError("Socket recvfrom needs a 'socket' argument.")
        bufsize = int(_require_number(_require_arg(args, "size")))
        data, addr = sock.recvfrom(bufsize)
        return {"data": data.decode("utf-8"), "address": addr[0], "port": addr[1]}
    if action == "websocket_connect":
        host = str(_require_arg(args, "host"))
        port = int(_require_number(_require_arg(args, "port")))
        path = str(args.get("path", "/"))
        s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        s.settimeout(30)
        s.connect((host, port))
        import hashlib, base64
        key = base64.b64encode(os.urandom(16)).decode()
        http_key = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(request.encode())
        response = s.recv(4096).decode()
        if "101" not in response:
            s.close()
            raise AngisRuntimeError("WebSocket handshake failed.")
        return {"socket": s, "host": host, "port": port, "path": path}
    if action == "websocket_send":
        if sock is None:
            raise AngisRuntimeError("WebSocket send needs a 'socket' argument.")
        data = str(_require_arg(args, "data")).encode("utf-8")
        length = len(data)
        frame = bytearray()
        frame.append(0x81)
        if length < 126:
            frame.append(0x80 | length)
        elif length < 65536:
            frame.append(0x80 | 126)
            frame.extend(length.to_bytes(2, "big"))
        else:
            frame.append(0x80 | 127)
            frame.extend(length.to_bytes(8, "big"))
        import random as _rand
        mask = bytes([_rand.randint(0, 255) for _ in range(4)])
        frame.extend(mask)
        frame.extend(b ^ mask[i % 4] for i, b in enumerate(data))
        sock.sendall(bytes(frame))
        return len(data)
    if action == "websocket_recv":
        if sock is None:
            raise AngisRuntimeError("WebSocket recv needs a 'socket' argument.")
        first = sock.recv(2)
        if len(first) < 2:
            raise AngisRuntimeError("WebSocket connection closed.")
        opcode = first[0] & 0x0F
        masked = (first[1] & 0x80) != 0
        length = first[1] & 0x7F
        if length == 126:
            ext = sock.recv(2)
            length = int.from_bytes(ext, "big")
        elif length == 127:
            ext = sock.recv(8)
            length = int.from_bytes(ext, "big")
        if masked:
            mask_bytes = sock.recv(4)
        payload = sock.recv(length)
        if masked:
            payload = bytes(b ^ mask_bytes[i % 4] for i, b in enumerate(payload))
        if opcode == 0x8:
            sock.close()
            return ""
        if opcode == 0x9:
            pong = bytearray()
            pong.append(0x8A)
            pong.append(length)
            pong.extend(payload)
            sock.sendall(bytes(pong))
            return ""
        return payload.decode("utf-8")
    if action == "websocket_close":
        if sock is None:
            raise AngisRuntimeError("WebSocket close needs a 'socket' argument.")
        frame = bytearray([0x88, 0x00])
        sock.sendall(bytes(frame))
        sock.close()
        return True
    raise AngisRuntimeError(f"Socket action {action!r} is not available.")


def _default_loading_asset(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "angis loading" / name


def _format_value(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _file_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".png", ".gif"}:
        return "image"
    if suffix in {".txt", ".md", ".angis", ".py", ".json", ".csv", ".html", ".css", ".js"}:
        return "text"
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".jpg", ".jpeg", ".webp", ".heic"}:
        return "image-file"
    return suffix[1:] if suffix else "file"


def _file_preview(path: Path) -> str:
    if _file_kind(path) != "text":
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = content.splitlines()[:6]
    preview = "\n".join(lines)
    return preview[:500]


def _app_to_html(app: AppSpec) -> str:
    width = app.width
    height = app.height
    layout = app.layout or {"kind": "free", "columns": 1}
    body = [f"<h1>{html.escape(app.title)}</h1>"]
    for text in app.texts:
        body.append(f"<p>{html.escape(text)}</p>")
    if app.scene in {"canvas", "2d screen", "2d world"}:
        body.append(f'<div class="canvas" style="width:{width}px;height:{height}px;">')
        for obj in app.objects or []:
            props = obj.properties or {}
            if obj.kind == "video":
                obj_width = int(props.get("width", 320)) if isinstance(props.get("width", 320), (int, float)) else 320
                obj_height = int(props.get("height", 180)) if isinstance(props.get("height", 180), (int, float)) else 180
                body.append(
                    f'<video controls src="{html.escape(obj.path)}" style="position:absolute;left:{obj.x}px;top:{obj.y}px;'
                    f'width:{obj_width}px;height:{obj_height}px;"></video>'
                )
                continue
            if obj.kind in {"input", "textbox"}:
                label = html.escape(obj.text or obj.name)
                body.append(f'<input aria-label="{label}" placeholder="{label}" style="position:absolute;left:{obj.x}px;top:{obj.y}px;width:{int(props.get("width", 180)) if isinstance(props.get("width", 180), (int, float)) else 180}px;height:32px;">')
                continue
            if obj.kind in {"slider"}:
                body.append(f'<input type="range" aria-label="{html.escape(obj.name)}" style="position:absolute;left:{obj.x}px;top:{obj.y}px;width:{int(props.get("width", 180)) if isinstance(props.get("width", 180), (int, float)) else 180}px;">')
                continue
            if obj.kind in {"checkbox", "toggle"}:
                body.append(f'<label style="position:absolute;left:{obj.x}px;top:{obj.y}px;"><input type="checkbox"> {html.escape(obj.text or obj.name)}</label>')
                continue
            color = html.escape(str(props.get("color", "#2563eb")))
            obj_width = int(props.get("width", props.get("size", 48))) if isinstance(props.get("width", props.get("size", 48)), (int, float)) else 48
            obj_height = int(props.get("height", props.get("size", 48))) if isinstance(props.get("height", props.get("size", 48)), (int, float)) else 48
            radius = "50%" if obj.kind in {"circle", "ball", "player", "enemy"} else "4px"
            label = html.escape(obj.text or obj.name)
            body.append(
                f'<div class="object" style="left:{obj.x}px;top:{obj.y}px;width:{obj_width}px;'
                f'height:{obj_height}px;background:{color};border-radius:{radius};">{label}</div>'
            )
        body.append("</div>")
    if app.scene in {"true 3d", "3d render"}:
        body.append(f'<div class="canvas" style="width:{width}px;height:{height}px;">')
        body.append('<div style="padding:16px;font-weight:700">Angis true 3D scene preview</div>')
        for obj in app.objects or []:
            body.append(f'<div style="padding-left:16px">{html.escape(obj.kind)} {html.escape(obj.name)} at x {obj.x} y {obj.y} z {obj.z}</div>')
        body.append("</div>")
    for label in app.buttons:
        body.append(f"<button>{html.escape(label)}</button>")
    imports = ", ".join(app.imports or [])
    columns = max(1, int(layout.get("columns", 1))) if isinstance(layout.get("columns", 1), int) else 1
    layout_css = f"body.layout-grid main{{display:grid;grid-template-columns:repeat({columns},minmax(0,1fr));gap:12px}}" if layout.get("kind") == "grid" else ""
    body_class = f"layout-{html.escape(str(layout.get('kind', 'free')))}"
    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="en" class="{body_class}">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{html.escape(app.title)}</title>",
            "<style>",
            "body{font-family:system-ui,sans-serif;margin:24px;background:#f8fafc;color:#111827}",
            ".canvas{position:relative;overflow:hidden;background:white;border:1px solid #cbd5e1}",
            ".object{position:absolute;display:flex;align-items:center;justify-content:center;color:white;font-weight:700}",
            "button{margin:6px;padding:8px 12px}",
            layout_css,
            "</style>",
            "</head>",
            "<body>",
            f"<!-- Angis imports: {html.escape(imports)} | backend: {html.escape(app.backend)} -->",
            f"<!-- Angis layout: {html.escape(str(layout))} | sound volume: {app.sound_volume} -->",
            *body,
            "</body>",
            "</html>",
        ]
    )


def _mac_app_plist(title: str) -> str:
    escaped = html.escape(title)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key><string>AngisApp</string>
  <key>CFBundleIdentifier</key><string>local.angis.{escaped}</string>
  <key>CFBundleName</key><string>{escaped}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict>
</plist>
"""


def _find_object(app: AppSpec, name: str) -> CreatorObject:
    for obj in app.objects or []:
        if obj.name == name:
            return obj
    raise AngisRuntimeError(f"Object {name!r} has not been created.")
