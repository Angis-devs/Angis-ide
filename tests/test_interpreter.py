import unittest
import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory

from angis.errors import AngisRuntimeError, AngisSyntaxError
from angis.interpreter import Interpreter, run_source
from angis.ir import AppSpec, GameSpec
from angis.parser import parse, parse_file


class InterpreterTests(unittest.TestCase):
    def test_run_source_outputs_prints_and_math_results(self):
        output = run_source(
            '''
            say "hello"
            add 5 and 3
            calculate 9 / 3
            '''
        )

        self.assertEqual(output, ["hello", "8", "3"])

    def test_variables_are_supported(self):
        interpreter = Interpreter()
        output = interpreter.run(
            parse(
                """
                set x to 5
                make y equal 7
                set total to x + y * 2
                set wordTotal to x plus y times 2
                show x
                show total
                show wordTotal
                what is x plus y
                """
            )
        )

        self.assertEqual(interpreter.variables, {"x": 5, "y": 7, "total": 19, "wordTotal": 19})
        self.assertEqual(output, ["5", "19", "19", "12"])

    def test_expressions_work_in_conditions_and_loops(self):
        output = run_source(
            """
            Set, x to 2.
            Set, y to 3.
            Set, total to x * y + 4.
            Set, wordTotal to x times y plus 4.
            If, total is at least x + y:
                Show, total.
            If, wordTotal is same as total:
                Show, wordTotal.
            While, x plus y is less than 8:
                Add, 1 to x.
            Show, x.
            """
        )

        self.assertEqual(output, ["10", "10", "5"])

    def test_strings_are_supported_in_variables(self):
        output = run_source(
            """
            store "Ada Lovelace" as name
            tell me name
            """
        )

        self.assertEqual(output, ["Ada Lovelace"])

    def test_capitalized_bare_word_is_text(self):
        output = run_source(
            """
            Set, name to Ada.
            Tell me name.
            """
        )

        self.assertEqual(output, ["Ada"])

    def test_boolean_values_work_in_variables_conditions_and_maps(self):
        output = run_source(
            """
            Set, ready to true.
            Set, visible to off.
            Create dictionary named player with alive: yes, hidden: no.
            If ready is true:
                Say, ready.
            If visible is false:
                Say, hidden.
            If player.alive is yes and player.hidden is no:
                Say, player active.
            Show, ready.
            Show, visible.
            """
        )

        self.assertEqual(output, ["ready", "hidden", "player active", "True", "False"])

    def test_contains_and_truthy_conditions_work(self):
        output = run_source(
            """
            Create list named inventory with wood, stone.
            Create dictionary named player with name: Ada, score: 42.
            Set, phrase to hello world.
            Set, ready to true.
            If inventory contains wood:
                Say, list contains.
            If player has score:
                Say, map has.
            If phrase contains world:
                Say, text contains.
            If ready:
                Say, ready.
            If not ready:
                Say, not printed.
            If shield is not in inventory:
                Say, no shield.
            """
        )

        self.assertEqual(output, ["list contains", "map has", "text contains", "ready", "no shield"])

    def test_natural_data_access_and_assignment_work(self):
        output = run_source(
            """
            Create dictionary named player with name: Ada, score: 42.
            Create list named inventory with wood, stone.
            Show score of player.
            Show item 0 of inventory.
            Set score of player to score of player plus 10.
            Set item 0 of inventory to sword.
            Give player health 10.
            Increase health of player by 5.
            Take 2 from health of player.
            Create list named numbers with 10, 20.
            Add 3 to item 1 of numbers.
            Take 1 from item 1 of numbers.
            Show score of player.
            Show item 0 of inventory.
            Show health of player.
            Show item 1 of numbers.
            If score of player is greater than 50:
                Say, score changed.
            If item 0 of inventory is sword:
                Say, item changed.
            Store Ada Lovelace as name.
            Store "picture.png" as fileName.
            If health of player is between 10 and 20:
                Say, health in range.
            If name starts with Ada:
                Say, name starts.
            If fileName ends with png:
                Say, file extension.
            If health of player is not between 1 and 5:
                Say, health outside low range.
            If name does not start with Bob:
                Say, not Bob.
            If fileName does not end with jpg:
                Say, not jpg.
            If name starts with ada ignoring case:
                Say, case insensitive.
            """
        )

        self.assertEqual(
            output,
            [
                "42",
                "wood",
                "52",
                "sword",
                "13",
                "22",
                "score changed",
                "item changed",
                "health in range",
                "name starts",
                "file extension",
                "health outside low range",
                "not Bob",
                "not jpg",
                "case insensitive",
            ],
        )

    def test_list_and_dictionary_literals_work(self):
        output = run_source(
            """
            Set inventory to [wood, stone, 3].
            Set player to {name: Ada, score: 42, items: [key, map]}.
            Show item 0 of inventory.
            Show item 2 of inventory.
            Show name of player.
            Show player.items[1].
            If inventory contains stone:
                Say, literal list works.
            If player has score:
                Say, literal map works.
            """
        )

        self.assertEqual(output, ["wood", "3", "Ada", "map", "literal list works", "literal map works"])

    def test_length_expressions_work(self):
        output = run_source(
            """
            Set inventory to [wood, stone, iron].
            Set player to {name: Ada, score: 42}.
            Set title to Angis.
            Show length of inventory.
            Show count of player.
            Show number of letters in title.
            Set total to count of inventory plus 1.
            Show total.
            Show first item of inventory.
            Show second item of inventory.
            Show last item of inventory.
            Show first letter of title.
            Show last letter of title.
            Show first 2 items of inventory.
            Show items 1 through 2 of inventory.
            Show letters 0 to 3 of title.
            Set emptyList to [].
            Set emptyMap to {}.
            Set emptyText to "".
            If number of items in inventory is 3:
                Say, count works.
            If inventory is not empty:
                Say, inventory has items.
            If emptyList is empty:
                Say, list empty.
            If emptyMap is empty:
                Say, map empty.
            If emptyText is blank:
                Say, text blank.
            """
        )

        self.assertEqual(
            output,
            [
                "3",
                "2",
                "5",
                "4",
                "wood",
                "stone",
                "iron",
                "A",
                "s",
                "['wood', 'stone']",
                "['stone', 'iron']",
                "Ang",
                "count works",
                "inventory has items",
                "list empty",
                "map empty",
                "text blank",
            ],
        )

    def test_natural_text_split_join_and_replace_work(self):
        output = run_source(
            """
            Set title to hello brave world.
            Split title by space as words.
            Join words with dash as slug.
            Replace brave in title with bright as renamed.
            Show first item of words.
            Show slug.
            Show renamed.
            """
        )

        self.assertEqual(output, ["hello", "hello-brave-world", "hello bright world"])

    def test_natural_list_transforms_work(self):
        output = run_source(
            """
            Set scores to [3, 1, 2, 1].
            Sort scores as sortedScores.
            Reverse scores as reversedScores.
            Unique scores as uniqueScores.
            Pick random item from scores as chosenScore.
            Show sortedScores.
            Show reversedScores.
            Show uniqueScores.
            If scores contains chosenScore:
                Say, random choice works.
            """
        )

        self.assertEqual(output[:3], ["[1, 1, 2, 3]", "[1, 2, 1, 3]", "[3, 1, 2]"])
        self.assertEqual(output[3], "random choice works")

    def test_natural_map_transforms_work(self):
        output = run_source(
            """
            Set player to {name: Ada, score: 42}.
            Set bonus to {level: 3}.
            Get score from player as playerScore.
            Get keys from player as playerKeys.
            Get values from player as playerValues.
            Merge player with bonus as updatedPlayer.
            Show playerScore.
            Show playerKeys.
            Show playerValues.
            Show level of updatedPlayer.
            If updatedPlayer has level:
                Say, merge works.
            """
        )

        self.assertEqual(output, ["42", "['name', 'score']", "['Ada', 42]", "3", "merge works"])

    def test_natural_file_actions_work(self):
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.txt"
            output_path = Path(temp_dir) / "output.txt"
            source.write_text("hello from file", encoding="utf-8")

            output = run_source(
                f"""
                Read file {source} as sourceText.
                Write copied text to file {output_path} as writeResult.
                Get info for file {output_path} as fileInfo.
                Show sourceText.
                Show writeResult.
                Show name of fileInfo.
                """
            )

        self.assertEqual(output, ["hello from file", "Wrote file output.txt", "output.txt"])

    def test_natural_csv_data_actions_work(self):
        with TemporaryDirectory() as temp_dir:
            table = Path(temp_dir) / "items.csv"
            table.write_text("name,score\nAda,42\nGrace,99\n", encoding="utf-8")

            output = run_source(
                f"""
                Read CSV file {table} as rows.
                Count rows in rows as rowCount.
                Get column name from rows as names.
                Keep rows where name is Ada as adaRows.
                Show rowCount.
                Show first item of names.
                Show score of first item of adaRows.
                """
            )

        self.assertEqual(output, ["2", "Ada", "42"])

    def test_natural_json_actions_work(self):
        output = run_source(
            """
            Parse JSON {"score": 42, "name": "Ada"} as data.
            Turn data into JSON as packed.
            Show score of data.
            If packed contains score:
                Say, json works.
            """
        )

        self.assertEqual(output, ["42", "json works"])

    def test_natural_math_actions_work(self):
        output = run_source(
            """
            Round 3.7 as rounded.
            Floor 3.7 as floored.
            Ceil 3.2 as ceiled.
            Absolute -5 as positive.
            Raise 2 to power 8 as powered.
            Clamp 14 between 1 and 10 as clamped.
            Pick random number between 1 and 6 as roll.
            Show rounded.
            Show floored.
            Show ceiled.
            Show positive.
            Show powered.
            Show clamped.
            If roll is between 1 and 6:
                Say, random range works.
            """
        )

        self.assertEqual(output, ["4", "3", "4", "5", "256", "10", "random range works"])

    def test_natural_path_actions_work(self):
        output = run_source(
            """
            Get file name from assets/items.csv as pathName.
            Get file extension from assets/items.csv as pathExtension.
            Get folder from assets/items.csv as pathFolder.
            Get stem from assets/items.csv as pathStem.
            Join path assets with items.csv as joinedPath.
            Show pathName.
            Show pathExtension.
            Show pathStem.
            If joinedPath ends with items.csv:
                Say, path join works.
            """
        )

        self.assertEqual(output, ["items.csv", ".csv", "items", "path join works"])

    def test_natural_time_actions_work(self):
        output = run_source(
            """
            Get current time as nowText.
            Get timestamp as secondsNow.
            Get todays date as todayText.
            Add 3 days to today as dueDate.
            Subtract 2 days from today as pastDate.
            Show nowText.
            Show todayText.
            Show dueDate.
            Show pastDate.
            If secondsNow is greater than 0:
                Say, timestamp works.
            """
        )

        today = dt.date.today()
        self.assertEqual(len(output), 5)
        self.assertRegex(output[0], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(output[1], today.isoformat())
        self.assertEqual(output[2], (today + dt.timedelta(days=3)).isoformat())
        self.assertEqual(output[3], (today - dt.timedelta(days=2)).isoformat())
        self.assertEqual(output[4], "timestamp works")

    def test_unset_variable_raises_safe_error(self):
        with self.assertRaisesRegex(AngisRuntimeError, "has not been set"):
            run_source("show missing")

    def test_division_by_zero_is_rejected(self):
        with self.assertRaisesRegex(AngisRuntimeError, "divide by zero"):
            run_source("divide 4 by 0")

    def test_sentence_style_program_runs(self):
        output = run_source(
            """
            Say, hello from the Angis IDE.
            Print, output phrases work.
            Display, strings work.

            Set, x to 5.
            Make, y equal 8.
            Store, Ada Lovelace as name.

            Show, x.
            Tell me name.

            Add, 5 and 3.
            What is, x plus y.
            Calculate, 7 =6.
            Divide, 20 by 5.
            """
        )

        self.assertEqual(
            output,
            [
                "hello from the Angis IDE",
                "output phrases work",
                "strings work",
                "5",
                "Ada Lovelace",
                "8",
                "13",
                "42",
                "4",
            ],
        )

    def test_app_program_builds_app_spec(self):
        opened: list[AppSpec] = []
        output = run_source(
            """
            App, My First App.
            Scene, 3D world.
            Text, Hello inside the app.
            Button, Click me.
            """,
            app_runner=opened.append,
        )

        self.assertEqual(output, [])
        self.assertEqual(opened[0].title, "My First App")
        self.assertEqual(opened[0].scene, "3d world")
        self.assertEqual(opened[0].texts, ["Hello inside the app"])
        self.assertEqual(opened[0].buttons, ["Click me"])

    def test_app_program_reports_ready_without_app_runner(self):
        output = run_source(
            """
            App, My First App.
            Text, Hello inside the app.
            """
        )

        self.assertEqual(output, ["App ready: My First App"])

    def test_loading_screen_sets_app_paths(self):
        with TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "loading screen.png"
            audio = Path(temp_dir) / "loading-adieo.mp3"
            image.write_bytes(b"image")
            audio.write_bytes(b"audio")
            opened: list[AppSpec] = []

            output = run_source(
                f"""
                App, Loading Demo.
                Loding screen pickter {image} with adieo {audio} then open app.
                Text, App opened after loading.
                """,
                app_runner=opened.append,
            )

        self.assertEqual(output, [])
        self.assertEqual(opened[0].loading_image, str(image.resolve()))
        self.assertEqual(opened[0].loading_audio, str(audio.resolve()))
        self.assertEqual(opened[0].texts, ["App opened after loading"])

    def test_default_loading_screen_uses_project_assets(self):
        opened: list[AppSpec] = []
        output = run_source(
            """
            App, Loading Demo.
            Loding screen.
            """,
            app_runner=opened.append,
        )

        self.assertEqual(output, [])
        self.assertTrue(opened[0].loading_image.endswith("angis loading/loading screen.png"))
        self.assertTrue(opened[0].loading_audio.endswith("angis loading/loading-adieo.mp3"))

    def test_flappy_game_rules_open_game(self):
        opened: list[GameSpec] = []
        output = run_source(
            """
            Bird on screen.
            When clicked, bird goes up.
            Bird falls down.
            Add obstacles.
            If bird hits obstacle, end game.
            """,
            game_runner=opened.append,
        )

        self.assertEqual(output, [])
        self.assertEqual(opened[0].name, "Flappy Bird")

    def test_attach_file_reports_safe_file_info(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "note.txt"
            path.write_text("hello", encoding="utf-8")

            output = run_source(f"Attach file at {path}.")

        self.assertEqual(len(output), 1)
        self.assertIn("Attached file: note.txt (5 bytes)", output[0])

    def test_attach_file_to_window_adds_file_to_app(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "note.txt"
            path.write_text("hello", encoding="utf-8")
            opened: list[AppSpec] = []

            output = run_source(
                f"""
                App, File Window.
                Set file attach to window at x 20 y 80 z 0 from file {path}.
                """,
                app_runner=opened.append,
            )

        self.assertEqual(output, [])
        self.assertEqual(opened[0].files[0].name, "note.txt")
        self.assertEqual(opened[0].files[0].size, 5)
        self.assertEqual((opened[0].files[0].x, opened[0].files[0].y, opened[0].files[0].z), (20, 80, 0))
        self.assertEqual(opened[0].files[0].kind, "text")
        self.assertEqual(opened[0].files[0].preview, "hello")

    def test_custom_phrase_places_file_with_coordinate_slots(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset.txt"
            path.write_text("hello", encoding="utf-8")
            opened: list[AppSpec] = []
            output = run_source(
                f"""
                App, File Window.
                Define phrase place {{file:path}} at {{x:number}} {{y:number}} {{z:number}} means Attach file file to window at x x y y z z.
                Place {path} at 20 80 1.
                """,
                app_runner=opened.append,
            )

        self.assertEqual(output, [])
        self.assertEqual(opened[0].files[0].name, "asset.txt")
        self.assertEqual((opened[0].files[0].x, opened[0].files[0].y, opened[0].files[0].z), (20, 80, 1))

    def test_custom_phrase_places_file_with_point_slot(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset.txt"
            path.write_text("hello", encoding="utf-8")
            opened: list[AppSpec] = []
            output = run_source(
                f"""
                App, File Window.
                Define phrase place {{file:path}} at {{location:point}} means Attach file file to window at x location[0] y location[1] z location[2].
                Place {path} at (20, 80, 1).
                """,
                app_runner=opened.append,
            )

        self.assertEqual(output, [])
        self.assertEqual(opened[0].files[0].name, "asset.txt")
        self.assertEqual((opened[0].files[0].x, opened[0].files[0].y, opened[0].files[0].z), (20, 80, 1))

    def test_attach_missing_file_raises_safe_error(self):
        with self.assertRaisesRegex(AngisRuntimeError, "Could not locate file"):
            run_source("Attach file at /no/such/file.txt.")

    def test_repeat_if_and_add_to_variable(self):
        output = run_source(
            """
            Set, score to 0.
            Repeat, 3 times:
                Add, 1 to score.
            If, score is 3:
                Say, done.
                Show, score.
            """
        )

        self.assertEqual(output, ["done", "3"])

    def test_natural_variable_mutation_phrases_run(self):
        output = run_source(
            """
            Set score to 10.
            Take 2 from score.
            Decrease score by 1.
            Multiply score by 3.
            Double score.
            Divide score by 2.
            Cut score in half.
            Show score.
            """
        )

        self.assertEqual(output, ["10.5"])

    def test_variable_mutation_divide_by_zero_is_rejected(self):
        with self.assertRaisesRegex(AngisRuntimeError, "divide by zero"):
            run_source(
                """
                Set score to 10.
                Divide score by 0.
                """
            )

    def test_if_else_blocks(self):
        output = run_source(
            """
            Set, score to 2.
            If, score is at least 3:
                Say, winner.
            Else:
                Say, keep going.
            If, score is less than 3:
                Say, low.
            Otherwise:
                Say, high.
            """
        )

        self.assertEqual(output, ["keep going", "low"])

    def test_logical_conditions(self):
        output = run_source(
            """
            Set, score to 4.
            Set, lives to 2.
            If, score is at least 3 and lives is greater than 0:
                Say, keep playing.
            If, score is less than 3 or lives is 2:
                Say, backup condition.
            If, not score is less than 3:
                Say, not low.
            """
        )

        self.assertEqual(output, ["keep playing", "backup condition", "not low"])

    def test_while_loop_and_stronger_conditions(self):
        output = run_source(
            """
            Set, score to 0.
            While, score is less than 3:
                Add, 1 to score.
            If, score is at least 3:
                Say, reached.
            If, score is at most 3:
                Show, score.
            """
        )

        self.assertEqual(output, ["reached", "3"])

    def test_while_loop_has_safe_iteration_limit(self):
        with self.assertRaisesRegex(AngisRuntimeError, "While loop stopped"):
            run_source(
                """
                Set, score to 0.
                While, score is less than 1:
                    Say, looping.
                """
            )

    def test_for_each_loops_over_lists_and_restores_variable(self):
        output = run_source(
            """
            Create list named inventory with wood, stone, iron.
            Set, item to "outside".
            For each, item in inventory:
                Show, item.
            Show, item.
            """
        )

        self.assertEqual(output, ["wood", "stone", "iron", "outside"])

    def test_for_each_loops_over_data_rows(self):
        output = run_source(
            """
            Use json parse with text: [{"name":"Ada"},{"name":"Grace"}] as rows.
            For each, row in rows:
                Show, row.name.
            """
        )

        self.assertEqual(output, ["Ada", "Grace"])

    def test_natural_control_flow_wording_runs(self):
        output = run_source(
            """
            Create list named inventory with wood, stone.
            Set, score to 0.
            Do this 2 times:
                Add, 1 to score.
            If score is same as 2 then:
                Say, same.
            If score is bigger than 1:
                Say, bigger.
            If score is under 5:
                Say, under.
            As long as score is less than 3:
                Add, 1 to score.
            For every item from inventory:
                Show, item.
            Show, score.
            """
        )

        self.assertEqual(output, ["same", "bigger", "under", "wood", "stone", "3"])

    def test_direct_map_field_and_list_index_access(self):
        output = run_source(
            """
            Create dictionary named player with name: Ada, score: 42.
            Create list named inventory with wood, stone, iron.
            Use json parse with text: [{"name":"Ada"},{"name":"Grace"}] as rows.
            Set, firstItem to inventory[0].
            Set, playerName to player.name.
            Set, firstRowName to rows[0].name.
            Show, firstItem.
            Show, playerName.
            Show, firstRowName.
            """
        )

        self.assertEqual(output, ["wood", "Ada", "Ada"])

    def test_direct_map_field_and_list_index_assignment(self):
        output = run_source(
            """
            Create dictionary named player with name: Ada, score: 42.
            Create list named inventory with wood, stone, iron.
            Use json parse with text: [{"name":"Ada"},{"name":"Grace"}] as rows.
            Set, player.score to 50.
            Set, inventory[1] to diamond.
            Set, rows[0].name to Lovelace.
            Show, player.score.
            Show, inventory[1].
            Show, rows[0].name.
            """
        )

        self.assertEqual(output, ["50", "diamond", "Lovelace"])

    def test_natural_data_phrases_run(self):
        output = run_source(
            """
            Create dictionary named player with name: Ada, score: 42.
            Create list named inventory with wood.
            Put shield in inventory.
            Store potion inside inventory.
            Remove shield from inventory.
            Take potion out of inventory.
            Put key in inventory.
            Make player have score 10.
            Give player health 99.
            Set name of player to Grace.
            Remove field score from player.
            Get map has with value: player, key: score as hasScore.
            Clear player health.
            Get map has with value: player, key: health as hasHealth.
            Show, inventory[1].
            Show, hasScore.
            Show, hasHealth.
            Show, player.name.
            """
        )

        self.assertEqual(output, ["key", "False", "False", "Grace"])

    def test_remove_missing_list_item_has_safe_error(self):
        with self.assertRaisesRegex(AngisRuntimeError, "is not in list"):
            run_source(
                """
                Create list named inventory with wood.
                Remove stone from inventory.
                """
            )

    def test_remove_missing_property_has_safe_error(self):
        with self.assertRaisesRegex(AngisRuntimeError, "does not exist"):
            run_source(
                """
                Create dictionary named player with name: Ada.
                Remove field score from player.
                """
            )

    def test_functions_can_be_defined_and_called(self):
        output = run_source(
            """
            Define, greet:
                Say, hello.
            Call, greet.
            Call, greet.
            """
        )

        self.assertEqual(output, ["hello", "hello"])

    def test_functions_can_take_parameters(self):
        output = run_source(
            """
            Set, name to "outside".
            Define, greet with name:
                Show, name.
            Define, addPair with left and right:
                Set, total to left + right.
                Show, total.
            Call, greet with Ada.
            Call, addPair with 4, 6.
            Show, name.
            """
        )

        self.assertEqual(output, ["Ada", "10", "outside"])

    def test_functions_can_return_values(self):
        output = run_source(
            """
            Define, addPair with left and right:
                Return, left + right.
            Define, firstName with row:
                Return, row.name.
            Use json parse with text: {"name":"Ada"} as person.
            Call, addPair with 4, 6 as total.
            Call, firstName with person as name.
            Show, total.
            Show, name.
            """
        )

        self.assertEqual(output, ["10", "Ada"])

    def test_object_methods_can_change_object_properties(self):
        output = run_source(
            """
            Create dictionary named player with name: Ada, health: 10.
            Define method heal for player with amount:
                Set, self.health to self.health + amount.
                Return, self.health.
            Call, player.heal with 5 as healed.
            Show, healed.
            Show, player.health.
            """
        )

        self.assertEqual(output, ["15", "15"])

    def test_blueprints_create_typed_objects_with_methods(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, health: 10.
            Create Player named hero with name: Grace.
            Create Player named enemy with name: Boss, health: 30.

            Define method heal for Player with amount:
                Set, self.health to self.health + amount.
                Return, self.health.

            Call, hero.heal with 5 as heroHealth.
            Call, enemy.heal with 2 as enemyHealth.
            Show, hero.name.
            Show, heroHealth.
            Show, enemy.name.
            Show, enemyHealth.
            """
        )

        self.assertEqual(output, ["Grace", "15", "Boss", "32"])

    def test_custom_commands_create_user_wording(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Define command give points with target and amount:
                Set, target.score to target.score + amount.
                Return, target.score.

            Give points with hero, 3 as newScore.
            Show, hero.score.
            Give points with hero, 7.
            Show, hero.score.
            Show, newScore.
            """
        )

        self.assertEqual(output, ["3", "10", "3"])

    def test_custom_phrase_templates_create_slot_wording(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Define phrase give {amount} points to {target}:
                Set, target.score to target.score + amount.
                Return, target.score.

            Give 3 points to hero as firstScore.
            Give 7 points to hero.
            Show, firstScore.
            Show, hero.score.
            """
        )

        self.assertEqual(output, ["3", "10"])

    def test_custom_phrase_templates_can_run_before_definition(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Give 3 points to hero as firstScore.
            Give 7 points to hero.

            Define phrase give {amount} points to {target}:
                Set, target.score to target.score + amount.
                Return, target.score.

            Show, firstScore.
            Show, hero.score.
            """
        )

        self.assertEqual(output, ["3", "10"])

    def test_teach_angis_block_phrases_keep_user_language_flow(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Teach Angis bless {target:name} with {amount:number} bars to do:
                Set, target.score to target.score + amount.
                Return, target.score.

            Bless hero with 4 bars as firstBlessing.
            Bless hero with 6 bars.
            Show, firstBlessing.
            Show, hero.score.
            """
        )

        self.assertEqual(output, ["4", "10"])

    def test_custom_phrase_stdlib_actions_resolve_slot_variables(self):
        with TemporaryDirectory() as temp_dir:
            note = Path(temp_dir) / "note.txt"
            output = run_source(
                f"""
                Teach Angis stash {{content:text}} inside {{path:path}} to do:
                    Write text content to file path as wrote.
                    Return, wrote.

                Teach Angis pull from {{path:path}} to do:
                    Read file path as text.
                    Return, text.

                Stash hello custom flow inside {note} as writeResult.
                Pull from {note} as readResult.
                Show, writeResult.
                Show, readResult.
                """
            )

        self.assertEqual(output, ["Wrote file note.txt", "hello custom flow"])

    def test_inline_custom_phrases_accept_do_and_run_wording(self):
        output = run_source(
            """
            Teach Angis flex {message:text} to do Show, message.
            When I say double flex {message:text}, it runs Show, message then Show, message.

            Flex stay native.
            Double flex my language flow.
            """
        )

        self.assertEqual(output, ["stay native", "my language flow", "my language flow"])

    def test_custom_phrase_block_when_i_say_can_use_do_suffix(self):
        output = run_source(
            """
            When I say drop {line:text}, do:
                Show, line.

            Drop keep Angis custom.
            """
        )

        self.assertEqual(output, ["keep Angis custom"])

    def test_custom_phrase_templates_support_optional_words(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Define phrase give {amount} points [to] {target}:
                Set, target.score to target.score + amount.
                Return, target.score.

            Give 3 points to hero as firstScore.
            Give 7 points hero as secondScore.
            Show, firstScore.
            Show, secondScore.
            Show, hero.score.
            """
        )

        self.assertEqual(output, ["3", "10", "10"])

    def test_custom_phrase_templates_support_alternative_words(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Define phrase give {amount} points (to|for) {target}:
                Set, target.score to target.score + amount.
                Return, target.score.

            Give 3 points to hero as firstScore.
            Give 7 points for hero as secondScore.
            Show, firstScore.
            Show, secondScore.
            Show, hero.score.
            """
        )

        self.assertEqual(output, ["3", "10", "10"])

    def test_custom_phrase_templates_support_typed_slots(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Define phrase give {amount:number} points to {target:name}:
                Set, target.score to target.score + amount.
                Return, target.score.

            Define phrase note {message:text}:
                Show, message.

            Give 3 points to hero as score.
            Note hello from typed text.
            Show, score.
            Show, hero.score.
            """
        )

        self.assertEqual(output, ["hello from typed text", "3", "3"])

    def test_custom_phrase_templates_support_key_slots(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0, health: 10.
            Create Player named hero with name: Grace.

            Define phrase set {field:key} of {target:name} to {value}:
                Set, target[field] to value.

            Define phrase show {field:key} of {target:name}:
                Show, target[field].

            Set score of hero to 9.
            Set health of hero to 12.
            Show score of hero.
            Show health of hero.
            """
        )

        self.assertEqual(output, ["9", "12"])

    def test_custom_phrase_key_slots_can_address_nested_paths(self):
        output = run_source(
            """
            Use json parse with text: {"name":"Grace","stats":{"score":0,"health":10}} as hero.

            Define phrase set {field:key} of {target:name} to {value}:
                Set, target[field] to value.

            Define phrase show {field:key} of {target:name}:
                Show, target[field].

            Set stats.score of hero to 9.
            Set stats.health of hero to 12.
            Show stats.score of hero.
            Show stats.health of hero.
            Show, hero.stats.score.
            """
        )

        self.assertEqual(output, ["9", "12", "9"])

    def test_custom_phrase_templates_support_path_slots(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset file.txt"
            path.write_text("hello", encoding="utf-8")
            output = run_source(
                f"""
                Define phrase attach {{file:path}} means Attach file at file.
                Attach {path}.
                """
            )

        self.assertIn("Attached file", output[0])
        self.assertIn("asset file.txt", output[0])

    def test_custom_phrase_templates_ignore_sentence_punctuation(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Define phrase give {amount:number} points to {target:name}:
                Set, target.score to target.score + amount.
                Return, target.score.

            Give, 3 points to hero! as score.
            Show, score.
            Show, hero.score.
            """
        )

        self.assertEqual(output, ["3", "3"])

    def test_literal_phrase_templates_run_without_slots(self):
        output = run_source(
            """
            Define phrase start game:
                Say, started.
            Define phrase reset everything:
                Say, reset.

            Start game.
            Reset, everything!
            """
        )

        self.assertEqual(output, ["started", "reset"])

    def test_inline_phrase_definitions_run(self):
        output = run_source(
            """
            Define phrase start game means Say, started.
            Define phrase note {message:text} means Show, message.

            Start game.
            Note hello inline phrase.
            """
        )

        self.assertEqual(output, ["started", "hello inline phrase"])

    def test_teaching_phrase_definitions_run(self):
        output = run_source(
            """
            Create list named scores with 1, 2, 3.
            When I say shout {message:text}, it means Set loud to text uppercase with text: message and then Show loud.
            Teach Angis score count to mean Count length of scores as totalScores and then Show totalScores.
            When I say quiet {message:text}:
                Set quietText to text lowercase with text: message.
                Show quietText.

            Shout hello taught words.
            Score count.
            Quiet HELLO BLOCK.
            """
        )

        self.assertEqual(output, ["HELLO TAUGHT WORDS", "3", "hello block"])

    def test_namespaced_phrase_definitions_run(self):
        output = run_source(
            """
            Define phrase app.start means Say, started.
            Define phrase app.stop means Say, stopped.

            App start.
            app.stop.
            """
        )

        self.assertEqual(output, ["started", "stopped"])

    def test_inline_phrase_definitions_run_multiple_steps(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.
            Define phrase boost {target:name} means Set, target.score to target.score + 1 and then Show, target.score.
            Define phrase reset {target:name} means Set, target.score to 0 then Show, target.score.
            Define phrase mark {target:name} means Set, target.score to 5; Show, target.score.

            Boost hero.
            Boost hero.
            Reset hero.
            Mark hero.
            """
        )

        self.assertEqual(output, ["1", "2", "0", "5"])

    def test_custom_phrase_typed_number_slot_rejects_text(self):
        with self.assertRaises(AngisSyntaxError):
            run_source(
                """
                Blueprint Player with name: Ada, score: 0.
                Create Player named hero with name: Grace.

                Define phrase give {amount:number} points to {target:name}:
                    Set, target.score to target.score + amount.

                Give many points to hero.
                """
            )

    def test_custom_phrase_templates_can_override_builtin_words(self):
        output = run_source(
            """
            Blueprint Player with name: Ada, score: 0.
            Create Player named hero with name: Grace.

            Define phrase show stats for {target}:
                Show, target.name.
                Show, target.score.

            Show stats for hero.
            """
        )

        self.assertEqual(output, ["Grace", "0"])

    def test_function_argument_count_is_checked(self):
        with self.assertRaisesRegex(AngisRuntimeError, "expects 1 argument"):
            run_source(
                """
                Define, greet with name:
                    Show, name.
                Call, greet.
                """
            )

    def test_undefined_function_has_safe_error(self):
        with self.assertRaisesRegex(AngisRuntimeError, "has not been defined"):
            run_source("Call, missing.")

    def test_creator_runtime_builds_app_objects_and_events(self):
        with TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "city.png"
            image.write_bytes(b"not real png")
            opened: list[AppSpec] = []
            output = run_source(
                f"""
                App, Creator World.
                Scene, 3D world.
                Create player named hero at x 0 y 0 z 0.
                Create image named city at x 0 y -40 z 4 from file {image}.
                Create button named start with text Start Mission.
                When key w pressed:
                    Move hero forward by 1.
                When button start clicked:
                    Show text Mission started.
                """,
                app_runner=opened.append,
            )

        self.assertEqual(output, [])
        self.assertEqual(len(opened[0].objects), 3)
        self.assertIn("key:w", opened[0].events)
        self.assertIn("button:start", opened[0].events)

    def test_creator_image_path_resolves_against_base_path(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            image = base / "duck.png"
            image.write_bytes(b"not real png")
            opened: list[AppSpec] = []
            interpreter = Interpreter(app_runner=opened.append, base_path=base)
            output = interpreter.run(
                parse(
                    """
                    App, Picture Test.
                    Scene, canvas.
                    Create image named duck at x 10 y 20 z 0 from file duck.png.
                    """
                )
            )

            self.assertEqual(output, [])
            duck = opened[0].objects[0]
            self.assertEqual(duck.path, str(image.resolve()))
            self.assertEqual(opened[0].files[0].path, str(image.resolve()))

    def test_creator_v2_state_lists_properties_and_events(self):
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            opened: list[AppSpec] = []
            output = run_source(
                f"""
                App, Creator V2.
                Scene, 3D world.
                Create player named hero at x 0 y 0 z 0.
                Create player named enemy at x 1 y 0 z 0.
                Set hero color to red.
                Create list named inventory with key, map.
                Add shield to list inventory.
                When mouse clicked:
                    Play sound click.
                Every 30 milliseconds:
                    Move hero right by 1.
                When hero touches enemy:
                    Show text Collision.
                Save state to file {state_path}.
                """,
                app_runner=opened.append,
            )

            self.assertEqual(output, [])
            self.assertTrue(state_path.exists())
            hero = next(obj for obj in opened[0].objects if obj.name == "hero")
            self.assertEqual(hero.properties["color"], "red")
            self.assertEqual(opened[0].lists["inventory"], ["key", "map", "shield"])
            self.assertIn("mouse:clicked", opened[0].events)
            self.assertIn("timer:30", opened[0].events)
            self.assertIn("collision:hero:enemy", opened[0].events)

    def test_canvas_runtime_builds_general_objects(self):
        opened: list[AppSpec] = []
        output = run_source(
            """
            import pygame
            App, Anything Canvas.
            Scene, canvas.
            Window size 800 by 500.
            Create rectangle named box at x 100 y 120.
            Create circle named ball at x 20 y 40.
            Create text named title at x 16 y 18 saying Hello world.
            Make purple box named panel at (30, 40, 1) size 120 by 80.
            Draw green circle named target at x 300 y 200 size 64 x 64.
            Set box color to red.
            Set box width to 140.
            Put box at (180, 210, 2).
            Resize box to 160 by 90.
            Set ball size to 60 x 60.
            When key d pressed:
                Move box right by 5.
            When a is pressed:
                Move box left by 5.
            When ball clicked:
                Show text Ball.
            When mouse clicks:
                Show text Mouse.
            Each 250 ms:
                Show text Tick.
            When box bumps into ball:
                Show text Hit.
            """,
            app_runner=opened.append,
        )

        self.assertEqual(output, [])
        self.assertEqual(opened[0].imports, ["pygame"])
        self.assertEqual(opened[0].backend, "pygame")
        self.assertEqual(opened[0].scene, "canvas")
        self.assertEqual((opened[0].width, opened[0].height), (800, 500))
        self.assertEqual([obj.kind for obj in opened[0].objects], ["rectangle", "circle", "text", "box", "circle"])
        box = opened[0].objects[0]
        ball = opened[0].objects[1]
        panel = opened[0].objects[3]
        target = opened[0].objects[4]
        self.assertEqual((box.x, box.y, box.z), (180, 210, 2))
        self.assertEqual(box.properties["color"], "red")
        self.assertEqual(box.properties["width"], 160)
        self.assertEqual(box.properties["height"], 90)
        self.assertEqual(ball.properties["width"], 60)
        self.assertEqual(ball.properties["height"], 60)
        self.assertEqual((panel.x, panel.y, panel.z), (30, 40, 1))
        self.assertEqual(panel.properties["color"], "purple")
        self.assertEqual((panel.properties["width"], panel.properties["height"]), (120, 80))
        self.assertEqual(target.properties["color"], "green")
        self.assertEqual((target.properties["width"], target.properties["height"]), (64, 64))
        self.assertIn("key:d", opened[0].events)
        self.assertIn("key:a", opened[0].events)
        self.assertIn("button:ball", opened[0].events)
        self.assertIn("mouse:clicked", opened[0].events)
        self.assertIn("timer:250", opened[0].events)
        self.assertIn("collision:box:ball", opened[0].events)

    def test_standard_library_imports_maps_debug_and_export(self):
        with TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "app.html"
            output = run_source(
                f"""
                import pygame
                import database
                import debug
                Create dictionary named player with health: 100, name: Ada.
                Set player score to 7.
                App, Exported App.
                Scene, canvas.
                Create rectangle named box at x 10 y 20.
                Export app to file {export_path}.
                Debug all.
                """
            )

            self.assertTrue(export_path.exists())
            self.assertIn("Exported app to", output[0])
            self.assertIn('"imports"', output[1])
            self.assertIn('"player"', output[1])

    def test_database_package_and_breakpoint_commands(self):
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app.sqlite"
            package_path = Path(temp_dir) / "package"
            output = run_source(
                f"""
                import database
                Open database file {db_path} as db.
                Run SQL "CREATE TABLE scores (name TEXT, score INTEGER)" on db.
                Run SQL "INSERT INTO scores VALUES ('Ada', 42)" on db.
                Run SQL "SELECT * FROM scores" on db as rows.
                App, Package Demo.
                Scene, canvas.
                Create rectangle named box at x 10 y 20.
                Breakpoint after database.
                Package app to folder {package_path}.
                """
            )

            self.assertTrue(db_path.exists())
            self.assertTrue((package_path / "index.html").exists())
            self.assertIn('"score": 42', output[3])
            self.assertIn("Breakpoint: after database", output[4])
            self.assertIn("Packaged app to", output[5])

    def test_phrase_library_file_runs_reusable_phrases(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "phrases.angis").write_text(
                """
                Define phrase note {message:text} means Show, message.
                Define phrase start game means Say, started.
                """,
                encoding="utf-8",
            )
            main = base / "main.angis"
            main.write_text(
                """
                use phrase library phrases.angis
                Start game.
                Note hello from library.
                """,
                encoding="utf-8",
            )

            output = Interpreter().run(parse_file(main))

        self.assertEqual(output, ["started", "hello from library"])

    def test_angis_module_import_runs_namespaced_functions(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "math_tools.angis").write_text(
                """
                Define greet with name:
                    Return, name.

                Define double with value:
                    Return, value * 2.
                """,
                encoding="utf-8",
            )
            main = base / "main.angis"
            main.write_text(
                """
                use module math_tools.angis as tools
                Call, tools.greet with Ada as message.
                Call, tools.double with 6 as doubled.
                Show message.
                Show doubled.
                """,
                encoding="utf-8",
            )

            output = Interpreter().run(parse_file(main))

        self.assertEqual(output, ["Ada", "12"])

    def test_angis_package_import_runs_folder_namespaces(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            package = base / "tools"
            (package / "math").mkdir(parents=True)
            (package / "text").mkdir()
            (package / "math" / "numbers.angis").write_text(
                """
                Define double with value:
                    Return, value * 2.
                """,
                encoding="utf-8",
            )
            (package / "text" / "names.angis").write_text(
                """
                Define echo with value:
                    Return, value.
                """,
                encoding="utf-8",
            )
            main = base / "main.angis"
            main.write_text(
                """
                use package tools as kit
                Call, kit.math.numbers.double with 6 as doubled.
                Call, kit.text.names.echo with Ada as name.
                Show doubled.
                Show name.
                """,
                encoding="utf-8",
            )

            output = Interpreter().run(parse_file(main))

        self.assertEqual(output, ["12", "Ada"])

    def test_phrase_pack_file_runs_from_nested_folder(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            phrases = base / "phrases"
            phrases.mkdir()
            (phrases / "text.angis").write_text("Define phrase note {message:text} means Show, message.\n", encoding="utf-8")
            (phrases / "game.angis").write_text(
                """
                use phrase pack text.angis
                Define phrase start game means Say, started.
                """,
                encoding="utf-8",
            )
            main = base / "main.angis"
            main.write_text(
                """
                use phrase pack phrases/game.angis
                Start game.
                Note nested pack works.
                """,
                encoding="utf-8",
            )

            output = Interpreter().run(parse_file(main))

        self.assertEqual(output, ["started", "nested pack works"])

    def test_phrase_pack_folder_runs_all_phrase_files(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            phrases = base / "phrases"
            phrases.mkdir()
            (phrases / "game.angis").write_text("Define phrase start game means Say, started.\n", encoding="utf-8")
            (phrases / "text.angis").write_text("Define phrase note {message:text} means Show, message.\n", encoding="utf-8")
            main = base / "main.angis"
            main.write_text(
                """
                use phrase pack phrases
                Start game.
                Note folder pack works.
                """,
                encoding="utf-8",
            )

            output = Interpreter().run(parse_file(main))

        self.assertEqual(output, ["started", "folder pack works"])

    def test_phrase_pack_folder_runs_nested_phrase_files(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            actions = base / "phrases" / "actions"
            ui = base / "phrases" / "ui"
            actions.mkdir(parents=True)
            ui.mkdir(parents=True)
            (actions / "game.angis").write_text("Define phrase start game means Say, started.\n", encoding="utf-8")
            (ui / "text.angis").write_text("Define phrase note {message:text} means Show, message.\n", encoding="utf-8")
            main = base / "main.angis"
            main.write_text(
                """
                use phrase pack phrases
                Start game.
                Note nested folder pack works.
                """,
                encoding="utf-8",
            )

            output = Interpreter().run(parse_file(main))

        self.assertEqual(output, ["started", "nested folder pack works"])

    def test_app_phrase_pack_builds_app_with_custom_words(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            phrases = base / "phrases"
            phrases.mkdir()
            asset = base / "readme.txt"
            asset.write_text("hello app", encoding="utf-8")
            (phrases / "app.angis").write_text(
                """
                Define phrase make app {title:text} means App, title.
                Define phrase make canvas means Scene, canvas.
                Define phrase put text {message:text} means Text, message.
                Define phrase put file {file:path} at {x:number} {y:number} {z:number} means Attach file file to window at x x y y z z.
                """,
                encoding="utf-8",
            )
            main = base / "main.angis"
            main.write_text(
                f"""
                use phrase pack phrases
                Make app Demo.
                Make canvas.
                Put text Hello App.
                Put file {asset} at 10 20 0.
                """,
                encoding="utf-8",
            )
            opened: list[AppSpec] = []

            output = Interpreter(app_runner=opened.append).run(parse_file(main))

        self.assertEqual(output, [])
        self.assertEqual(opened[0].title, "Demo")
        self.assertEqual(opened[0].scene, "canvas")
        self.assertEqual(opened[0].texts, ["Hello App"])
        self.assertEqual(opened[0].files[0].name, "readme.txt")
        self.assertEqual((opened[0].files[0].x, opened[0].files[0].y, opened[0].files[0].z), (10, 20, 0))

    def test_video_object_true_3d_and_mac_app_package(self):
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "clip.mp4"
            video_path.write_bytes(b"not a real video")
            app_path = Path(temp_dir) / "Demo.app"
            opened: list[AppSpec] = []
            output = run_source(
                f"""
                App, Media Demo.
                Scene, true 3D.
                Create cube named core at x 0 y 0 z 0.
                Set core size to 120.
                Play video {video_path} at x 20 y 30.
                Package app to folder {app_path}.
                """,
                app_runner=opened.append,
            )

            self.assertEqual(opened[0].scene, "true 3d")
            self.assertTrue(any(obj.kind == "video" for obj in opened[0].objects))
            self.assertTrue((app_path / "Contents" / "Info.plist").exists())
            self.assertIn("Packaged macOS app to", output[0])

    def test_ui_layout_video_sound_and_windows_package_scaffold(self):
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "clip.mp4"
            video_path.write_bytes(b"not a real video")
            package_path = Path(temp_dir) / "Demo.exe"
            opened: list[AppSpec] = []
            output = run_source(
                f"""
                App, Studio.
                Scene, canvas.
                Layout, grid with 3 columns.
                Create input named nameBox at x 20 y 70.
                Set nameBox width to 220.
                Set sound volume to 65.
                Play video {video_path} at x 10 y 20 size 640 by 360.
                Package app to folder {package_path}.
                """,
                app_runner=opened.append,
            )

            self.assertEqual(opened[0].layout, {"kind": "grid", "columns": 3})
            self.assertEqual(opened[0].sound_volume, 65)
            self.assertEqual(opened[0].objects[0].kind, "input")
            video = next(obj for obj in opened[0].objects if obj.kind == "video")
            self.assertEqual(video.properties["width"], 640)
            self.assertEqual(video.properties["height"], 360)
            self.assertTrue((package_path.with_suffix("") / "index.html").exists())
            self.assertIn("Packaged Windows app scaffold to", output[0])

    def test_standard_library_actions_run_without_raw_python_execution(self):
        with TemporaryDirectory() as temp_dir:
            note = Path(temp_dir) / "note.txt"
            table = Path(temp_dir) / "items.csv"
            table.write_text("name,score\nAda,42\nGrace,99\n", encoding="utf-8")
            output = run_source(
                f"""
                Create list named choices with red, blue, green.
                Create dictionary named player with name: Ada, score: 42.
                Use math sqrt with value: 81 as root.
                Use json parse with text: {{"score": 42}} as data.
                Use json stringify with value: data as packed.
                Use file write with path: {note}, text: hello file as writeResult.
                Use file read with path: {note} as fileText.
                Use file info with path: {note} as fileInfo.
                Use text uppercase with text: hello as loud.
                Use text split with text: red-blue-green, by: - as parts.
                Use text join with values: choices, by: / as joined.
                Use csv read with path: {table} as rows.
                Use data count with rows: rows as rowCount.
                Use data column with rows: rows, column: name as names.
                Use data filter equals with rows: rows, column: name, value: Ada as adaRows.
                Use list length with values: choices as choiceCount.
                Use list append with values: choices, value: yellow as moreChoices.
                Use map keys with value: player as playerKeys.
                Use map get with value: player, key: name as playerName.
                Use path extension with path: {table} as extension.
                Ask text to starts with text: hello, prefix: he as starts.
                Tell text to ends with text: hello, suffix: lo as ends.
                Tell math to clamp with value: 14, min: 1, max: 10 as clamped.
                Get math maximum with left: 2, right: 9 as biggest.
                Get file exists with path: {note} as noteExists.
                Run list at with values: choices, index: 1 as secondChoice.
                Run list slice with values: choices, start: 0, end: 2 as firstTwo.
                Get map has with value: player, key: score as hasScore.
                Get path stem with path: {table} as tableStem.
                Get uppercase of hello natural as loudNatural.
                Calculate square root of 81 as rootNatural.
                Count length of choices as countNatural.
                Find file name of {table} as fileNameNatural.
                Check if file exists at {table} as existsNatural.
                Set loudAssigned to uppercase of hello assigned.
                Make rootAssigned equal square root of 81.
                Let countAssigned = length of choices.
                Set extAssigned to file extension of {table}.
                Set existsAssigned to file exists at {table}.
                Set loudBridge to text uppercase with text: hello bridge.
                Make clampedBridge equal math clamp with value: 14, min: 1, max: 10.
                Let secondBridge = list at with values: choices, index: 1.
                Set hasScoreBridge to map has with value: player, key: score.
                Show root.
                Show packed.
                Show writeResult.
                Show fileText.
                Show loud.
                Show joined.
                Show rowCount.
                Show choiceCount.
                Show playerName.
                Show extension.
                Show starts.
                Show ends.
                Show clamped.
                Show biggest.
                Show noteExists.
                Show secondChoice.
                Show firstTwo.
                Show hasScore.
                Show tableStem.
                Show loudNatural.
                Show rootNatural.
                Show countNatural.
                Show fileNameNatural.
                Show existsNatural.
                Show loudAssigned.
                Show rootAssigned.
                Show countAssigned.
                Show extAssigned.
                Show existsAssigned.
                Show loudBridge.
                Show clampedBridge.
                Show secondBridge.
                Show hasScoreBridge.
                Debug capabilities.
                Use capabilities language as languageCaps.
                Use capabilities runtime as runtimeCaps.
                Use capabilities functions as functionCaps.
                Show languageCaps.
                Show runtimeCaps.
                Show functionCaps.
                """
            )

        self.assertEqual(output[0], "9")
        self.assertEqual(output[1], '{"score": 42}')
        self.assertEqual(output[2], "Wrote file note.txt")
        self.assertEqual(output[3], "hello file")
        self.assertEqual(output[4], "HELLO")
        self.assertEqual(output[5], "red/blue/green")
        self.assertEqual(output[6], "2")
        self.assertEqual(output[7], "3")
        self.assertEqual(output[8], "Ada")
        self.assertEqual(output[9], ".csv")
        self.assertEqual(output[10], "True")
        self.assertEqual(output[11], "True")
        self.assertEqual(output[12], "10")
        self.assertEqual(output[13], "9")
        self.assertEqual(output[14], "True")
        self.assertEqual(output[15], "blue")
        self.assertEqual(output[16], "['red', 'blue']")
        self.assertEqual(output[17], "True")
        self.assertEqual(output[18], "items")
        self.assertEqual(output[19], "HELLO NATURAL")
        self.assertEqual(output[20], "9")
        self.assertEqual(output[21], "3")
        self.assertEqual(output[22], "items.csv")
        self.assertEqual(output[23], "True")
        self.assertEqual(output[24], "HELLO ASSIGNED")
        self.assertEqual(output[25], "9")
        self.assertEqual(output[26], "3")
        self.assertEqual(output[27], ".csv")
        self.assertEqual(output[28], "True")
        self.assertEqual(output[29], "HELLO BRIDGE")
        self.assertEqual(output[30], "10")
        self.assertEqual(output[31], "blue")
        self.assertEqual(output[32], "True")
        self.assertIn('"data"', output[33])
        self.assertIn("folder_packages", output[34])
        self.assertIn("debug_state", output[35])
        self.assertIn("[", output[36])

    def test_debug_trace_reports_executed_angis_lines(self):
        output = run_source(
            """
            Set, x to 1.
            Add, 2 to x.
            Show x.
            Debug trace.
            """
        )

        self.assertEqual(output[0], "3")
        self.assertIn('"instruction": "SetVar"', output[1])
        self.assertIn('"source": "Set x to 1"', output[1])
        self.assertIn('"instruction": "AddToVar"', output[1])
        self.assertIn('"source": "Debug trace"', output[1])

    def test_capability_checks_work(self):
        output = run_source(
            """
            Check capability folder_packages as canUsePackages.
            Check capability made_up_feature as canUseMadeUp.
            Use capabilities has with name: math.sqrt as canUseSqrt.
            Show canUsePackages.
            Show canUseMadeUp.
            Show canUseSqrt.
            """
        )

        self.assertEqual(output, ["True", "False", "True"])


    def test_math_trig_actions_work(self):
        output = run_source(
            """
            Use math sin with value: 90 as result.
            Show result.
            Use math cos with value: 0 as result2.
            Show result2.
            """
        )
        self.assertAlmostEqual(float(output[0]), 1.0, places=5)
        self.assertAlmostEqual(float(output[1]), 1.0, places=5)

    def test_math_log_actions_work(self):
        output = run_source(
            """
            Use math log with value: 1 as result.
            Show result.
            Use math log10 with value: 100 as result2.
            Show result2.
            """
        )
        self.assertAlmostEqual(float(output[0]), 0.0, places=5)
        self.assertAlmostEqual(float(output[1]), 2.0, places=5)

    def test_convert_to_string_works(self):
        output = run_source(
            """
            Use convert to_string with value: 42 as str.
            Show str.
            """
        )
        self.assertEqual(output[0], "42")

    def test_convert_to_number_works(self):
        output = run_source(
            """
            Use convert to_number with value: 42 as num.
            Show num.
            """
        )
        self.assertEqual(output[0], "42")

    def test_bitwise_actions_work(self):
        output = run_source(
            """
            Use bitwise and with left: 5, right: 3 as r1.
            Show r1.
            Use bitwise or with left: 5, right: 3 as r2.
            Show r2.
            Use bitwise xor with left: 5, right: 3 as r3.
            Show r3.
            Use bitwise not with value: 5 as r4.
            Show r4.
            Use bitwise shift_left with value: 5, amount: 1 as r5.
            Show r5.
            Use bitwise shift_right with value: 5, amount: 1 as r6.
            Show r6.
            """
        )
        self.assertEqual(output[0], "1")   # 5 & 3
        self.assertEqual(output[1], "7")   # 5 | 3
        self.assertEqual(output[2], "6")   # 5 ^ 3
        self.assertEqual(output[3], "-6")  # ~5
        self.assertEqual(output[4], "10")  # 5 << 1
        self.assertEqual(output[5], "2")   # 5 >> 1

    def test_text_char_at_works(self):
        output = run_source(
            """
            Use text char_at with text: hello, index: 1 as char.
            Show char.
            """
        )
        self.assertEqual(output[0], "e")

    def test_text_substring_works(self):
        output = run_source(
            """
            Use text substring with text: hello world, start: 0, end: 5 as sub.
            Show sub.
            """
        )
        self.assertEqual(output[0], "hello")

    def test_text_pad_and_repeat_work(self):
        output = run_source(
            """
            Use text pad_start with text: hi, length: 5, char: * as padded.
            Show padded.
            Use text pad_end with text: hi, length: 5, char: * as padded2.
            Show padded2.
            Use text repeat with text: ab, times: 3 as repeated.
            Show repeated.
            """
        )
        self.assertEqual(output[0], "***hi")
        self.assertEqual(output[1], "hi***")
        self.assertEqual(output[2], "ababab")

    def test_file_mkdir_and_delete_work(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            new_dir = base / "test_subdir"
            output = run_source(f"Use file mkdir with path: {new_dir!s} as result.\nShow result.\n")
            self.assertTrue(new_dir.is_dir())
            output2 = run_source(f"Use file delete with path: {new_dir!s} as result.\nShow result.\n")
            self.assertFalse(new_dir.is_dir())

    def test_file_copy_and_move_work(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            src = base / "source.txt"
            dst = base / "dest.txt"
            dst2 = base / "moved.txt"
            src.write_text("hello", encoding="utf-8")
            run_source(f"Use file copy with source: {src!s}, destination: {dst!s} as result.\n")
            self.assertTrue(dst.is_file())
            self.assertEqual(dst.read_text(encoding="utf-8"), "hello")
            run_source(f"Use file move with source: {dst!s}, destination: {dst2!s} as result.\n")
            self.assertFalse(dst.is_file())
            self.assertTrue(dst2.is_file())
            self.assertEqual(dst2.read_text(encoding="utf-8"), "hello")

    def test_file_list_dir_works(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "a.txt").write_text("a", encoding="utf-8")
            (base / "b.txt").write_text("b", encoding="utf-8")
            output = run_source(f"Use file list_dir with path: {base!s} as files.\nShow files.\n")
            self.assertIn("a.txt", output[0])
            self.assertIn("b.txt", output[0])

    def test_raise_error_instruction_works(self):
        with self.assertRaises(AngisRuntimeError) as ctx:
            run_source('Raise error This is a test error.')
        self.assertIn("This is a test error", str(ctx.exception))

    def test_assert_passes_when_true(self):
        output = run_source(
            """
            Set x to 5.
            Assert x is 5 else x should be 5.
            Say ok.
            """
        )
        self.assertEqual(output[0], "ok")

    def test_assert_fails_when_false(self):
        with self.assertRaises(AngisRuntimeError) as ctx:
            run_source(
                """
                Set x to 3.
                Assert x is 5 else x was supposed to be 5.
                """
            )
        self.assertIn("Assertion failed", str(ctx.exception))
        self.assertIn("x was supposed to be 5", str(ctx.exception))

    def test_get_args_works(self):
        import sys
        saved = sys.argv
        try:
            sys.argv = ["program.angis", "hello", "world"]
            output = run_source("Get command line arguments as args.\nShow args.\n")
            self.assertIn("hello", output[0])
            self.assertIn("world", output[0])
        finally:
            sys.argv = saved

    def test_get_env_works(self):
        import os
        key = "ANGIS_TEST_VAR"
        os.environ[key] = "test_value"
        try:
            output = run_source(f"Get environment variable {key} as val.\nShow val.\n")
            self.assertEqual(output[0], "test_value")
        finally:
            del os.environ[key]

    def test_text_regex_match_works(self):
        output = run_source(
            """
            Use text regex_match with text: hello123, pattern: [a-z]+ as result.
            Show result.
            """
        )
        self.assertEqual(output[0], "hello")

    def test_text_regex_replace_works(self):
        output = run_source(
            """
            Use text regex_replace with text: hello world, pattern: world, replacement: there as result.
            Show result.
            """
        )
        self.assertEqual(output[0], "hello there")

    def test_time_format_works(self):
        output = run_source(
            """
            Use time format with value: 2024-01-15, format: %B as formatted.
            Show formatted.
            """
        )
        self.assertEqual(output[0], "January")

    def test_switch_block_runs(self):
        for val, expected in [(1, "one"), (2, "two or three"), (3, "two or three"), (99, "other")]:
            with self.subTest(val=val):
                output = run_source(
                    f"""
                    Set x to {val}.
                    Switch x:
                        Case 1:
                            Show "one".
                        Case 2, 3:
                            Show "two or three".
                        Default:
                            Show "other".
                    """
                )
                self.assertEqual(output[0], expected)

    def test_try_block_catches_error(self):
        output = run_source(
            """
            Try:
                Set x to 1 / 0.
                Show "no_error".
            Except:
                Show "caught".
            Show "after".
            """
        )
        self.assertEqual(output, ["caught", "after"])

    def test_try_block_passes_on_success(self):
        output = run_source(
            """
            Try:
                Set x to 42.
                Show x.
            Except:
                Show "error".
            """
        )
        self.assertEqual(output, ["42"])

    def test_break_stops_repeat(self):
        output = run_source(
            """
            Repeat 100 times:
                Break.
                Show "not_reached".
            Show "after".
            """
        )
        self.assertEqual(output, ["after"])

    def test_break_stops_while(self):
        output = run_source(
            """
            Set x to 0.
            While x is less than 100:
                Set x to x + 1.
                If x is 3:
                    Break.
            Show x.
            """
        )
        self.assertEqual(output, ["3"])

    def test_continue_skips_to_next_iteration(self):
        output = run_source(
            """
            Repeat 5 times:
                Continue.
                Show "not_reached".
            Show "after".
            """
        )
        self.assertEqual(output, ["after"])

    def test_string_interpolation_with_variable(self):
        output = run_source(
            """
            Set name to Angis.
            Show "Hello {name}!"
            """
        )
        self.assertEqual(output[0], "Hello Angis!")

    def test_string_interpolation_with_expression(self):
        output = run_source(
            """
            Set x to 5.
            Set y to 3.
            Show "{x} + {y} = {x + y}"
            """
        )
        self.assertEqual(output[0], "5 + 3 = 8")

    def test_parenthesized_expressions_evaluate(self):
        output = run_source(
            """
            Set x to (3 + 4) * 2.
            Show x.
            """
        )
        self.assertEqual(output[0], "14")

    def test_parentheses_override_precedence_evaluate(self):
        output = run_source(
            """
            Set x to (3 + 4) * (2 + 1).
            Show x.
            """
        )
        self.assertEqual(output[0], "21")

    def test_unary_minus_evaluates(self):
        output = run_source(
            """
            Set score to 10.
            Set x to -score.
            Show x.
            """
        )
        self.assertEqual(output[0], "-10")

    def test_unary_not_evaluates(self):
        output = run_source(
            """
            Set ready to true.
            Set x to not ready.
            Show x.
            """
        )
        self.assertEqual(output[0], "False")

    def test_nested_parentheses_evaluate(self):
        output = run_source(
            """
            Set x to ((1 + 2) * 3).
            Show x.
            """
        )
        self.assertEqual(output[0], "9")

    def test_unary_minus_with_parentheses_evaluates(self):
        output = run_source(
            """
            Set a to 5.
            Set b to 3.
            Set x to -(a + b).
            Show x.
            """
        )
        self.assertEqual(output[0], "-8")

    def test_unary_not_with_parentheses_evaluates(self):
        output = run_source(
            """
            Set a to 5.
            Set b to 3.
            Set x to not (a > b).
            Show x.
            """
        )
        self.assertEqual(output[0], "False")


    # ── Dynamic Python Bridge ──────────────────────────────────────────────

    def test_dynamic_python_bridge_import_module_and_call_function(self):
        output = run_source("""
            import python os as os
            Use os getcwd as cwd.
            Show cwd.
            """)
        self.assertIn("Angis", output[0])

    def test_dynamic_python_bridge_dotted_path_resolution(self):
        output = run_source("""
            import python os as os
            Run os path join with left: "/a", right: "b" as joined.
            Show joined.
            """)
        self.assertEqual(output[0], "/a/b")

    def test_dynamic_python_bridge_non_callable_attribute(self):
        output = run_source("""
            import python os as os
            Get os sep as sep.
            Show sep.
            """)
        self.assertEqual(output[0], "/")

    def test_dynamic_python_bridge_linesep_constant(self):
        output = run_source("""
            import python os as os
            Run os linesep as ls.
            Show ls.
            """)
        self.assertEqual(output[0], "\n")

    def test_dynamic_python_bridge_kwargs_passed_correctly(self):
        output = run_source("""
            import python os as os
            Run os path join with left: "/x", right: "y" as res.
            Show res.
            """)
        self.assertEqual(output[0], "/x/y")

    def test_dynamic_python_bridge_positional_fallback(self):
        output = run_source("""
            import python math as math
            Run math degrees with value: 3.14159 as deg.
            Show deg.
            """)
        self.assertAlmostEqual(float(output[0]), 180.0, delta=1)

    def test_dynamic_python_bridge_isclose(self):
        output = run_source("""
            import python math as math
            Run math isclose with a: 0.1, b: 0.1, rel_tol: 0.01 as close.
            Show close.
            """)
        self.assertEqual(output[0], "True")

    def test_dynamic_python_bridge_get_form_same_as_use(self):
        output = run_source("""
            import python os as os
            Get os getcwd as cwd.
            Show cwd.
            """)
        self.assertIn("Angis", output[0])

    def test_dynamic_python_bridge_run_form(self):
        output = run_source("""
            import python os as os
            Run os getcwd as cwd.
            Show cwd.
            """)
        self.assertIn("Angis", output[0])

    def test_dynamic_python_bridge_json_dumps_fallthrough(self):
        output = run_source("""
            import python json as json
            Run json dumps with obj: {"key": "val"}, indent: 2 as text.
            Show text.
            """)
        self.assertIn('"key"', output[0])

    def test_dynamic_python_bridge_datetime_now(self):
        output = run_source("""
            import python datetime as datetime
            Run datetime datetime now as now.
            Show now.
            """)
        self.assertIn("20", output[0])

    def test_dynamic_python_bridge_module_alias(self):
        output = run_source("""
            import python os as myos
            Use myos getcwd as cwd.
            Show cwd.
            """)
        self.assertIn("Angis", output[0])

    def test_dynamic_python_bridge_nonexistent_module_errors(self):
        with self.assertRaises(AngisRuntimeError):
            run_source("""
                import python nonexistentxyz as bad
                """)

    def test_dynamic_python_bridge_nonexistent_function_errors(self):
        with self.assertRaises(AngisRuntimeError):
            run_source("""
                import python os as os
                Run os this_function_does_not_exist_xyz as x.
                """)

    def test_dynamic_python_bridge_math_fallthrough_unknown_action(self):
        output = run_source("""
            import python math as math
            Run math degrees with value: 180 as deg.
            Show deg.
            """)
        # math.degrees is not in the hardcoded stdlib, routes through bridge
        self.assertAlmostEqual(float(output[0]), 10313.240, delta=1)

    def test_dynamic_python_bridge_cpu_count(self):
        output = run_source("""
            import python os as os
            Run os cpu_count as cores.
            Show cores.
            """)
        self.assertTrue(int(output[0]) >= 1)

    def test_dynamic_python_bridge_no_args_callable(self):
        output = run_source("""
            import python os as os
            Use os getcwd as cwd.
            Show cwd.
            """)
        self.assertIn("Angis", output[0])


if __name__ == "__main__":
    unittest.main()
