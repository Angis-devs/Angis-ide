"""Intermediate representation for Angis programs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


Value = Union[str, int, float, bool]


@dataclass(frozen=True)
class Reference:
    name: str


@dataclass(frozen=True)
class RangeExpr:
    start: "Expression"
    end: "Expression"


Expression = Union[Value, Reference, "BinaryOp", "UnaryOp", "Access", "SliceOf", "LengthOf", "Lambda", "Comprehension", "RangeExpr", "PythonEval", list["Expression"], dict[str, "Expression"]]


@dataclass(frozen=True)
class BinaryOp:
    op: str
    left: Expression
    right: Expression


@dataclass(frozen=True)
class UnaryOp:
    op: str
    right: Expression


@dataclass(frozen=True)
class Access:
    target: Expression
    key: Expression


@dataclass(frozen=True)
class SliceOf:
    target: Expression
    start: Expression
    end: Expression


@dataclass(frozen=True)
class LengthOf:
    value: Expression


@dataclass(frozen=True)
class TernaryExpr:
    condition: Expression
    true_expr: Expression
    false_expr: Expression


@dataclass(frozen=True)
class WalrusExpr:
    name: str
    value: Expression


@dataclass(frozen=True)
class Instruction:
    confidence: float
    source: str


@dataclass(frozen=True)
class Print(Instruction):
    value: Expression

    def __str__(self) -> str:
        return f"PRINT({format_expr(self.value)})"


@dataclass(frozen=True)
class SetVar(Instruction):
    name: str
    value: Expression

    def __str__(self) -> str:
        return f"SET({self.name}, {format_expr(self.value)})"


@dataclass(frozen=True)
class SetAccess(Instruction):
    target: Access
    value: Expression

    def __str__(self) -> str:
        return f"SET_ACCESS({format_expr(self.target)}, {format_expr(self.value)})"


@dataclass(frozen=True)
class AddToVar(Instruction):
    name: str
    value: Expression

    def __str__(self) -> str:
        return f"ADD_TO({self.name}, {format_expr(self.value)})"


@dataclass(frozen=True)
class UpdateVar(Instruction):
    name: str
    op: str
    value: Expression

    def __str__(self) -> str:
        return f"UPDATE({self.name} {self.op}= {format_expr(self.value)})"


@dataclass(frozen=True)
class Condition:
    left: Expression
    operator: str
    right: Expression

    def __str__(self) -> str:
        return f"{format_expr(self.left)} {self.operator} {format_expr(self.right)}"


@dataclass(frozen=True)
class LogicalCondition:
    operator: str
    left: object
    right: object | None = None

    def __str__(self) -> str:
        if self.operator == "not":
            return f"not {self.left}"
        return f"({self.left} {self.operator} {self.right})"


@dataclass(frozen=True)
class IfBlock(Instruction):
    condition: object
    body: list[object]
    else_body: list[object] | None = None

    def __str__(self) -> str:
        return f"IF({self.condition})"


@dataclass(frozen=True)
class RepeatBlock(Instruction):
    count: Expression
    body: list[object]

    def __str__(self) -> str:
        return f"REPEAT({format_expr(self.count)})"


@dataclass(frozen=True)
class WhileBlock(Instruction):
    condition: Condition
    body: list[object]

    def __str__(self) -> str:
        return f"WHILE({self.condition})"


@dataclass(frozen=True)
class ForEachBlock(Instruction):
    item_name: str
    collection: Expression
    body: list[object]

    def __str__(self) -> str:
        return f"FOR_EACH({self.item_name} in {format_expr(self.collection)})"


@dataclass(frozen=True)
class FunctionDef(Instruction):
    name: str
    body: list[object]
    params: list[str] | None = None
    param_types: dict[str, str] | None = None
    return_type: str = ""
    decorators: list[str] | None = None

    def __str__(self) -> str:
        return f"FUNCTION({self.name})"


@dataclass(frozen=True)
class FunctionCall(Instruction):
    name: str
    args: list[Expression] | None = None
    result_name: str = ""
    result_names: list[str] | None = None

    def __str__(self) -> str:
        return f"CALL({self.name})"


@dataclass(frozen=True)
class ObjectMethodDef(Instruction):
    object_name: str
    method_name: str
    body: list[object]
    params: list[str] | None = None
    param_types: dict[str, str] | None = None
    return_type: str = ""

    def __str__(self) -> str:
        return f"METHOD({self.object_name}.{self.method_name})"


@dataclass(frozen=True)
class ObjectMethodCall(Instruction):
    object_name: str
    method_name: str
    args: list[Expression] | None = None
    result_name: str = ""
    result_names: list[str] | None = None

    def __str__(self) -> str:
        return f"CALL_METHOD({self.object_name}.{self.method_name})"


@dataclass(frozen=True)
class YieldValue(Instruction):
    value: Expression
    send_var: str = ""

    def __str__(self) -> str:
        return f"YIELD({format_expr(self.value)})"


@dataclass(frozen=True)
class Spawn(Instruction):
    name: str
    args: list[Expression]
    result_name: str = ""

    def __str__(self) -> str:
        return f"SPAWN({self.name})"


@dataclass(frozen=True)
class Await(Instruction):
    target: str
    result_name: str = ""

    def __str__(self) -> str:
        return f"AWAIT({self.target})"


@dataclass(frozen=True)
class ReturnValue(Instruction):
    value: Expression | None = None
    values: list[Expression] | None = None

    def __str__(self) -> str:
        if self.values:
            return f"RETURN({', '.join(format_expr(v) for v in self.values)})"
        return f"RETURN({format_expr(self.value)})"


@dataclass(frozen=True)
class EventBlock(Instruction):
    kind: str
    name: str
    body: list[object]

    def __str__(self) -> str:
        return f"WHEN({self.kind} {self.name})"


@dataclass(frozen=True)
class ImportModule(Instruction):
    name: str

    def __str__(self) -> str:
        return f"IMPORT({self.name})"


@dataclass(frozen=True)
class PythonEval:
    expression: str
    result_name: str = ""

    def __str__(self) -> str:
        return f"PYTHON_EVAL({self.expression})"


@dataclass(frozen=True)
class PythonExec(Instruction):
    code: str

    def __str__(self) -> str:
        return f"PYTHON_EXEC({self.code[:50]})"


@dataclass(frozen=True)
class PythonImport(Instruction):
    module: str
    result_name: str = ""
    names: list[str] | None = None

    def __str__(self) -> str:
        return f"PYTHON_IMPORT({self.module})"


@dataclass(frozen=True)
class AsyncFunctionDef(Instruction):
    name: str
    body: list[object]
    params: list[str] | None = None
    param_types: dict[str, str] | None = None
    return_type: str = ""

    def __str__(self) -> str:
        return f"ASYNC_FUNCTION({self.name})"


@dataclass(frozen=True)
class AwaitExpr(Instruction):
    value: Expression
    result_name: str = ""

    def __str__(self) -> str:
        return f"AWAIT_EXPR({format_expr(self.value)})"


@dataclass(frozen=True)
class WatchFile(Instruction):
    path: str

    def __str__(self) -> str:
        return f"WATCH({self.path})"


@dataclass(frozen=True)
class NativeGUI(Instruction):
    action: str
    args: dict[str, Expression]
    result_name: str = ""

    def __str__(self) -> str:
        return f"NATIVE_GUI({self.action})"


@dataclass(frozen=True)
class UseStdLibAction(Instruction):
    module: str
    action: str
    args: dict[str, Expression]
    name: str

    def __str__(self) -> str:
        return f"USE({self.module}.{self.action} as {self.name})"


@dataclass(frozen=True)
class DefineBlueprint(Instruction):
    name: str
    items: dict[str, Expression]
    inherits: str = ""

    def __str__(self) -> str:
        return f"BLUEPRINT({self.name})"


@dataclass(frozen=True)
class CreateFromBlueprint(Instruction):
    blueprint_name: str
    name: str
    items: dict[str, Expression]

    def __str__(self) -> str:
        return f"CREATE_FROM({self.blueprint_name} as {self.name})"


@dataclass(frozen=True)
class CreateMap(Instruction):
    name: str
    items: dict[str, Expression]

    def __str__(self) -> str:
        return f"MAP({self.name})"


@dataclass(frozen=True)
class BlueprintInitDef(Instruction):
    blueprint_name: str
    params: list[str]
    param_types: dict[str, str] | None = None
    body: list[object] = field(default_factory=list)

    def __str__(self) -> str:
        return f"INIT({self.blueprint_name})"


@dataclass(frozen=True)
class DebugState(Instruction):
    target: str

    def __str__(self) -> str:
        return f"DEBUG({self.target})"


@dataclass(frozen=True)
class ExportApp(Instruction):
    path: str

    def __str__(self) -> str:
        return f"EXPORT_APP({self.path})"


@dataclass(frozen=True)
class PackageApp(Instruction):
    path: str

    def __str__(self) -> str:
        return f"PACKAGE_APP({self.path})"


@dataclass(frozen=True)
class DebugBreakpoint(Instruction):
    label: str

    def __str__(self) -> str:
        return f"BREAKPOINT({self.label})"


@dataclass(frozen=True)
class OpenDatabase(Instruction):
    path: str
    name: str

    def __str__(self) -> str:
        return f"DATABASE({self.path} as {self.name})"


@dataclass(frozen=True)
class ExecuteSql(Instruction):
    database: str
    sql: str
    name: str = ""

    def __str__(self) -> str:
        suffix = f" as {self.name}" if self.name else ""
        return f"SQL({self.database}{suffix})"


@dataclass(frozen=True)
class PlayVideo(Instruction):
    path: str
    x: int
    y: int
    width: int = 320
    height: int = 180

    def __str__(self) -> str:
        return f"VIDEO({self.path} at x {self.x} y {self.y} size {self.width}x{self.height})"


@dataclass(frozen=True)
class Add(Instruction):
    left: Expression
    right: Expression

    def __str__(self) -> str:
        return f"ADD({format_expr(self.left)}, {format_expr(self.right)})"


@dataclass(frozen=True)
class Subtract(Instruction):
    left: Expression
    right: Expression

    def __str__(self) -> str:
        return f"SUBTRACT({format_expr(self.left)}, {format_expr(self.right)})"


@dataclass(frozen=True)
class Multiply(Instruction):
    left: Expression
    right: Expression

    def __str__(self) -> str:
        return f"MULTIPLY({format_expr(self.left)}, {format_expr(self.right)})"


@dataclass(frozen=True)
class Divide(Instruction):
    left: Expression
    right: Expression

    def __str__(self) -> str:
        return f"DIVIDE({format_expr(self.left)}, {format_expr(self.right)})"


@dataclass(frozen=True)
class AppStart(Instruction):
    title: Expression

    def __str__(self) -> str:
        return f"APP({format_expr(self.title)})"


@dataclass(frozen=True)
class AppText(Instruction):
    value: Expression

    def __str__(self) -> str:
        return f"APP_TEXT({format_expr(self.value)})"


@dataclass(frozen=True)
class AppButton(Instruction):
    label: Expression

    def __str__(self) -> str:
        return f"APP_BUTTON({format_expr(self.label)})"


@dataclass(frozen=True)
class AppScene(Instruction):
    name: Expression

    def __str__(self) -> str:
        return f"APP_SCENE({format_expr(self.name)})"


@dataclass(frozen=True)
class AppLayout(Instruction):
    kind: str
    columns: int = 1

    def __str__(self) -> str:
        suffix = f", columns={self.columns}" if self.kind == "grid" else ""
        return f"APP_LAYOUT({self.kind}{suffix})"


@dataclass(frozen=True)
class AppSize(Instruction):
    width: int
    height: int

    def __str__(self) -> str:
        return f"APP_SIZE({self.width}x{self.height})"


@dataclass(frozen=True)
class AppBackground(Instruction):
    color: str

    def __str__(self) -> str:
        return f"APP_BG({self.color})"


@dataclass(frozen=True)
class AppFileAttach(Instruction):
    path: Expression
    file_name: str = ""
    x: Expression = 0
    y: Expression = 0
    z: Expression = 0

    def __str__(self) -> str:
        base = f"APP_FILE({format_expr(self.path)}"
        if self.file_name:
            base += f" as {self.file_name!r}"
        base += f" at x {format_expr(self.x)} y {format_expr(self.y)} z {format_expr(self.z)})"
        return base


@dataclass(frozen=True)
class AppLoadingScreen(Instruction):
    image_path: str
    audio_path: str

    def __str__(self) -> str:
        return f"LOADING(image={self.image_path!r}, audio={self.audio_path!r})"


@dataclass(frozen=True)
class CreateObject(Instruction):
    kind: str
    name: str
    x: int
    y: int
    z: int
    text: str = ""
    path: str = ""
    properties: dict[str, Expression] | None = None

    def __str__(self) -> str:
        return f"CREATE({self.kind} {self.name} at x {self.x} y {self.y} z {self.z})"


@dataclass(frozen=True)
class MoveObject(Instruction):
    name: str
    direction: str
    amount: int

    def __str__(self) -> str:
        return f"MOVE({self.name} {self.direction} {self.amount})"


@dataclass(frozen=True)
class PlaceObject(Instruction):
    name: str
    x: int
    y: int
    z: int = 0

    def __str__(self) -> str:
        return f"PLACE({self.name} at x {self.x} y {self.y} z {self.z})"


@dataclass(frozen=True)
class ResizeObject(Instruction):
    name: str
    width: int
    height: int

    def __str__(self) -> str:
        return f"RESIZE({self.name} {self.width}x{self.height})"


@dataclass(frozen=True)
class SetProperty(Instruction):
    object_name: str
    property_name: str
    value: Expression

    def __str__(self) -> str:
        return f"PROPERTY({self.object_name}.{self.property_name} = {format_expr(self.value)})"


@dataclass(frozen=True)
class RotateObject(Instruction):
    name: str
    axis: str
    angle: float

    def __str__(self) -> str:
        return f"ROTATE({self.name} {self.axis} {self.angle})"


@dataclass(frozen=True)
class SetCamera(Instruction):
    x: float
    y: float
    z: float
    rotation_x: float = 0.0
    rotation_y: float = 0.0

    def __str__(self) -> str:
        return f"CAMERA({self.x}, {self.y}, {self.z} rx={self.rotation_x} ry={self.rotation_y})"


@dataclass(frozen=True)
class SetCameraMode(Instruction):
    mode: str

    def __str__(self) -> str:
        return f"CAMERA_MODE({self.mode!r})"


@dataclass(frozen=True)
class AnimateObject(Instruction):
    name: str
    direction: str
    amount: int
    milliseconds: int

    def __str__(self) -> str:
        return f"ANIMATE({self.name} {self.direction} {self.amount} every {self.milliseconds})"


@dataclass(frozen=True)
class ShowText(Instruction):
    text: str

    def __str__(self) -> str:
        return f"SHOW_TEXT({self.text!r})"


@dataclass(frozen=True)
class PlaySound(Instruction):
    name: str

    def __str__(self) -> str:
        return f"SOUND({self.name})"


@dataclass(frozen=True)
class StopSound(Instruction):
    def __str__(self) -> str:
        return "STOP_SOUND()"


@dataclass(frozen=True)
class Sleep(Instruction):
    milliseconds: int

    def __str__(self) -> str:
        return f"SLEEP({self.milliseconds}ms)"


@dataclass(frozen=True)
class SetSoundVolume(Instruction):
    volume: int

    def __str__(self) -> str:
        return f"SOUND_VOLUME({self.volume})"


@dataclass(frozen=True)
class CreateList(Instruction):
    name: str
    items: list[Expression]

    def __str__(self) -> str:
        return f"LIST({self.name})"


@dataclass(frozen=True)
class AddToList(Instruction):
    name: str
    item: Expression

    def __str__(self) -> str:
        return f"LIST_ADD({self.name}, {format_expr(self.item)})"


@dataclass(frozen=True)
class RemoveFromList(Instruction):
    name: str
    item: Expression

    def __str__(self) -> str:
        return f"LIST_REMOVE({self.name}, {format_expr(self.item)})"


@dataclass(frozen=True)
class RemoveProperty(Instruction):
    object_name: str
    property_name: str

    def __str__(self) -> str:
        return f"PROPERTY_REMOVE({self.object_name}.{self.property_name})"


@dataclass(frozen=True)
class SaveState(Instruction):
    path: str

    def __str__(self) -> str:
        return f"SAVE_STATE({self.path})"


@dataclass(frozen=True)
class LoadState(Instruction):
    path: str

    def __str__(self) -> str:
        return f"LOAD_STATE({self.path})"


@dataclass(frozen=True)
class FetchUrl(Instruction):
    url: str
    name: str

    def __str__(self) -> str:
        return f"FETCH({self.url} as {self.name})"


@dataclass(frozen=True)
class HttpRequest(Instruction):
    method: str
    url: str
    name: str
    body: str = ""

    def __str__(self) -> str:
        return f"HTTP({self.method} {self.url} as {self.name})"


@dataclass
class CreatorObject:
    kind: str
    name: str
    x: int
    y: int
    z: int
    text: str = ""
    path: str = ""
    properties: dict[str, object] | None = None


@dataclass
class FileInfo:
    name: str
    path: str
    size: int
    x: int = 0
    y: int = 0
    z: int = 0
    kind: str = "file"
    preview: str = ""


@dataclass
class AppSpec:
    title: str
    texts: list[str]
    buttons: list[str]
    scene: str = "text"
    width: int = 720
    height: int = 460
    bg: str = "#f8fafc"
    imports: list[str] | None = None
    backend: str = "tk"
    files: list[FileInfo] | None = None
    objects: list[CreatorObject] | None = None
    events: dict[str, list[object]] | None = None
    lists: dict[str, list[object]] | None = None
    maps: dict[str, dict[str, object]] | None = None
    layout: dict[str, object] | None = None
    sound_volume: int = 100
    loading_image: str = ""
    loading_audio: str = ""
    camera_init: dict[str, float] | None = None
    camera_mode: str = "fixed"
    resources: dict[str, str] | None = None


@dataclass(frozen=True)
class GameStart(Instruction):
    name: Expression

    def __str__(self) -> str:
        return f"GAME({format_expr(self.name)})"


@dataclass(frozen=True)
class GameRule(Instruction):
    text: Expression

    def __str__(self) -> str:
        return f"GAME_RULE({format_expr(self.text)})"


@dataclass
class GameSpec:
    name: str


@dataclass(frozen=True)
class RunFile(Instruction):
    path: str

    def __str__(self) -> str:
        return f"CALL({self.path!r})"


@dataclass(frozen=True)
class FileAttach(Instruction):
    path: Expression

    def __str__(self) -> str:
        return f"FILE({format_expr(self.path)})"


@dataclass(frozen=True)
class Break(Instruction):
    def __str__(self) -> str:
        return "BREAK"


@dataclass(frozen=True)
class Continue(Instruction):
    def __str__(self) -> str:
        return "CONTINUE"


@dataclass(frozen=True)
class SwitchBlock(Instruction):
    condition: Expression
    cases: list[tuple[list[Expression], list[object]]]
    default_body: list[object] | None = None

    def __str__(self) -> str:
        return f"SWITCH({format_expr(self.condition)})"


@dataclass(frozen=True)
class MatchBlock(Instruction):
    condition: Expression
    cases: list[tuple[list[Expression], list[object]]]
    default_body: list[object] | None = None
    variables: list[tuple[str, str]] | None = None  # (variable_name, pattern_position)

    def __str__(self) -> str:
        return f"MATCH({format_expr(self.condition)})"


@dataclass(frozen=True)
class AsyncForBlock(Instruction):
    item_name: str
    collection: Expression
    body: list[object]

    def __str__(self) -> str:
        return f"ASYNC_FOR({self.item_name} in {format_expr(self.collection)})"


@dataclass(frozen=True)
class AsyncWithBlock(Instruction):
    resource: Expression
    body: list[object]
    variable_name: str = ""

    def __str__(self) -> str:
        return f"ASYNC_WITH({format_expr(self.resource)})"


@dataclass(frozen=True)
class TryBlock(Instruction):
    body: list[object]
    except_body: list[object]
    finally_body: list[object] = field(default_factory=list)
    variable_name: str = ""

    def __str__(self) -> str:
        return "TRY"


@dataclass(frozen=True)
class WithBlock(Instruction):
    body: list[object]
    resource: Expression
    variable_name: str = ""
    close_action: str = "close"

    def __str__(self) -> str:
        return f"WITH({format_expr(self.resource)} as {self.variable_name})"


@dataclass(frozen=True)
class ErrorDef(Instruction):
    name: str

    def __str__(self) -> str:
        return f"ERROR_DEF({self.name})"


@dataclass(frozen=True)
class OperatorOverloadDef(Instruction):
    operator: str
    blueprint_name: str
    param1: str
    param2: str
    body: list[object]

    def __str__(self) -> str:
        return f"OVERLOAD({self.operator} for {self.blueprint_name})"


@dataclass(frozen=True)
class SetLiteral:
    values: list[Expression]

    def __str__(self) -> str:
        return f"{{{' '.join(format_expr(v) for v in self.values)}}}"


@dataclass(frozen=True)
class TupleLiteral:
    values: list[Expression]

    def __str__(self) -> str:
        return f"({' '.join(format_expr(v) for v in self.values)})"


@dataclass(frozen=True)
class Lambda:
    params: list[str]
    body: object

    def __str__(self) -> str:
        return f"LAMBDA({', '.join(self.params)})"


@dataclass(frozen=True)
class Comprehension:
    expr: Expression
    item_var: str
    collection: Expression
    filter_expr: object | None = None
    is_dict: bool = False
    key_expr: Expression | None = None

    def __str__(self) -> str:
        suffix = f" if {self.filter_expr}" if self.filter_expr else ""
        if self.is_dict and self.key_expr is not None:
            return f"{{{format_expr(self.key_expr)}: {format_expr(self.expr)} for {self.item_var} in {format_expr(self.collection)}{suffix}}}"
        return f"[{format_expr(self.expr)} for {self.item_var} in {format_expr(self.collection)}{suffix}]"


@dataclass(frozen=True)
class MapOver(Instruction):
    expr: Expression
    collection: Expression
    result_name: str

    def __str__(self) -> str:
        return f"MAP({format_expr(self.collection)} as {self.result_name})"


@dataclass(frozen=True)
class FilterItems(Instruction):
    condition: Expression
    collection: Expression
    result_name: str

    def __str__(self) -> str:
        return f"FILTER({format_expr(self.collection)} as {self.result_name})"


@dataclass(frozen=True)
class ReduceItems(Instruction):
    expr: Expression
    collection: Expression
    initial: Expression
    result_name: str

    def __str__(self) -> str:
        return f"REDUCE({format_expr(self.collection)} as {self.result_name})"


@dataclass(frozen=True)
class ReadInput(Instruction):
    prompt: Expression
    result_name: str = ""

    def __str__(self) -> str:
        return f"READ_INPUT({format_expr(self.prompt)} as {self.result_name})"


@dataclass(frozen=True)
class RaiseError(Instruction):
    message: Expression
    error_type: str = ""

    def __str__(self) -> str:
        return f"RAISE({format_expr(self.message)})"


@dataclass(frozen=True)
class AssertTrue(Instruction):
    condition_text: str
    message: Expression

    def __str__(self) -> str:
        return f"ASSERT({self.condition_text}, {format_expr(self.message)})"


@dataclass(frozen=True)
class GetArgs(Instruction):
    result_name: str

    def __str__(self) -> str:
        return f"GET_ARGS as {self.result_name}"


@dataclass(frozen=True)
class GetEnv(Instruction):
    var_name: str
    result_name: str

    def __str__(self) -> str:
        return f"GET_ENV({self.var_name}) as {self.result_name}"


def format_expr(expr: Expression) -> str:
    if isinstance(expr, Reference):
        return expr.name
    if isinstance(expr, BinaryOp):
        return f"{expr.op}({format_expr(expr.left)}, {format_expr(expr.right)})"
    if isinstance(expr, UnaryOp):
        return f"{expr.op}({format_expr(expr.right)})"
    if isinstance(expr, Access):
        return f"{format_expr(expr.target)}[{format_expr(expr.key)}]"
    if isinstance(expr, SliceOf):
        return f"{format_expr(expr.target)}[{format_expr(expr.start)}:{format_expr(expr.end)}]"
    if isinstance(expr, LengthOf):
        return f"length({format_expr(expr.value)})"
    if isinstance(expr, Lambda):
        return str(expr)
    if isinstance(expr, Comprehension):
        return str(expr)
    if isinstance(expr, SetLiteral):
        return str(expr)
    if isinstance(expr, TupleLiteral):
        return str(expr)
    if isinstance(expr, TernaryExpr):
        return f"if({format_expr(expr.true_expr)}, {format_expr(expr.false_expr)})"
    if isinstance(expr, WalrusExpr):
        return f"({expr.name} := {format_expr(expr.value)})"
    return repr(expr) if isinstance(expr, str) else str(expr)
