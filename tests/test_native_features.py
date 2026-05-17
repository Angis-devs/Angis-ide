from angis.parser import parse
from angis.interpreter import Interpreter
from angis.intents import parse_atom, parse_expression
from angis.ir import SetLiteral, TupleLiteral, Comprehension, Lambda, TernaryExpr, WalrusExpr


def test_set_of_literal():
    result = parse_atom("set of 1, 2, 3")
    assert isinstance(result, SetLiteral)
    assert len(result.values) == 3


def test_tuple_of_literal():
    result = parse_atom("tuple of 1, 2, 3")
    assert isinstance(result, TupleLiteral)
    assert len(result.values) == 3


def test_set_of_evaluates():
    code = """
set s to set of 1, 2, 3
show s
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    s = interp.variables.get("s")
    assert isinstance(s, set)
    assert s == {1, 2, 3}


def test_tuple_of_evaluates():
    code = """
set t to tuple of 1, 2, 3
show t
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    t = interp.variables.get("t")
    assert isinstance(t, tuple)
    assert t == (1, 2, 3)


def test_natural_comprehension():
    result = parse_atom("for each x in items collect x * 2")
    assert isinstance(result, Comprehension)
    assert result.item_var == "x"


def test_natural_comprehension_with_filter():
    result = parse_atom("for each x in items get x if x > 0")
    assert isinstance(result, Comprehension)
    assert result.filter_expr is not None


def test_natural_comprehension_evaluates():
    code = """
set items to [1, 2, 3, 4, 5]
set doubled to for each x in items collect x * 2
show doubled
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    doubled = interp.variables.get("doubled")
    assert doubled == [2, 4, 6, 8, 10]


def test_natural_comprehension_with_filter_evaluates():
    code = """
set items to [1, 2, 3, 4, 5, 6]
set evens to for each x in items get x if x % 2 equals 0
show evens
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    evens = interp.variables.get("evens")
    assert evens == [2, 4, 6]


def test_lambda_evaluates():
    code = """
set double to lambda x into x * 2
call double with 5 as result
show result
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    result = interp.variables.get("result")
    assert result == 10


def test_lambda_multi_param():
    code = """
set add to lambda a, b into a + b
call add with 3, 7 as result
show result
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    result = interp.variables.get("result")
    assert result == 10


def test_operator_overload():
    code = """
define blueprint Point with x: 0, y: 0

+ for Point with a, b:
    return a.x + b.x, a.y + b.y

create Point named p1 with x: 1, y: 2
create Point named p2 with x: 3, y: 4
set p3 to p1 + p2
show p3
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    p3 = interp.variables.get("p3")
    assert isinstance(p3, tuple)
    assert p3 == (4, 6)


def test_operator_overload_mul():
    code = """
define blueprint Vec with x: 0, y: 0

* for Vec with a, b:
    return a.x * b.x, a.y * b.y

create Vec named v1 with x: 2, y: 3
create Vec named v2 with x: 5, y: 7
set v3 to v1 * v2
show v3
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)
    v3 = interp.variables.get("v3")
    assert isinstance(v3, tuple)
    assert v3 == (10, 21)


def test_set_from_interpreter():
    interp = Interpreter()
    ast = parse('set s to set of 1, 2, 3\n')
    interp.run(ast)
    assert interp.variables["s"] == {1, 2, 3}


def test_tuple_from_interpreter():
    interp = Interpreter()
    ast = parse('set t to tuple of 1, 2, 3\n')
    interp.run(ast)
    assert interp.variables["t"] == (1, 2, 3)


def test_for_each_collect():
    interp = Interpreter()
    ast = parse('set items to [1, 2, 3]\nset r to for each x in items collect x + 10\n')
    interp.run(ast)
    assert interp.variables["r"] == [11, 12, 13]


def test_ternary_expression_parses():
    result = parse_expression("a if b else c")
    assert isinstance(result, TernaryExpr)


def test_ternary_expression_evaluates():
    code = """
set x to 5
set y to "yes" if x > 3 else "no"
show y
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["y"] == "yes"
    assert out[0] == "yes"


def test_ternary_expression_evaluates_false():
    code = """
set x to 1
set y to "yes" if x > 3 else "no"
show y
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["y"] == "no"
    assert out[0] == "no"


def test_walrus_expression_parses():
    result = parse_expression("(y := 5)")
    assert isinstance(result, WalrusExpr)
    assert result.name == "y"


def test_walrus_expression_evaluates():
    code = """
set x to (y := 5) + 3
show x
show y
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["x"] == 8
    assert interp.variables["y"] == 5


def test_match_block_evaluates():
    code = """
set x to 2
match x:
    case 1:
        show "one"
    case 2:
        show "two"
    default:
        show "other"
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert out == ["two"]


def test_match_block_default():
    code = """
set x to 99
match x:
    case 1:
        show "one"
    case 2:
        show "two"
    default:
        show "other"
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert out == ["other"]


def test_enhanced_param_types():
    code = """
define process with items: list[int]:
    show items
set data to [1, 2, 3]
call process with data as _
"""
    ast = parse(code)
    interp = Interpreter()
    interp.run(ast)


def test_blueprint_init_evaluates():
    code = """
define blueprint Player with name: "", health: 0

on create for Player with name and health:
    set self.health to health * 2

create Player named hero with name: "Ada", health: 10
show hero
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    hero = interp.variables.get("hero")
    assert hero is not None
    assert hero.get("health") == 20
    assert hero.get("name") == "Ada"


def test_decorator_parses():
    code = """
@log
define greet with name:
    show name
"""
    ast = parse(code)
    assert len(ast) == 1
    assert ast[0].decorators == ["log"]


def test_multiple_decorators():
    code = """
@log
@timed
define process with value:
    show value
"""
    ast = parse(code)
    assert len(ast) == 1
    assert ast[0].decorators == ["log", "timed"]


def test_python_eval_expression():
    code = 'set result to python(len([1,2,3]))\nshow result\n'
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["result"] == 3


def test_python_eval_inline_syntax():
    code = 'set x to 5\nset y to 3\nset result to {{py: x * y + 10}}\nshow result\n'
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["result"] == 25


def test_python_exec_statement():
    code = 'run python: result = 42\nshow result\n'
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["result"] == 42


def test_python_module_import_and_call():
    code = """
import python math as math
set result to python(math.sqrt(81))
show result
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["result"] == 9.0


def test_python_eval_statement_pattern():
    code = """
import python json as json
eval python json.dumps({"a": 1}) as result
show result
"""
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert interp.variables["result"] == '{"a": 1}'


def test_python_inline_in_output():
    code = 'set x to 10\nshow {{py: x * 2}}\n'
    ast = parse(code)
    interp = Interpreter()
    out = interp.run(ast)
    assert "20" in out
