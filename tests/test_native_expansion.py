from pathlib import Path
from tempfile import TemporaryDirectory

from angis.ir import Await, CreateObject, EventBlock, FunctionCall, Spawn, UseStdLibAction
from angis.parser import parse, parse_file
from angis.interpreter import Interpreter
from angis.transpile import transpile


def run(code: str) -> Interpreter:
    interp = Interpreter()
    interp.run(parse(code))
    return interp


def test_validation_phrases_are_native_actions():
    code = '''
check if "me@example.com" is an email as email_ok
check if "https://example.com/a b" is a url as url_ok
check if "hello" is not empty as filled
check if 7 is between 1 and 10 as in_range
check if "abc123" matches "^[a-z]+\\d+$" as matches
'''
    interp = run(code)
    assert interp.variables["email_ok"] is True
    assert interp.variables["url_ok"] is True
    assert interp.variables["filled"] is True
    assert interp.variables["in_range"] is True
    assert interp.variables["matches"] is True


def test_more_stdlib_native_phrases_for_url_path_random_and_text():
    code = '''
encode url "hello world" as encoded
parse url "https://example.com:443/path?q=1" as parts
resolve path "." as here
get random decimal between 1 and 2 as decimal
flip coin as coin
get words of "one two three" as words
slugify "Hello Angis World!" as slug
reverse text "abc" as backwards
'''
    interp = run(code)
    assert interp.variables["encoded"] == "hello%20world"
    assert interp.variables["parts"]["host"] == "example.com"
    assert interp.variables["parts"]["path"] == "/path"
    assert isinstance(interp.variables["here"], str)
    assert 1 <= interp.variables["decimal"] <= 2
    assert isinstance(interp.variables["coin"], bool)
    assert interp.variables["words"] == ["one", "two", "three"]
    assert interp.variables["slug"] == "hello-angis-world"
    assert interp.variables["backwards"] == "cba"


def test_structured_object_helpers_are_native():
    code = '''
define blueprint Person with name: "unknown", age: 0
create Person named ada with name: "Ada", age: 36
create Person named ada2 with name: "Ada", age: 36
clone object ada as ada_copy
compare object ada to ada2 as same
list object fields ada as fields
'''
    interp = run(code)
    assert interp.variables["ada_copy"] == {"name": "Ada", "age": 36}
    assert interp.variables["same"] is True
    assert interp.variables["fields"] == ["name", "age"]


def test_app_widget_primitives_keep_properties():
    instructions = parse('''
app "Native Widgets"
create input named email at x 10 y 20 with placeholder "email"
create slider named volume at x 20 y 30 from 0 to 100 value 50
create checkbox named agree at x 30 y 40 checked with text "Agree"
''')
    created = [item for item in instructions if isinstance(item, CreateObject)]
    assert [item.kind for item in created] == ["input", "slider", "checkbox"]
    interp = Interpreter()
    interp.run(instructions)
    objects = {obj.name: obj for obj in interp.app.objects}
    assert objects["email"].properties["placeholder"] == "email"
    assert objects["volume"].properties == {"min": 0, "max": 100, "value": 50}
    assert objects["agree"].properties["checked"] is True
    assert objects["agree"].text == "Agree"


def test_module_specific_import_phrase_stays_angis_native():
    with TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        (base / "math_tools.angis").write_text(
            '''
define double with value:
    return value * 2
''',
            encoding="utf-8",
        )
        main = base / "main.angis"
        main.write_text(
            '''
use function double from module math_tools.angis
call double with 6 as doubled
''',
            encoding="utf-8",
        )

        instructions = parse_file(main)
        interp = Interpreter()
        interp.run(instructions)

    assert any(isinstance(item, FunctionCall) and item.name == "double" for item in instructions)
    assert interp.variables["doubled"] == 12


def test_new_native_expansion_tests_do_not_teach_python_escape_hatch():
    text = Path(__file__).read_text(encoding="utf-8").lower()
    assert "from " + "python" not in text
    assert "python" + "import" not in text


def test_debug_trace_is_native_action_and_transpiles():
    instructions = parse('''
set x to 1
show debug trace as trace
''')
    assert isinstance(instructions[-1], UseStdLibAction)
    interp = Interpreter()
    interp.run(instructions)
    assert isinstance(interp.variables["trace"], dict)
    assert "variables" in interp.variables["trace"]
    py = transpile(instructions)
    assert "_stdlib_debug_trace" in py


def test_code_anything_native_aliases_for_database_networking_and_packages(tmp_path):
    db_path = tmp_path / "people.db"
    package_path = tmp_path / "bundle"
    instructions = parse(f'''
create database file "{db_path}" named people_db
run query "create table people(name text)" on people_db
run query "insert into people(name) values ('Ada')" on people_db
run query "select name from people" on people_db as rows
send get request to https://example.com/api as response
build app package in folder "{package_path}"
''')
    assert instructions[0].__class__.__name__ == "OpenDatabase"
    assert instructions[3].__class__.__name__ == "ExecuteSql"
    assert instructions[4].__class__.__name__ == "HttpRequest"
    assert instructions[5].__class__.__name__ == "PackageApp"

    interp = Interpreter()
    interp.run(instructions[:4])
    assert interp.variables["rows"] == [{"name": "Ada"}]


def test_advanced_data_structure_native_phrases_are_runtime_actions():
    code = '''
make range from 1 to 3 as nums
extend nums with [4, 5] as more_nums
set profile to {name: "Ada", age: 36}
put key language in profile to "Angis" as updated_profile
remove key age from updated_profile as public_profile
'''
    interp = run(code)
    assert interp.variables["nums"] == [1, 2, 3]
    assert interp.variables["more_nums"] == [1, 2, 3, 4, 5]
    assert interp.variables["updated_profile"] == {"name": "Ada", "age": 36, "language": "Angis"}
    assert interp.variables["public_profile"] == {"name": "Ada", "language": "Angis"}


def test_code_anything_native_system_crypto_and_encoding(monkeypatch):
    monkeypatch.setenv("ANGIS_TEST_ENV", "ready")
    code = '''
encode text "hello" as base64 as encoded
base64 decode encoded as decoded
hash text "hello" with sha256 as digest
get environment variable "ANGIS_TEST_ENV" as env_value
get system platform as platform_name
get system architecture as arch
'''
    interp = run(code)
    assert interp.variables["encoded"] == "aGVsbG8="
    assert interp.variables["decoded"] == "hello"
    assert interp.variables["digest"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert interp.variables["env_value"] == "ready"
    assert isinstance(interp.variables["platform_name"], str) and interp.variables["platform_name"]
    assert isinstance(interp.variables["arch"], str) and interp.variables["arch"]
    py = transpile(parse(code))
    assert "_stdlib_encoding_base64_encode" in py
    assert "_stdlib_crypto_hash" in py


def test_code_anything_native_file_json_regex_and_uuid(tmp_path):
    data_file = tmp_path / "note.txt"
    code = f'''
write text "hello" to file "{data_file}" as wrote
append text " world" to file "{data_file}" as appended
read file "{data_file}" as contents
check if file "{data_file}" exists as exists
list files in folder "{tmp_path}" as files
parse json "{{\"name\": \"Ada\", \"age\": 36}}" as profile
turn profile into json as json_text
find pattern "\\d+" in "abc123" as digits
replace pattern "\\d+" in "abc123" with "456" as replaced
make uuid as identifier
'''
    interp = run(code)
    assert interp.variables["contents"] == "hello world\n"
    assert interp.variables["exists"] is True
    assert any(item["name"] == "note.txt" for item in interp.variables["files"])
    assert interp.variables["profile"] == {"age": 36, "name": "Ada"}
    assert interp.variables["json_text"] == '{"age": 36, "name": "Ada"}'
    assert interp.variables["digits"] == "123"
    assert interp.variables["replaced"] == "abc456"
    assert len(interp.variables["identifier"]) == 36
    py = transpile(parse(code))
    assert "_stdlib_file_write" in py
    assert "_stdlib_json_parse" in py
    assert "_stdlib_text_regex_search" in py
    assert "_stdlib_id_uuid" in py


def test_code_anything_gui_async_imports_network_security_and_more_stdlib(tmp_path):
    helper = tmp_path / "helpers.angis"
    helper.write_text(
        '''
define triple with value:
    return value * 3
''',
        encoding="utf-8",
    )
    safe_file = tmp_path / "safe.txt"
    code = f'''
app "Everything App"
create label named greeting at x 10 y 20 with text "Hello"
create button named save at x 30 y 40 with text "Save"
define slow_double with value:
    return value * 2
run slow_double in background with 21 as job
wait for job as doubled
use everything from module "{helper}" as helpers
call helpers_triple with 7 as tripled
check if path "{safe_file}" is inside folder "{tmp_path}" as safe_path
redact secrets in text "token=abc password=hunter2 email=a@example.com" as redacted
check if port 127.0.0.1:1 is open as port_open
get median of [3, 1, 2] as median_value
get standard deviation of [2, 4, 4, 4, 5, 5, 7, 9] as deviation
'''
    main = tmp_path / "main.angis"
    main.write_text(code, encoding="utf-8")
    instructions = parse_file(main)
    created = [item for item in instructions if isinstance(item, CreateObject)]
    assert [item.kind for item in created] == ["label", "button"]
    assert any(isinstance(item, Spawn) and item.name == "slow_double" for item in instructions)
    assert any(isinstance(item, Await) and item.target == "job" for item in instructions)
    interp = Interpreter()
    interp.run(instructions)
    objects = {obj.name: obj for obj in interp.app.objects}
    assert objects["greeting"].text == "Hello"
    assert objects["save"].text == "Save"
    assert interp.variables["doubled"] == 42
    assert interp.variables["tripled"] == 21
    assert interp.variables["safe_path"] is True
    assert "[REDACTED]" in interp.variables["redacted"]
    assert interp.variables["port_open"] is False
    assert interp.variables["median_value"] == 2
    assert round(interp.variables["deviation"], 5) == 2.0
    py = transpile(instructions)
    assert "_stdlib_security_path_inside" in py
    assert "_stdlib_network_port_open" in py
    assert "_stdlib_statistics_median" in py


def test_code_anything_web_package_permissions_tests_deploy_and_game_graphics(tmp_path):
    deploy_folder = tmp_path / "dist"
    code = f'''
app "Full Stack Angis"
create button named save at x 10 y 20 with text "Save"
when save clicked:
    set clicked to true
create circle named ball at x 40 y 50 size 24 color blue
create rectangle named wall at x 0 y 100 width 200 height 20 color gray
define web route get "/hello" returning "hello" as hello_route
create package manifest named "full-stack-angis" version "1.0.0" as manifest
request permission file read for path "{tmp_path}" as read_permission
make deployment plan for app "Full Stack Angis" to folder "{deploy_folder}" as deploy_plan
test that 2 equals 2 as equality_ok
test that "Angis" contains "gis" as contains_ok
'''
    instructions = parse(code)
    created = [item for item in instructions if isinstance(item, CreateObject)]
    events = [item for item in instructions if isinstance(item, EventBlock)]
    assert [item.kind for item in created] == ["button", "circle", "rectangle"]
    assert events and events[0].kind == "button" and events[0].name == "save"

    interp = Interpreter()
    interp.run(instructions)
    objects = {obj.name: obj for obj in interp.app.objects}
    assert objects["ball"].properties["size"] == 24
    assert objects["ball"].properties["color"] == "blue"
    assert objects["wall"].properties["width"] == 200
    assert interp.variables["hello_route"] == {"method": "GET", "path": "/hello", "response": "hello"}
    assert interp.variables["manifest"]["name"] == "full-stack-angis"
    assert interp.variables["manifest"]["version"] == "1.0.0"
    assert interp.variables["read_permission"]["allowed"] is True
    assert interp.variables["deploy_plan"]["app"] == "Full Stack Angis"
    assert interp.variables["deploy_plan"]["target"] == str(deploy_folder)
    assert interp.variables["equality_ok"] is True
    assert interp.variables["contains_ok"] is True
    py = transpile(instructions)
    assert "_stdlib_web_route" in py
    assert "_stdlib_package_manifest" in py
    assert "_stdlib_permission_request" in py
    assert "_stdlib_deploy_plan" in py
    assert "_stdlib_testing_equals" in py
