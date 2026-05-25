"""GPU-accelerated 3D renderer using ModernGL and glfw."""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

from .ir import AppSpec, CreatorObject

try:
    import glfw
    import moderngl as mgl
    _HAS_GL = True
except ImportError:
    _HAS_GL = False


# ── Shape primitives (vertex + index buffers for solid triangles) ──────────

def _cube_mesh() -> tuple[list[tuple[float, float, float]], list[int]]:
    h = 0.5
    verts = [
        (-h, -h, -h), ( h, -h, -h), ( h,  h, -h), (-h,  h, -h),  # back
        (-h, -h,  h), ( h, -h,  h), ( h,  h,  h), (-h,  h,  h),  # front
    ]
    indices = [
        0,1,2, 0,2,3,  # back
        4,6,5, 4,7,6,  # front
        0,4,5, 0,5,1,  # bottom
        3,2,6, 3,6,7,  # top
        0,3,7, 0,7,4,  # left
        1,5,6, 1,6,2,  # right
    ]
    return verts, indices


def _pyramid_mesh() -> tuple[list[tuple[float, float, float]], list[int]]:
    h = 0.5
    verts = [
        (-h, -h, -h), ( h, -h, -h), ( h, -h,  h), (-h, -h,  h),  # base
        ( 0,  h,  0),  # apex
    ]
    indices = [
        0,1,4, 1,2,4, 2,3,4, 3,0,4,  # 4 sides
        1,0,2, 2,0,3,  # base (2 tris)
    ]
    return verts, indices


def _sphere_mesh(stacks: int = 8, slices: int = 12) -> tuple[list[tuple[float, float, float]], list[int]]:
    verts: list[tuple[float, float, float]] = []
    indices: list[int] = []
    for i in range(stacks + 1):
        theta = math.pi * i / stacks
        for j in range(slices):
            phi = 2 * math.pi * j / slices
            x = 0.5 * math.sin(theta) * math.cos(phi)
            y = 0.5 * math.cos(theta)
            z = 0.5 * math.sin(theta) * math.sin(phi)
            verts.append((x, y, z))
    for i in range(stacks):
        for j in range(slices):
            a = i * slices + j
            b = a + slices
            next_j = (j + 1) % slices
            indices.extend([a, b, b + 1, a, b + 1, a + 1])
            a1 = i * slices + next_j
            b1 = a1 + slices
            indices.extend([a1, b1, b1 + 1, a1, b1 + 1, a1 + 1])
    return verts, indices


def _cylinder_mesh(segments: int = 16) -> tuple[list[tuple[float, float, float]], list[int]]:
    verts: list[tuple[float, float, float]] = [(0, -0.5, 0), (0, 0.5, 0)]  # center bottom, center top
    for i in range(segments):
        a = 2 * math.pi * i / segments
        x = 0.5 * math.cos(a)
        z = 0.5 * math.sin(a)
        verts.append((x, -0.5, z))
    for i in range(segments):
        a = 2 * math.pi * i / segments
        x = 0.5 * math.cos(a)
        z = 0.5 * math.sin(a)
        verts.append((x, 0.5, z))
    indices: list[int] = []
    for i in range(segments):
        n = (i + 1) % segments
        bottom = 2 + i
        bottom_n = 2 + n
        top = 2 + segments + i
        top_n = 2 + segments + n
        idxs = [bottom, top, top_n, bottom, top_n, bottom_n]
        indices.extend(idxs)
    for i in range(segments):
        n = (i + 1) % segments
        bi = 2 + i
        bn = 2 + n
        indices.extend([0, bn, bi])
        ti = 2 + segments + i
        tn = 2 + segments + n
        indices.extend([1, ti, tn])
    return verts, indices


def _torus_mesh(ring: int = 16, tube: int = 12) -> tuple[list[tuple[float, float, float]], list[int]]:
    verts: list[tuple[float, float, float]] = []
    indices: list[int] = []
    R, r = 0.5, 0.15
    for i in range(ring):
        theta = 2 * math.pi * i / ring
        for j in range(tube):
            phi = 2 * math.pi * j / tube
            x = (R + r * math.cos(phi)) * math.cos(theta)
            y = r * math.sin(phi)
            z = (R + r * math.cos(phi)) * math.sin(theta)
            verts.append((x, y, z))
    for i in range(ring):
        for j in range(tube):
            a = i * tube + j
            b = ((i + 1) % ring) * tube + j
            next_j = (j + 1) % tube
            a1 = a + 1 if j + 1 < tube else i * tube
            b1 = b + 1 if j + 1 < tube else ((i + 1) % ring) * tube
            indices.extend([a, b, b1, a, b1, a1])
    return verts, indices


_SHAPE_CACHE: dict[str, tuple[list[tuple[float, float, float]], list[int]]] = {}


def _get_mesh(kind: str):
    if kind not in _SHAPE_CACHE:
        builders = {
            "cube": _cube_mesh,
            "pyramid": _pyramid_mesh,
            "sphere": _sphere_mesh,
            "cylinder": _cylinder_mesh,
            "torus": _torus_mesh,
        }
        builder = builders.get(kind, _cube_mesh)
        _SHAPE_CACHE[kind] = builder()
    return _SHAPE_CACHE[kind]


# ── Shaders ────────────────────────────────────────────────────────────────

_VERTEX_SHADER = """
#version 330 core
uniform mat4 u_mvp;
uniform vec3 u_color;
in vec3 in_pos;
out vec3 v_color;
void main() {
    gl_Position = u_mvp * vec4(in_pos, 1.0);
    v_color = u_color;
}
"""

_FRAGMENT_SHADER = """
#version 330 core
in vec3 v_color;
out vec4 fragColor;
void main() {
    fragColor = vec4(v_color, 1.0);
}
"""


# ── Matrix utilities (no numpy) ───────────────────────────────────────────

def _mat4_identity() -> list[float]:
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]


def _mat4_multiply(a: list[float], b: list[float]) -> list[float]:
    res = [0.0] * 16
    for i in range(4):
        for j in range(4):
            s = 0.0
            for k in range(4):
                s += a[i * 4 + k] * b[k * 4 + j]
            res[i * 4 + j] = s
    return res


def _translate(x: float, y: float, z: float) -> list[float]:
    m = _mat4_identity()
    m[12], m[13], m[14] = x, y, z
    return m


def _scale(sx: float, sy: float, sz: float) -> list[float]:
    return [sx,0,0,0, 0,sy,0,0, 0,0,sz,0, 0,0,0,1]


def _rotate_x(angle_deg: float) -> list[float]:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [1,0,0,0, 0,c,-s,0, 0,s,c,0, 0,0,0,1]


def _rotate_y(angle_deg: float) -> list[float]:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1]


def _rotate_z(angle_deg: float) -> list[float]:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [c,-s,0,0, s,c,0,0, 0,0,1,0, 0,0,0,1]


def _look_at(eye: tuple[float, ...], target: tuple[float, ...], up: tuple[float, ...]) -> list[float]:
    f = (target[0] - eye[0], target[1] - eye[1], target[2] - eye[2])
    fl = math.sqrt(f[0]**2 + f[1]**2 + f[2]**2)
    if fl == 0:
        return _mat4_identity()
    f = (f[0]/fl, f[1]/fl, f[2]/fl)
    s = (
        f[1] * up[2] - f[2] * up[1],
        f[2] * up[0] - f[0] * up[2],
        f[0] * up[1] - f[1] * up[0],
    )
    sl = math.sqrt(s[0]**2 + s[1]**2 + s[2]**2)
    if sl == 0:
        return _mat4_identity()
    s = (s[0]/sl, s[1]/sl, s[2]/sl)
    u = (s[1]*f[2] - s[2]*f[1], s[2]*f[0] - s[0]*f[2], s[0]*f[1] - s[1]*f[0])
    return [
        s[0], u[0], -f[0], 0,
        s[1], u[1], -f[1], 0,
        s[2], u[2], -f[2], 0,
        -(s[0]*eye[0] + s[1]*eye[1] + s[2]*eye[2]),
        -(u[0]*eye[0] + u[1]*eye[1] + u[2]*eye[2]),
        f[0]*eye[0] + f[1]*eye[1] + f[2]*eye[2],
        1,
    ]


def _perspective(fov_deg: float, aspect: float, near: float, far: float) -> list[float]:
    f = 1.0 / math.tan(math.radians(fov_deg) / 2)
    nf = 1.0 / (near - far)
    return [
        f/aspect, 0, 0, 0,
        0, f, 0, 0,
        0, 0, (far + near) * nf, -1,
        0, 0, 2 * far * near * nf, 0,
    ]


def _hex_color(name: str) -> tuple[float, float, float]:
    s = name.lstrip("#")
    try:
        r = int(s[0:2], 16) / 255
        g = int(s[2:4], 16) / 255
        b = int(s[4:6], 16) / 255
    except (ValueError, IndexError):
        return 0.5, 0.5, 0.5
    return r, g, b


_NAMED_COLORS: dict[str, tuple[float, float, float]] = {
    "red": (1, 0, 0), "green": (0, 1, 0), "blue": (0, 0, 1),
    "white": (1, 1, 1), "black": (0, 0, 0), "gray": (0.5, 0.5, 0.5),
    "grey": (0.5, 0.5, 0.5), "yellow": (1, 1, 0), "cyan": (0, 1, 1),
    "magenta": (1, 0, 1), "orange": (1, 0.65, 0), "purple": (0.5, 0, 0.5),
    "pink": (1, 0.75, 0.8), "brown": (0.6, 0.3, 0.1),
}


def _parse_color(value: object) -> tuple[float, float, float]:
    if isinstance(value, str):
        if value.startswith("#"):
            return _hex_color(value)
        return _NAMED_COLORS.get(value.lower(), (0.5, 0.5, 0.5))
    return 0.5, 0.5, 0.5


# ── Object state ───────────────────────────────────────────────────────────

class _ObjState:
    __slots__ = ("kind", "x", "y", "z", "rot_x", "rot_y", "rot_z",
                 "auto_rx", "auto_ry", "auto_rz", "scale", "color")

    def __init__(self, kind: str, x: float, y: float, z: float, color: tuple[float, ...]):
        self.kind = kind
        self.x = x
        self.y = y
        self.z = z
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0
        self.auto_rx = 0.0
        self.auto_ry = 0.0
        self.auto_rz = 0.0
        self.scale = 1.0
        self.color = color


def _build_state(app: AppSpec) -> dict[str, _ObjState]:
    state: dict[str, _ObjState] = {}
    for obj in app.objects or []:
        props = obj.properties or {}
        c = _parse_color(props.get("color", props.get("colour", "")))
        st = _ObjState(
            kind=obj.kind or "cube",
            x=obj.x / 100 - 1.5 if obj.x != 0 else 0,
            y=obj.y / 100 - 1.5 if obj.y != 0 else 0,
            z=obj.z / 100 if obj.z != 0 else 0,
            color=c,
        )
        st.scale = float(props.get("size", props.get("width", 40))) / 40 or 1.0
        st.auto_rx = float(props.get("auto_rotate_x", 0))
        st.auto_ry = float(props.get("auto_rotate_y", 0))
        st.auto_rz = float(props.get("auto_rotate_z", 0))
        state[obj.name] = st
    return state


def _sync_state(state: dict[str, _ObjState], app: AppSpec) -> None:
    for obj in app.objects or []:
        st = state.get(obj.name)
        if st is None:
            continue
        p = obj.properties or {}
        if "rotation_x" in p: st.rot_x = float(p["rotation_x"])
        if "rotation_y" in p: st.rot_y = float(p["rotation_y"])
        if "rotation_z" in p: st.rot_z = float(p["rotation_z"])
        if "auto_rotate_x" in p: st.auto_rx = float(p["auto_rotate_x"])
        if "auto_rotate_y" in p: st.auto_ry = float(p["auto_rotate_y"])
        if "auto_rotate_z" in p: st.auto_rz = float(p["auto_rotate_z"])
        if "size" in p: st.scale = float(p["size"]) / 40
        if "width" in p: st.scale = float(p["width"]) / 40
        c = p.get("color", p.get("colour", ""))
        if c: st.color = _parse_color(c)


def _auto_rotate(state: dict[str, _ObjState]) -> None:
    for st in state.values():
        st.rot_x = (st.rot_x + st.auto_rx) % 360
        st.rot_y = (st.rot_y + st.auto_ry) % 360
        st.rot_z = (st.rot_z + st.auto_rz) % 360


# ── Main renderer loop ─────────────────────────────────────────────────────

def render_3d_app(
    app: AppSpec,
    instruction_runner: Callable[[list[object]], None],
    parent: object = None,
    interpreter: object = None,
) -> None:
    if not _HAS_GL:
        print("OpenGL not available (install moderngl + glfw). Falling through.", file=sys.stderr)
        return

    if not glfw.init():
        print("Failed to initialize glfw", file=sys.stderr)
        return

    ci = app.camera_init or {}
    cam_state = {
        "distance": abs(ci.get("z", -4.0)),
        "pitch": math.radians(float(ci.get("rx", 15))),
        "yaw": math.radians(float(ci.get("ry", 0))),
        "target_x": float(ci.get("x", 0)),
        "target_y": float(ci.get("y", 0)),
        "target_z": float(ci.get("z", 0)),
    }
    cam_mode = app.camera_mode or "fixed"
    width, height = app.width or 800, app.height or 600

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(width, height, app.title or "Angis 3D", None, None)
    if not window:
        glfw.terminate()
        print("Failed to create glfw window", file=sys.stderr)
        return

    glfw.make_context_current(window)
    ctx = mgl.create_context()

    # Compile shaders
    prog = ctx.program(
        vertex_shader=_VERTEX_SHADER,
        fragment_shader=_FRAGMENT_SHADER,
    )
    mvp_loc = prog["u_mvp"]
    color_loc = prog["u_color"]

    # Build object state
    obj_state = _build_state(app)

    # Pre-create VBO/VAO for each shape
    from array import array as _array

    mesh_vaos: dict[str, tuple[mgl.VertexArray, int]] = {}
    for kind in ("cube", "pyramid", "sphere", "cylinder", "torus"):
        verts, indices = _get_mesh(kind)
        flat = _array("f")
        for v in verts:
            flat.extend(v)
        vbo = ctx.buffer(flat.tobytes())
        ibo = ctx.buffer(_array("I", indices).tobytes())
        vao = ctx.vertex_array(prog, [(vbo, "3f", "in_pos")], ibo)
        mesh_vaos[kind] = (vao, len(indices))

    # Configure GL
    ctx.enable(mgl.DEPTH_TEST)
    ctx.enable(mgl.CULL_FACE)
    ctx.clear_color = 0.15, 0.15, 0.2, 1.0

    # Camera control state
    mouse_down = False
    last_mx, last_my = 0.0, 0.0
    pressed_keys: set[int] = set()

    def _update_camera():
        if cam_mode in {"first_person", "third_person"} and "bird" in obj_state:
            b = obj_state["bird"]
            if cam_mode == "first_person":
                cam_state["target_x"] = b.x
                cam_state["target_y"] = b.y
                cam_state["target_z"] = b.z + 0.5
            else:
                d = cam_state["distance"]
                cam_state["target_x"] = b.x
                cam_state["target_y"] = b.y + 0.3
                cam_state["target_z"] = b.z - d + 0.5

    def _camera_matrix() -> list[float]:
        d = cam_state["distance"]
        pitch = cam_state["pitch"]
        yaw = cam_state["yaw"]
        tx = cam_state["target_x"]
        ty = cam_state["target_y"]
        tz = cam_state["target_z"]
        eye_x = tx + d * math.sin(yaw) * math.cos(pitch)
        eye_y = ty + d * math.sin(pitch)
        eye_z = tz + d * math.cos(yaw) * math.cos(pitch)
        return _look_at((eye_x, eye_y, eye_z), (tx, ty, tz), (0, 1, 0))

    def _handle_key(key: int, scancode: int, action: int, mods: int):
        if action == glfw.PRESS:
            pressed_keys.add(key)
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)
            glfw_key = glfw.get_key_name(key, scancode)
            if glfw_key:
                instruction_runner([])
        elif action == glfw.RELEASE:
            pressed_keys.discard(key)

    def _handle_mouse_button(button: int, action: int, mods: int):
        nonlocal mouse_down
        if button == glfw.MOUSE_BUTTON_LEFT:
            mouse_down = action == glfw.PRESS
            if action == glfw.PRESS:
                instruction_runner([])

    def _handle_cursor_pos(x: float, y: float):
        nonlocal last_mx, last_my
        if mouse_down:
            dx = x - last_mx
            dy = y - last_my
            cam_state["yaw"] += dx * 0.005
            cam_state["pitch"] = max(-math.pi / 2.1, min(math.pi / 2.1,
                                                         cam_state["pitch"] - dy * 0.005))
        last_mx, last_my = x, y

    def _handle_scroll(xoff: float, yoff: float):
        cam_state["distance"] = max(0.5, cam_state["distance"] - yoff * 0.5)

    glfw.set_key_callback(window, _handle_key)
    glfw.set_mouse_button_callback(window, _handle_mouse_button)
    glfw.set_cursor_pos_callback(window, _handle_cursor_pos)
    glfw.set_scroll_callback(window, _handle_scroll)

    last_time = time.time()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        now = time.time()
        dt = now - last_time
        last_time = now

        _update_camera()
        _sync_state(obj_state, app)
        _auto_rotate(obj_state)

        ctx.clear()
        view_mat = _camera_matrix()
        proj_mat = _perspective(60, width / height, 0.1, 100)
        vp = _mat4_multiply(proj_mat, view_mat)

        for st in obj_state.values():
            vao, count = mesh_vaos.get(st.kind, mesh_vaos["cube"])
            model = _mat4_multiply(
                _mat4_multiply(
                    _mat4_multiply(
                        _translate(st.x, st.y, st.z),
                        _rotate_x(st.rot_x),
                    ),
                    _rotate_y(st.rot_y),
                ),
                _rotate_z(st.rot_z),
            )
            model = _mat4_multiply(model, _scale(st.scale, st.scale, st.scale))
            mvp = _mat4_multiply(vp, model)
            from array import array as _array
            mvp_loc.write(_array("f", mvp).tobytes())
            color_loc.write(_array("f", st.color).tobytes())
            vao.render(mgl.TRIANGLES)

        glfw.swap_buffers(window)

    ctx.release()
    glfw.terminate()
