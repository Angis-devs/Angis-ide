import unittest

from angis.errors import AngisSyntaxError
from angis.ir import (
    Add,
    AddToList,
    AddToVar,
    Access,
    AppButton,
    AppFileAttach,
    AppLayout,
    AppLoadingScreen,
    AppScene,
    AppSize,
    AppStart,
    AppText,
    AssertTrue,
    BinaryOp,
    Condition,
    CreateFromBlueprint,
    CreateList,
    CreateMap,
    CreateObject,
    DefineBlueprint,
    DebugState,
    EventBlock,
    ExportApp,
    FileAttach,
    ForEachBlock,
    FunctionCall,
    FunctionDef,
    MatchBlock,
    AsyncForBlock,
    AsyncWithBlock,
    BlueprintInitDef,
    SetLiteral,
    TupleLiteral,
    Comprehension,
    TernaryExpr,
    WalrusExpr,
    OperatorOverloadDef,
    Lambda,
    GameRule,
    GameStart,
    GetArgs,
    GetEnv,
    HttpRequest,
    IfBlock,
    ImportModule,
    LengthOf,
    LogicalCondition,
    ObjectMethodCall,
    ObjectMethodDef,
    PlaceObject,
    Print,
    RaiseError,
    ReadInput,
    Reference,
    RemoveFromList,
    RemoveProperty,
    RepeatBlock,
    ResizeObject,
    ReturnValue,
    SetAccess,
    SetProperty,
    SetSoundVolume,
    SetVar,
    SliceOf,
    StopSound,
    SwitchBlock,
    TryBlock,
    UnaryOp,
    Break,
    Continue,
    UpdateVar,
    UseStdLibAction,
    WhileBlock,
)
from angis.parser import parse
from angis.parser import parse_file
from pathlib import Path
from tempfile import TemporaryDirectory


class ParserTests(unittest.TestCase):
    def test_output_synonyms_parse_to_print(self):
        instructions = parse(
            '''
            say "hello"
            print "hello"
            show "hello"
            display "hello"
            tell me "hello"
            '''
        )

        self.assertTrue(all(isinstance(instruction, Print) for instruction in instructions))
        self.assertEqual([instruction.value for instruction in instructions], ["hello"] * 5)
        self.assertGreaterEqual(min(instruction.confidence for instruction in instructions), 0.96)

    def test_variable_synonyms_parse_to_set(self):
        instructions = parse(
            """
            set x to 5
            make y equal 6
            z is 7
            let total = 8
            store 9 as count
            set result to x + y * 2
            set wordResult to x plus y times 2
            set ready to true
            set visible to off
            set firstName to rows[0].name
            set player.score to 50
            """
        )

        self.assertEqual(
            [instruction.name for instruction in instructions if isinstance(instruction, SetVar)],
            ["x", "y", "z", "total", "count", "result", "wordResult", "ready", "visible", "firstName"],
        )
        self.assertIsInstance(instructions[-6].value, BinaryOp)
        self.assertIsInstance(instructions[-5].value, BinaryOp)
        self.assertIs(instructions[-4].value, True)
        self.assertIs(instructions[-3].value, False)
        self.assertIsInstance(instructions[-2].value, Access)
        self.assertIsInstance(instructions[-1], SetAccess)

    def test_natural_data_phrases_parse(self):
        instructions = parse(
            """
            Create dictionary named player with name: Ada, score: 42.
            Create list named inventory with wood.
            Put shield in inventory.
            Store potion inside inventory.
            Remove shield from inventory.
            Take potion out of inventory.
            Make player have score 10.
            Give player health 99.
            Set name of player to Grace.
            Remove field score from player.
            Clear player health.
            """
        )

        self.assertIsInstance(instructions[0], CreateMap)
        self.assertIsInstance(instructions[1], CreateList)
        self.assertIsInstance(instructions[2], AddToList)
        self.assertEqual(instructions[2].name, "inventory")
        self.assertEqual(instructions[2].item, "shield")
        self.assertIsInstance(instructions[3], AddToList)
        self.assertEqual(instructions[3].item, "potion")
        self.assertIsInstance(instructions[4], RemoveFromList)
        self.assertEqual((instructions[4].name, instructions[4].item), ("inventory", "shield"))
        self.assertIsInstance(instructions[5], RemoveFromList)
        self.assertEqual((instructions[5].name, instructions[5].item), ("inventory", "potion"))
        self.assertIsInstance(instructions[6], SetProperty)
        self.assertEqual((instructions[6].object_name, instructions[6].property_name, instructions[6].value), ("player", "score", 10))
        self.assertIsInstance(instructions[7], SetProperty)
        self.assertEqual((instructions[7].object_name, instructions[7].property_name, instructions[7].value), ("player", "health", 99))
        self.assertIsInstance(instructions[8], SetProperty)
        self.assertEqual((instructions[8].object_name, instructions[8].property_name, instructions[8].value), ("player", "name", "Grace"))
        self.assertIsInstance(instructions[9], RemoveProperty)
        self.assertEqual((instructions[9].object_name, instructions[9].property_name), ("player", "score"))
        self.assertIsInstance(instructions[10], RemoveProperty)
        self.assertEqual((instructions[10].object_name, instructions[10].property_name), ("player", "health"))

    def test_natural_data_access_phrases_parse(self):
        instructions = parse(
            """
            Show score of player.
            Show item 0 of inventory.
            Set score of player to score of player plus 10.
            Set item 0 of inventory to sword.
            Increase health of player by 5.
            Take 2 from health of player.
            Add 3 to item 1 of inventory.
            Take 1 from item 1 of inventory.
            """
        )

        self.assertIsInstance(instructions[0], Print)
        self.assertIsInstance(instructions[0].value, Access)
        self.assertIsInstance(instructions[1], Print)
        self.assertIsInstance(instructions[1].value, Access)
        self.assertIsInstance(instructions[2], SetProperty)
        self.assertIsInstance(instructions[2].value, BinaryOp)
        self.assertIsInstance(instructions[3], SetAccess)
        self.assertIsInstance(instructions[4], SetProperty)
        self.assertIsInstance(instructions[4].value, BinaryOp)
        self.assertIsInstance(instructions[5], SetProperty)
        self.assertIsInstance(instructions[5].value, BinaryOp)
        self.assertIsInstance(instructions[6], SetAccess)
        self.assertIsInstance(instructions[6].value, BinaryOp)
        self.assertIsInstance(instructions[7], SetAccess)
        self.assertIsInstance(instructions[7].value, BinaryOp)

    def test_list_and_dictionary_literals_parse(self):
        instructions = parse(
            """
            Set inventory to [wood, stone, 3].
            Set player to {name: Ada, score: 42, items: [key, map]}.
            Show player.items[0].
            """
        )

        self.assertIsInstance(instructions[0], SetVar)
        self.assertEqual(instructions[0].value, ["wood", "stone", 3])
        self.assertIsInstance(instructions[1], SetVar)
        self.assertEqual(instructions[1].value["name"], "Ada")
        self.assertEqual(instructions[1].value["items"], ["key", "map"])
        self.assertIsInstance(instructions[2], Print)
        self.assertIsInstance(instructions[2].value, Access)

    def test_length_expressions_parse(self):
        instructions = parse(
            """
            Show length of inventory.
            Set total to count of inventory plus 1.
            If number of items in inventory is 3:
                Say, count works.
            Show first item of inventory.
            Show last item of inventory.
            Show first letter of title.
            Show first 2 items of inventory.
            Show items 1 through 2 of inventory.
            Show letters 0 to 3 of title.
            If inventory is not empty:
                Say, has items.
            If emptyList is empty:
                Say, empty list.
            """
        )

        self.assertIsInstance(instructions[0], Print)
        self.assertIsInstance(instructions[0].value, LengthOf)
        self.assertIsInstance(instructions[1], SetVar)
        self.assertIsInstance(instructions[1].value, BinaryOp)
        self.assertIsInstance(instructions[2], IfBlock)
        self.assertIsInstance(instructions[3], Print)
        self.assertIsInstance(instructions[3].value, Access)
        self.assertIsInstance(instructions[4], Print)
        self.assertIsInstance(instructions[4].value, Access)
        self.assertIsInstance(instructions[5], Print)
        self.assertIsInstance(instructions[5].value, Access)
        self.assertIsInstance(instructions[6], Print)
        self.assertIsInstance(instructions[6].value, SliceOf)
        self.assertIsInstance(instructions[7], Print)
        self.assertIsInstance(instructions[7].value, SliceOf)
        self.assertIsInstance(instructions[8], Print)
        self.assertIsInstance(instructions[8].value, SliceOf)
        self.assertIsInstance(instructions[9], IfBlock)
        self.assertEqual(instructions[9].condition.operator, "not empty")
        self.assertIsInstance(instructions[10], IfBlock)
        self.assertEqual(instructions[10].condition.operator, "empty")

    def test_natural_variable_mutation_phrases_parse(self):
        instructions = parse(
            """
            Set score to 10.
            Take 2 from score.
            Decrease score by 1.
            Multiply score by 3.
            Double score.
            Divide score by 2.
            Cut score in half.
            """
        )

        self.assertIsInstance(instructions[0], SetVar)
        self.assertTrue(all(isinstance(instruction, UpdateVar) for instruction in instructions[1:]))
        self.assertEqual([instruction.op for instruction in instructions[1:]], ["-", "-", "*", "*", "/", "/"])
        self.assertEqual([instruction.value for instruction in instructions[1:]], [2, 1, 3, 2, 2, 2])

    def test_natural_contains_and_truthy_conditions_parse(self):
        instructions = parse(
            """
            If inventory contains wood:
                Say, found wood.
            If shield is not in inventory:
                Say, no shield.
            If ready:
                Say, ready.
            If not ready:
                Say, not ready.
            If health of player is between 1 and 10:
                Say, health ok.
            If name of player starts with A:
                Say, name ok.
            If fileName ends with png:
                Say, image ok.
            If health of player is not between 1 and 10:
                Say, health outside.
            If name of player does not start with B:
                Say, not B.
            If fileName does not end with jpg:
                Say, not jpg.
            If name starts with ada ignoring case:
                Say, case ok.
            """
        )

        conditions = [instruction.condition for instruction in instructions]
        self.assertTrue(all(isinstance(condition, (Condition, LogicalCondition)) for condition in conditions))
        self.assertEqual(conditions[0].operator, "contains")
        self.assertEqual(conditions[1].operator, "not contains")
        self.assertEqual(conditions[2].operator, "truthy")
        self.assertIsInstance(conditions[3], LogicalCondition)
        self.assertIsInstance(conditions[4], LogicalCondition)
        self.assertEqual(conditions[5].operator, "starts with")
        self.assertEqual(conditions[6].operator, "ends with")
        self.assertIsInstance(conditions[7], LogicalCondition)
        self.assertEqual(conditions[8].operator, "not starts with")
        self.assertEqual(conditions[9].operator, "not ends with")
        self.assertEqual(conditions[10].operator, "starts with ignoring case")

    def test_math_synonyms_parse_to_add(self):
        instructions = parse(
            """
            add 5 and 3
            what is 5 plus 3
            calculate 5 + 3
            give me 5 added to 3
            """
        )

        self.assertTrue(all(isinstance(instruction, Add) for instruction in instructions))

    def test_supports_comments_and_variable_references(self):
        instructions = parse(
            """
            # a comment
            set x to 5 # inline comment
            show x
            """
        )

        self.assertEqual(len(instructions), 2)
        self.assertIsInstance(instructions[1], Print)
        self.assertEqual(instructions[1].value, Reference("x"))

    def test_unclear_phrase_has_helpful_error(self):
        with self.assertRaisesRegex(AngisSyntaxError, "Try a language print, variable, or math phrase"):
            parse("please do the thing")

    def test_sentence_style_phrases_parse(self):
        instructions = parse(
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

        self.assertEqual(len(instructions), 12)
        self.assertIsInstance(instructions[0], Print)
        self.assertEqual(instructions[0].value, "hello from the Angis IDE")
        self.assertIsInstance(instructions[3], SetVar)
        self.assertEqual(instructions[5].value, "Ada Lovelace")

    def test_app_phrases_parse(self):
        instructions = parse(
            """
            App, My First App.
            Scene, lobby.
            Text, Hello inside the app.
            Button, Click me.
            """
        )

        self.assertIsInstance(instructions[0], AppStart)
        self.assertIsInstance(instructions[1], AppScene)
        self.assertIsInstance(instructions[2], AppText)
        self.assertIsInstance(instructions[3], AppButton)

    def test_loading_screen_phrase_parses(self):
        instructions = parse(
            """
            App, Loading Demo.
            Loding screen pickter /tmp/loading screen.png with adieo /tmp/loading-adieo.mp3 then open app.
            """
        )

        self.assertIsInstance(instructions[1], AppLoadingScreen)
        self.assertEqual(instructions[1].image_path, "/tmp/loading screen.png")
        self.assertEqual(instructions[1].audio_path, "/tmp/loading-adieo.mp3")

    def test_default_loading_screen_phrase_parses(self):
        instructions = parse(
            """
            App, Loading Demo.
            Loding screen.
            """
        )

        self.assertIsInstance(instructions[1], AppLoadingScreen)
        self.assertEqual(instructions[1].image_path, "")
        self.assertEqual(instructions[1].audio_path, "")

    def test_flappy_game_code_phrases_parse(self):
        instructions = parse(
            """
            Bird on screen.
            When clicked, bird goes up.
            Bird falls down.
            Add obstacles.
            If bird hits obstacle, end game.
            """
        )

        self.assertIsInstance(instructions[0], GameStart)
        self.assertTrue(all(isinstance(instruction, GameRule) for instruction in instructions[1:]))

    def test_game_shortcut_is_not_supported(self):
        with self.assertRaisesRegex(AngisSyntaxError, "Bird on screen"):
            parse("Game, Flappy Bird.")

    def test_file_phrase_parses(self):
        instructions = parse("Attach file at /tmp/example.txt.")

        self.assertEqual(len(instructions), 1)
        self.assertIsInstance(instructions[0], FileAttach)
        self.assertEqual(instructions[0].path, "/tmp/example.txt")

    def test_attach_file_to_window_phrase_parses(self):
        instructions = parse(
            """
            App, File Window.
            Set file attach to window at x 20 y 80 z 0 from file /tmp/example.txt.
            Set, px to 25.
            Attach file /tmp/other.txt to window at x px y 90 z 1.
            """
        )

        self.assertIsInstance(instructions[1], AppFileAttach)
        self.assertEqual(instructions[1].path, "/tmp/example.txt")
        self.assertEqual((instructions[1].x, instructions[1].y, instructions[1].z), (20, 80, 0))
        self.assertIsInstance(instructions[3], AppFileAttach)
        self.assertEqual(instructions[3].x, Reference("px"))

    def test_general_language_blocks_parse(self):
        instructions = parse(
            """
            Set, score to 0.
            Repeat, 3 times:
                Add, 1 to score.
            If, score is 3:
                Say, done.
            Else:
                Say, not done.
            If, score is at least 3 and lives is greater than 0:
                Say, logical.
            While, score is less than 5:
                Add, 1 to score.
            For each, item in inventory:
                Show, item.
            Do this 2 times:
                Say, natural repeat.
            If score is same as 5 then:
                Say, same.
            If score is bigger than 4:
                Say, bigger.
            If score is under 10:
                Say, under.
            As long as score is less than 6:
                Add, 1 to score.
            For every thing from inventory:
                Show, thing.
            Define, greet with name:
                Return, name.
            Call, greet with Ada as message.
            Define method heal for player with amount:
                Set, self.health to self.health + amount.
            Call, player.heal with 5.
            Define command give points with target and amount:
                Set, target.score to target.score + amount.
            Give points with player, 3.
            Define phrase give {amount} points to {target}:
                Set, target.score to target.score + amount.
            Give 3 points to player.
            Define phrase show stats for {target}:
                Show, target.score.
            Show stats for player.
            """
        )

        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[1], RepeatBlock)
        self.assertIsInstance(instructions[1].body[0], AddToVar)
        self.assertIsInstance(instructions[2], IfBlock)
        self.assertEqual(len(instructions[2].else_body), 1)
        self.assertIsInstance(instructions[3], IfBlock)
        self.assertIsInstance(instructions[3].condition, LogicalCondition)
        self.assertIsInstance(instructions[4], WhileBlock)
        self.assertIsInstance(instructions[5], ForEachBlock)
        self.assertEqual(instructions[5].item_name, "item")
        self.assertIsInstance(instructions[6], RepeatBlock)
        self.assertIsInstance(instructions[7], IfBlock)
        self.assertIsInstance(instructions[8], IfBlock)
        self.assertIsInstance(instructions[9], IfBlock)
        self.assertIsInstance(instructions[10], WhileBlock)
        self.assertIsInstance(instructions[11], ForEachBlock)
        self.assertEqual(instructions[11].item_name, "thing")
        self.assertIsInstance(instructions[12], FunctionDef)
        self.assertEqual(instructions[12].params, ["name"])
        self.assertIsInstance(instructions[12].body[0], ReturnValue)
        self.assertIsInstance(instructions[13], FunctionCall)
        self.assertEqual(instructions[13].args, ["Ada"])
        self.assertEqual(instructions[13].result_name, "message")
        self.assertIsInstance(instructions[14], ObjectMethodDef)
        self.assertEqual(instructions[14].object_name, "player")
        self.assertEqual(instructions[14].method_name, "heal")
        self.assertEqual(instructions[14].params, ["amount"])
        self.assertIsInstance(instructions[15], ObjectMethodCall)
        self.assertEqual(instructions[15].args, [5])
        self.assertIsInstance(instructions[16], FunctionDef)
        self.assertEqual(instructions[16].name, "command_give_points")
        self.assertEqual(instructions[16].params, ["target", "amount"])
        self.assertIsInstance(instructions[17], FunctionCall)
        self.assertEqual(instructions[17].name, "command_give_points")
        self.assertEqual(instructions[17].confidence, 0.88)
        self.assertIsInstance(instructions[18], FunctionDef)
        self.assertEqual(instructions[18].name, "command_give_points_to")
        self.assertEqual(instructions[18].params, ["amount", "target"])
        self.assertIsInstance(instructions[19], FunctionCall)
        self.assertEqual(instructions[19].name, "command_give_points_to")
        self.assertEqual(instructions[19].args, [3, Reference("player")])
        self.assertEqual(instructions[19].confidence, 0.91)
        self.assertIsInstance(instructions[20], FunctionDef)
        self.assertEqual(instructions[20].name, "command_show_stats_for")
        self.assertIsInstance(instructions[21], FunctionCall)
        self.assertEqual(instructions[21].name, "command_show_stats_for")
        self.assertEqual(instructions[21].confidence, 0.91)

    def test_creator_runtime_phrases_parse(self):
        instructions = parse(
            """
            App, Creator World.
            Scene, 3D world.
            Create player named hero at x 0 y 0 z 0.
            Create image named city at x 0 y -40 z 4 from file /tmp/city.png.
            Create button named start with text Start Mission.
            When key w pressed:
                Move hero forward by 1.
            When button start clicked:
                Show text Mission started.
            """
        )

        self.assertIsInstance(instructions[2], CreateObject)
        self.assertIsInstance(instructions[3], CreateObject)
        self.assertIsInstance(instructions[4], CreateObject)
        self.assertIsInstance(instructions[5], EventBlock)
        self.assertIsInstance(instructions[6], EventBlock)

    def test_blueprint_phrases_parse(self):
        instructions = parse(
            """
            Blueprint Player with name: Ada, health: 10.
            Create Player named hero with name: Grace.
            Define method heal for Player with amount:
                Set, self.health to self.health + amount.
            Call, hero.heal with 5.
            """
        )

        self.assertIsInstance(instructions[0], DefineBlueprint)
        self.assertEqual(instructions[0].name, "Player")
        self.assertIsInstance(instructions[1], CreateFromBlueprint)
        self.assertEqual(instructions[1].blueprint_name, "Player")
        self.assertEqual(instructions[1].name, "hero")
        self.assertIsInstance(instructions[2], ObjectMethodDef)
        self.assertEqual(instructions[2].object_name, "Player")
        self.assertIsInstance(instructions[3], ObjectMethodCall)

    def test_phrase_templates_parse_before_definition(self):
        instructions = parse(
            """
            Give 3 points to player.
            Define phrase give {amount} points to {target}:
                Set, target.score to target.score + amount.
            """
        )

        self.assertIsInstance(instructions[0], FunctionCall)
        self.assertEqual(instructions[0].name, "command_give_points_to")
        self.assertEqual(instructions[0].args, [3, Reference("player")])
        self.assertIsInstance(instructions[1], FunctionDef)

    def test_phrase_templates_parse_optional_words(self):
        instructions = parse(
            """
            Define phrase give {amount} points [to] {target}:
                Set, target.score to target.score + amount.
            Give 3 points to player.
            Give 7 points player.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].name, "command_give_points_to")
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, [3, Reference("player")])
        self.assertIsInstance(instructions[2], FunctionCall)
        self.assertEqual(instructions[2].args, [7, Reference("player")])

    def test_phrase_templates_parse_alternative_words(self):
        instructions = parse(
            """
            Define phrase give {amount} points (to|for) {target}:
                Set, target.score to target.score + amount.
            Give 3 points to player.
            Give 7 points for player.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].name, "command_give_points_to")
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, [3, Reference("player")])
        self.assertIsInstance(instructions[2], FunctionCall)
        self.assertEqual(instructions[2].args, [7, Reference("player")])

    def test_phrase_templates_parse_typed_slots(self):
        instructions = parse(
            """
            Define phrase give {amount:number} points to {target:name}:
                Set, target.score to target.score + amount.
            Give 3 points to player.
            Define phrase say note {message:text}:
                Show, message.
            Say note hello from typed text.
            """
        )

        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, [3, Reference("player")])
        self.assertIsInstance(instructions[3], FunctionCall)
        self.assertEqual(instructions[3].args, ["hello from typed text"])

    def test_phrase_templates_parse_key_slots(self):
        instructions = parse(
            """
            Define phrase set {field:key} of {target:name} to {value}:
                Set, target[field] to value.
            Set score of player to 9.
            Set stats.score of player to 10.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].params, ["field", "target", "value"])
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, ["score", Reference("player"), 9])
        self.assertEqual(instructions[2].args, ["stats.score", Reference("player"), 10])

    def test_phrase_templates_parse_path_slots(self):
        instructions = parse(
            """
            Define phrase attach {file:path} means Attach file at file.
            Attach /tmp/example file.txt.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].params, ["file"])
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, ["/tmp/example file.txt"])

    def test_phrase_templates_parse_point_slots(self):
        instructions = parse(
            """
            Define phrase place {file:path} at {location:point} means Attach file file to window at x location[0] y location[1] z location[2].
            Place /tmp/example.txt at (20, 80, 1).
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].params, ["file", "location"])
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, ["/tmp/example.txt", [20, 80, 1]])

    def test_phrase_templates_ignore_sentence_punctuation(self):
        instructions = parse(
            """
            Define phrase give {amount:number} points to {target:name}:
                Set, target.score to target.score + amount.
            Give, 3 points to player!
            """
        )

        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, [3, Reference("player")])

    def test_literal_phrase_templates_parse_without_slots(self):
        instructions = parse(
            """
            Define phrase start game:
                Say, started.
            Start game.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].name, "command_start_game")
        self.assertEqual(instructions[0].params, [])
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].name, "command_start_game")
        self.assertEqual(instructions[1].args, [])

    def test_inline_phrase_definitions_parse(self):
        instructions = parse(
            """
            Define phrase start game means Say, started.
            Start game.
            Define phrase note {message:text} means Show, message.
            Note hello inline phrase.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].name, "command_start_game")
        self.assertEqual(instructions[0].params, [])
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].name, "command_start_game")
        self.assertIsInstance(instructions[2], FunctionDef)
        self.assertEqual(instructions[2].params, ["message"])
        self.assertIsInstance(instructions[3], FunctionCall)
        self.assertEqual(instructions[3].args, ["hello inline phrase"])

    def test_teaching_phrase_definitions_parse(self):
        instructions = parse(
            """
            When I say shout {message:text}, it means Set loud to text uppercase with text: message and then Show loud.
            Shout hello taught words.
            Teach Angis score count to mean Count length of scores as totalScores.
            Score count.
            When I say quiet {message:text}:
                Set quietText to text lowercase with text: message.
                Show quietText.
            Quiet HELLO BLOCK.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].name, "command_shout")
        self.assertEqual(instructions[0].params, ["message"])
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].args, ["hello taught words"])
        self.assertIsInstance(instructions[2], FunctionDef)
        self.assertEqual(instructions[2].name, "command_score_count")
        self.assertIsInstance(instructions[3], FunctionCall)
        self.assertEqual(instructions[3].name, "command_score_count")
        self.assertIsInstance(instructions[4], FunctionDef)
        self.assertEqual(instructions[4].name, "command_quiet")
        self.assertIsInstance(instructions[5], FunctionCall)
        self.assertEqual(instructions[5].args, ["HELLO BLOCK"])

    def test_namespaced_phrase_definitions_parse(self):
        instructions = parse(
            """
            Define phrase app.start means Say, started.
            App start.
            app.start.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].name, "command_app_start")
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].name, "command_app_start")
        self.assertIsInstance(instructions[2], FunctionCall)
        self.assertEqual(instructions[2].name, "command_app_start")

    def test_inline_phrase_definitions_parse_multiple_steps(self):
        instructions = parse(
            """
            Define phrase boost {target:name} means Set, target.score to target.score + 1 and then Show, target.score.
            Boost player.
            Define phrase reset {target:name} means Set, target.score to 0 then Show, target.score.
            Reset player.
            Define phrase mark {target:name} means Set, target.score to 5; Show, target.score.
            Mark player.
            """
        )

        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(len(instructions[0].body), 2)
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertIsInstance(instructions[2], FunctionDef)
        self.assertEqual(len(instructions[2].body), 2)
        self.assertIsInstance(instructions[4], FunctionDef)
        self.assertEqual(len(instructions[4].body), 2)

    def test_phrase_typed_slots_reject_wrong_shapes(self):
        with self.assertRaises(AngisSyntaxError):
            parse(
                """
                Define phrase give {amount:number} points to {target:name}:
                    Set, target.score to target.score + amount.
                Give many points to player.
                """
            )
        with self.assertRaises(AngisSyntaxError):
            parse(
                """
                Define phrase give {amount:number} points to {target:name}:
                    Set, target.score to target.score + amount.
                Give 3 points to player one.
                """
            )

    def test_creator_v2_phrases_parse(self):
        instructions = parse(
            """
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
                Animate hero right by 1 every 30 milliseconds.
            When hero touches enemy:
                Show text Collision.
            Save state to file /tmp/state.json.
            Load state from file /tmp/state.json.
            Fetch https://example.com as page.
            """
        )

        self.assertIsInstance(instructions[5], CreateList)
        self.assertTrue(any(isinstance(item, EventBlock) and item.kind == "mouse" for item in instructions))
        self.assertTrue(any(isinstance(item, EventBlock) and item.kind == "timer" for item in instructions))
        self.assertTrue(any(isinstance(item, EventBlock) and item.kind == "collision" for item in instructions))

    def test_canvas_runtime_phrases_parse(self):
        instructions = parse(
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
            """
        )

        self.assertIsInstance(instructions[0], ImportModule)
        self.assertEqual(instructions[0].name, "pygame")
        self.assertIsInstance(instructions[3], AppSize)
        self.assertIsInstance(instructions[4], CreateObject)
        self.assertEqual(instructions[4].kind, "rectangle")
        self.assertEqual(instructions[6].kind, "text")
        self.assertEqual(instructions[7].properties["color"], "purple")
        self.assertEqual((instructions[7].x, instructions[7].y, instructions[7].z), (30, 40, 1))
        self.assertEqual((instructions[7].properties["width"], instructions[7].properties["height"]), (120, 80))
        self.assertEqual(instructions[8].properties["color"], "green")
        self.assertEqual((instructions[8].properties["width"], instructions[8].properties["height"]), (64, 64))
        self.assertIsInstance(instructions[11], PlaceObject)
        self.assertEqual((instructions[11].x, instructions[11].y, instructions[11].z), (180, 210, 2))
        self.assertIsInstance(instructions[12], ResizeObject)
        self.assertEqual((instructions[12].width, instructions[12].height), (160, 90))
        self.assertIsInstance(instructions[13], ResizeObject)
        self.assertEqual((instructions[13].width, instructions[13].height), (60, 60))
        self.assertIsInstance(instructions[-6], EventBlock)
        self.assertEqual((instructions[-6].kind, instructions[-6].name), ("key", "d"))
        self.assertEqual((instructions[-5].kind, instructions[-5].name), ("key", "a"))
        self.assertEqual((instructions[-4].kind, instructions[-4].name), ("button", "ball"))
        self.assertEqual((instructions[-3].kind, instructions[-3].name), ("mouse", "clicked"))
        self.assertEqual((instructions[-2].kind, instructions[-2].name), ("timer", "250"))
        self.assertEqual((instructions[-1].kind, instructions[-1].name), ("collision", "box:ball"))

    def test_standard_library_phrases_parse(self):
        instructions = parse(
            """
            import database
            import debug
            Create dictionary named player with health: 100, name: Ada.
            Http post https://example.com with body hello as response.
            Debug all.
            Export app to file /tmp/app.html.
            """
        )

        self.assertIsInstance(instructions[0], ImportModule)
        self.assertIsInstance(instructions[2], CreateMap)
        self.assertIsInstance(instructions[3], HttpRequest)
        self.assertIsInstance(instructions[4], DebugState)
        self.assertIsInstance(instructions[5], ExportApp)

    def test_ui_media_and_sound_phrases_parse(self):
        instructions = parse(
            """
            App, Studio.
            Scene, canvas.
            Layout, grid with 3 columns.
            Create button named start at x 20 y 30 with text Start.
            Create input named nameBox at x 20 y 70.
            Set sound volume to 70.
            Stop sound.
            Play video /tmp/clip.mp4 at x 10 y 20 size 640 by 360.
            """
        )

        self.assertIsInstance(instructions[2], AppLayout)
        self.assertEqual(instructions[2].kind, "grid")
        self.assertEqual(instructions[2].columns, 3)
        self.assertIsInstance(instructions[3], CreateObject)
        self.assertEqual((instructions[3].x, instructions[3].y), (20, 30))
        self.assertEqual(instructions[4].kind, "input")
        self.assertIsInstance(instructions[5], SetSoundVolume)
        self.assertIsInstance(instructions[6], StopSound)
        self.assertEqual(instructions[7].width, 640)
        self.assertEqual(instructions[7].height, 360)

    def test_standard_library_action_phrases_parse(self):
        instructions = parse(
            """
            Use math sqrt with value: 81 as root.
            Use random integer with min: 1, max: 6 as roll.
            Use time now as stamp.
            Use json parse with text: {"score": 42} as data.
            Use text uppercase with text: hello as loud.
            Use csv read with path: /tmp/items.csv as rows.
            Use list length with values: choices as choiceCount.
            Use map keys with value: player as playerKeys.
            Use data count with rows: rows as rowCount.
            Use path extension with path: /tmp/items.csv as ext.
            Ask text to uppercase with text: hello as loud.
            Tell math to clamp with value: 14, min: 1, max: 10 as clamped.
            Get file exists with path: /tmp/items.csv as fileExists.
            Run list at with values: choices, index: 0 as firstChoice.
            Get uppercase of hello as loud2.
            Calculate square root of 81 as root2.
            Count length of choices as choiceCount2.
            Find file extension of /tmp/items.csv as ext2.
            Check if file exists at /tmp/items.csv as exists2.
            Set loud3 to uppercase of hello.
            Make root3 equal square root of 81.
            Let ext3 = file extension of /tmp/items.csv.
            Set exists3 to file exists at /tmp/items.csv.
            Set loud4 to text uppercase with text: hello.
            Make clamped4 equal math clamp with value: 14, min: 1, max: 10.
            Let second4 = list at with values: choices, index: 1.
            Set hasScore4 to map has with value: player, key: score.
            Split title by space as words.
            Join words with dash as slug.
            Replace old in title with new as renamed.
            Sort scores as sortedScores.
            Reverse scores as reversedScores.
            Unique scores as uniqueScores.
            Pick random item from scores as chosenScore.
            Get score from player as playerScore.
            Get keys from player as playerKeys.
            Get values from player as playerValues.
            Merge player with bonus as updatedPlayer.
            Read file /tmp/source.txt as sourceText.
            Write hello to file /tmp/output.txt as writeResult.
            Get info for file /tmp/output.txt as fileInfo.
            Read CSV file /tmp/items.csv as rows.
            Count rows in rows as rowCount2.
            Get column name from rows as names2.
            Keep rows where name is Ada as adaRows2.
            Parse JSON {"score": 42} as data2.
            Turn player into JSON as packed2.
            Round 3.7 as rounded2.
            Floor 3.7 as floored2.
            Ceil 3.2 as ceiled2.
            Absolute -5 as absolute2.
            Raise 2 to power 8 as power2.
            Clamp 14 between 1 and 10 as clamped2.
            Pick random number between 1 and 6 as roll2.
            Get file name from /tmp/items.csv as pathName.
            Get file extension from /tmp/items.csv as pathExtension.
            Get folder from /tmp/items.csv as pathFolder.
            Get stem from /tmp/items.csv as pathStem.
            Join path /tmp with items.csv as joinedPath.
            Get current time as nowText.
            Get timestamp as secondsNow.
            Get todays date as todayText.
            Add 3 days to today as dueDate.
            What is 4 days from today as laterDate.
            Subtract 2 days from today as pastDate.
            Debug capabilities.
            """
        )

        self.assertTrue(all(isinstance(instruction, UseStdLibAction) for instruction in instructions[:-1]))
        self.assertEqual(instructions[0].module, "math")
        self.assertEqual(instructions[0].action, "sqrt")
        self.assertEqual(instructions[1].args["min"], 1)
        self.assertEqual(instructions[3].args["text"], '{"score": 42}')
        self.assertEqual(instructions[4].module, "text")
        self.assertEqual(instructions[5].module, "csv")
        self.assertEqual(instructions[6].module, "list")
        self.assertEqual(instructions[7].module, "map")
        self.assertEqual(instructions[8].module, "data")
        self.assertEqual(instructions[9].module, "path")
        self.assertEqual(instructions[10].module, "text")
        self.assertEqual(instructions[10].action, "uppercase")
        self.assertEqual(instructions[11].module, "math")
        self.assertEqual(instructions[11].action, "clamp")
        self.assertEqual(instructions[12].module, "file")
        self.assertEqual(instructions[12].action, "exists")
        self.assertEqual(instructions[13].module, "list")
        self.assertEqual(instructions[13].action, "at")
        self.assertEqual(instructions[14].module, "text")
        self.assertEqual(instructions[14].action, "uppercase")
        self.assertEqual(instructions[15].module, "math")
        self.assertEqual(instructions[15].action, "sqrt")
        self.assertEqual(instructions[16].module, "list")
        self.assertEqual(instructions[16].action, "length")
        self.assertEqual(instructions[17].module, "path")
        self.assertEqual(instructions[17].action, "extension")
        self.assertEqual(instructions[18].module, "file")
        self.assertEqual(instructions[18].action, "exists")
        self.assertEqual(instructions[19].module, "text")
        self.assertEqual(instructions[19].action, "uppercase")
        self.assertEqual(instructions[19].name, "loud3")
        self.assertEqual(instructions[20].module, "math")
        self.assertEqual(instructions[20].action, "sqrt")
        self.assertEqual(instructions[20].name, "root3")
        self.assertEqual(instructions[21].module, "path")
        self.assertEqual(instructions[21].action, "extension")
        self.assertEqual(instructions[21].name, "ext3")
        self.assertEqual(instructions[22].module, "file")
        self.assertEqual(instructions[22].action, "exists")
        self.assertEqual(instructions[22].name, "exists3")
        self.assertEqual(instructions[23].module, "text")
        self.assertEqual(instructions[23].action, "uppercase")
        self.assertEqual(instructions[23].name, "loud4")
        self.assertEqual(instructions[24].module, "math")
        self.assertEqual(instructions[24].action, "clamp")
        self.assertEqual(instructions[24].name, "clamped4")
        self.assertEqual(instructions[25].module, "list")
        self.assertEqual(instructions[25].action, "at")
        self.assertEqual(instructions[25].name, "second4")
        self.assertEqual(instructions[26].module, "map")
        self.assertEqual(instructions[26].action, "has")
        self.assertEqual(instructions[26].name, "hasScore4")
        self.assertEqual(instructions[27].action, "split")
        self.assertEqual(instructions[28].action, "join")
        self.assertEqual(instructions[29].action, "replace")
        self.assertEqual(instructions[30].action, "sort")
        self.assertEqual(instructions[31].action, "reverse")
        self.assertEqual(instructions[32].action, "unique")
        self.assertEqual(instructions[33].module, "random")
        self.assertEqual(instructions[33].action, "choice")
        self.assertEqual(instructions[34].module, "map")
        self.assertEqual(instructions[34].action, "get")
        self.assertEqual(instructions[35].action, "keys")
        self.assertEqual(instructions[36].action, "values")
        self.assertEqual(instructions[37].action, "merge")
        self.assertEqual(instructions[38].action, "read")
        self.assertEqual(instructions[39].action, "write")
        self.assertEqual(instructions[40].action, "info")
        self.assertEqual(instructions[41].module, "csv")
        self.assertEqual(instructions[41].action, "read")
        self.assertEqual(instructions[42].action, "count")
        self.assertEqual(instructions[43].action, "column")
        self.assertEqual(instructions[44].action, "filter_equals")
        self.assertEqual(instructions[45].module, "json")
        self.assertEqual(instructions[45].action, "parse")
        self.assertEqual(instructions[45].args["text"], '{"score": 42}')
        self.assertEqual(instructions[46].module, "json")
        self.assertEqual(instructions[46].action, "stringify")
        self.assertEqual(instructions[47].action, "round")
        self.assertEqual(instructions[48].action, "floor")
        self.assertEqual(instructions[49].action, "ceil")
        self.assertEqual(instructions[50].action, "absolute")
        self.assertEqual(instructions[51].action, "power")
        self.assertEqual(instructions[52].action, "clamp")
        self.assertEqual(instructions[53].module, "random")
        self.assertEqual(instructions[53].action, "integer")
        self.assertEqual(instructions[54].module, "path")
        self.assertEqual(instructions[54].action, "name")
        self.assertEqual(instructions[55].action, "extension")
        self.assertEqual(instructions[56].action, "parent")
        self.assertEqual(instructions[57].action, "stem")
        self.assertEqual(instructions[58].action, "join")
        self.assertEqual(instructions[59].module, "time")
        self.assertEqual(instructions[59].action, "now")
        self.assertEqual(instructions[60].module, "time")
        self.assertEqual(instructions[60].action, "timestamp")
        self.assertEqual(instructions[61].action, "today")
        self.assertEqual(instructions[62].action, "add_days")
        self.assertEqual(instructions[62].args["days"], 3)
        self.assertEqual(instructions[63].action, "add_days")
        self.assertEqual(instructions[64].action, "subtract_days")
        self.assertIsInstance(instructions[-1], DebugState)
        self.assertEqual(instructions[-1].target, "capabilities")

    def test_include_file_parses_across_angis_files(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "shared.angis").write_text("Say, shared.\n", encoding="utf-8")
            main = base / "main.angis"
            main.write_text("include shared.angis\nSay, main.\n", encoding="utf-8")

            instructions = parse_file(main)

        self.assertEqual(len(instructions), 2)
        self.assertIsInstance(instructions[0], Print)

    def test_phrase_library_file_defines_reusable_phrases(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "phrases.angis").write_text(
                """
                Define phrase note {message:text} means Show, message.
                """,
                encoding="utf-8",
            )
            main = base / "main.angis"
            main.write_text(
                """
                use phrase library phrases.angis
                Note hello from library.
                """,
                encoding="utf-8",
            )

            instructions = parse_file(main)

        self.assertEqual(len(instructions), 2)
        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].name, "command_note")

    def test_phrase_pack_file_can_live_in_nested_folder(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            phrases = base / "phrases"
            phrases.mkdir()
            (phrases / "game.angis").write_text("Define phrase start game means Say, started.\n", encoding="utf-8")
            main = base / "main.angis"
            main.write_text("use phrase pack phrases/game.angis\nStart game.\n", encoding="utf-8")

            instructions = parse_file(main)

        self.assertEqual(len(instructions), 2)
        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertIsInstance(instructions[1], FunctionCall)
        self.assertEqual(instructions[1].name, "command_start_game")

    def test_phrase_pack_folder_loads_all_angis_files(self):
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

            instructions = parse_file(main)

        self.assertEqual(len(instructions), 4)
        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertIsInstance(instructions[1], FunctionDef)
        self.assertEqual(instructions[2].name, "command_start_game")
        self.assertEqual(instructions[3].name, "command_note")

    def test_phrase_pack_folder_loads_nested_angis_files(self):
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

            instructions = parse_file(main)

        self.assertEqual(len(instructions), 4)
        self.assertEqual(instructions[2].name, "command_start_game")
        self.assertEqual(instructions[3].name, "command_note")

    def test_app_phrase_pack_defines_app_building_words(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            phrases = base / "phrases"
            phrases.mkdir()
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
                """
                use phrase pack phrases
                Make app Demo.
                Make canvas.
                Put text Hello App.
                Put file /tmp/readme.txt at 10 20 0.
                """,
                encoding="utf-8",
            )

            instructions = parse_file(main)

        self.assertEqual(instructions[4].name, "command_make_app")
        self.assertEqual(instructions[5].name, "command_make_canvas")
        self.assertEqual(instructions[6].name, "command_put_text")
        self.assertEqual(instructions[7].name, "command_put_file_at")


    def test_user_input_phrase_parses_to_read_input(self):
        instructions = parse("Ask input with prompt What is your name as userName.")
        self.assertEqual(len(instructions), 1)
        self.assertIsInstance(instructions[0], ReadInput)
        self.assertEqual(instructions[0].prompt, "What is your name")
        self.assertEqual(instructions[0].result_name, "userName")

    def test_no_prompt_input_parses(self):
        instructions = parse("Read input as data.")
        self.assertIsInstance(instructions[0], ReadInput)
        self.assertEqual(instructions[0].prompt, "")
        self.assertEqual(instructions[0].result_name, "data")

    def test_raise_error_phrase_parses(self):
        instructions = parse("Raise error Something went wrong.")
        self.assertEqual(len(instructions), 1)
        self.assertIsInstance(instructions[0], RaiseError)

    def test_assert_phrase_parses(self):
        instructions = parse("Assert score is greater than 0 else Score must be positive.")
        self.assertIsInstance(instructions[0], AssertTrue)
        self.assertIn("score is greater than 0", instructions[0].condition_text)
        self.assertEqual(instructions[0].message, "Score must be positive")

    def test_get_args_phrase_parses(self):
        instructions = parse("Get command line arguments as args.")
        self.assertIsInstance(instructions[0], GetArgs)
        self.assertEqual(instructions[0].result_name, "args")

    def test_get_env_phrase_parses(self):
        instructions = parse("Get environment variable PATH as myPath.")
        self.assertIsInstance(instructions[0], GetEnv)
        self.assertEqual(instructions[0].var_name, "PATH")
        self.assertEqual(instructions[0].result_name, "myPath")

    def test_new_math_phrases_parse_to_stdlib(self):
        instructions = parse(
            """
            Get sine of 45 as result.
            Get cosine of 60 as result.
            Get tangent of 30 as result.
            Get natural log of 10 as result2.
            Get log10 of 100 as result3.
            """
        )
        self.assertTrue(all(isinstance(i, UseStdLibAction) for i in instructions))
        self.assertEqual(instructions[0].action, "sin")
        self.assertEqual(instructions[1].action, "cos")
        self.assertEqual(instructions[2].action, "tan")
        self.assertEqual(instructions[3].action, "log")
        self.assertEqual(instructions[4].action, "log10")

    def test_convert_phrases_parse_to_stdlib(self):
        instructions = parse(
            """
            Turn 42 into text as str.
            Turn hello into number as num.
            """
        )
        self.assertTrue(all(isinstance(i, UseStdLibAction) for i in instructions))
        self.assertEqual(instructions[0].action, "to_string")
        self.assertEqual(instructions[1].action, "to_number")

    def test_bitwise_phrases_parse_to_stdlib(self):
        instructions = parse(
            """
            Bitwise and of 5 and 3 as result.
            Bitwise or of 5 and 3 as result2.
            Bitwise xor of 5 and 3 as result3.
            Bitwise not of 5 as result4.
            Bitwise left 5 by 1 as result5.
            Bitwise right 5 by 1 as result6.
            """
        )
        self.assertTrue(all(isinstance(i, UseStdLibAction) for i in instructions))
        self.assertEqual(instructions[0].action, "and")
        self.assertEqual(instructions[1].action, "or")
        self.assertEqual(instructions[2].action, "xor")
        self.assertEqual(instructions[3].action, "not")
        self.assertEqual(instructions[4].action, "shift_left")
        self.assertEqual(instructions[5].action, "shift_right")

    def test_new_text_phrases_parse_to_stdlib(self):
        instructions = parse(
            """
            Character at index 1 of hello as char.
            Code at index 0 of hello as code.
            Get substring of hello from 1 to 4 as sub.
            Pad hello start with * to 10 as padded.
            Pad hello end with * to 10 as padded2.
            Repeat hello 3 times as repeated.
            Regex match [a-z]+ in hello as found.
            Regex search world in hello world as found2.
            Regex replace l+ in hello with L as result.
            """
        )
        self.assertTrue(all(isinstance(i, UseStdLibAction) for i in instructions))
        actions = [i.action for i in instructions]
        self.assertEqual(actions, ["char_at", "char_code_at", "substring", "pad_start", "pad_end", "repeat", "regex_match", "regex_search", "regex_replace"])

    def test_file_operation_phrases_parse_to_stdlib(self):
        instructions = parse(
            """
            Make directory /tmp/newdir as result.
            List directory /tmp as files.
            Copy file /tmp/a.txt to /tmp/b.txt as result.
            Move file /tmp/a.txt to /tmp/b.txt as result2.
            Delete file /tmp/a.txt as result3.
            """
        )
        self.assertTrue(all(isinstance(i, UseStdLibAction) for i in instructions))
        self.assertEqual(instructions[0].action, "mkdir")
        self.assertEqual(instructions[1].action, "list_dir")
        self.assertEqual(instructions[2].action, "copy")
        self.assertEqual(instructions[3].action, "move")
        self.assertEqual(instructions[4].action, "delete")

    def test_time_format_phrase_parses(self):
        instructions = parse("Format date 2024-01-15 using %B as formatted.")
        self.assertIsInstance(instructions[0], UseStdLibAction)
        self.assertEqual(instructions[0].module, "time")
        self.assertEqual(instructions[0].action, "format")

    def test_switch_block_parses(self):
        instructions = parse(
            """
            Switch, x:
                Case, 1:
                    Say one.
                Case, 2, 3:
                    Say two or three.
                Default:
                    Say other.
            """
        )
        self.assertIsInstance(instructions[0], SwitchBlock)
        self.assertEqual(len(instructions[0].cases), 2)
        self.assertIsNotNone(instructions[0].default_body)
        self.assertIsInstance(instructions[0].cases[0][0][0], int)
        self.assertEqual(instructions[0].cases[0][0][0], 1)

    def test_try_block_parses(self):
        instructions = parse(
            """
            Try:
                Set x to 1 / 0.
            Except:
                Say error.
            """
        )
        self.assertIsInstance(instructions[0], TryBlock)
        self.assertEqual(len(instructions[0].body), 1)
        self.assertEqual(len(instructions[0].except_body), 1)

    def test_break_and_continue_parse(self):
        instructions = parse(
            """
            Repeat 5 times:
                Break.
            While x is less than 10:
                Continue.
            """
        )
        self.assertIsInstance(instructions[0], RepeatBlock)
        self.assertIsInstance(instructions[0].body[0], Break)
        self.assertIsInstance(instructions[1], WhileBlock)
        self.assertIsInstance(instructions[1].body[0], Continue)

    def test_string_interpolation_parses(self):
        instructions = parse('Show "Hello {name}!"')
        self.assertIsInstance(instructions[0], Print)
        self.assertIsInstance(instructions[0].value, BinaryOp)

    def test_parenthesized_expressions_parse(self):
        instructions = parse("Show (3 + 4) * 2.")
        self.assertIsInstance(instructions[0], Print)
        self.assertIsInstance(instructions[0].value, BinaryOp)
        self.assertEqual(instructions[0].value.op, "*")

    def test_parentheses_override_precedence(self):
        instructions = parse("Set x to (3 + 4) * 2.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, BinaryOp)
        self.assertEqual(instructions[0].value.op, "*")
        self.assertIsInstance(instructions[0].value.left, BinaryOp)
        self.assertEqual(instructions[0].value.left.op, "+")

    def test_unary_minus_parses(self):
        instructions = parse("Set x to -score.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, UnaryOp)
        self.assertEqual(instructions[0].value.op, "-")

    def test_unary_not_parses(self):
        instructions = parse("Set x to not ready.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, UnaryOp)
        self.assertEqual(instructions[0].value.op, "not")

    def test_nested_parentheses_parse(self):
        instructions = parse("Show ((1 + 2) * 3).")
        self.assertIsInstance(instructions[0], Print)
        self.assertIsInstance(instructions[0].value, BinaryOp)
        self.assertEqual(instructions[0].value.op, "*")

    def test_unary_minus_with_parentheses_parses(self):
        instructions = parse("Set x to -(a + b).")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, UnaryOp)
        self.assertEqual(instructions[0].value.op, "-")
        self.assertIsInstance(instructions[0].value.right, BinaryOp)
        self.assertEqual(instructions[0].value.right.op, "+")

    def test_set_literal_parses(self):
        instructions = parse("Set x to set of 1, 2, 3.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, SetLiteral)
        self.assertEqual(instructions[0].value.values, [1, 2, 3])

    def test_tuple_literal_parses(self):
        from angis.ir import TupleLiteral
        instructions = parse("Set x to tuple of 1, 2, 3.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, TupleLiteral)
        self.assertEqual(instructions[0].value.values, [1, 2, 3])

    def test_natural_comprehension_parses(self):
        from angis.ir import Comprehension
        instructions = parse("Set result to for each x in items collect x * 2.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, Comprehension)

    def test_natural_comprehension_with_filter_parses(self):
        instructions = parse("Set result to for each x in items collect x * 2 if x > 0.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, Comprehension)

    def test_natural_lambda_parses(self):
        instructions = parse("Set f to lambda x into x * 2.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, Lambda)

    def test_natural_lambda_arrow_parses(self):
        instructions = parse("Set f to arrow x to x * 2.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, Lambda)

    def test_natural_lambda_fn_parses(self):
        instructions = parse("Set f to fn x => x * 2.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, Lambda)

    def test_ternary_expression_parses(self):
        instructions = parse("Set x to a if b else c.")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, TernaryExpr)

    def test_walrus_expression_parses(self):
        from angis.ir import WalrusExpr
        instructions = parse("Set x to (y := 5).")
        self.assertIsInstance(instructions[0], SetVar)
        self.assertIsInstance(instructions[0].value, WalrusExpr)
        self.assertEqual(instructions[0].value.name, "y")
        self.assertEqual(instructions[0].value.value, 5)

    def test_enhanced_param_types_parse(self):
        instructions = parse(
            """
            Define, process with items: list[int]:
                Say, done.
            """
        )
        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].params, ["items"])
        self.assertEqual(instructions[0].param_types, {"items": "list"})

    def test_operator_overload_parses(self):
        from angis.ir import OperatorOverloadDef
        instructions = parse(
            """
            + for Point with a, b:
                Say, overloaded.
            """
        )
        self.assertIsInstance(instructions[0], OperatorOverloadDef)
        self.assertEqual(instructions[0].blueprint_name, "Point")
        self.assertEqual(instructions[0].operator, "+")
        self.assertEqual(instructions[0].param1, "a")
        self.assertEqual(instructions[0].param2, "b")

    def test_match_block_parses(self):
        instructions = parse(
            """
            Match, x:
                Case, 1:
                    Say one.
                Case, 2:
                    Say two.
                Default:
                    Say other.
            """
        )
        self.assertIsInstance(instructions[0], MatchBlock)

    def test_decorator_parses(self):
        instructions = parse(
            """
            @log
            Define, greet with name:
                Say, hello.
            """
        )
        self.assertIsInstance(instructions[0], FunctionDef)
        self.assertEqual(instructions[0].decorators, ["log"])

    def test_async_for_parses(self):
        instructions = parse(
            """
            Async for each item in stream:
                Say, item.
            """
        )
        self.assertIsInstance(instructions[0], AsyncForBlock)

    def test_async_with_parses(self):
        instructions = parse(
            """
            Async with resource:
                Say, using.
            """
        )
        self.assertIsInstance(instructions[0], AsyncWithBlock)

    def test_blueprint_init_parses(self):
        instructions = parse(
            """
            On create for Player with name and health:
                Set, self.health to health.
            """
        )
        self.assertIsInstance(instructions[0], BlueprintInitDef)
        self.assertEqual(instructions[0].blueprint_name, "Player")
        self.assertEqual(instructions[0].params, ["name", "health"])


if __name__ == "__main__":
    unittest.main()
