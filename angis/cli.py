"""Command line interface for Angis."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .errors import AngisError
from .interpreter import Interpreter
from .parser import parse_file
from .pygame_runner import run_pygame_app
from .transpile import transpile


def _event_runner(interpreter: Interpreter, instructions: list[object]) -> None:
    from .interpreter import _LoopControl

    for instr in instructions:
        try:
            interpreter._run_instruction(instr, [])
        except _LoopControl:
            break


def _run_visual_app(app_spec: object, interpreter: Interpreter) -> None:
    scene = getattr(app_spec, "scene", "text")
    if scene in {"true 3d", "3d render"}:
        from .tk_runner import render_3d_app

        render_3d_app(app_spec, lambda instrs: _event_runner(interpreter, instrs), interpreter=interpreter)
    elif app_spec.backend == "tk":
        from .tk_runner import run_tk_app

        run_tk_app(app_spec, lambda instrs: _event_runner(interpreter, instrs), interpreter=interpreter)
    else:
        from .pygame_runner import run_pygame_app

        run_pygame_app(app_spec)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="angis", description="Run Angis programs.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_parser = subcommands.add_parser("run", help="Run a .angis file")
    run_parser.add_argument("file", type=Path)

    pygame_parser = subcommands.add_parser("pygame", help="Run an Angis app with the real pygame backend")
    pygame_parser.add_argument("file", type=Path)

    debug_parser = subcommands.add_parser("debug", help="Step through a .angis file instruction by instruction")
    debug_parser.add_argument("file", type=Path)
    debug_parser.add_argument("--no-wait", action="store_true", help="Print the debug trace without waiting for Enter")

    ir_parser = subcommands.add_parser("ir", help="Print intermediate representation for a .angis file")
    ir_parser.add_argument("file", type=Path)

    compile_parser = subcommands.add_parser("compile", help="Compile an Angis file to Python")
    compile_parser.add_argument("input", type=Path, help="Input .angis file")
    compile_parser.add_argument("output", type=Path, nargs="?", help="Output .py file (default: print to stdout)")

    watch_parser = subcommands.add_parser("watch", help="Watch a .angis file for changes and auto-reload")
    watch_parser.add_argument("file", type=Path)

    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            file_path = Path(args.file).expanduser().resolve()
            instructions = parse_file(file_path)
            opened: list[object] = []
            interp = Interpreter(output=sys.stdout, app_runner=opened.append, base_path=file_path.parent)
            interp.run(instructions)
            if opened and (opened[-1].objects or opened[-1].events):
                _run_visual_app(opened[-1], interp)
        elif args.command == "pygame":
            file_path = Path(args.file).expanduser().resolve()
            instructions = parse_file(file_path)
            opened = []
            Interpreter(app_runner=opened.append, base_path=file_path.parent).run(instructions)
            if not opened:
                raise AngisError("No app was created. Start with: App, My App.")
            run_pygame_app(opened[-1])
        elif args.command == "debug":
            instructions = parse_file(args.file)
            interpreter = Interpreter(output=sys.stdout)
            for index, instruction in enumerate(instructions, start=1):
                print(f"[{index}/{len(instructions)}] {instruction}")
                if not args.no_wait:
                    input("Press Enter to step...")
                interpreter._run_instruction(instruction, [])
        elif args.command == "ir":
            for instruction in parse_file(args.file):
                print(f"{instruction}  confidence={instruction.confidence:.2f}")
        elif args.command == "compile":
            instructions = parse_file(args.input)
            code = transpile(instructions)
            if args.output:
                output_path = Path(args.output).expanduser().resolve()
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(code, encoding="utf-8")
                print(f"Compiled {args.input} -> {output_path}")
            else:
                print(code, end="")
        elif args.command == "watch":
            file_path = Path(args.file).expanduser().resolve()
            print(f"Watching {file_path} for changes...")
            print("Press Ctrl+C to stop.")
            last_mtime = file_path.stat().st_mtime
            try:
                while True:
                    import time
                    time.sleep(1)
                    if file_path.is_file():
                        new_mtime = file_path.stat().st_mtime
                        if new_mtime != last_mtime:
                            last_mtime = new_mtime
                            print(f"\n--- Reloading {file_path.name} ---")
                            try:
                                instructions = parse_file(file_path)
                                interp = Interpreter(output=sys.stdout, base_path=file_path.parent)
                                interp.run(instructions)
                            except Exception as exc:
                                print(f"Reload error: {exc}")
            except KeyboardInterrupt:
                print("\nWatcher stopped.")
        return 0
    except AngisError as exc:
        print(f"Angis error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
