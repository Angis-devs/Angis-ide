# Angis

Angis is a local Python 3.14+ prototype for a programming language that maps human-like phrases into clear programming actions. It does not call cloud AI APIs. Phrase handling is implemented with an expandable intent parser.

## Python Version

Angis targets Python 3.14.5 or newer. On macOS, use the official python.org `macOS 64-bit universal2 installer` for Python 3.14 so the same install runs natively on Apple Silicon and Intel Macs.

Do not modify Apple's `/usr/bin/python3`. Install Python 3.14 separately, then run Angis with:

```bash
python3.14 -m angis run examples/hello.angis
```

The bundled `launch_angis.sh` and `install_angis_mac_app.sh` prefer `python3.14` and reject older Python runtimes.

## Run

```bash
python3.14 -m angis run examples/hello.angis
python3.14 -m angis run examples/variables.angis
python3.14 -m angis run examples/math.angis
```

Print the intermediate representation:

```bash
python3.14 -m angis ir examples/math.angis
```

Run an app with the optional real pygame backend:

```bash
python3.14 -m angis pygame examples/full_system.angis
```

This requires `pygame` to be installed in the same Python environment. If it is missing, Angis gives a safe error instead of falling back silently.

Step through a program in the CLI debugger:

```bash
python3.14 -m angis debug examples/true_3d.angis
python3.14 -m angis debug examples/true_3d.angis --no-wait
```

Launch the built-in IDE:

```bash
python3.14 -m angis.ide
```

The IDE shows the startup picture from `angis loading/loading screen.png`, plays `angis loading/loading-adieo.mp3`, then opens the editor.


## Syntax

Comments start with `#` and can appear on their own line or after code. Strings use single or double quotes. Numbers can be integers or decimals. Variables use names like `x`, `total`, or `user_name`.

General language features:

```angis
import pygame
import database
import debug

Set, score to 0.
Set, bonus to 2.
Set, total to score + bonus * 3.

Repeat, 3 times:
    Add, 1 to score.

If, score + bonus is at least 5:
    Say, score reached three.
    Show, score.

Define, greet:
    Say, hello from a function.

Call, greet.

Create dictionary named player with name: Ada, health: 10.
Define method heal for player with amount:
    Set, self.health to self.health + amount.
    Return, self.health.

Call, player.heal with 5 as healed.
Show, healed.

Blueprint Player with name: Ada, health: 10.
Create Player named hero with name: Grace.
Define method heal for Player with amount:
    Set, self.health to self.health + amount.
    Return, self.health.

Call, hero.heal with 5 as heroHealth.
Show, heroHealth.

Define command give points with target and amount:
    Set, target.score to target.score + amount.
    Return, target.score.

Run command give points with hero, 3 as newScore.
Show, newScore.

Give points with hero, 7 as nextScore.
Show, nextScore.

Define phrase give {amount} points to {target}:
    Set, target.score to target.score + amount.
    Return, target.score.

Give 3 points to hero as phraseScore.
Show, phraseScore.

Optional words go in brackets:

Define phrase add {amount} points [to] {target}:
    Set, target.score to target.score + amount.

Add 5 points to hero.
Add 5 points hero.

Alternative words go in parentheses with `|`:

Define phrase give {amount} points (to|for) {target}:
    Set, target.score to target.score + amount.

Give 3 points to hero.
Give 7 points for hero.

Slots can declare a type:

Define phrase give {amount:number} points to {target:name}:
    Set, target.score to target.score + amount.

Define phrase note {message:text}:
    Show, message.

Note hello from typed text.

Typed slots also control matching: `{amount:number}` only accepts numbers, and `{target:name}` only accepts a variable or object name.

Custom phrase calls tolerate sentence punctuation:

Give, 3 points to hero!

Use `{field:key}` when the phrase should capture an object property name:

Define phrase set {field:key} of {target:name} to {value}:
    Set, target[field] to value.

Set score of hero to 9.
Set stats.score of hero to 10.

Use `{file:path}` when the phrase should capture a local file path:

Define phrase attach {file:path} means Attach file at file.
Attach /Users/fellflow/Desktop/Angis/README.md.

Path slots can combine with numeric slots for placement:

Define phrase place {file:path} at {x:number} {y:number} {z:number} means Attach file file to window at x x y y z z.

Use `{location:point}` for three coordinates:

Define phrase place {file:path} at {location:point} means Attach file file to window at x location[0] y location[1] z location[2].
Place /Users/fellflow/Desktop/Angis/README.md at (20, 80, 0).

Literal custom phrases do not need slots:

Define phrase start game:
    Say, started.

Start game.

Phrase names can use namespaces with dots. They can be called with the dot or with a space, so packs can grow without changing the base language:

Define phrase app.start means Say, started.
Define phrase app.stop means Say, stopped.

App start.
app.stop.

Short one-line phrase definitions use `means`:

Define phrase start game means Say, started.
Define phrase note {message:text} means Show, message.

Note hello from one line.

You can teach Angis your wording with a more natural form:

When I say shout {message:text}, it means Set loud to text uppercase with text: message and then Show loud.
Shout hello from my words.

Teach Angis count names to mean Count length of names as nameCount.
Count names.

The teaching form also works as a block:

When I say quiet {message:text}:
    Set quietText to text lowercase with text: message.
    Show quietText.

Quiet HELLO.

Use `and then` for multiple actions in one line:

Define phrase boost {target:name} means Set, target.score to target.score + 1 and then Show, target.score.

`then` and semicolons work too:

Define phrase reset {target:name} means Set, target.score to 0 then Show, target.score.
Define phrase mark {target:name} means Set, target.score to 5; Show, target.score.

Define phrase show stats for {target}:
    Show, target.name.
    Show, target.score.

Show stats for hero.

Custom phrases can be used before their `Define phrase` block appears later in the file:

Give 3 points to hero as earlyScore.

Define phrase give {amount} points to {target}:
    Set, target.score to target.score + amount.
    Return, target.score.
```

Supported block commands:

- `If, score is 3:`
- `If, score is not 3:`
- `If, score is greater than 2:`
- `If, score is less than 10:`
- `If, score is at least 3:`
- `If, score is at most 10:`
- `If, score is at least 3 and lives is greater than 0:`
- `If, score is less than 3 or lives is 0:`
- `If, not score is less than 3:`
- `If, inventory contains wood:`
- `If, shield is not in inventory:`
- `If, ready:`
- `Else:`
- `Otherwise:`
- `While, score is less than 10:`
- `For each, item in inventory:`
- `Repeat, 5 times:`
- `Define, name:`
- `Define, greet with name:`
- `Define method heal for player with amount:`
- `Blueprint Player with name: Ada, health: 10.`
- `Create Player named hero with name: Grace.`
- `Call, name.`
- `Call, greet with Ada.`
- `Call, player.heal with 5.`
- `Return, value.`
- `Call, addPair with 4, 6 as total.`

Natural control-flow wording also works:

```angis
Do this 2 times:
    Say, repeat.

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
```
- `Add, 1 to score.`
- `Set, total to score + bonus * 3.`
- `Define command give points with target and amount:`
- `Run command give points with hero, 3 as newScore.`
- `Give points with hero, 7 as nextScore.`
- `Define phrase give {amount} points to {target}:`
- `Give 3 points to hero as phraseScore.`
- Optional phrase text uses brackets: `Define phrase add {amount} points [to] {target}:`
- Alternative phrase words use parentheses: `Define phrase give {amount} points (to|for) {target}:`
- Typed phrase slots use `name`, `number`, `text`, `key`, `path`, `point`, or `value`: `{amount:number}`, `{target:name}`, `{field:key}`, `{file:path}`, `{location:point}`, `{message:text}`. `point` slots produce a three-number list, usable as `location[0]`, `location[1]`, and `location[2]`.
- Custom phrase calls ignore punctuation like commas and exclamation marks around words.
- Literal phrase templates can have no slots: `Define phrase start game:`
- One-line phrase aliases use `means`: `Define phrase note {message:text} means Show, message.`
- One-line phrase aliases can run multiple actions with `and then`, `then`, or `;`.
- Custom phrase templates are checked before built-in one-line intents, so a phrase like `Show stats for hero.` can call your own command instead of the built-in `Show` command.

Standard library imports:

```angis
import pygame
import canvas
import physics
import sound
import network
import database
import sqlite3
import ui
import video
import packaging
import debug
import std
import math
import random
import time
import json
import file
import text
import csv
import data
import list
import map
import path
import capabilities
```

Imports are safe Angis modules. They do not run arbitrary Python code, but they enable/record the runtime area the app is using. `import pygame` marks the app as using the pygame-style visual/game backend while the current IDE still renders through the local Tk canvas runtime.

Safe standard-library actions:

```angis
Use math sqrt with value: 81 as root.
Use math power with base: 2, exponent: 8 as power.
Tell math to clamp with value: 14, min: 1, max: 10 as clamped.
Get math maximum with left: 2, right: 9 as biggest.
Use random integer with min: 1, max: 6 as roll.
Round 3.7 as rounded.
Floor 3.7 as floored.
Ceil 3.2 as ceiled.
Absolute -5 as positive.
Raise 2 to power 8 as powered.
Clamp 14 between 1 and 10 as clamped2.
Pick random number between 1 and 6 as roll2.
Use time now as stamp.
Get current time as nowText.
Get timestamp as secondsNow.
Get todays date as todayText.
Add 3 days to today as dueDate.
What is 4 days from today as laterDate.
Subtract 2 days from today as pastDate.
Use json parse with text: {"score": 42} as data.
Use json stringify with value: data as packed.
Parse JSON {"score": 42} as data2.
Turn data2 into JSON as packed2.
Use text uppercase with text: hello as loud.
Ask text to starts with text: hello, prefix: he as starts.
Tell text to ends with text: hello, suffix: lo as ends.
Use text split with text: red-blue-green, by: - as parts.
Use text join with values: parts, by: / as joined.
Split title by space as words.
Join words with dash as slug.
Replace old in title with new as renamed.
Get file exists with path: /Users/fellflow/Desktop/Angis/examples/hello.angis as fileExists.
Use file read with path: /Users/fellflow/Desktop/Angis/examples/hello.angis as sourceText.
Use file write with path: /Users/fellflow/Desktop/Angis/assets/output.txt, text: hello as writeResult.
Use file info with path: /Users/fellflow/Desktop/Angis/examples/hello.angis as fileInfo.
Read file /Users/fellflow/Desktop/Angis/examples/hello.angis as sourceText2.
Write hello to file /Users/fellflow/Desktop/Angis/assets/output2.txt as writeResult2.
Get info for file /Users/fellflow/Desktop/Angis/assets/output2.txt as fileInfo2.
Use csv read with path: /Users/fellflow/Desktop/Angis/assets/items.csv as rows.
Use data count with rows: rows as rowCount.
Use data column with rows: rows, column: name as names.
Use data filter equals with rows: rows, column: name, value: Ada as adaRows.
Read CSV file /Users/fellflow/Desktop/Angis/assets/items.csv as rows2.
Count rows in rows2 as rowCount2.
Get column name from rows2 as names2.
Keep rows2 where name is Ada as adaRows2.
Use list length with values: names as nameCount.
Run list at with values: names, index: 0 as firstName.
Run list slice with values: names, start: 0, end: 2 as firstTwoNames.
Use list unique with values: names as uniqueNames.
Sort names as sortedNames.
Reverse names as reversedNames.
Unique names as uniqueNames2.
Pick random item from names as chosenName.
Use map keys with value: data as keys.
Use map get with value: data, key: score as score.
Get map has with value: data, key: score as hasScore.
Get score from data as score2.
Get keys from data as keys2.
Get values from data as values2.
Merge data with bonus as updatedData.
Use path extension with path: /Users/fellflow/Desktop/Angis/assets/items.csv as extension.
Get path stem with path: /Users/fellflow/Desktop/Angis/assets/items.csv as fileStem.
Get file name from /Users/fellflow/Desktop/Angis/assets/items.csv as pathName.
Get file extension from /Users/fellflow/Desktop/Angis/assets/items.csv as pathExtension.
Get folder from /Users/fellflow/Desktop/Angis/assets/items.csv as pathFolder.
Get stem from /Users/fellflow/Desktop/Angis/assets/items.csv as pathStem.
Join path /Users/fellflow/Desktop/Angis/assets with items.csv as joinedPath.
Use capabilities list as available.
Use capabilities language as languageFeatures.
Use capabilities runtime as runtimeFeatures.
Use capabilities functions as loadedFunctions.
Check capability folder_packages as canUsePackages.
Use capabilities has with name: math.sqrt as canUseSqrt.
Debug capabilities.
```

These commands are Angis' expansion point for doing more things with the same language style. They call registered safe local actions, not arbitrary Python code.
The capability registry reports standard-library actions, language features, runtime features, loaded imports, loaded functions, methods, and blueprints.
Capability checks return `True` or `False`, so programs can guard optional features before using them.
`Use`, `Ask`, `Tell`, `Get`, and `Run` can all call the same registered actions.

Some common actions also have shorter human-style forms:

```angis
Get uppercase of hello as loud.
Calculate square root of 81 as root.
Count length of names as nameCount.
Find file name of /Users/fellflow/Desktop/Angis/examples/hello.angis as fileName.
Find file extension of /Users/fellflow/Desktop/Angis/examples/hello.angis as extension.
Check if file exists at /Users/fellflow/Desktop/Angis/examples/hello.angis as fileExists.
```

The same common actions can assign straight into a variable:

```angis
Set loud to uppercase of hello.
Make root equal square root of 81.
Let nameCount = length of names.
Set extension to file extension of /Users/fellflow/Desktop/Angis/examples/hello.angis.
Set fileExists to file exists at /Users/fellflow/Desktop/Angis/examples/hello.angis.
```

For any registered standard-library module, assignment can also use the module and action name directly:

```angis
Set loud to text uppercase with text: hello.
Make clamped equal math clamp with value: 14, min: 1, max: 10.
Let secondName = list at with values: names, index: 1.
Set hasScore to map has with value: player, key: score.
```

Direct data access:

```angis
Create dictionary named player with name: Ada, score: 42.
Create list named inventory with wood, stone, iron.
Use json parse with text: [{"name":"Ada"},{"name":"Grace"}] as rows.

Show, player.name.
Show, inventory[0].
Show, rows[0].name.

Set, player.score to 50.
Set, inventory[1] to diamond.
Set, rows[0].name to Lovelace.
```

Literal list and dictionary values can be assigned directly:

```angis
Set inventory to [wood, stone, 3].
Set player to {name: Ada, score: 42, items: [key, map]}.

Show item 0 of inventory.
Show name of player.
Show player.items[1].
```

Length and count expressions work with lists, dictionaries, and text:

```angis
Show length of inventory.
Show count of player.
Show number of letters in title.

Set total to count of inventory plus 1.

Show first item of inventory.
Show second item of inventory.
Show last item of inventory.
Show first letter of title.
Show last letter of title.
Show first 2 items of inventory.
Show items 1 through 2 of inventory.
Show letters 0 to 3 of title.

If number of items in inventory is 3:
    Say, count works.

If inventory is not empty:
    Say, inventory has items.

If emptyList is empty:
    Say, list empty.

If emptyText is blank:
    Say, text blank.
```

Natural data wording works too:

```angis
Put shield in inventory.
Store potion inside inventory.
Remove shield from inventory.
Take potion out of inventory.
Make player have health 99.
Give player level 3.
Set name of player to Grace.
Show health of player.
Set score of player to score of player plus 10.
Show item 0 of inventory.
Set item 0 of inventory to sword.
Increase health of player by 5.
Take 2 from health of player.
Add 3 to item 1 of numbers.
Take 1 from item 1 of numbers.
Remove field level from player.
Clear player health.
```

Boolean values:

```angis
Set, ready to true.
Set, visible to off.
Create dictionary named player with alive: yes, hidden: no.

If ready is true:
    Say, ready.

If ready:
    Say, ready still works.

If player.alive is yes and player.hidden is no:
    Say, player active.
```

Contains conditions work with text, lists, and dictionaries:

```angis
Create list named inventory with wood, stone.
Create dictionary named player with name: Ada, score: 42.
Set phrase to hello world.

If inventory contains wood:
    Say, list contains.

If player has score:
    Say, map has score.

If phrase contains world:
    Say, text contains world.

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
```

Word math works inside expressions, variables, conditions, loops, function returns, and custom phrases:

```angis
Set total to x plus y times 2.
Set half to total divided by 2.
Set left to total minus y.

If total is bigger than x times 3:
    Show, total.
```

Natural variable mutation:

```angis
Take 2 from score.
Decrease score by 1.
Multiply score by 3.
Double score.
Divide score by 2.
Cut score in half.
```

Data, debugging, and export:

```angis
Create list named inventory with key, map.
Add shield to list inventory.

Create dictionary named player with health: 100, name: Ada.
Set player score to 7.

Debug all.
Debug variables.
Debug lists.
Debug maps.
Debug imports.
Debug trace.
Debug app.

Export app to file /Users/fellflow/Desktop/Angis/assets/my_app.html.
```

`Export app to file ...` writes a local `.html` app preview. It does not upload or run shell commands.
`Debug trace.` prints the executed Angis source lines and IR instruction names in order.

Multi-file modules:

```angis
include shared.angis
import file shared.angis
use phrase library phrase_library.angis
use module modules/math_tools.angis as tools
use package packages/tools as kit

Call, tools.greet with Ada as message.
Call, tools.double with 6 as doubled.
Call, kit.math.numbers.double with 6 as packageDoubled.
```

Included files, phrase libraries, and modules must end in `.angis`. Recursive includes are blocked.
`use module ... as name` prefixes functions from that file, so `tools.greet` and `tools.double` can be called without mixing their names into the main file.
`use package ... as name` loads every `.angis` file in a folder. The folder path becomes part of the call name, so `packages/tools/math/numbers.angis` can be called as `kit.math.numbers.double`.

Phrase libraries can define custom wording once:

```angis
# phrase_library.angis
Define phrase note {message:text} means Show, message.
Define phrase start game means Say, started.
```

Then another file can use it:

```angis
use phrase library phrase_library.angis
Start game.
Note hello from library.
```

Phrase packs can live in folders and include other packs:

```angis
use phrase pack phrases/game.angis
```

You can also load every `.angis` phrase file in a folder:

```angis
use phrase pack phrases
```

Folder packs load `.angis` files in nested subfolders too, so `phrases/game/actions.angis` is included by `use phrase pack phrases`.

Phrase packs can define app-building wording:

```angis
use phrase pack phrases/app.angis

Make app Custom Words.
Make canvas.
Put text Hello from custom app wording.
Put file /Users/fellflow/Desktop/Angis/README.md at 20 80 0.
```

SQLite databases:

```angis
import database

Open database file /Users/fellflow/Desktop/Angis/assets/app.sqlite as db.
Run SQL "CREATE TABLE IF NOT EXISTS scores (name TEXT, score INTEGER)" on db.
Run SQL "INSERT INTO scores VALUES ('Ada', 42)" on db.
Run SQL "SELECT * FROM scores" on db as rows.
Debug variables.
```

Debugging and packaging:

```angis
Breakpoint after setup.
Debug all.
Export app to file /Users/fellflow/Desktop/Angis/assets/my_app.html.
Package app to folder /Users/fellflow/Desktop/Angis/assets/my_app_package.
Package app to folder /Users/fellflow/Desktop/Angis/assets/MyApp.app.
Package app to folder /Users/fellflow/Desktop/Angis/assets/MyApp.exe.
```

On macOS, `.app` creates a local app bundle. `.exe` creates a Windows package scaffold because building a real Windows executable requires Windows build tools.

UI layout and controls:

```angis
App, Studio.
Scene, canvas.
Layout, grid with 3 columns.

Create button named start at x 20 y 30 with text Start.
Create input named nameBox at x 20 y 80.
Create slider named speed at x 20 y 130.
Create checkbox named musicOn at x 20 y 180.
```

True 3D:

```angis
import std

App, True 3D Demo.
Scene, true 3D.
Window size 900 by 620.

Create cube named core at x 0 y 0 z 0.
Set core color to blue.
Set core size to 160.
```

`Scene, true 3D.` uses Angis' built-in software 3D renderer in the IDE. It currently renders rotating wireframe cube-style objects.

Video:

```angis
import video

App, Video Demo.
Scene, canvas.
Play video /Users/fellflow/Desktop/movie.mp4 at x 20 y 30 size 640 by 360.
Export app to file /Users/fellflow/Desktop/video_demo.html.
```

In the IDE, video objects appear as video panels. In exported HTML, Angis writes a real `<video controls>` element pointing at the local file.

Sound:

```angis
Set sound volume to 70.
Play sound /Users/fellflow/Desktop/click.mp3.
Stop sound.
```

Networking:

```angis
Fetch https://example.com as page.
Http get https://example.com as page.
Http post https://example.com with body hello as response.
```

HTTP commands use Python's local networking stack with a timeout and store the response text in a variable.

Creator runtime:

```angis
App, Creator World.
Scene, 3D world.

Create player named hero at x 0 y 0 z 0.
Create image named city at x 0 y -40 z 4 from file /Users/fellflow/Desktop/Angis/assets/gta_style_city.png.
Create button named start with text Start Mission.

When key w pressed:
    Move hero forward by 1.

When key s pressed:
    Move hero backward by 1.

When button start clicked:
    Show text Mission started.
    Move hero forward by 2.
```

Supported creator commands:

- `Create player named hero at x 0 y 0 z 0.`
- `Create rectangle named box at x 100 y 120.`
- `Create circle named ball at x 20 y 40.`
- `Create text named title at x 16 y 18 saying Hello world.`
- `Create image named city at x 0 y -40 z 4 from file /path/image.png.`
- `Create button named start with text Start Mission.`
- `Set hero color to red.`
- `Set hero size to 22.`
- `Set box width to 140.`
- `Set box height to 80.`
- `When key w pressed:`
- `When button start clicked:`
- `When mouse clicked:`
- `Every 500 milliseconds:`
- `When hero touches enemy:`
- `Move hero forward by 1.`
- `Move hero backward by 1.`
- `Move hero left by 1.`
- `Move hero right by 1.`
- `Animate enemy left by 1 every 500 milliseconds.`
- `Show text Mission started.`
- `Play sound click.`
- `Create list named inventory with key, map.`
- `Add shield to list inventory.`
- `Save state to file /path/state.json.`
- `Load state from file /path/state.json.`
- `Fetch https://example.com as page.`

General canvas apps:

```angis
App, Anything Canvas.
Scene, canvas.
Window size 800 by 500.

Text, Use A and D to move the box. Click the ball.

Create rectangle named box at x 100 y 220.
Set box color to red.
Set box width to 120.
Set box height to 80.
Put box at (140, 220, 0).
Resize box to 140 by 90.

Make purple box named panel at (30, 90, 0) size 160 by 70.
Draw green circle named target at x 620 y 210 size 72 x 72.

Create circle named ball at x 520 y 210.
Set ball color to green.
Set ball size to 70.
Place ball at x 520 y 210 z 0.
Set ball size to 72 x 72.

Create text named title at x 24 y 32 saying Angis canvas objects.
Set title color to black.
Set title size to 22.

When key d pressed:
    Move box right by 12.

When key a pressed:
    Move box left by 12.

When ball clicked:
    Show text You clicked the ball.

When mouse clicks:
    Show text Mouse clicked.

When box bumps into ball:
    Show text Collision detected.

Each 500 ms:
    Animate ball left by 1 every 500 milliseconds.
```

`Scene, canvas.` opens a 2D visual app window. Angis draws named objects, applies object properties, places and resizes objects, runs key/click/timer events, moves objects, animates objects, and detects rectangle-style collisions. Event headers accept natural variants like `When a is pressed:`, `When ball clicked:`, `When mouse clicks:`, `Each 500 ms:`, and `When box bumps into ball:`.

Output intent:

```angis
say "hello"
print "hello"
show "hello"
display "hello"
tell me "hello"

Say, hello.
Print, hello.
Display, hello.
```

Variable intent:

```angis
set x to 5
make x equal 5
x is 5
let x = 5
store 5 as x

Set, x to 5.
Make, x equal 5.
Store, Ada Lovelace as name.
```

Math intent:

```angis
add 5 and 3
what is 5 plus 3
calculate 5 + 3
give me 5 added to 3
subtract 2 from 10
what is 10 minus 2
multiply 4 and 6
divide 20 by 5

Add, 5 and 3.
What is, 5 plus 3.
Calculate, 7 =6.
Divide, 20 by 5.
```

App intent:

```angis
App, My First App.
Scene, lobby.
Text, Hello inside the app.
Button, Click me.
```

When this runs in the IDE, Angis opens a separate app window with the text and buttons. In the CLI, Angis reports that the app is ready.

Loading screen intent:

```angis
App, Loading Demo.
Loding screen.
Text, App opened after loading.
```

When this runs in the IDE on macOS, Angis shows `angis loading/loading screen.png`, plays `angis loading/loading-adieo.mp3`, waits for the audio duration, then opens the app window. The parser also accepts full-path wording like `Loading screen picture /path/loading.png with audio /path/loading.mp3 then open app.`

Scene options:

```angis
Scene, lobby.
Scene, 3D world.
```

Example app:

```angis
# Minecraft style app

App, Minecraft Builder.
Text, Welcome to your block world.
Text, Collect wood.
Text, Mine stone.
Text, Build a shelter.
Text, Avoid monsters at night.

Button, Punch Tree.
Button, Mine Stone.
Button, Build House.
Button, Sleep.
```

Game intent:

```angis
Bird on screen.
When clicked, bird goes up.
Bird falls down.
Add obstacles.
If bird hits obstacle, end game.
```

When this runs in the IDE, Angis opens a playable bird game. Click the game window or press Space to flap upward. Gravity pulls the bird down, obstacles move across the screen, and a collision ends the run.

File intent:

```angis
Attach file at /Users/fellflow/Desktop/Angis/README.md.
Locate file at ~/Desktop/Angis/examples/hello.angis.
Find file at /tmp/note.txt.
```

Angis validates that the path exists and is a file, then reports the file name, size, and resolved path. It does not run shell commands or read the file contents.

Attach a file into an app window:

```angis
App, File Window.
Text, The attached file should appear below.
Set file attach to window at x 20 y 80 z 0 from file /Users/fellflow/Desktop/Angis/README.md.
Attach file /Users/fellflow/Desktop/Angis/README.md to window at x 20 y 80 z 0.
Button, Confirm File.
```

Attach an image into a 3D-world app:

```angis
App, San Andreas World.
Scene, 3D world.
Set file attach to window at x 0 y -40 z 4 from file /Users/fellflow/Desktop/Angis/assets/gta_style_city.png.
Button, Start Mission.
```

File attachment behavior:

- `.png`, `.gif`, `.jpg`, `.jpeg`, `.webp`, and `.bmp` render as images when local Pillow support is available. PNG/GIF work through Tk directly.
- Text/code files such as `.txt`, `.md`, `.angis`, `.py`, `.json`, `.csv`, `.html`, `.css`, and `.js` show a small preview.
- Any other file type still attaches as a file card with name, type, size, path, and x/y/z coordinates.

## Intermediate Representation

The parser normalizes phrases into these IR instructions:

- `PRINT(value)`
- `SET(name, value)`
- `ADD(left, right)`
- `SUBTRACT(left, right)`
- `MULTIPLY(left, right)`
- `DIVIDE(left, right)`

Each instruction carries a confidence score. Unrecognized or unclear phrases raise safe, helpful errors with syntax hints.

## Extending Phrases

Add new phrase support in `angis/intents.py` by adding an `IntentPattern` to `PATTERNS`. Patterns should:

- Use a precise regular expression.
- Return one IR instruction.
- Assign a confidence score between `0.0` and `1.0`.
- Keep ambiguous phrases lower confidence than direct forms.

## Natural Language & AI Fallback

Angis features a local AI fallback system in `angis/ai.py`. If the standard intent parser doesn't understand a phrase, it will attempt to:
1. Match it against a cache of known "natural" phrases.
2. Use heuristics to identify common patterns (like `x = 5`).
3. Handle basic keywords in additional languages (Italian, Portuguese, Japanese).

You can "teach" Angis new phrases by adding them to `~/.angis_ai_cache.json` or by using the `angis.ai` module programmatically.

## Security

Angis does not use `eval()` or `exec()`, and Angis programs cannot run shell commands. The IDE only opens and saves `.angis` files.

## Tests

```bash
python -m unittest discover
```
