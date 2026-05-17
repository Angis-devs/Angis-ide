"""Tkinter visual runner for Angis apps — renders objects, handles events, collision, animation."""

from __future__ import annotations

import math
import random
import subprocess
import time
import tkinter as tk
from pathlib import Path
from typing import Any, Callable

from .errors import AngisRuntimeError
from .ir import AnimateObject, AppSpec, CreatorObject, MoveObject, PlaySound, RotateObject, SetCamera, SetProperty, SetSoundVolume, ShowText, StopSound


def run_tk_app(app: AppSpec, instruction_runner: Callable[[list[object]], None], parent: tk.Tk | tk.Toplevel | None = None, interpreter: object | None = None) -> None:
    if parent is not None:
        root = parent
        for w in root.winfo_children():
            w.destroy()
    else:
        root = tk.Tk()
    root.title(app.title)
    root.geometry(f"{app.width}x{app.height}")
    root.resizable(False, False)
    canvas = tk.Canvas(root, width=app.width, height=app.height, bg=app.bg, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    objects: dict[str, dict[str, Any]] = {}
    canvas_ids: dict[str, list[int]] = {}
    canvas_images: dict[str, tk.PhotoImage] = {}
    pressed_keys: set[str] = set()
    notification_text: str = ""
    notification_timer: str | None = None

    for obj in app.objects or []:
        props = dict(obj.properties or {})
        ob = {
            "kind": obj.kind,
            "name": obj.name,
            "x": obj.x,
            "y": obj.y,
            "z": obj.z,
            "text": obj.text or "",
            "path": obj.path or "",
            "props": props,
        }
        objects[obj.name] = ob
        canvas_ids[obj.name] = []

    def _color(value: object) -> str:
        if not isinstance(value, str):
            return "#2563eb"
        v = value.strip().lower()
        named = {
            "red": "#dc2626", "green": "#16a34a", "blue": "#2563eb",
            "yellow": "#eab308", "purple": "#9333ea", "orange": "#ea580c",
            "pink": "#ec4899", "brown": "#92400e", "gray": "#6b7280",
            "grey": "#6b7280", "black": "#111827", "white": "#ffffff",
            "cyan": "#06b6d4", "lime": "#65a30d", "teal": "#0d9488",
            "indigo": "#4f46e5", "violet": "#8b5cf6", "fuchsia": "#d946ef",
            "rose": "#f43f5e", "amber": "#d97706", "emerald": "#059669",
            "sky": "#0284c7", "slate": "#475569", "zinc": "#52525b",
            "neutral": "#525252", "stone": "#57534e",
            "darkgreen": "#166534", "darkred": "#991b1b",
            "lightgray": "#d1d5db", "lightgrey": "#d1d5db",
            "gold": "#ca8a04", "silver": "#9ca3af",
        }
        if v in named:
            return named[v]
        if v.startswith("#") and len(v) in {4, 7}:
            return v
        return "#2563eb"

    def _font(size: int = 14, bold: bool = False, family: str = "Segoe UI") -> tuple[str, int, str]:
        weight = "bold" if bold else "normal"
        return (family, size, weight)

    def _arrange_by_layout() -> None:
        layout = app.layout or {"kind": "free"}
        kind = layout.get("kind", "free")
        if kind == "free":
            return
        objs = sorted(objects.values(), key=lambda o: o["z"])
        if not objs:
            return
        if kind == "grid":
            cols = max(1, int(layout.get("columns", 3)))
            padding = 12
            cell_w = (app.width - padding * (cols + 1)) // cols
            cell_h = 80
            for i, ob in enumerate(objs):
                col = i % cols
                row = i // cols
                ob["x"] = padding + col * (cell_w + padding)
                ob["y"] = padding + row * (cell_h + padding)
                props = ob["props"]
                if "width" not in props and "size" not in props:
                    props["width"] = cell_w
                if "height" not in props and "size" not in props:
                    props["height"] = cell_h
        elif kind == "horizontal":
            padding = 12
            gap = 8
            x = padding
            for ob in objs:
                ob["x"] = x
                props = ob["props"]
                w = int(props.get("width", props.get("size", 80)))
                h = int(props.get("height", props.get("size", 48)))
                ob["y"] = (app.height - h) // 2
                x += w + gap

    def _render() -> None:
        for name in list(canvas_ids):
            for cid in canvas_ids[name]:
                canvas.delete(cid)
            canvas_ids[name] = []

        _arrange_by_layout()
        sorted_objs = sorted(objects.values(), key=lambda o: o["z"])
        for ob in sorted_objs:
            name = ob["name"]
            kind = ob["kind"]
            x, y = ob["x"], ob["y"]
            props = ob["props"]
            color = _color(props.get("color", "#2563eb"))
            w = int(props.get("width", props.get("size", 48))) if isinstance(props.get("width", props.get("size", 48)), (int, float)) else 48
            h = int(props.get("height", props.get("size", 48))) if isinstance(props.get("height", props.get("size", 48)), (int, float)) else 48
            ids: list[int] = []

            if kind in {"image", "sprite"}:
                path = ob.get("path") or ob["props"].get("path", "")
                if path:
                    p = Path(path).expanduser()
                    if p.is_file():
                        try:
                            img = tk.PhotoImage(file=str(p))
                            img_w, img_h = img.width(), img.height()
                            scale = min(w / img_w, h / img_h, 1.0) if img_w and img_h else 1.0
                            if scale < 1:
                                img = img.subsample(int(1 / scale), int(1 / scale))
                            cid = canvas.create_image(x, y, anchor="nw", image=img)
                            canvas_images[name] = img
                            ids.append(cid)
                        except Exception:
                            cid = canvas.create_rectangle(x, y, x + w, y + h, fill="#e5e7eb", outline="#9ca3af")
                            ids.append(cid)
                            cid = canvas.create_text(x + w // 2, y + h // 2, text="?", font=_font(16), fill="#6b7280")
                            ids.append(cid)
                else:
                    cid = canvas.create_rectangle(x, y, x + w, y + h, fill="#e5e7eb", outline="#9ca3af")
                    ids.append(cid)

            elif kind in {"circle", "ball", "player", "enemy", "sphere"}:
                cid = canvas.create_oval(x, y, x + w, y + h, fill=color, outline="")
                ids.append(cid)
                border = props.get("border", "")
                if border:
                    bw = int(props.get("border_width", 2))
                    cid = canvas.create_oval(x, y, x + w, y + h, outline=_color(border), width=bw)
                    ids.append(cid)
                if kind in {"player", "enemy"} and props.get("show_health", False):
                    hp = int(props.get("health", 100))
                    max_hp = int(props.get("max_health", 100))
                    bar_w = w
                    bar_h = 4
                    ratio = max(0, hp / max_hp) if max_hp else 0
                    cid = canvas.create_rectangle(x, y - 8, x + bar_w, y - 8 + bar_h, fill="#374151", outline="")
                    ids.append(cid)
                    cid = canvas.create_rectangle(x, y - 8, x + bar_w * ratio, y - 8 + bar_h, fill=_color(props.get("health_color", "green")), outline="")
                    ids.append(cid)

            elif kind in {"text", "label"}:
                text = ob.get("text", props.get("text", name))
                size = int(props.get("font_size", 14))
                bold = props.get("bold", False) in {True, "true", "yes", "True"}
                ff = str(props.get("font_family", "Segoe UI"))
                cid = canvas.create_text(x, y, anchor="nw", text=text, font=_font(size, bold, ff), fill=color, justify="left")
                ids.append(cid)

            elif kind in {"button", "btn"}:
                text = ob.get("text", props.get("text", name))
                bg = _color(props.get("background", "#3b82f6"))
                fg = _color(props.get("color", "#ffffff"))
                r = int(props.get("radius", 6))
                cid = canvas.create_rectangle(x, y, x + w, y + h, fill=bg, outline="", width=0)
                ids.append(cid)
                if r > 0:
                    cid = canvas.create_rectangle(x + r, y, x + w - r, y + h, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_rectangle(x, y + r, x + w, y + h - r, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x, y, x + r * 2, y + r * 2, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x + w - r * 2, y, x + w, y + r * 2, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x, y + h - r * 2, x + r * 2, y + h, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x + w - r * 2, y + h - r * 2, x + w, y + h, fill=bg, outline="", width=0)
                    ids.append(cid)
                border = props.get("border", "")
                if border:
                    bw = int(props.get("border_width", 1))
                    cid = canvas.create_rectangle(x, y, x + w, y + h, outline=_color(border), width=bw)
                    ids.append(cid)
                cid = canvas.create_text(x + w // 2, y + h // 2, text=text, font=_font(13, True), fill=fg)
                ids.append(cid)

            elif kind in {"input", "textbox"}:
                text = ob.get("text", "")
                cid = canvas.create_rectangle(x, y, x + w, y + h, fill="white", outline="#9ca3af", width=1)
                ids.append(cid)
                cid = canvas.create_text(x + 6, y + h // 2, anchor="w", text=text, font=_font(12), fill="#111827")
                ids.append(cid)

            elif kind in {"panel", "box"}:
                bg = _color(props.get("background", props.get("color", "#f1f5f9")))
                border = _color(props.get("border", "#cbd5e1"))
                bw = int(props.get("border_width", 1))
                r = int(props.get("border_radius", 0))
                if r > 0:
                    cid = canvas.create_rectangle(x + r, y, x + w - r, y + h, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_rectangle(x, y + r, x + w, y + h - r, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x, y, x + r * 2, y + r * 2, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x + w - r * 2, y, x + w, y + r * 2, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x, y + h - r * 2, x + r * 2, y + h, fill=bg, outline="", width=0)
                    ids.append(cid)
                    cid = canvas.create_oval(x + w - r * 2, y + h - r * 2, x + w, y + h, fill=bg, outline="", width=0)
                    ids.append(cid)
                    if border and bw:
                        cid = canvas.create_rectangle(x, y, x + w, y + h, outline=border, width=bw)
                        ids.append(cid)
                else:
                    cid = canvas.create_rectangle(x, y, x + w, y + h, fill=bg, outline=border, width=bw)
                    ids.append(cid)

            else:
                border_color = _color(props.get("border", props.get("color", "#94a3b8")))
                bw = int(props.get("border_width", 1))
                cid = canvas.create_rectangle(x, y, x + w, y + h, fill=color, outline=border_color, width=bw)
                ids.append(cid)

            canvas_ids[name] = ids

        if notification_text:
            nw = 400
            nh = 40
            nx = app.width // 2 - nw // 2
            ny = 20
            cid = canvas.create_rectangle(nx, ny, nx + nw, ny + nh, fill="#1e293b", outline="", width=0)
            canvas_ids["__notification__bg__"] = [cid]
            cid = canvas.create_text(nx + nw // 2, ny + nh // 2, text=notification_text, font=_font(14, True), fill="white")
            canvas_ids["__notification__text__"] = [cid]

        if app.files:
            fw, fh = 200, app.height
            fx, fy = app.width - fw, 0
            cid = canvas.create_rectangle(fx, fy, fx + fw, fy + fh, fill="#f1f5f9", outline="#cbd5e1", width=1)
            canvas_ids["__files__bg__"] = [cid]
            cid = canvas.create_text(fx + 10, fy + 8, anchor="nw", text="Files", font=_font(14, True), fill="#475569")
            canvas_ids["__files__header__"] = [cid]
            y_off = fy + 36
            for fi in app.files:
                label = f"{fi.name} ({fi.kind})"
                cid = canvas.create_text(fx + 10, y_off, anchor="nw", text=label, font=_font(11), fill="#334155")
                canvas_ids.setdefault("__files__items__", []).append(cid)
                y_off += 22

    def _set_notification(text: str) -> None:
        nonlocal notification_text, notification_timer
        notification_text = text
        if notification_timer:
            root.after_cancel(notification_timer)
        notification_timer = root.after(3000, _clear_notification)
        _render()

    def _clear_notification() -> None:
        nonlocal notification_text, notification_timer
        notification_text = ""
        notification_timer = None
        _render()

    def _handle_event(name: str) -> None:
        if app.events and name in app.events:
            try:
                instruction_runner(app.events[name])
            except AngisRuntimeError as exc:
                _set_notification(str(exc))
            _render()

    def _move_object(name: str, direction: str, amount: int) -> None:
        ob = objects.get(name)
        if not ob:
            return
        dx, dy = 0, 0
        if direction in {"up", "forward"}:
            dy = -amount
        elif direction in {"down", "backward"}:
            dy = amount
        elif direction == "left":
            dx = -amount
        elif direction == "right":
            dx = amount
        ob["x"] = max(0, min(app.width - 10, ob["x"] + dx))
        ob["y"] = max(0, min(app.height - 10, ob["y"] + dy))

    def _set_prop(name: str, prop: str, value: object) -> None:
        ob = objects.get(name)
        if not ob:
            return
        if prop in {"x", "y", "z"}:
            ob[prop] = int(value) if isinstance(value, (int, float)) else value
        elif prop in {"text"}:
            ob["text"] = str(value)
        elif prop in {"path"}:
            ob["path"] = str(value)
        else:
            ob["props"][prop] = value

    def _check_collision(a: CreatorObject, b: CreatorObject) -> bool:
        ob_a = objects.get(a.name)
        ob_b = objects.get(b.name)
        if not ob_a or not ob_b:
            return False
        props_a = ob_a["props"]
        props_b = ob_b["props"]
        ax, ay = ob_a["x"], ob_a["y"]
        aw = int(props_a.get("width", props_a.get("size", 48)))
        ah = int(props_a.get("height", props_a.get("size", 48)))
        bx, by = ob_b["x"], ob_b["y"]
        bw = int(props_b.get("width", props_b.get("size", 48)))
        bh = int(props_b.get("height", props_b.get("size", 48)))
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _execute_move(move: object) -> None:
        if isinstance(move, MoveObject):
            _move_object(move.name, move.direction, move.amount)

    def _execute_setprop(sp: object) -> None:
        if isinstance(sp, SetProperty):
            _set_prop(sp.object_name, sp.property_name, sp.value)

    def _execute_showtext(st: object) -> None:
        if isinstance(st, ShowText):
            _set_notification(st.text)

    def _execute_animate(ao: AnimateObject) -> None:
        ob = objects.get(ao.name)
        if not ob:
            return
        dx, dy = 0, 0
        if ao.direction in {"up", "forward"}:
            dy = -ao.amount
        elif ao.direction in {"down", "backward"}:
            dy = ao.amount
        elif ao.direction == "left":
            dx = -ao.amount
        elif ao.direction == "right":
            dx = ao.amount
        steps = max(1, ao.milliseconds // 16)
        step_dx = dx / steps
        step_dy = dy / steps

        def _step(count: int = steps) -> None:
            if count <= 0:
                return
            ob["x"] += step_dx
            ob["y"] += step_dy
            _render()
            root.after(16, lambda c=count - 1: _step(c))

        _step()

    _bg_sound_process: subprocess.Popen | None = None
    _sound_volume: int = getattr(app, "sound_volume", 100)

    def _play_sound(name: str) -> None:
        nonlocal _bg_sound_process
        _stop_sound()
        p = Path(name).expanduser()
        if not p.is_file():
            path = Path(name)
            if not path.is_file():
                return
            p = path
        try:
            _bg_sound_process = subprocess.Popen(
                ["afplay", str(p)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass

    def _stop_sound() -> None:
        nonlocal _bg_sound_process
        if _bg_sound_process is not None:
            try:
                _bg_sound_process.terminate()
                _bg_sound_process.wait(timeout=2)
            except Exception:
                pass
            _bg_sound_process = None

    def _sync_object_props() -> None:
        for obj in app.objects or []:
            ob = objects.get(obj.name)
            if ob:
                for key, val in (obj.properties or {}).items():
                    ob["props"][key] = val

    def _drain_notifications_2d() -> None:
        if interpreter is not None:
            pending = getattr(interpreter, "_pending_notifications", None)
            if pending:
                for t in pending:
                    _set_notification(t)
                pending.clear()

    def _run_event_instructions(instructions: list[object]) -> None:
        for instr in instructions:
            if isinstance(instr, ShowText) and interpreter is not None:
                instruction_runner([instr])
                _drain_notifications_2d()
            elif isinstance(instr, MoveObject):
                _execute_move(instr)
            elif isinstance(instr, AnimateObject):
                _execute_animate(instr)
            elif isinstance(instr, ShowText):
                _execute_showtext(instr)
            elif isinstance(instr, PlaySound):
                _play_sound(instr.name)
            elif isinstance(instr, StopSound):
                _stop_sound()
            elif isinstance(instr, SetSoundVolume):
                _sound_volume = instr.volume
            else:
                try:
                    instruction_runner([instr])
                    _drain_notifications_2d()
                except AngisRuntimeError as exc:
                    _set_notification(str(exc))
        _sync_object_props()

    def _on_key(event: tk.Event) -> None:
        key = event.keysym.lower()
        pressed_keys.add(key)
        _handle_event(f"key:{key}")
        _render()

    def _on_key_release(event: tk.Event) -> None:
        key = event.keysym.lower()
        pressed_keys.discard(key)
        _handle_event(f"key_release:{key}")

    def _on_mouse_click(event: tk.Event) -> None:
        mx, my = event.x, event.y
        for ob in objects.values():
            if ob["kind"] in {"button", "btn"}:
                props = ob["props"]
                x, y = ob["x"], ob["y"]
                w = int(props.get("width", 80))
                h = int(props.get("height", 36))
                if x <= mx <= x + w and y <= my <= y + h:
                    _handle_event(f"button:{ob['name']}")
                    return

    _timer_scheduled: dict[str, str] = {}

    def _run_timer_events() -> None:
        if not app.events:
            return
        for event_key in list(app.events.keys()):
            if event_key.startswith("collision:"):
                parts = event_key.split(":")
                if len(parts) == 3:
                    _, left_name, right_name = parts
                    left_obj = None
                    right_obj = None
                    for ob in objects.values():
                        if ob["name"] == left_name:
                            left_obj = CreatorObject(
                                kind=ob["kind"], name=ob["name"],
                                x=ob["x"], y=ob["y"], z=ob["z"],
                                properties=dict(ob["props"]),
                            )
                    for ob in objects.values():
                        if ob["name"] == right_name:
                            right_obj = CreatorObject(
                                kind=ob["kind"], name=ob["name"],
                                x=ob["x"], y=ob["y"], z=ob["z"],
                                properties=dict(ob["props"]),
                            )
                    if left_obj and right_obj and _check_collision(left_obj, right_obj):
                        _run_event_instructions(app.events[event_key])

    def _schedule_timers() -> None:
        if not app.events:
            return
        for event_key in list(app.events.keys()):
            if not event_key.startswith("timer:"):
                continue
            ms_str = event_key.split(":", 1)[1]
            try:
                ms = int(ms_str)
            except ValueError:
                continue
            if event_key in _timer_scheduled:
                continue
            def _fire(key: str = event_key, interval: int = ms) -> None:
                _run_event_instructions(app.events[key])
                _render()
                root.after(interval, lambda k=key, i=interval: _fire(k, i))
            _timer_scheduled[event_key] = root.after(ms, lambda k=event_key, i=ms: _fire(k, i))

    def _collision_loop() -> None:
        _run_timer_events()
        _render()
        if any(k.startswith("collision:") for k in (app.events or [])):
            root.after(50, _collision_loop)

    canvas.focus_set()
    root.bind("<KeyPress>", _on_key)
    root.bind("<KeyRelease>", _on_key_release)
    canvas.bind("<Button-1>", _on_mouse_click)

    _render()
    if app.loading_audio:
        _play_sound(app.loading_audio)
    _schedule_timers()
    if any(k.startswith("collision:") for k in (app.events or [])):
        root.after(50, _collision_loop)
    if parent is None:
        root.mainloop()


# ── 3D Wireframe Renderer ──────────────────────────────────────────────

_SHAPES: dict[str, tuple[list[tuple[float, float, float]], list[tuple[int, int]]]] = {}

def _cube_shape() -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    r = 0.5
    verts = [(-r, -r, -r), (r, -r, -r), (r, r, -r), (-r, r, -r),
             (-r, -r, r), (r, -r, r), (r, r, r), (-r, r, r)]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    return verts, edges

def _pyramid_shape() -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    r = 0.5
    verts = [(-r, -r, -r), (r, -r, -r), (r, -r, r), (-r, -r, r), (0, r, 0)]
    edges = [(0,1),(1,2),(2,3),(3,0),(0,4),(1,4),(2,4),(3,4)]
    return verts, edges

def _sphere_shape(stacks: int = 3, slices: int = 6) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    verts: list[tuple[float, float, float]] = []
    for i in range(stacks + 1):
        theta = math.pi * i / stacks
        for j in range(slices):
            phi = 2 * math.pi * j / slices
            x = math.sin(theta) * math.cos(phi) * 0.5
            y = math.cos(theta) * 0.5
            z = math.sin(theta) * math.sin(phi) * 0.5
            verts.append((x, y, z))
    edges: list[tuple[int, int]] = []
    for i in range(stacks):
        for j in range(slices):
            a = i * slices + j
            b = i * slices + (j + 1) % slices
            c = (i + 1) * slices + j
            d = (i + 1) * slices + (j + 1) % slices
            edges.append((a, b))
            edges.append((a, c))
    return verts, edges

def _cylinder_shape(segments: int = 12) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    r = 0.5
    verts: list[tuple[float, float, float]] = []
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        verts.append((r * math.cos(theta), -0.5, r * math.sin(theta)))
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        verts.append((r * math.cos(theta), 0.5, r * math.sin(theta)))
    verts.append((0, -0.5, 0))
    verts.append((0, 0.5, 0))
    edges: list[tuple[int, int]] = []
    for i in range(segments):
        edges.append((i, (i + 1) % segments))
        edges.append((segments + i, segments + (i + 1) % segments))
        edges.append((i, segments + i))
    for i in range(segments):
        edges.append((i, 2 * segments))
        edges.append((segments + i, 2 * segments + 1))
    return verts, edges

def _torus_shape(ring_segments: int = 12, tube_segments: int = 8) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    R, r = 0.5, 0.2
    verts: list[tuple[float, float, float]] = []
    for i in range(ring_segments):
        theta = 2 * math.pi * i / ring_segments
        for j in range(tube_segments):
            phi = 2 * math.pi * j / tube_segments
            cx, cz = R * math.cos(theta), R * math.sin(theta)
            x = cx + r * math.cos(theta) * math.cos(phi)
            y = r * math.sin(phi)
            z = cz + r * math.sin(theta) * math.cos(phi)
            verts.append((x, y, z))
    edges: list[tuple[int, int]] = []
    for i in range(ring_segments):
        for j in range(tube_segments):
            a = i * tube_segments + j
            b = i * tube_segments + (j + 1) % tube_segments
            c = ((i + 1) % ring_segments) * tube_segments + j
            edges.append((a, b))
            edges.append((a, c))
    return verts, edges

def _get_shape(kind: str) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    if kind not in _SHAPES:
        if kind == "sphere":
            _SHAPES[kind] = _sphere_shape()
        elif kind == "pyramid":
            _SHAPES[kind] = _pyramid_shape()
        elif kind == "cylinder":
            _SHAPES[kind] = _cylinder_shape()
        elif kind == "torus":
            _SHAPES[kind] = _torus_shape()
        else:
            _SHAPES[kind] = _cube_shape()
    return _SHAPES[kind]

def _rotate_point(p: tuple[float, float, float], rx: float, ry: float, rz: float) -> tuple[float, float, float]:
    x, y, z = p
    if rx:
        y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    if ry:
        x, z = x * math.cos(ry) - z * math.sin(ry), x * math.sin(ry) + z * math.cos(ry)
    if rz:
        x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    return (x, y, z)

_render_gen: int = 0

def render_3d_app(app: AppSpec, instruction_runner: Callable[[list[object]], None], parent: tk.Tk | tk.Toplevel | None = None, interpreter: object | None = None) -> None:
    global _render_gen
    _render_gen += 1
    gen = _render_gen
    if parent is not None:
        root = parent
        for w in root.winfo_children():
            w.destroy()
        for seq in ("<KeyPress>", "<KeyRelease>", "<Button-1>"):
            root.unbind(seq)
    else:
        root = tk.Tk()
    root.title(app.title)
    root.geometry(f"{app.width}x{app.height}")
    root.resizable(False, False)
    canvas = tk.Canvas(root, width=app.width, height=app.height, bg="#0a0a1a", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    obj_state: dict[str, dict[str, float]] = {}
    _images_3d: dict[str, tk.PhotoImage] = {}
    ci = app.camera_init or {}
    cam_x = float(ci.get("x", 0.0))
    cam_y = float(ci.get("y", 0.0))
    cam_z = float(ci.get("z", -4.0))
    cam_rx = math.radians(float(ci.get("rx", 0.0)))
    cam_ry = math.radians(float(ci.get("ry", 0.0)))
    pressed: set[str] = set()
    _bg_sound_process: subprocess.Popen | None = None
    _notification_3d: str = ""
    _notification_timer_3d: str | None = None

    def _play_sound_3d(name: str) -> None:
        nonlocal _bg_sound_process
        _stop_sound_3d()
        p = Path(name).expanduser()
        if not p.is_file():
            path = Path(name)
            if not path.is_file():
                return
            p = path
        try:
            _bg_sound_process = subprocess.Popen(
                ["afplay", str(p)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass

    def _stop_sound_3d() -> None:
        nonlocal _bg_sound_process
        if _bg_sound_process is not None:
            try:
                _bg_sound_process.terminate()
                _bg_sound_process.wait(timeout=2)
            except Exception:
                pass
            _bg_sound_process = None

    def _set_notification_3d(text: str) -> None:
        nonlocal _notification_3d, _notification_timer_3d
        _notification_3d = text
        if _notification_timer_3d:
            root.after_cancel(_notification_timer_3d)
        _notification_timer_3d = root.after(3000, _clear_notification_3d)
        _render_3d()

    def _clear_notification_3d() -> None:
        nonlocal _notification_3d, _notification_timer_3d
        _notification_3d = ""
        _notification_timer_3d = None
        _render_3d()

    for obj in app.objects or []:
        props = dict(obj.properties or {})
        obj_state[obj.name] = {
            "x": float(obj.x) / 100 - 1.5,
            "y": float(obj.y) / 100 - 1.5,
            "z": float(getattr(obj, "z", 0)) / 100 or 0.0,
            "rotation_x": float(props.get("rotation_x", 0)),
            "rotation_y": float(props.get("rotation_y", 0)),
            "rotation_z": float(props.get("rotation_z", 0)),
            "auto_rotate_x": float(props.get("auto_rotate_x", 0)),
            "auto_rotate_y": float(props.get("auto_rotate_y", 0)),
            "auto_rotate_z": float(props.get("auto_rotate_z", 0)),
            "scale": float(props.get("size", props.get("width", 40))) / 40,
            "scale_x": float(props.get("scale_x", 0)),
            "scale_y": float(props.get("scale_y", 0)),
            "scale_z": float(props.get("scale_z", 0)),
            "color": props.get("color", "#00ff88"),
            "image": getattr(obj, "path", "") or props.get("image", ""),
            "kind": obj.kind,
        }

    def _project(wx: float, wy: float, wz: float) -> tuple[float, float] | None:
        dx, dy, dz = wx - cam_x, wy - cam_y, wz - cam_z
        if cam_rx:
            dy, dz = dy * math.cos(cam_rx) - dz * math.sin(cam_rx), dy * math.sin(cam_rx) + dz * math.cos(cam_rx)
        if cam_ry:
            dx, dz = dx * math.cos(cam_ry) - dz * math.sin(cam_ry), dx * math.sin(cam_ry) + dz * math.cos(cam_ry)
        if dz <= 0.1:
            return None
        fov = 300
        sx = app.width / 2 + fov * dx / dz
        sy = app.height / 2 - fov * dy / dz
        return (sx, sy)

    def _sync_3d_state() -> None:
        for obj in app.objects or []:
            state = obj_state.get(obj.name)
            if state is None:
                continue
            props = obj.properties or {}
            state["rotation_x"] = float(props.get("rotation_x", state.get("rotation_x", 0)))
            state["rotation_y"] = float(props.get("rotation_y", state.get("rotation_y", 0)))
            state["rotation_z"] = float(props.get("rotation_z", state.get("rotation_z", 0)))
            state["auto_rotate_x"] = float(props.get("auto_rotate_x", state.get("auto_rotate_x", 0)))
            state["auto_rotate_y"] = float(props.get("auto_rotate_y", state.get("auto_rotate_y", 0)))
            state["auto_rotate_z"] = float(props.get("auto_rotate_z", state.get("auto_rotate_z", 0)))
            state["scale"] = float(props.get("size", props.get("width", 40))) / 40
            state["scale_x"] = float(props.get("scale_x", state.get("scale_x", 0)))
            state["scale_y"] = float(props.get("scale_y", state.get("scale_y", 0)))
            state["scale_z"] = float(props.get("scale_z", state.get("scale_z", 0)))
            state["color"] = props.get("color", state.get("color", "#00ff88"))
            state["image"] = props.get("image", state.get("image", ""))
            state["x"] = float(props.get("x", obj.x)) / 100 - 1.5
            state["y"] = float(props.get("y", obj.y)) / 100 - 1.5
            state["z"] = float(props.get("z", obj.z)) / 100 or 0.0

    def _resolve_resource(name: str) -> str:
        resources = getattr(app, "resources", None) or {}
        if name in resources:
            return resources[name]
        return name

    def _load_3d_image(path: str, scale: float) -> tk.PhotoImage | None:
        nonlocal _images_3d
        path = _resolve_resource(path)
        key = f"{path}|{scale:.2f}"
        if key in _images_3d:
            return _images_3d[key]
        try:
            p = Path(path)
            if not p.is_file() and interpreter is not None:
                bp = getattr(interpreter, "base_path", None)
                if bp is not None:
                    p = bp / path
            if not p.is_file():
                p = Path(__file__).parent.parent / path
            if not p.is_file():
                return None
            try:
                from PIL import Image as PILImage, ImageTk
                pil = PILImage.open(p)
                w = max(8, int(pil.width * scale))
                h = max(8, int(pil.height * scale))
                pil = pil.resize((w, h), PILImage.NEAREST)
                _images_3d[key] = ImageTk.PhotoImage(pil)
            except ImportError:
                _images_3d[key] = tk.PhotoImage(file=str(p))
            return _images_3d[key]
        except Exception:
            return None

    def _render_3d() -> None:
        if gen != _render_gen:
            return
        canvas.delete("all")
        _sync_3d_state()
        for name, state in obj_state.items():
            img_file = state.get("image", "")
            if img_file:
                center = _project(state["x"], state["y"], state["z"])
                if center is not None:
                    img = _load_3d_image(img_file, state["scale"] * 3)
                    if img is not None:
                        canvas.create_image(center[0], center[1], image=img)
                        continue
            verts, edges = _get_shape(state["kind"])
            rx = math.radians(state["rotation_x"])
            ry = math.radians(state["rotation_y"])
            rz = math.radians(state["rotation_z"])
            s = state["scale"]
            sx = state.get("scale_x", 0) or s
            sy = state.get("scale_y", 0) or s
            sz = state.get("scale_z", 0) or s
            projected: list[tuple[float, float] | None] = []
            for v in verts:
                rv = _rotate_point((v[0] * sx, v[1] * sy, v[2] * sz), rx, ry, rz)
                pw = _project(state["x"] + rv[0], state["y"] + rv[1], state["z"] + rv[2])
                projected.append(pw)
            color = str(state.get("color", "#00ff88"))
            for a, b in edges:
                pa = projected[a]
                pb = projected[b]
                if pa is not None and pb is not None:
                    canvas.create_line(pa[0], pa[1], pb[0], pb[1], fill=color, width=1.5)
        if _notification_3d:
            nw = 400
            nh = 40
            nx = app.width // 2 - nw // 2
            ny = 20
            canvas.create_rectangle(nx, ny, nx + nw, ny + nh, fill="#1e293b", outline="", width=0)
            canvas.create_text(nx + nw // 2, ny + nh // 2, text=_notification_3d, font=("Helvetica", 14, "bold"), fill="white")

    def _drain_notifications() -> None:
        if interpreter is not None:
            pending = getattr(interpreter, "_pending_notifications", None)
            if pending:
                for t in pending:
                    _set_notification_3d(t)
                pending.clear()

    def _handle_3d_event(event_key: str) -> None:
        if app.events and event_key in app.events:
            for instr in app.events[event_key]:
                if isinstance(instr, PlaySound):
                    _play_sound_3d(instr.name)
                elif isinstance(instr, StopSound):
                    _stop_sound_3d()
                elif isinstance(instr, ShowText) and interpreter is None:
                    _set_notification_3d(instr.text)
                else:
                    try:
                        instruction_runner([instr])
                        _drain_notifications()
                    except Exception:
                        pass
            _render_3d()

    def _on_key_3d(event: tk.Event) -> None:
        key = event.keysym.lower()
        pressed.add(key)
        _handle_3d_event(f"key:{key}")

    def _on_key_release_3d(event: tk.Event) -> None:
        key = event.keysym.lower()
        pressed.discard(key)
        _handle_3d_event(f"key_release:{key}")

    def _auto_rotate_objects() -> None:
        for state in obj_state.values():
            ax = float(state.get("auto_rotate_x", 0))
            ay = float(state.get("auto_rotate_y", 0))
            az = float(state.get("auto_rotate_z", 0))
            if ax:
                state["rotation_x"] = (state["rotation_x"] + ax) % 360
            if ay:
                state["rotation_y"] = (state["rotation_y"] + ay) % 360
            if az:
                state["rotation_z"] = (state["rotation_z"] + az) % 360

    def _camera_loop() -> None:
        nonlocal cam_x, cam_y, cam_z, cam_rx, cam_ry
        if gen != _render_gen:
            return
        if app.camera_mode in ("first_person", "third_person"):
            bird = obj_state.get("bird")
            if bird:
                bx = bird.get("x", 0)
                by = bird.get("y", 0)
                bz = bird.get("z", 0)
                if app.camera_mode == "first_person":
                    cam_x = bx
                    cam_y = by
                    cam_z = bz + 0.5
                else:
                    cam_x = bx
                    cam_y = by + 0.3
                    cam_z = bz - 2.5
                cam_rx = 0.0
                cam_ry = 0.0
        _auto_rotate_objects()
        _render_3d()
        root.after(30, _camera_loop)

    _timer_scheduled_3d: dict[str, str] = {}

    def _schedule_timers_3d() -> None:
        if not app.events:
            return
        for event_key in list(app.events.keys()):
            if not event_key.startswith("timer:"):
                continue
            ms_str = event_key.split(":", 1)[1]
            try:
                ms = int(ms_str)
            except ValueError:
                continue
            if event_key in _timer_scheduled_3d:
                continue
            def _fire(key: str = event_key, interval: int = ms) -> None:
                if gen != _render_gen:
                    return
                _handle_3d_event(key)
                root.after(interval, lambda k=key, i=interval: _fire(k, i))
            _timer_scheduled_3d[event_key] = root.after(ms, lambda k=event_key, i=ms: _fire(k, i))

    def _on_mouse_click_3d(event: tk.Event) -> None:
        _handle_3d_event("mouse:clicked")

    canvas.focus_set()
    root.bind("<KeyPress>", _on_key_3d)
    root.bind("<KeyRelease>", _on_key_release_3d)
    canvas.bind("<Button-1>", _on_mouse_click_3d)
    _render_3d()
    _schedule_timers_3d()
    root.after(30, _camera_loop)
    if parent is None:
        root.mainloop()
