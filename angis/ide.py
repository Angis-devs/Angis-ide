"""Simple built-in Angis IDE using Tkinter."""

from __future__ import annotations

import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import wave

from .errors import AngisError
from .interpreter import Interpreter
from .ir import AnimateObject, AppSpec, GameSpec, MoveObject, PlaySound, SetSoundVolume, ShowText, StopSound
from .lang import _ as _lang_ui
from .parser import parse_source

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - optional local dependency
    Image = None
    ImageTk = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = PROJECT_ROOT / "logo" / "logo.png"
STARTUP_IMAGE = PROJECT_ROOT / "angis loading" / "loading screen.png"
STARTUP_AUDIO = PROJECT_ROOT / "angis loading" / "loading-adieo.mp3"
STARTUP_MAX_SIZE = 720


class AngisIDE(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(_lang_ui("window_title"))
        self.geometry("920x680")
        self.current_file: Path | None = None
        self.app_windows: list[tk.Toplevel] = []
        self.image_refs: list[object] = []
        self._tabs: list[dict] = []
        self._tab_counter = 0
        self._toolbar_buttons: dict[str, ttk.Button] = {}
        self._panes: ttk.PanedWindow | None = None
        self._editor_frame: ttk.LabelFrame | None = None
        self._output_frame: ttk.LabelFrame | None = None
        self._error_frame: ttk.LabelFrame | None = None
        self._build_ui()
        self._set_app_icon(self)

    def _set_app_icon(self, window: tk.Misc) -> None:
        _set_window_icon(window, LOGO_PATH)

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8, pady=8)

        def tb(key: str, cmd, pad_left: int = 0) -> ttk.Button:
            b = ttk.Button(toolbar, text=_lang_ui(key), command=cmd)
            b.pack(side=tk.LEFT, padx=(pad_left, 6))
            self._toolbar_buttons[key] = b
            return b

        tb("open", self.open_file)
        tb("save", self.save_file)
        tb("save_as", self.save_file_as)
        tb("cut", lambda: self._editor_event("<<Cut>>"), 12)
        tb("copy", lambda: self._editor_event("<<Copy>>"))
        tb("paste", lambda: self._editor_event("<<Paste>>"))
        tb("run", self.run_code, 12)
        tb("settings", self._open_settings)
        ttk.Button(toolbar, text=_lang_ui("close_tab"), command=self.close_current_tab).pack(side=tk.RIGHT, padx=(6, 0))

        self._panes = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self._panes.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._editor_frame = ttk.LabelFrame(self._panes, text=_lang_ui("editor"))

        self._notebook = ttk.Notebook(self._editor_frame)
        self._notebook.pack(fill=tk.BOTH, expand=True)
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_switch)

        close_key = "<Command-w>" if sys.platform == "darwin" else "<Control-w>"
        self.bind(close_key, lambda _e: self.close_current_tab())

        self.editor = tk.Text(self._editor_frame)
        self._line_numbers = tk.Canvas(self._editor_frame)
        self._editor_font = tkfont.Font(family="Courier", size=11)

        self._panes.add(self._editor_frame, weight=4)

        self._add_tab(None, "")

        self._output_frame = ttk.LabelFrame(self._panes, text=_lang_ui("output"))
        self.output = tk.Text(self._output_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True)
        self._panes.add(self._output_frame, weight=1)

        self._error_frame = ttk.LabelFrame(self._panes, text=_lang_ui("errors"))
        self.errors = tk.Text(self._error_frame, height=5, state=tk.DISABLED, wrap=tk.WORD, foreground="#9b1c1c")
        self.errors.pack(fill=tk.BOTH, expand=True)
        self._panes.add(self._error_frame, weight=1)
        self._build_readonly_menus()

    def _rebuild_ui_texts(self) -> None:
        for key, btn in self._toolbar_buttons.items():
            btn.config(text=_lang_ui(key))
        if self._editor_frame:
            self._editor_frame.config(text=_lang_ui("editor"))
        if self._output_frame:
            self._output_frame.config(text=_lang_ui("output"))
        if self._error_frame:
            self._error_frame.config(text=_lang_ui("errors"))
        current_name = self.current_file.name if self.current_file else ""
        if current_name:
            self.title(f"{_lang_ui('window_title')} - {current_name}")
        else:
            self.title(_lang_ui("window_title"))
        for i, tab in enumerate(self._tabs):
            path = tab["path"]
            label = path.name if path else f"{_lang_ui('untitled')} {i + 1}"
            self._notebook.tab(i, text=label)
        # rebuild context menus
        self._build_editor_menu()
        self._build_readonly_menus()

    def _open_settings(self) -> None:
        from .lang import get_language, get_supported_languages, set_language
        dialog = tk.Toplevel(self)
        dialog.title(_lang_ui("set_language"))
        dialog.geometry("360x160")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text=_lang_ui("choose_language")).pack(pady=(20, 8))
        langs = get_supported_languages()
        var = tk.StringVar()
        current = get_language()
        combo = ttk.Combobox(dialog, textvariable=var, state="readonly", width=24)
        combo["values"] = [f"{p['name']} ({p['code']})" for p in langs]
        for i, p in enumerate(langs):
            if p["code"] == current.code:
                combo.current(i)
                break
        else:
            combo.current(0)
        combo.pack()

        def apply() -> None:
            sel = combo.current()
            if sel >= 0:
                set_language(langs[sel]["code"])
                self._rebuild_ui_texts()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(16, 0))
        ttk.Button(btn_frame, text=_lang_ui("apply"), command=apply).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text=_lang_ui("cancel"), command=dialog.destroy).pack(side=tk.LEFT)

    def _make_tab_widgets(self) -> tuple[tk.Frame, tk.Text, tk.Canvas]:
        frame = tk.Frame(self._notebook)
        ln = tk.Canvas(frame, width=40, bg="#f0f0f0", highlightthickness=0)
        ln.pack(side=tk.LEFT, fill=tk.Y)
        ed = tk.Text(frame, wrap=tk.WORD, undo=True, font=self._editor_font)
        ed.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ed.bind("<KeyRelease>", lambda _e, c=ln, e=ed: self._update_line_numbers_for(e, c))
        ed.bind("<MouseWheel>", lambda _e, c=ln, e=ed: self._update_line_numbers_for(e, c))
        ed.bind("<ButtonRelease-1>", lambda _e, c=ln, e=ed: self._update_line_numbers_for(e, c))
        ed.bind("<Configure>", lambda _e, c=ln, e=ed: self._update_line_numbers_for(e, c))
        ln.bind("<MouseWheel>", lambda e, ed_w=ed, ln_c=ln: self._on_gutter_wheel_for(e, ed_w, ln_c))
        ln.bind("<Button-1>", lambda _e, ed_w=ed: ed_w.focus_set())
        self.editor = ed
        self._line_numbers = ln
        self._build_editor_menu()
        return frame, ed, ln

    def _add_tab(self, path: Path | None, content: str = "") -> int:
        self._tab_counter += 1
        label = path.name if path else f"{_lang_ui('untitled')} {self._tab_counter}"
        frame, ed, ln = self._make_tab_widgets()
        self._notebook.add(frame, text=label)
        tab = {"path": path, "editor": ed, "line_numbers": ln, "frame": frame}
        self._tabs.append(tab)
        idx = len(self._tabs) - 1
        self._notebook.select(idx)
        self._activate_tab(idx)
        if content:
            ed.insert("1.0", content)
        return idx

    def _activate_tab(self, index: int) -> None:
        tab = self._tabs[index]
        self.editor = tab["editor"]
        self._line_numbers = tab["line_numbers"]
        self.current_file = tab["path"]
        self._editor_font = tkfont.Font(font=self.editor["font"])
        self.after_idle(lambda: self._update_line_numbers_for(self.editor, self._line_numbers))

    def _on_tab_switch(self, _event: object = None) -> None:
        sel = self._notebook.index(self._notebook.select())
        if sel < len(self._tabs):
            self._activate_tab(sel)

    def _tab_index(self, editor: tk.Text) -> int:
        for i, t in enumerate(self._tabs):
            if t["editor"] is editor:
                return i
        return -1

    def close_current_tab(self) -> None:
        idx = self._notebook.index(self._notebook.select())
        self._close_tab(idx)

    def _close_tab(self, index: int) -> None:
        if len(self._tabs) <= 1:
            return
        tab = self._tabs.pop(index)
        self._notebook.forget(tab["frame"])
        sel = self._notebook.index(self._notebook.select())
        if sel < len(self._tabs):
            self._activate_tab(sel)

    def open_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[(_lang_ui("angis_files"), "*.angis"), (_lang_ui("all_files"), "*")])
        if not path:
            return
        file_path = self._validate_path(Path(path), must_exist=True)
        content = file_path.read_text(encoding="utf-8")
        self._add_tab(file_path, content)
        self.title(f"{_lang_ui('window_title')} - {file_path.name}")

    def save_file(self) -> None:
        if self.current_file is None:
            self.save_file_as()
            return
        self._write_current(self.current_file)

    def save_file_as(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".angis", filetypes=[(_lang_ui("angis_files"), "*.angis"), (_lang_ui("text_files"), "*.txt"), (_lang_ui("all_files"), "*")])
        if not path:
            return
        file_path = self._validate_path(Path(path), must_exist=False)
        idx = self._tab_index(self.editor)
        if idx >= 0:
            self._tabs[idx]["path"] = file_path
            label = file_path.name
            self._notebook.tab(idx, text=label)
        self.current_file = file_path
        self._write_current(file_path)
        self.title(f"{_lang_ui('window_title')} - {file_path.name}")

    def run_code(self) -> None:
        self._set_text(self.output, "")
        self._set_text(self.errors, "")
        try:
            source = self.editor.get("1.0", tk.END)
            base_path = self.current_file.parent if self.current_file else None
            instructions = parse_source(source, base_path)
            apps: list[AppSpec] = []
            self._last_interpreter = Interpreter(
                app_runner=apps.append,
                game_runner=self.open_angis_game,
                base_path=base_path,
            )
            lines = self._last_interpreter.run(instructions)
            self._set_text(self.output, "\n".join(lines))
            for app in apps:
                if app.objects or app.events:
                    self.open_angis_app(app)
        except AngisError as exc:
            self._set_text(self.errors, str(exc))

    def open_angis_app(self, app: AppSpec) -> None:
        if app.loading_image or app.loading_audio:
            self._show_loading_then_open(app)
            return
        self._open_angis_app_now(app)

    def _open_angis_app_now(self, app: AppSpec) -> None:
        window = tk.Toplevel(self)
        window.title(app.title)
        self._set_app_icon(window)
        canvas_scenes = {"canvas", "2d screen", "2d world"}
        true_3d_scenes = {"true 3d", "3d render"}
        window.geometry(f"{app.width}x{app.height}" if app.scene in canvas_scenes | true_3d_scenes | {"3d world", "three d world"} else "520x420")
        self.app_windows.append(window)

        if app.scene in true_3d_scenes:
            self._render_true_3d_app(window, app)
            return
        if app.scene in {"3d world", "three d world"}:
            self._render_3d_world_app(window, app)
            return
        if app.scene in canvas_scenes:
            self._render_canvas_app(window, app)
            return

        frame = ttk.Frame(window, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(frame, text=app.title, font=("TkDefaultFont", 16, "bold"))
        title.pack(anchor=tk.W, pady=(0, 12))

        for text in app.texts:
            ttk.Label(frame, text=text, wraplength=360).pack(anchor=tk.W, pady=(0, 8))

        for file_info in app.files or []:
            image = self._load_app_image(file_info.path, max_width=420, max_height=180)
            if image is not None:
                ttk.Label(frame, image=image).pack(anchor=tk.W, pady=(0, 8))
            ttk.Label(frame, text=self._file_card_text(file_info), wraplength=420).pack(anchor=tk.W, pady=(0, 6))
            if file_info.preview:
                preview = tk.Text(frame, height=min(6, len(file_info.preview.splitlines()) + 1), width=56, wrap=tk.WORD)
                preview.insert("1.0", file_info.preview)
                preview.configure(state=tk.DISABLED)
                preview.pack(anchor=tk.W, pady=(0, 8))
            ttk.Label(frame, text=file_info.path, wraplength=420, foreground="#4b5563").pack(anchor=tk.W, pady=(0, 8))

        status = ttk.Label(frame, text="")
        status.pack(anchor=tk.W, pady=(8, 0))

        for label in app.buttons:
            ttk.Button(
                frame,
                text=label,
                command=lambda value=label: status.configure(text=f"Clicked: {value}"),
            ).pack(anchor=tk.W, pady=(6, 0))

    def _render_canvas_app(self, window: tk.Toplevel, app: AppSpec) -> None:
        canvas_height = max(120, app.height - 42)
        design = {"width": max(1, app.width), "height": max(1, canvas_height), "scale_x": 1.0, "scale_y": 1.0}
        canvas = tk.Canvas(window, width=app.width, height=canvas_height, bg="#f8fafc", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        status = ttk.Label(window, text=_lang_ui("canvas_ready"))
        status.pack(fill=tk.X)
        objects = {
            obj.name: {
                "x": obj.x,
                "y": obj.y,
                "z": obj.z,
                "kind": obj.kind,
                "text": obj.text,
                "path": obj.path,
                "properties": obj.properties or {},
            }
            for obj in app.objects or []
        }
        animations: list[AnimateObject] = []
        state = {"checking_collision": False, "message": _lang_ui("canvas_ready"), "sound_volume": app.sound_volume}
        audio_players: list[subprocess.Popen] = []

        def number_property(obj: dict[str, object], name: str, default: int) -> int:
            value = obj["properties"].get(name, default)
            return int(value) if isinstance(value, (int, float)) else default

        def bounds(name: str) -> tuple[int, int, int, int]:
            obj = objects[name]
            x = int(obj["x"])
            y = int(obj["y"])
            width = number_property(obj, "width", number_property(obj, "size", 48))
            height = number_property(obj, "height", number_property(obj, "size", 48))
            return x, y, x + width, y + height

        def screen_rect(obj: dict[str, object]) -> tuple[float, float, float, float]:
            x = int(obj["x"]) * design["scale_x"]
            y = int(obj["y"]) * design["scale_y"]
            width = number_property(obj, "width", number_property(obj, "size", 48)) * design["scale_x"]
            height = number_property(obj, "height", number_property(obj, "size", 48)) * design["scale_y"]
            return x, y, x + width, y + height

        def draw() -> None:
            canvas.delete("all")
            actual_width = max(1, canvas.winfo_width())
            actual_height = max(1, canvas.winfo_height())
            design["scale_x"] = actual_width / design["width"]
            design["scale_y"] = actual_height / design["height"]
            background = "#f8fafc"
            for obj in objects.values():
                if obj["kind"] == "background":
                    background = str(obj["properties"].get("color", background))
            canvas.configure(bg=background)
            if app.backend == "pygame" or app.imports:
                imports = ", ".join(app.imports or [])
                backend_label = app.backend
                if app.backend == "pygame" and not _module_available("pygame"):
                    backend_label = "pygame-style canvas (pygame not installed)"
                canvas.create_rectangle(0, 0, actual_width, 34, fill="#111827", outline="")
                canvas.create_text(
                    14,
                    17,
                    anchor=tk.W,
                    text=f"backend: {backend_label}   imports: {imports}",
                    fill="#e5e7eb",
                    font=("TkDefaultFont", 11, "bold"),
                )
            for text in app.texts:
                y = 46 + app.texts.index(text) * 22 if app.imports else 16 + app.texts.index(text) * 22
                canvas.create_text(16, y, anchor=tk.NW, text=text, fill="#111827", font=("TkDefaultFont", 12))
            for name, obj in sorted(objects.items(), key=lambda item: int(item[1]["z"])):
                kind = str(obj["kind"]).lower()
                x1, y1, x2, y2 = screen_rect(obj)
                props = obj["properties"]
                fill = str(props.get("color", "#2563eb"))
                outline = str(props.get("outline", "#111827"))
                width = max(1, int(x2 - x1))
                height = max(1, int(y2 - y1))
                if kind in {"circle", "ball", "player", "enemy"}:
                    canvas.create_oval(x1, y1, x2, y2, fill=fill, outline=outline, width=2)
                    canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(obj["text"] or name), fill=str(props.get("textcolor", "#ffffff")), font=("TkDefaultFont", max(10, min(20, width // 4)), "bold"))
                elif kind in {"text", "label"}:
                    size = max(8, int(number_property(obj, "size", 18) * min(design["scale_x"], design["scale_y"])))
                    canvas.create_text(x1, y1, anchor=tk.NW, text=str(obj["text"] or name), fill=fill, font=("TkDefaultFont", size, "bold"))
                elif kind == "image":
                    image = self._load_app_image(str(obj["path"]), max_width=width, max_height=height)
                    if image is not None:
                        canvas.create_image(x1, y1, anchor=tk.NW, image=image)
                    else:
                        canvas.create_rectangle(x1, y1, x2, y2, fill="#e5e7eb", outline=outline)
                        canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=name, fill="#111827")
                elif kind == "video":
                    canvas.create_rectangle(x1, y1, x2, y2, fill="#111827", outline="#334155", width=2)
                    canvas.create_polygon((x1 + x2) / 2 - 18, (y1 + y2) / 2 - 24, (x1 + x2) / 2 - 18, (y1 + y2) / 2 + 24, (x1 + x2) / 2 + 24, (y1 + y2) / 2, fill="#f8fafc")
                    canvas.create_text((x1 + x2) / 2, y2 - 18, text=Path(str(obj["path"])).name, fill="#e5e7eb", font=("TkDefaultFont", 10, "bold"))
                elif kind in {"input", "textbox"}:
                    canvas.create_rectangle(x1, y1, x2, y2, fill="#ffffff", outline=outline, width=2)
                    canvas.create_text(x1 + 10, (y1 + y2) / 2, anchor=tk.W, text=str(obj["text"] or name), fill="#64748b", font=("TkDefaultFont", 11))
                elif kind == "slider":
                    mid_y = (y1 + y2) / 2
                    canvas.create_line(x1, mid_y, x2, mid_y, fill=outline, width=4)
                    canvas.create_oval(x1 + width * 0.45 - 8, mid_y - 8, x1 + width * 0.45 + 8, mid_y + 8, fill=fill, outline=outline)
                elif kind in {"checkbox", "toggle"}:
                    side = min(width, height, 28)
                    canvas.create_rectangle(x1, y1, x1 + side, y1 + side, fill="#ffffff", outline=outline, width=2)
                    canvas.create_text(x1 + side + 8, y1 + side / 2, anchor=tk.W, text=str(obj["text"] or name), fill="#111827", font=("TkDefaultFont", 11, "bold"))
                else:
                    canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=2)
                    canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(obj["text"] or name), fill=str(props.get("textcolor", "#ffffff")), font=("TkDefaultFont", max(10, min(20, width // 5)), "bold"))
            status.configure(text=state["message"])

        def apply_move(name: str, direction: str, amount: int) -> None:
            if name not in objects:
                return
            if direction in {"forward", "right"}:
                objects[name]["x"] += amount
            elif direction in {"backward", "left"}:
                objects[name]["x"] -= amount
            elif direction == "up":
                objects[name]["y"] -= amount
            elif direction == "down":
                objects[name]["y"] += amount

        def run_actions(actions: list[object]) -> None:
            interp = getattr(self, '_last_interpreter', None)
            for action in actions:
                if isinstance(action, MoveObject):
                    apply_move(action.name, action.direction, action.amount)
                    state["message"] = f"Moved {action.name}"
                elif isinstance(action, AnimateObject):
                    animations.append(action)
                    state["message"] = f"Animating {action.name}"
                elif isinstance(action, ShowText):
                    state["message"] = action.text
                    if interp is not None:
                        interp._pending_notifications.append(action.text)
                elif isinstance(action, PlaySound):
                    player = self._play_named_sound(window, action.name, int(state["sound_volume"]))
                    if player is not None:
                        audio_players.append(player)
                    state["message"] = f"Played sound: {action.name}"
                elif isinstance(action, StopSound):
                    for player in list(audio_players):
                        if player.poll() is None:
                            player.terminate()
                    audio_players.clear()
                    state["message"] = "Stopped sound"
                elif isinstance(action, SetSoundVolume):
                    state["sound_volume"] = action.volume
                    state["message"] = f"Sound volume: {action.volume}"
                elif interp is not None:
                    try:
                        interp._run_instruction(action, [])
                    except Exception:
                        break
            # Drain pending notifications from interpreter
            if interp is not None:
                pending = getattr(interp, "_pending_notifications", None)
                if pending:
                    state["message"] = pending[-1]
                    pending.clear()
            check_collisions()
            draw()

        def check_collisions() -> None:
            if state["checking_collision"]:
                return
            state["checking_collision"] = True
            for key, actions in (app.events or {}).items():
                if not key.startswith("collision:"):
                    continue
                _prefix, pair = key.split(":", 1)
                left, right = pair.split(":", 1)
                if left not in objects or right not in objects:
                    continue
                left_bounds = bounds(left)
                right_bounds = bounds(right)
                touching = left_bounds[0] < right_bounds[2] and left_bounds[2] > right_bounds[0] and left_bounds[1] < right_bounds[3] and left_bounds[3] > right_bounds[1]
                if touching:
                    run_actions(actions)
                    break
            state["checking_collision"] = False

        def timer_tick(milliseconds: int, actions: list[object]) -> None:
            if window.winfo_exists():
                run_actions(actions)
                window.after(milliseconds, lambda: timer_tick(milliseconds, actions))

        def animation_tick() -> None:
            for animation in animations:
                apply_move(animation.name, animation.direction, animation.amount)
            if animations:
                check_collisions()
                draw()
            if window.winfo_exists():
                window.after(60, animation_tick)

        def key(event: tk.Event) -> None:
            actions = (app.events or {}).get(f"key:{event.keysym.lower()}", [])
            if actions:
                run_actions(actions)

        def click(event: tk.Event) -> None:
            design_x = event.x / design["scale_x"]
            design_y = event.y / design["scale_y"]
            for name in reversed(list(objects)):
                x1, y1, x2, y2 = bounds(name)
                if x1 <= design_x <= x2 and y1 <= design_y <= y2:
                    actions = (app.events or {}).get(f"button:{name.lower()}", [])
                    if actions:
                        run_actions(actions)
                        return
            run_actions((app.events or {}).get("mouse:clicked", []))

        window.bind("<Key>", key)
        canvas.bind("<Button-1>", lambda event: (canvas.focus_set(), click(event)))
        canvas.bind("<Configure>", lambda _event: draw())
        canvas.focus_set()
        draw()
        for key_name, actions in (app.events or {}).items():
            if key_name.startswith("timer:"):
                milliseconds = int(key_name.split(":", 1)[1])
                window.after(milliseconds, lambda ms=milliseconds, body=actions: timer_tick(ms, body))
        animation_tick()

    def _render_true_3d_app(self, window: tk.Toplevel, app: AppSpec) -> None:
        from .tk_runner import render_3d_app as _tk_render_3d
        from .interpreter import _LoopControl
        interp = getattr(self, '_last_interpreter', None)

        def _event_runner(instructions: list[object]) -> None:
            if interp is None:
                return
            for instr in instructions:
                try:
                    interp._run_instruction(instr, [])
                except _LoopControl:
                    break

        _tk_render_3d(app, _event_runner, parent=window, interpreter=interp)

    def _show_loading_then_open(self, app: AppSpec) -> None:
        loading = tk.Toplevel(self)
        loading.title(f"Loading {app.title}")
        loading.geometry("560x420")
        loading.configure(bg="#0f172a")
        self._set_app_icon(loading)
        self.app_windows.append(loading)

        loading_frame = tk.Frame(loading, bg="#0f172a")
        loading_frame.pack(fill=tk.BOTH, expand=True)

        image = self._load_app_image(app.loading_image, max_width=520, max_height=240) if app.loading_image else None
        if image is not None:
            tk.Label(loading_frame, image=image, bg="#0f172a").pack(pady=(30, 4))
        else:
            tk.Label(loading_frame, text=_lang_ui("loading"), font=("TkDefaultFont", 28, "bold"), bg="#0f172a", fg="#f8fafc").pack(pady=(60, 12))

        BAR_W = 360
        BAR_H = 16
        bar_canvas = tk.Canvas(loading_frame, width=BAR_W, height=BAR_H, bg="#1e293b", highlightthickness=0)
        bar_canvas.pack()
        bar_fill = bar_canvas.create_rectangle(0, 0, 0, BAR_H, fill="#a855f7", outline="")

        tk.Label(loading_frame, text=app.title, bg="#0f172a", fg="#94a3b8").pack(pady=(16, 0))

        player = self._play_audio_file(app.loading_audio) if app.loading_audio else None
        duration_ms = self._audio_duration_ms(app.loading_audio) if app.loading_audio else 2000
        duration_ms = max(1000, min(duration_ms, 30000))

        state = {"pct": 0, "finished": False}

        def animate() -> None:
            if state["finished"]:
                return
            if not loading.winfo_exists():
                return
            state["pct"] = min(state["pct"] + 2, 100)
            bar_canvas.coords(bar_fill, 0, 0, int(BAR_W * state["pct"] / 100), BAR_H)
            bar_canvas.update()
            if state["pct"] < 100:
                self.after(max(1, duration_ms // 50), animate)

        def finish() -> None:
            if state["finished"]:
                return
            state["finished"] = True
            state["pct"] = 100
            bar_canvas.coords(bar_fill, 0, 0, BAR_W, BAR_H)
            if player is not None and player.poll() is None:
                player.terminate()
            if loading.winfo_exists():
                loading.destroy()
            self._open_angis_app_now(app)

        animate()
        loading.after(duration_ms, finish)

    def _play_audio_file(self, path: str) -> subprocess.Popen | None:
        if not path:
            return None
        player = _play_audio_path(path)
        if player is not None:
            return player
        self.bell()
        return None

    def _audio_duration_ms(self, path: str) -> int:
        return _audio_duration_ms(path)

    def _mp3_duration_ms(self, path: str) -> int:
        return _mp3_duration_ms(path)

    def _render_3d_world_app(self, window: tk.Toplevel, app: AppSpec) -> None:
        canvas = tk.Canvas(window, width=720, height=460, bg="#101827", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        state = {"x": 0, "z": 0, "message": _lang_ui("use_wasd"), "checking_collision": False}
        objects = {
            obj.name: {
                "x": obj.x,
                "y": obj.y,
                "z": obj.z,
                "kind": obj.kind,
                "text": obj.text,
                "properties": obj.properties or {},
            }
            for obj in app.objects or []
        }
        animations: list[AnimateObject] = []
        status = ttk.Label(window, text="")
        status.place(x=24, y=420)

        def project(world_x: float, world_z: float) -> tuple[float, float, float]:
            depth = max(1.0, world_z + 9.0 - state["z"] * 0.2)
            scale = 180 / depth
            screen_x = 360 + (world_x - state["x"] * 0.15) * scale
            screen_y = 130 + depth * 28
            return screen_x, screen_y, scale

        def draw_world() -> None:
            canvas.delete("all")
            canvas.create_rectangle(0, 0, 720, 170, fill="#17223a", outline="")
            canvas.create_rectangle(0, 170, 720, 460, fill="#1d2b22", outline="")
            canvas.create_line(0, 170, 720, 170, fill="#78a3ff", width=2)

            for offset in range(-8, 9):
                x1 = 360 + offset * 42
                canvas.create_line(x1, 170, 360 + offset * 190, 460, fill="#2f6040")
            for row in range(1, 10):
                y = 170 + row * row * 3.3
                canvas.create_line(0, y, 720, y, fill="#315f42")

            static_objects = [(-3, 2), (3, 3), (-5, 5), (5, 6), (0, 8)]
            for index, (world_x, world_z) in enumerate(static_objects):
                screen_x, screen_y, scale = project(world_x, world_z)
                size = max(18, min(82, scale * 0.45))
                color = ["#d94848", "#e59f3a", "#44a36f", "#8b5cf6", "#38bdf8"][index]
                canvas.create_rectangle(
                    screen_x - size / 2,
                    screen_y - size,
                    screen_x + size / 2,
                    screen_y,
                    fill=color,
                    outline="#0f172a",
                    width=2,
                )

            for name, obj in objects.items():
                if obj["kind"] not in {"player"}:
                    continue
                screen_x, screen_y, _scale = project(obj["x"], obj["z"])
                screen_y = min(355, max(125, screen_y + obj["y"]))
                fill = obj["properties"].get("color", "#22c55e")
                size = int(obj["properties"].get("size", 18))
                canvas.create_oval(screen_x - size, screen_y - size, screen_x + size, screen_y + size, fill=fill, outline="#052e16", width=2)
                canvas.create_text(screen_x, screen_y + 28, text=name, fill="#dcfce7", font=("TkDefaultFont", 10, "bold"))

            canvas.create_oval(330, 305, 390, 365, fill="#f8fafc", outline="#0f172a", width=3)
            canvas.create_polygon(360, 282, 330, 330, 390, 330, fill="#facc15", outline="#0f172a", width=2)
            canvas.create_text(24, 20, anchor=tk.NW, text=app.title, font=("TkDefaultFont", 24, "bold"), fill="#f8fafc")
            canvas.create_text(
                24,
                54,
                anchor=tk.NW,
                text=f"Scene: 3D world  x={state['x']} z={state['z']}",
                font=("TkDefaultFont", 12),
                fill="#cbd5e1",
            )
            y = 82
            for text in app.texts[:5]:
                canvas.create_text(24, y, anchor=tk.NW, text=text, font=("TkDefaultFont", 12), fill="#e2e8f0")
                y += 22
            for file_info in (app.files or [])[:4]:
                screen_x, screen_y, scale = project(file_info.x, file_info.z)
                screen_y = min(350, max(115, screen_y + file_info.y))
                image = self._load_app_image(file_info.path, max_width=180, max_height=100)
                if image is not None:
                    canvas.create_image(screen_x, screen_y, image=image, anchor=tk.CENTER)
                    canvas.create_text(
                        screen_x,
                        screen_y + image.height() / 2 + 12,
                        anchor=tk.CENTER,
                        text=file_info.name,
                        font=("TkDefaultFont", 10, "bold"),
                        fill="#facc15",
                    )
                else:
                    card_width = 150
                    card_height = 66 if not file_info.preview else 108
                    canvas.create_rectangle(
                        screen_x - card_width / 2,
                        screen_y - card_height / 2,
                        screen_x + card_width / 2,
                        screen_y + card_height / 2,
                        fill="#f8fafc",
                        outline="#334155",
                        width=2,
                    )
                    canvas.create_text(
                        screen_x,
                        screen_y - 18,
                        anchor=tk.CENTER,
                        text=file_info.name,
                        font=("TkDefaultFont", 12, "bold"),
                        fill="#0f172a",
                    )
                    canvas.create_text(
                        screen_x,
                        screen_y + 2,
                        anchor=tk.CENTER,
                        text=f"{file_info.kind} | {file_info.size} bytes",
                        font=("TkDefaultFont", 10),
                        fill="#475569",
                    )
                    if file_info.preview:
                        canvas.create_text(
                            screen_x,
                            screen_y + 30,
                            anchor=tk.CENTER,
                            text=file_info.preview.splitlines()[0][:22],
                            font=("TkDefaultFont", 9),
                            fill="#64748b",
                        )
            status.configure(text=state["message"])

        def move(dx: int, dz: int) -> None:
            state["x"] += dx
            state["z"] += dz
            state["message"] = f"Moved to x={state['x']} z={state['z']}"
            draw_world()

        audio_players: list[subprocess.Popen] = []

        def run_creator_actions(actions: list[object]) -> None:
            for action in actions:
                if isinstance(action, MoveObject) and action.name in objects:
                    apply_move(action.name, action.direction, action.amount)
                    state["message"] = f"Moved {action.name} {action.direction} by {action.amount}"
                elif isinstance(action, AnimateObject):
                    animations.append(action)
                    state["message"] = f"Animating {action.name}"
                elif isinstance(action, ShowText):
                    state["message"] = action.text
                elif isinstance(action, PlaySound):
                    player = self._play_named_sound(window, action.name, app.sound_volume)
                    if player is not None:
                        audio_players.append(player)
                    state["message"] = f"Played sound: {action.name}"
                elif isinstance(action, StopSound):
                    for player in list(audio_players):
                        if player.poll() is None:
                            player.terminate()
                    audio_players.clear()
                    state["message"] = "Stopped sound"
                elif isinstance(action, SetSoundVolume):
                    app.sound_volume = action.volume
                    state["message"] = f"Sound volume: {action.volume}"
            check_collisions()
            draw_world()

        def apply_move(name: str, direction: str, amount: int) -> None:
            if name not in objects:
                return
            if direction == "forward":
                objects[name]["z"] += amount
            elif direction == "backward":
                objects[name]["z"] -= amount
            elif direction == "left":
                objects[name]["x"] -= amount
            elif direction == "right":
                objects[name]["x"] += amount
            elif direction == "up":
                objects[name]["y"] -= amount
            elif direction == "down":
                objects[name]["y"] += amount

        def check_collisions() -> None:
            if state["checking_collision"]:
                return
            state["checking_collision"] = True
            for key, actions in (app.events or {}).items():
                if not key.startswith("collision:"):
                    continue
                _prefix, pair = key.split(":", 1)
                left, right = pair.split(":", 1)
                if left in objects and right in objects and abs(objects[left]["x"] - objects[right]["x"]) <= 1 and abs(objects[left]["z"] - objects[right]["z"]) <= 1:
                    run_creator_actions(actions)
                    break
            state["checking_collision"] = False

        def timer_tick(milliseconds: int, actions: list[object]) -> None:
            if window.winfo_exists():
                run_creator_actions(actions)
                window.after(milliseconds, lambda: timer_tick(milliseconds, actions))

        def animation_tick() -> None:
            for animation in list(animations):
                apply_move(animation.name, animation.direction, animation.amount)
            if animations:
                check_collisions()
                draw_world()
            if window.winfo_exists():
                window.after(60, animation_tick)

        def key(event: tk.Event) -> None:
            keys = {
                "w": (0, 1),
                "Up": (0, 1),
                "s": (0, -1),
                "Down": (0, -1),
                "a": (-1, 0),
                "Left": (-1, 0),
                "d": (1, 0),
                "Right": (1, 0),
            }
            if event.keysym in keys:
                dx, dz = keys[event.keysym]
                move(dx, dz)
            event_actions = (app.events or {}).get(f"key:{event.keysym.lower()}")
            if event_actions:
                run_creator_actions(event_actions)

        def mouse_clicked(_event: tk.Event) -> None:
            event_actions = (app.events or {}).get("mouse:clicked", [])
            if event_actions:
                run_creator_actions(event_actions)

        x = 24
        for label in app.buttons[:6]:
            button_object_name = ""
            for obj in app.objects or []:
                if obj.kind == "button" and obj.text == label:
                    button_object_name = obj.name
                    break
            button = ttk.Button(
                window,
                text=label,
                command=lambda value=label, name=button_object_name: (
                    run_creator_actions((app.events or {}).get(f"button:{name.lower()}", []))
                    if name
                    else (state.update(message=f"Action: {value}"), draw_world())
                ),
            )
            button.place(x=x, y=380)
            x += 112

        window.bind("<Key>", key)
        canvas.bind("<Button-1>", lambda event: (canvas.focus_set(), mouse_clicked(event)))
        canvas.focus_set()
        draw_world()
        for key_name, actions in (app.events or {}).items():
            if key_name.startswith("timer:"):
                milliseconds = int(key_name.split(":", 1)[1])
                window.after(milliseconds, lambda ms=milliseconds, body=actions: timer_tick(ms, body))
        animation_tick()

    def _load_app_image(self, path: str, max_width: int, max_height: int) -> tk.PhotoImage | None:
        suffix = Path(path).suffix.lower()
        if suffix not in {".png", ".gif", ".jpg", ".jpeg", ".webp", ".bmp"}:
            return None
        if suffix in {".png", ".gif"}:
            try:
                image = tk.PhotoImage(file=path)
            except tk.TclError:
                return None
            while image.width() > max_width or image.height() > max_height:
                image = image.subsample(2, 2)
        else:
            if Image is None or ImageTk is None:
                return None
            try:
                pil_image = Image.open(path)
                pil_image.thumbnail((max_width, max_height))
                image = ImageTk.PhotoImage(pil_image)
            except Exception:
                return None
        self.image_refs.append(image)
        return image

    def _play_named_sound(self, window: tk.Misc, name: str, volume: int = 100) -> subprocess.Popen | None:
        path = Path(name).expanduser()
        if path.is_file() and path.suffix.lower() in {".mp3", ".wav", ".aiff", ".aif"}:
            player = _play_audio_path(str(path.resolve()), volume=max(0.0, min(1.0, volume / 100)))
            if player is not None:
                return player
        window.bell()
        return None

    def _file_card_text(self, file_info: object) -> str:
        return (
            f"File: {file_info.name} | type: {file_info.kind} | {file_info.size} bytes "
            f"| x {file_info.x} y {file_info.y} z {file_info.z}"
        )

    def open_angis_game(self, game: GameSpec) -> None:
        window = tk.Toplevel(self)
        window.title(game.name)
        window.geometry("520x640")
        self._set_app_icon(window)
        self.app_windows.append(window)

        canvas = tk.Canvas(window, width=480, height=600, bg="#8fd3ff", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        state = {
            "bird_y": 260.0,
            "velocity": 0.0,
            "pipes": [[520.0, 210.0], [820.0, 310.0]],
            "score": 0,
            "running": True,
        }
        width = 480
        height = 600
        bird_x = 120
        bird_radius = 16
        gap = 150
        pipe_width = 62

        def reset() -> None:
            state["bird_y"] = 260.0
            state["velocity"] = 0.0
            state["pipes"] = [[520.0, 210.0], [820.0, 310.0]]
            state["score"] = 0
            state["running"] = True

        def flap(_event: tk.Event | None = None) -> None:
            if not state["running"]:
                reset()
                return
            state["velocity"] = -8.5

        def draw() -> None:
            canvas.delete("all")
            canvas.create_rectangle(0, height - 70, width, height, fill="#63b35d", outline="")
            canvas.create_text(14, 14, anchor=tk.NW, text=f"{_lang_ui('score')}: {state['score']}", font=("TkDefaultFont", 18, "bold"))
            canvas.create_text(14, 42, anchor=tk.NW, text=_lang_ui("click_or_space"), font=("TkDefaultFont", 11))

            bird_y = state["bird_y"]
            canvas.create_oval(
                bird_x - bird_radius,
                bird_y - bird_radius,
                bird_x + bird_radius,
                bird_y + bird_radius,
                fill="#ffd84d",
                outline="#9a6b00",
                width=2,
            )
            canvas.create_polygon(bird_x + 10, bird_y - 2, bird_x + 26, bird_y + 5, bird_x + 10, bird_y + 12, fill="#ff8c32", outline="")
            canvas.create_oval(bird_x + 4, bird_y - 8, bird_x + 10, bird_y - 2, fill="#1f2933", outline="")

            for pipe_x, pipe_gap_y in state["pipes"]:
                canvas.create_rectangle(pipe_x, 0, pipe_x + pipe_width, pipe_gap_y - gap / 2, fill="#2fb344", outline="#16702a", width=2)
                canvas.create_rectangle(pipe_x, pipe_gap_y + gap / 2, pipe_x + pipe_width, height - 70, fill="#2fb344", outline="#16702a", width=2)

            if not state["running"]:
                canvas.create_rectangle(65, 230, 415, 345, fill="#ffffff", outline="#1f2933", width=2)
                canvas.create_text(240, 265, text=_lang_ui("game_over"), font=("TkDefaultFont", 28, "bold"), fill="#1f2933")
                canvas.create_text(240, 305, text=_lang_ui("click_restart"), font=("TkDefaultFont", 14), fill="#1f2933")

        def hit_pipe(pipe_x: float, pipe_gap_y: float) -> bool:
            bird_left = bird_x - bird_radius
            bird_right = bird_x + bird_radius
            if bird_right < pipe_x or bird_left > pipe_x + pipe_width:
                return False
            bird_top = state["bird_y"] - bird_radius
            bird_bottom = state["bird_y"] + bird_radius
            return bird_top < pipe_gap_y - gap / 2 or bird_bottom > pipe_gap_y + gap / 2

        def tick() -> None:
            if state["running"]:
                state["velocity"] += 0.45
                state["bird_y"] += state["velocity"]

                for pipe in state["pipes"]:
                    pipe[0] -= 3.0
                    if pipe[0] + pipe_width < 0:
                        pipe[0] = max(other[0] for other in state["pipes"]) + 300
                        pipe[1] = 170 + ((state["score"] * 73) % 220)
                        state["score"] += 1

                hit_ground = state["bird_y"] + bird_radius > height - 70
                hit_sky = state["bird_y"] - bird_radius < 0
                hit_obstacle = any(hit_pipe(pipe_x, pipe_gap_y) for pipe_x, pipe_gap_y in state["pipes"])
                if hit_ground or hit_sky or hit_obstacle:
                    state["running"] = False

            draw()
            if window.winfo_exists():
                window.after(24, tick)

        window.bind("<space>", flap)
        canvas.bind("<Button-1>", flap)
        canvas.focus_set()
        tick()

    def _build_editor_menu(self) -> None:
        self.editor_menu = tk.Menu(self, tearoff=False)
        self.editor_menu.add_command(label=_lang_ui("cut"), command=lambda: self._editor_event("<<Cut>>"))
        self.editor_menu.add_command(label=_lang_ui("copy"), command=lambda: self._editor_event("<<Copy>>"))
        self.editor_menu.add_command(label=_lang_ui("paste"), command=lambda: self._editor_event("<<Paste>>"))
        self.editor_menu.add_separator()
        self.editor_menu.add_command(label=_lang_ui("select_all"), command=self._select_all)
        self.editor.bind("<Button-2>", self._show_editor_menu)
        self.editor.bind("<Button-3>", self._show_editor_menu)
        self.editor.bind("<Control-a>", lambda _event: self._select_all())
        self.editor.bind("<Command-a>", lambda _event: self._select_all())

    def _on_gutter_wheel_for(self, event: tk.Event, ed: tk.Text, ln: tk.Canvas) -> str:
        ed.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._update_line_numbers_for(ed, ln)
        return "break"

    def _update_line_numbers_for(self, ed: tk.Text, ln: tk.Canvas) -> None:
        ln.delete("all")
        ed.update_idletasks()
        line_count = int(ed.index("end-1c").split(".")[0])
        font = tkfont.Font(font=ed["font"])
        ascent = font.metrics("ascent")
        pad = 6
        width = len(str(line_count)) * font.measure("8") + 20
        ln.config(width=width)
        for i in range(1, line_count + 1):
            dline = ed.dlineinfo(f"{i}.0")
            if dline is not None:
                y = dline[1]
                ln.create_text(
                    ln.winfo_width() - pad, y + ascent // 2,
                    text=str(i), anchor="e",
                    fill="#888888", font=font,
                )

    def _editor_event(self, event_name: str) -> None:
        self.editor.focus_set()
        self.editor.event_generate(event_name)

    def _select_all(self) -> str:
        self.editor.focus_set()
        self.editor.tag_add(tk.SEL, "1.0", tk.END)
        self.editor.mark_set(tk.INSERT, "1.0")
        self.editor.see(tk.INSERT)
        return "break"

    def _show_editor_menu(self, event: tk.Event) -> str:
        self.editor.focus_set()
        self.editor_menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _build_readonly_menus(self) -> None:
        self.readonly_menu = tk.Menu(self, tearoff=False)
        self.readonly_menu.add_command(label=_lang_ui("copy"), command=self._copy_focused_text)
        self.readonly_menu.add_command(label=_lang_ui("select_all"), command=self._select_all_focused_text)
        for widget in (self.output, self.errors):
            widget.bind("<Button-2>", self._show_readonly_menu)
            widget.bind("<Button-3>", self._show_readonly_menu)
            widget.bind("<Control-a>", lambda _event: self._select_all_focused_text())
            widget.bind("<Command-a>", lambda _event: self._select_all_focused_text())
            widget.bind("<<Cut>>", self._block_readonly_edit)
            widget.bind("<<Paste>>", self._block_readonly_edit)
            widget.bind("<Key>", self._block_readonly_key)

    def _show_readonly_menu(self, event: tk.Event) -> str:
        event.widget.focus_set()
        self.readonly_menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _copy_focused_text(self) -> str:
        widget = self.focus_get()
        if isinstance(widget, tk.Text):
            widget.event_generate("<<Copy>>")
        return "break"

    def _select_all_focused_text(self) -> str:
        widget = self.focus_get()
        if isinstance(widget, tk.Text):
            widget.tag_add(tk.SEL, "1.0", tk.END)
            widget.mark_set(tk.INSERT, "1.0")
            widget.see(tk.INSERT)
        return "break"

    def _block_readonly_edit(self, _event: tk.Event) -> str:
        return "break"

    def _block_readonly_key(self, event: tk.Event) -> str | None:
        allowed_shortcuts = {"a", "c"}
        if event.state & 0x4 and event.keysym.lower() in allowed_shortcuts:
            return None
        if event.state & 0x8 and event.keysym.lower() in allowed_shortcuts:
            return None
        navigation_keys = {
            "Left",
            "Right",
            "Up",
            "Down",
            "Home",
            "End",
            "Prior",
            "Next",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Command",
            "Meta_L",
            "Meta_R",
        }
        if event.keysym in navigation_keys:
            return None
        return "break"

    def _write_current(self, path: Path) -> None:
        path.write_text(self.editor.get("1.0", tk.END).rstrip() + "\n", encoding="utf-8")
        messagebox.showinfo("Angis IDE", f"Saved {path.name}")

    def _validate_path(self, path: Path, must_exist: bool) -> Path:
        resolved = path.expanduser().resolve()
        if must_exist and not resolved.is_file():
            raise AngisError(f"File does not exist: {resolved}")
        return resolved

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state=tk.DISABLED)


def _show_startup_splash(master: tk.Tk) -> None:
    if not STARTUP_IMAGE.is_file() and not STARTUP_AUDIO.is_file():
        return

    splash = tk.Toplevel(master)
    splash.title("Angis")
    _set_window_icon(splash, LOGO_PATH)
    splash.update_idletasks()
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    splash.geometry(f"{screen_w}x{screen_h}+0+0")
    splash.configure(bg="#0f172a")
    splash.resizable(False, False)
    splash.transient(master)
    splash.grab_set()
    splash.attributes("-fullscreen", True)

    canvas = tk.Canvas(splash, width=screen_w, height=screen_h, highlightthickness=0, bg="#0f172a")
    canvas.place(x=0, y=0)

    player = _play_audio_path(str(STARTUP_AUDIO)) if STARTUP_AUDIO.is_file() else None
    duration_ms = _audio_duration_ms(str(STARTUP_AUDIO)) if STARTUP_AUDIO.is_file() else 2500
    duration_ms = max(1000, min(duration_ms, 30000))

    image = _load_standalone_image(splash, STARTUP_IMAGE, max_width=screen_w, max_height=screen_h) if STARTUP_IMAGE.is_file() else None
    if image is not None:
        canvas.image = image
        iw, ih = image.width(), image.height()
        ix = (screen_w - iw) // 2
        iy = (screen_h - ih) // 2
        canvas.create_image(ix, iy, anchor=tk.NW, image=image)

        bpx = ix + int(iw * 0.15)
        bpw = int(iw * 0.70)
        bar_bottom = iy + int(ih * 0.86) + max(6, int(ih * 0.045))
        bph = max(10, int(ih * 0.065))
        bpy = bar_bottom - bph
        canvas.create_rectangle(bpx, bpy, bpx + bpw, bpy + bph, fill="#1e293b", outline="", tags="bar_track")
        bf = canvas.create_rectangle(bpx, bpy, bpx, bpy + bph, fill="#a855f7", outline="", tags="bar_fill")

    if image is None:
        canvas.create_text(screen_w // 2, screen_h // 2, text="Angis", font=("TkDefaultFont", 32, "bold"), fill="#f8fafc")
        splash.after(duration_ms, lambda: splash.destroy() if splash.winfo_exists() else None)
        splash.wait_window()
        return

    state = {"pct": 0, "done": False}

    def close() -> None:
        if state["done"]:
            return
        state["done"] = True
        canvas.coords(bf, bpx, bpy, bpx + bpw, bpy + bph)
        if player is not None and player.poll() is None:
            player.terminate()
        if splash.winfo_exists():
            splash.destroy()

    def tick() -> None:
        if state["done"] or not splash.winfo_exists():
            return
        state["pct"] = min(state["pct"] + 2, 100)
        fw = int(bpw * state["pct"] / 100)
        canvas.coords(bf, bpx, bpy, bpx + fw, bpy + bph)
        if state["pct"] < 100:
            splash.after(max(1, duration_ms // 50), tick)
        else:
            close()

    tick()
    splash.after(duration_ms, close)
    master.wait_window(splash)


_ICON_CACHE: list[tk.PhotoImage] = []


def _set_window_icon(window: tk.Misc, icon_path: Path) -> None:
    if not icon_path.is_file():
        return
    if _ICON_CACHE:
        try:
            window.iconphoto(True, _ICON_CACHE[0])
        except Exception:
            pass
        return
    suffix = icon_path.suffix.lower()
    if suffix in {".png", ".gif"}:
        try:
            icon = tk.PhotoImage(file=str(icon_path))
            if icon.width() > 64 or icon.height() > 64:
                icon = icon.subsample(max(1, icon.width() // 48), max(1, icon.height() // 48))
            _ICON_CACHE.append(icon)
            window.iconphoto(True, icon)
        except tk.TclError:
            pass
    elif suffix in {".jpg", ".jpeg", ".webp", ".bmp"} and Image is not None and ImageTk is not None:
        try:
            pil_image = Image.open(icon_path)
            pil_image.thumbnail((64, 64))
            icon = ImageTk.PhotoImage(pil_image)
            _ICON_CACHE.append(icon)
            window.iconphoto(True, icon)
        except Exception:
            pass


def _startup_splash_size(path: Path) -> tuple[int, int]:
    if not path.is_file() or Image is None:
        return STARTUP_MAX_SIZE, STARTUP_MAX_SIZE
    try:
        with Image.open(path) as image:
            width, height = image.size
    except Exception:
        return STARTUP_MAX_SIZE, STARTUP_MAX_SIZE
    scale = min(STARTUP_MAX_SIZE / width, STARTUP_MAX_SIZE / height, 1.0)
    return max(1, int(width * scale)), max(1, int(height * scale))


def _load_standalone_image(root: tk.Misc, path: Path, max_width: int, max_height: int, cover: bool = False) -> tk.PhotoImage | None:
    suffix = path.suffix.lower()
    if suffix not in {".png", ".gif", ".jpg", ".jpeg", ".webp", ".bmp"}:
        return None
    if Image is not None and ImageTk is not None:
        try:
            pil_image = Image.open(path)
            iw, ih = pil_image.size
            scale = min(max_width / iw, max_height / ih)
            dw = max(1, int(iw * scale))
            dh = max(1, int(ih * scale))
            pil_image = pil_image.resize((dw, dh), Image.LANCZOS)
            return ImageTk.PhotoImage(pil_image, master=root)
        except Exception:
            return None
    if suffix in {".png", ".gif"}:
        try:
            image = tk.PhotoImage(master=root, file=str(path))
        except tk.TclError:
            return None
        while image.width() > max_width or image.height() > max_height:
            image = image.subsample(2, 2)
        return image
    if Image is None or ImageTk is None:
        return None
    try:
        pil_image = Image.open(path)
        pil_image.thumbnail((max_width, max_height))
        return ImageTk.PhotoImage(pil_image, master=root)
    except Exception:
        return None


def _resize_cover(image: object, width: int, height: int) -> object:
    source_width, source_height = image.size
    scale = max(width / source_width, height / source_height)
    resized_width = max(width, int(source_width * scale))
    resized_height = max(height, int(source_height * scale))
    resized = image.resize((resized_width, resized_height), Image.LANCZOS)
    left = (resized_width - width) // 2
    top = (resized_height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _play_audio_path(path: str, volume: float = 1.0) -> subprocess.Popen | None:
    if sys.platform != "darwin":
        return None
    if not Path(path).is_file():
        return None
    try:
        return subprocess.Popen(
            ["/usr/bin/afplay", "-v", f"{max(0.0, min(1.0, volume)):.2f}", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except OSError:
        return None


def _module_available(name: str) -> bool:
    try:
        __import__(name)
    except Exception:
        return False
    return True


def _audio_duration_ms(path: str) -> int:
    suffix = Path(path).suffix.lower()
    try:
        if suffix == ".wav":
            with wave.open(path, "rb") as audio:
                return int(audio.getnframes() / audio.getframerate() * 1000)
        if suffix == ".mp3":
            return _mp3_duration_ms(path)
    except (OSError, EOFError, wave.Error, ZeroDivisionError):
        return 3000
    return 3000


def _mp3_duration_ms(path: str) -> int:
    bitrates = {
        1: {
            1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
            2: [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384],
            3: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
        },
        2: {
            1: [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256],
            2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
            3: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
        },
    }
    sample_rates = {1: [44100, 48000, 32000], 2: [22050, 24000, 16000], 25: [11025, 12000, 8000]}
    samples_per_frame = {
        (1, 1): 384,
        (1, 2): 1152,
        (1, 3): 1152,
        (2, 1): 384,
        (2, 2): 1152,
        (2, 3): 576,
        (25, 1): 384,
        (25, 2): 1152,
        (25, 3): 576,
    }

    data = Path(path).read_bytes()
    index = 0
    if data[:3] == b"ID3" and len(data) >= 10:
        size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        index = 10 + size

    total_seconds = 0.0
    while index + 4 <= len(data):
        header = struct.unpack(">I", data[index : index + 4])[0]
        if (header & 0xFFE00000) != 0xFFE00000:
            index += 1
            continue
        version_bits = (header >> 19) & 0x3
        layer_bits = (header >> 17) & 0x3
        bitrate_index = (header >> 12) & 0xF
        sample_rate_index = (header >> 10) & 0x3
        padding = (header >> 9) & 0x1
        version = {3: 1, 2: 2, 0: 25}.get(version_bits)
        layer = {3: 1, 2: 2, 1: 3}.get(layer_bits)
        if not version or not layer or bitrate_index in {0, 15} or sample_rate_index == 3:
            index += 1
            continue
        bitrate = bitrates[1 if version == 1 else 2][layer][bitrate_index] * 1000
        sample_rate = sample_rates[version][sample_rate_index]
        samples = samples_per_frame[(version, layer)]
        total_seconds += samples / sample_rate
        if layer == 1:
            frame_size = int((12 * bitrate / sample_rate + padding) * 4)
        else:
            frame_size = int(144 * bitrate / sample_rate + padding) if version == 1 else int(72 * bitrate / sample_rate + padding)
        index += max(frame_size, 1)

    if total_seconds <= 0:
        size = os.path.getsize(path)
        total_seconds = max(1.0, size / 16000)
    return int(total_seconds * 1000)


def main(file_to_open: str | Path | None = None) -> None:
    root = AngisIDE()
    if file_to_open is not None:
        file_path = Path(file_to_open).expanduser().resolve()
        content = file_path.read_text(encoding="utf-8")
        root._add_tab(file_path, content)
        root.title(f"{_lang_ui('window_title')} - {file_path.name}")
    _show_startup_splash(root)
    root.mainloop()


if __name__ == "__main__":
    main()
