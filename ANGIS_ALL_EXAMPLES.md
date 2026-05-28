# Angis all examples

Total .angis example files: 105

This file contains every example from /Users/fellflow/Apps/Angis/examples.

## 1. 3d_flappy_bird.angis

```angis
App, 3D Flappy Bird.
Scene, true 3D.
Window size 800 by 600.
camera at x 0 y 0 z -10.
mode third person.

Set score to 0.
Set gravity to 2.
Set flap to -18.
Set bird_y to 150.
Set velocity to 0.
Set pipe_z to 15.
Set pipe_speed to 0.4.
Set game_over to false.

Create sphere named bird at x 0 y 150 z 0.
Set bird color to #ffcc00.
Set bird size to 15.

Create box named upperPipe at x 0 y -60 z 15.
Set upperPipe color to #22c55e.
Set upperPipe scale_x to 2.
Set upperPipe scale_y to 1.
Set upperPipe scale_z to 0.5.

Create box named lowerPipe at x 0 y 330 z 15.
Set lowerPipe color to #22c55e.
Set lowerPipe scale_x to 2.
Set lowerPipe scale_y to 1.
Set lowerPipe scale_z to 0.5.

on click:
    If game_over is true:
        Set score to 0.
        Set bird_y to 150.
        Set velocity to 0.
        Set pipe_z to 15.
        Set bird y to bird_y.
        Set upperPipe z to pipe_z.
        Set lowerPipe z to pipe_z.
        Set game_over to false.
    If game_over is false:
        Set velocity to flap.

every 30 ms:
    If game_over is false:
        Set velocity to velocity plus gravity.
        Set bird_y to bird_y plus velocity.
        Set bird y to bird_y.
        Set pipe_z to pipe_z minus pipe_speed.
        Set upperPipe z to pipe_z.
        Set lowerPipe z to pipe_z.
        If pipe_z is less than -2:
            Set pipe_z to 15.
            Add 1 to score.
        If bird_y is greater than 550:
            Set game_over to true.
        If bird_y is less than 10:
            Set game_over to true.
        If pipe_z is less than 1:
            If pipe_z is greater than -1:
                If bird_y is less than 70:
                    Set game_over to true.
                If bird_y is greater than 230:
                    Set game_over to true.
```

## 2. alternative_phrase_words.angis

```angis
# Alternative words make one phrase understand word choices

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
```

## 3. angis_flow.angis

```angis
# ─── Angis Flow — Everything Angis Can & Cannot Code ───
# Run: python -m angis run examples/angis_flow.angis
# Tours 42 capability categories and lists remaining limitations.

Say, ═══ Angis: A General-Purpose Language Tour ═══

# ============ 1. VARIABLES & DATA TYPES ============
Say, === 1. Variables & Data Types ===
Set my_int to 42.
Set my_float to 3.14.
Set my_string to "Hello Angis".
Set my_bool to true.
Set my_list to [1, 2, 3].
Set my_dict to {name: "Ada", score: 100}.
Say my_int.
Say my_string.
Show my_bool.

# ============ 2. MATH & OPERATORS ============
Say, === 2. Math & Operators ===
Set sum to 10 + 5.
Set diff to 10 - 5.
Set product to 10 * 5.
Set quotient to 10 / 3.
Set remainder to 10 % 3.
Set power to 2 ** 8.
Set word_sum to 10 plus 5.
Set word_diff to 10 minus 5.
Set word_product to 10 times 5.
Say sum.
Say power.

# ============ 3. COMPARISONS & BOOLEANS ============
Say, === 3. Comparisons & Booleans ===
If 5 is greater than 3:
    Say 5 is greater than 3.
If 4 equals 4:
    Say 4 equals 4.
If 2 is at most 5:
    Say 2 is at most 5.
If 5 is between 1 and 10:
    Say 5 is between 1 and 10.
If 5 is greater than 2 and 5 is less than 10:
    Say Combined conditions with and.
If 5 is greater than 2 or 5 is less than 0:
    Say Combined conditions with or.
If not 5 is less than 0:
    Say Not operator works.
Set name to "Angis".
If name starts with "Ang":
    Say Starts with works.
If name contains "gis":
    Say Contains works.
Unless 5 is less than 0:
    Say Unless works.

# ============ 4. CONTROL FLOW ============
Say, === 4. Control Flow ===
# If/Else
Set score to 85.
If score is at least 90:
    Say Grade A.
Else:
    If score is at least 80:
        Say Grade B.
    Else:
        Say Other grade.

# While loop
Set count to 0.
While count is less than 3:
    Say count.
    Set count to count + 1.

# Repeat loop
Repeat 3 times:
    Say Repeating.

# For each
Set items to [a, b, c].
For each, item in items:
    Show item.

# For each with range
For each x in range from 1 to 5:
    Show x.

# Switch/Match
Set color to 2.
Switch color:
    Case 1:
        Say Red.
    Case 2:
        Say Blue.
    Default:
        Say Unknown.

# ============ 5. FUNCTIONS ============
Say, === 5. Functions ===
Define greet with name:
    Show "Hello".
    Show name.
    Return "done".

Call greet with World as greeting.
Show greeting.

Define addPair with left and right:
    Set total to left + right.
    Return total.

Call addPair with 7, 8 as sum_result.
Show sum_result.

# Recursion via loop
Define factorial with n:
    Set result to 1.
    Set i to 1.
    While i is at most n:
        Set result to result * i.
        Set i to i + 1.
    Return result.

Call factorial with 6 as fact_6.
Show fact_6.

# ============ 6. LISTS ============
Say, === 6. Lists ===
Create list named fruits with apple, banana, cherry.
Add date to list fruits.
Put elderberry in fruits.
Remove banana from fruits.

Sort fruits as sorted_fruits.
Reverse sorted_fruits as reversed_fruits.
Shuffle fruits as shuffled_fruits.

Get first item of fruits as first_fruit.
Get last item of fruits as last_fruit.
Pick random item from fruits as random_fruit.
Get length of fruits as fruit_count.

Show sorted_fruits.
Show first_fruit.
Show fruit_count.

# List extend
Create list named more with grape, kiwi.
Extend fruits with more as extended.
Show extended.

# List unique
Create list named dupes with 1, 2, 2, 3, 3.
unique dupes as uniq.
Show uniq.

# List sum and average
Get sum of [10, 20, 30] as total_sum.
Get average of [10, 20, 30] as avg_val.
Show total_sum.
Show avg_val.

# List insert
Insert 0 at index 0 in fruits as with_pineapple.
Show with_pineapple.

# Comprehensions
Set nums to [1, 2, 3, 4, 5].
Set doubled to for each x in nums collect x * 2.
Show doubled.

# ============ 7. MAPS / DICTIONARIES ============
Say, === 7. Maps & Dictionaries ===
Create dictionary named user with name: Ada, role: admin, score: 42.
Set user_email to "ada@example.com".
Get score from user as user_score.
Get keys from user as user_keys.
Get values from user as user_values.
Remove key role from user as cleaned_user.

# Map merge
Create dictionary named extras with level: 5, title: wizard.
Merge user with extras as merged_user.
Show merged_user.

Show user_score.
Show user_keys.

# Check if key exists via stdlib
Say Map has key check available.

# ============ 8. BLUEPRINTS (CLASSES) ============
Say, === 8. Blueprints (Classes) ===
Blueprint Animal with name: "unknown", sound: "silent".
Define method speak for Animal:
    Show self.name.
    Return self.sound.

Create Animal named dog with name: "Fido", sound: "woof".
Call dog.speak as dog_sound.
Show dog_sound.

# Objects are real Python classes with isinstance, type, __dict__
Say Blueprint instances are native Python class objects.
Say isinstance check and type() work natively.

# Clone an object
Clone object dog as twin.
Show twin.

# List object fields
List object fields dog as fields.
Show fields.

# Operator overloading
Blueprint Vec2 with x: 0, y: 0.
Define + for Vec2 with left, right:
    Set nx to left.x + right.x.
    Set ny to left.y + right.y.
    Create Vec2 named result with x: nx, y: ny.
    Return result.

Create Vec2 named a with x: 3, y: 4.
Create Vec2 named b with x: 1, y: 2.
Set c to a + b.
Show c.x.
Show c.y.

# Constructor
On create for Vec2 with x and y:
    Say Vec2 created.

# ============ 9. FILE I/O ============
Say, === 9. File I/O ===
Write Hello Angis to file /tmp/angis_flow_demo.txt as write_result.
Show write_result.
Append text ! to file /tmp/angis_flow_demo.txt as append_result.
Read file /tmp/angis_flow_demo.txt as content.
Show content.

Get file name of /tmp/angis_flow_demo.txt as file_name.
Get file extension of /tmp/angis_flow_demo.txt as file_ext.
Get stem from /tmp/angis_flow_demo.txt as file_stem.
Check if file exists at /tmp/angis_flow_demo.txt as file_exists.
Show file_name.
Show file_ext.
Show file_exists.

# File info
Get info for file /tmp/angis_flow_demo.txt as info.
Show info.

# File glob and directory listing available
Say File glob, list dir, copy, move, delete available.

# ============ 10. TEXT OPERATIONS ============
Say, === 10. Text Operations ===
Set sample to "  Hello Angis World!  ".
Get uppercase of sample as upper.
Get lowercase of sample as lower.
Get trimmed text of sample as trimmed.
Get words of sample as word_list.
Split trimmed by space as split_words.
Join split_words with - as slug.
Replace World in trimmed with Flow as replaced.
Show trimmed.
Show slug.
Show replaced.

# Text checks
Check if trimmed starts with Hello as starts_ok.
Check if trimmed ends with World as ends_ok.
Check if trimmed contains Angis as contains_ok.
Show starts_ok.
Show ends_ok.
Show contains_ok.

# Text transform
Slugify "Hello Angis World" as slugified.
Show slugified.

# Reverse text
Reverse text Angis as reversed_text.
Show reversed_text.

# ============ 11. MATH FUNCTIONS ============
Say, === 11. Math Functions ===
Round 3.7 as rounded.
Floor 3.7 as floored.
Ceil 3.2 as ceiled.
Absolute -5 as absoluted.
Calculate square root of 81 as sqrt_val.
Raise 2 to power 10 as pow_val.
Clamp 14 between 1 and 10 as clamped.
Pick random number between 1 and 100 as random_num.
Show rounded.
Show sqrt_val.
Show clamped.
Show random_num.

# More math (binary comparisons)
Find the maximum of 10 and 30 as max_val.
Find the minimum of 10 and 30 as min_val.
Show max_val.
Show min_val.

# ============ 12. JSON ============
Say, === 12. JSON ===
Create dictionary named person with name: Ada, age: 30.
Turn person into json as json_text.
Show json_text.
Say JSON parse also available.

# ============ 13. SQLite ============
Say, === 13. SQLite ===
Create database file /tmp/angis_flow.db named test_db.
Run query create table if not exists notes (text text) on test_db.
Run query insert into notes values ("Angis stores data") on test_db.
Run query select * from notes on test_db as rows.
Show rows.

# ============ 14. REGEX ============
Say, === 14. Regex ===
Find pattern \d+ in abc123xyz as found_digits.
Show found_digits.
Replace pattern \d+ in abc123xyz with 456 as replaced_text.
Show replaced_text.

# ============ 15. HASHING & ENCODING ============
Say, === 15. Hashing & Encoding ===
Hash text hello with sha256 as hashed.
Show hashed.
Encode text hello as base64 as encoded_text.
Show encoded_text.
Base64 decode encoded_text as decoded_text.
Show decoded_text.

# ============ 16. VALIDATION ============
Say, === 16. Validation ===
Set email_str to "user@example.com".
Check if email_str is an email as valid_email.
Show valid_email.
Set url_str to "https://example.com:443/path".
Parse url url_str as url_parts.
Show url_parts.

# ============ 17. SHELL EXECUTION ============
Say, === 17. Shell Execution ===
Use shell to run "echo hello from shell" as shell_result.
Show shell_result.
Say Shell provides stdout, stderr, returncode.
Say Use shell spawn for background processes.

# ============ 18. SYSTEM INFO ============
Say, === 18. System Info ===
Get system platform as platform.
Show platform.

# ============ 18. TIME & DATE ============
Say, === 18. Time & Date ===
Get current time as now.
Show now.
Get timestamp as epoch.
Show epoch.
Get todays date as today.
Show today.

# ============ 19. ERROR HANDLING ============
Say, === 19. Error Handling ===
Try:
    Raise error Something went wrong.
Except as err:
    Say Caught error.
    Show err.

Try:
    Say No error here.
Except as e:
    Say Should not print.

Assert 2 + 2 is 4 else Math is broken.
Say Assertion passed.

# ============ 20. CUSTOM PHRASES (DSL) ============
Say, === 20. Custom Phrases (DSL) ===
Define phrase give {amount} points to {target}:
    Set target.score to target.score + amount.

Create dictionary named player with score: 0.
Give 50 points to player.
Give 25 points to player.
Show player.score.

Define phrase start game means Say Game started.
Start game.

Define phrase award {target:name} with {amount:number} points:
    Set target.score to target.score + amount.

Create dictionary named hero with score: 0.
Award hero with 100 points.
Show hero.score.

# ============ 21. PYTHON INTEROP ============
Say, === 21. Python Interop ===
import python os as os
import python math as math
import python json as json

Get os getcwd as cwd.
Show cwd.
Run math degrees with value: 3.14159 as deg.
Show deg.
Run json dumps with obj: {lang: Angis, can_code: yes}, indent: 2 as pretty.
Show pretty.

# Inline Python
Run python: py_answer = 42.
Show py_answer.

# Python eval
Eval python math.sqrt(144) as sqrt_py.
Show sqrt_py.

# ============ 22. MODULES & INCLUDES ============
Say, === 22. Modules & Includes ===
Say Include other .angis files with include filename.angis.
Say Use modules with use module path as name.

# ============ 23. DEBUGGING ============
Say, === 23. Debugging ===
Say Debug all prints runtime state.
Say Breakpoint pauses execution.

# ============ 24. UUID & IDENTIFIERS ============
Say, === 24. UUID & Identifiers ===
Make uuid as unique_id.
Show unique_id.

# ============ 25. CONCURRENCY ============
Say, === 25. Concurrency ===
Define slow_calc with n:
    Return n * 2.
Run slow_calc in background with 21 as job.
Wait for job as doubled.
Show doubled.

# ============ 26. COMPREHENSIONS ============
Say, === 26. Comprehensions ===
Set nums to [1, 2, 3, 4, 5].
Set dbl to for each x in nums collect x * 2.
Show dbl.

# Lambda
Set doubler to lambda x => x * 2.
Show doubler.

# ============ 27. ENVIRONMENT & ARGS ============
Say, === 27. Environment ===
env USER as user_name.
Show user_name.
Get variable PATH as path_var.
Show path_var.

# ============ 29. 2D CANVAS APPS ============
Say, === 29. 2D Canvas Apps ===
Say App / Scene canvas / Create text, button, input, slider, checkbox.
Say When clicked / When key pressed / Every ms timer / on click.
Say 2D shapes: circle, rectangle. Collision detection.

# ============ 31. EXPORT & BUILD ============
Say, === 31. Export & Build ===
Say Export app to HTML.
Say Build standalone binary: python -m angis build file.angis -o out/.
Say Produces 11MB native Mach-O / ELF / PE executable.
Say No Python installation needed on target machine.

# ============ 32. RANDOM ============
Say, === 32. Random ===
Flip coin as flip.
Show flip.
Pick random number between 1 and 6 as dice.
Show dice.
Pick random item from [a, b, c] as pick.
Show pick.

# ============ 33. STATISTICS ============
Say, === 33. Statistics ===
Get median of [1, 2, 3, 4, 100] as med.
Show med.
Get mode of [1, 1, 2, 3] as mode_val.
Show mode_val.
Get standard deviation of [2, 4, 4, 4, 5, 5, 7, 9] as stdev_val.
Show stdev_val.

# ============ 34. SOCKET / NETWORKING ============
Say, === 34. Networking ===
Say HTTP fetch with fetch url.
Say Socket support for TCP/UDP/WebSocket.

# ============ 35. BITWISE OPERATIONS ============
Say, === 35. Bitwise Operations ===
Say Bitwise and, or, xor, not, shift left, shift right.

# ============ 36. OBJECT OPERATIONS ============
Say, === 36. Object Operations ===
Say Operator overloading: define + for Blueprint with param.
Say Clone objects, list fields.

# ============ 37. FILE DIRECTORY LISTING ============
Say, === 37. Directory Listing ===
Say List directory available via stdlib.

# ============ 38. MULTI-LANGUAGE SUPPORT ============
Say, === 38. Multi-Language Support ===
Say Built-in languages: en, es, fr, de, it, pt.
Say Use: set_language "es" to switch parser keywords.

# ============ 39. PATH OPERATIONS ============
Say, === 39. Path Operations ===
Get file name from /tmp/folder/data.csv as p_name.
Get file extension from /tmp/folder/data.csv as p_ext.
Get folder from /tmp/folder/data.csv as p_folder.
Get stem from /tmp/folder/data.csv as p_stem.
Join path /tmp/folder with data.csv as p_joined.
Resolve path .. as p_resolved.
Show p_name.
Show p_ext.
Show p_joined.
Show p_resolved.

# ============ 40. SLEEP / DELAY ============
Say, === 40. Sleep ===
Say Sleep N ms pauses execution.

# ============ 41. BITWISE OPERATORS ============
Say, === 41. Bitwise Operators ===
Set bw_a to 12.
Set bw_b to 10.
Set bw_and to bw_a & bw_b.
Set bw_or to bw_a | bw_b.
Set bw_xor to bw_a ^ bw_b.
Set bw_not to ~bw_a.
Set bw_shl to bw_a << 2.
Set bw_shr to bw_a >> 1.
Say Bitwise on 12 & 10: and, or, xor, not, shift left, shift right.
Show bw_and.
Show bw_or.
Show bw_xor.
Show bw_not.
Show bw_shl.
Show bw_shr.

# ============ 42. RAW BYTE BUFFERS ============
Say, === 42. Raw Byte Buffers ===
Use buffer create with size: 16 as bb.
Use buffer write_int32 with buf: bb, offset: 0, value: 42 as _.
Use buffer write_int32 with buf: bb, offset: 4, value: 100 as _.
Use buffer write with buf: bb, offset: 8, data: "angis" as _.
Use buffer read_int32 with buf: bb, offset: 0 as bb_v1.
Use buffer read_int32 with buf: bb, offset: 4 as bb_v2.
Use buffer read with buf: bb, offset: 8, length: 5 as bb_str.
Use buffer hex with buf: bb as bb_hex.
Show bb_v1.
Show bb_v2.
Show bb_str.
Show bb_hex.

# ============ 43. STRUCT PACK / UNPACK ============
Say, === 43. Struct Pack / Unpack ===
Use struct pack with format: "<3i", values: [10, 20, 30] as bb_packed.
Use struct sizeof with format: "<3i" as bb_sz.
Use buffer hex with buf: bb_packed as bb_p_hex.
Show bb_sz.
Show bb_p_hex.
Use struct unpack with format: "<3i", buf: bb_packed as bb_vals.
Show bb_vals.
Use buffer create with size: 4 as bb_target.
Use struct pack_into with format: "<i", buf: bb_target, offset: 0, values: [255] as _.
Use struct unpack_from with format: "<I", buf: bb_target, offset: 0 as bb_unpacked.
Show bb_unpacked.

# ============ 44. C FFI (Foreign Function Interface) ============
Say, === 44. C FFI (Native Calls) ===
Use ffi load with path: "libc.dylib" as bb_libc.
Use ffi int32 as bb_int32.
Use ffi sizeof with value: bb_int32 as bb_int_sz.
Say Size of int32.
Show bb_int_sz.
Use ffi call with lib: bb_libc, name: "printf", args: ["C FFI works!\n"] as bb_ret.
Say printf returned.
Show bb_ret.

# ============ 45. MEMORY-MAPPED FILES ============
Say, === 45. Memory-Mapped Files ===
Use file write with path: "/tmp/angis_mmap_demo.bin", text: "MMAP demo OK" as _.
Use mmap map with path: "/tmp/angis_mmap_demo.bin", length: 12 as bb_map.
Use mmap read with map: bb_map, offset: 0, length: 12 as bb_map_data.
Show bb_map_data.
Use mmap close with map: bb_map as _.

# ============ ═══ LIMITATIONS ═══ ============
Say, ═══ What Angis Cannot Code ═══
Say, 1. No cloud AI API dependencies. All parsing is offline.
Say, 2. Not production-scale: prototype maturity.
Say, 3. No real-time OS or embedded targets.
Say, Everything else is fair game — see above for 46 capability categories.

# ─── DONE ───
Say Done.
Say ═══ Angis Flow Complete ═══
Say You can code almost anything in Angis.
Say For anything else, Python interop covers you.
```

## 4. anything_canvas.angis

```angis
# General visual app example

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
    Play sound click.

When mouse clicks:
    Show text Mouse clicked.

When box bumps into ball:
    Show text Collision detected.

Each 500 ms:
    Animate ball left by 1 every 500 milliseconds.
```

## 5. anything_language.angis

```angis
# General Angis wording over safe local standard library actions

Create list named names with Ada, Grace, Linus.
Create dictionary named player with name: Ada, score: 42.

When I say shout {message:text}, it means Set taughtLoud to text uppercase with text: message and then Show taughtLoud.
Teach Angis count names to mean Count length of names as taughtCount and then Show taughtCount.
When I say quiet {message:text}:
    Set taughtQuiet to text lowercase with text: message.
    Show taughtQuiet.

Ask text to uppercase with text: hello from angis as loud.
Ask text to starts with text: hello from angis, prefix: hello as starts.
Tell math to clamp with value: 14, min: 1, max: 10 as clamped.
Get math maximum with left: 2, right: 9 as biggest.
Run list at with values: names, index: 1 as secondName.
Run list slice with values: names, start: 0, end: 2 as firstTwo.
Get map has with value: player, key: score as hasScore.
Get path stem with path: /Users/fellflow/Desktop/Angis/examples/hello.angis as fileStem.
Get uppercase of hello natural words as naturalLoud.
Calculate square root of 81 as naturalRoot.
Count length of names as naturalCount.
Find file extension of /Users/fellflow/Desktop/Angis/examples/hello.angis as naturalExtension.
Check if file exists at /Users/fellflow/Desktop/Angis/examples/hello.angis as naturalExists.
Set assignedLoud to uppercase of hello assigned words.
Make assignedRoot equal square root of 81.
Let assignedCount = length of names.
Set assignedExtension to file extension of /Users/fellflow/Desktop/Angis/examples/hello.angis.
Set assignedExists to file exists at /Users/fellflow/Desktop/Angis/examples/hello.angis.
Set bridgeLoud to text uppercase with text: hello bridge words.
Make bridgeClamp equal math clamp with value: 14, min: 1, max: 10.
Let bridgeSecond = list at with values: names, index: 1.
Set bridgeHasScore to map has with value: player, key: score.

Shout hello taught words.
Count names.
Quiet HELLO BLOCK WORDS.

Show loud.
Show starts.
Show clamped.
Show biggest.
Show secondName.
Show firstTwo.
Show hasScore.
Show fileStem.
Show naturalLoud.
Show naturalRoot.
Show naturalCount.
Show naturalExtension.
Show naturalExists.
Show assignedLoud.
Show assignedRoot.
Show assignedCount.
Show assignedExtension.
Show assignedExists.
Show bridgeLoud.
Show bridgeClamp.
Show bridgeSecond.
Show bridgeHasScore.
```

## 6. apex_style.angis

```angis
# Apex Legends style world app

App, Apex Drop Zone.
Scene, 3D world.
Text, Choose your legend.
Text, Drop into the arena.
Text, Find weapons.
Text, Use tactical abilities.
Text, Stay inside the ring.

Button, Pick Legend.
Button, Launch Drop.
Button, Ping Enemy.
Button, Use Tactical.
Button, Use Ultimate.
Button, Champion Squad.
```

## 7. app.angis

```angis
# Angis app example

App, My First Angis App.
Text, Hello inside a real app window.
Text, This is not just output text.
Button, Click me.
Button, Save.
```

## 8. blueprints.angis

```angis
# Reusable object blueprints

Blueprint Player with name: Ada, health: 10, score: 0.
Create Player named hero with name: Grace.
Create Player named enemy with name: Boss, health: 30.

Define method heal for Player with amount:
    Set, self.health to self.health + amount.
    Return, self.health.

Define method scorePoint for Player:
    Set, self.score to self.score + 1.
    Return, self.score.

Call, hero.heal with 5 as heroHealth.
Call, hero.scorePoint as heroScore.
Call, enemy.heal with 2 as enemyHealth.

Show, hero.name.
Show, heroHealth.
Show, heroScore.
Show, enemy.name.
Show, enemyHealth.
```

## 9. booleans.angis

```angis
# Boolean values

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
```

## 10. bouncing_balls.angis

```angis
App, Bouncing Balls Simulation.
Scene, canvas.
Window size 700 by 550.
Dark background.

# --- Create the balls ---

Create circle named ball1 at x 100 y 50.
Set ball1 color to #ff6b6b.
Set ball1 size to 28.

Create circle named ball2 at x 250 y 80.
Set ball2 color to #ffd93d.
Set ball2 size to 22.

Create circle named ball3 at x 400 y 40.
Set ball3 color to #6bcb77.
Set ball3 size to 34.

Create circle named ball4 at x 550 y 100.
Set ball4 color to #4d96ff.
Set ball4 size to 18.

Create circle named ball5 at x 350 y 150.
Set ball5 color to #c084fc.
Set ball5 size to 26.

# --- Physics state ---

Set b1x to 100. Set b1y to 50. Set b1dx to 4. Set b1dy to 3.
Set b2x to 250. Set b2y to 80. Set b2dx to -3. Set b2dy to 5.
Set b3x to 400. Set b3y to 40. Set b3dx to 2. Set b3dy to -4.
Set b4x to 550. Set b4y to 100. Set b4dx to -5. Set b4dy to 2.
Set b5x to 350. Set b5y to 150. Set b5dx to 3. Set b5dy to -4.

Set gravity to 0.35.
Set damping to 0.85.
Set left_wall to 5.
Set right_wall to 665.
Set top_wall to 5.
Set bottom_wall to 515.

Set bounce_count to 0.

Create text named title at x 10 y 10 saying "Bouncing Balls — Physics Simulation".
Set title color to #94a3b8.
Set title size to 14.

Create text named info at x 10 y 510 saying "Bounces: 0".
Set info color to #64748b.
Set info size to 12.

# --- Physics loop ---

every 30 ms:
    # ---- Ball 1 ----
    Set b1dy to b1dy + gravity.
    Set b1x to b1x + b1dx.
    Set b1y to b1y + b1dy.
    If b1x is less than left_wall:
        Set b1x to left_wall.
        Set b1dx to 0 - b1dx.
        Add 1 to bounce_count.
    If b1x is greater than right_wall:
        Set b1x to right_wall.
        Set b1dx to 0 - b1dx.
        Add 1 to bounce_count.
    If b1y is less than top_wall:
        Set b1y to top_wall.
        Set b1dy to 0 - b1dy.
        Add 1 to bounce_count.
    If b1y is greater than bottom_wall:
        Set b1y to bottom_wall.
        Set b1dy to 0 - (b1dy * damping).
        Add 1 to bounce_count.
    Set ball1 x to b1x.
    Set ball1 y to b1y.

    # ---- Ball 2 ----
    Set b2dy to b2dy + gravity.
    Set b2x to b2x + b2dx.
    Set b2y to b2y + b2dy.
    If b2x is less than left_wall:
        Set b2x to left_wall.
        Set b2dx to 0 - b2dx.
        Add 1 to bounce_count.
    If b2x is greater than right_wall:
        Set b2x to right_wall.
        Set b2dx to 0 - b2dx.
        Add 1 to bounce_count.
    If b2y is less than top_wall:
        Set b2y to top_wall.
        Set b2dy to 0 - b2dy.
        Add 1 to bounce_count.
    If b2y is greater than bottom_wall:
        Set b2y to bottom_wall.
        Set b2dy to 0 - (b2dy * damping).
        Add 1 to bounce_count.
    Set ball2 x to b2x.
    Set ball2 y to b2y.

    # ---- Ball 3 ----
    Set b3dy to b3dy + gravity.
    Set b3x to b3x + b3dx.
    Set b3y to b3y + b3dy.
    If b3x is less than left_wall:
        Set b3x to left_wall.
        Set b3dx to 0 - b3dx.
        Add 1 to bounce_count.
    If b3x is greater than right_wall:
        Set b3x to right_wall.
        Set b3dx to 0 - b3dx.
        Add 1 to bounce_count.
    If b3y is less than top_wall:
        Set b3y to top_wall.
        Set b3dy to 0 - b3dy.
        Add 1 to bounce_count.
    If b3y is greater than bottom_wall:
        Set b3y to bottom_wall.
        Set b3dy to 0 - (b3dy * damping).
        Add 1 to bounce_count.
    Set ball3 x to b3x.
    Set ball3 y to b3y.

    # ---- Ball 4 ----
    Set b4dy to b4dy + gravity.
    Set b4x to b4x + b4dx.
    Set b4y to b4y + b4dy.
    If b4x is less than left_wall:
        Set b4x to left_wall.
        Set b4dx to 0 - b4dx.
        Add 1 to bounce_count.
    If b4x is greater than right_wall:
        Set b4x to right_wall.
        Set b4dx to 0 - b4dx.
        Add 1 to bounce_count.
    If b4y is less than top_wall:
        Set b4y to top_wall.
        Set b4dy to 0 - b4dy.
        Add 1 to bounce_count.
    If b4y is greater than bottom_wall:
        Set b4y to bottom_wall.
        Set b4dy to 0 - (b4dy * damping).
        Add 1 to bounce_count.
    Set ball4 x to b4x.
    Set ball4 y to b4y.

    # ---- Ball 5 ----
    Set b5dy to b5dy + gravity.
    Set b5x to b5x + b5dx.
    Set b5y to b5y + b5dy.
    If b5x is less than left_wall:
        Set b5x to left_wall.
        Set b5dx to 0 - b5dx.
        Add 1 to bounce_count.
    If b5x is greater than right_wall:
        Set b5x to right_wall.
        Set b5dx to 0 - b5dx.
        Add 1 to bounce_count.
    If b5y is less than top_wall:
        Set b5y to top_wall.
        Set b5dy to 0 - b5dy.
        Add 1 to bounce_count.
    If b5y is greater than bottom_wall:
        Set b5y to bottom_wall.
        Set b5dy to 0 - (b5dy * damping).
        Add 1 to bounce_count.
    Set ball5 x to b5x.
    Set ball5 y to b5y.

    # ---- Update HUD ----
    Turn bounce_count into text as bc.
    Set info text to "Bounces: " + bc.
```

## 11. capabilities_demo.angis

```angis
App, Angis Full Capabilities Demo.
Scene, true 3D.
Window size 1000 by 700.
camera at x 0 y 0 z -14.
mode third person.

Set demo_step to 0.
Set started to false.

Create text named step_label at x 0 y 280 z 0 saying "Angis: Full Language Capabilities Demo".
Set step_label color to white.
Set step_label size to 14.

Create text named code_display at x 0 y 240 z 0 saying "19 categories | Press Space or click to begin".
Set code_display color to #aaaaaa.
Set code_display size to 10.

Create sphere named demo_sphere at x -3 y 0 z 0.
Set demo_sphere color to #4488ff.
Set demo_sphere size to 1.0.
Set demo_sphere auto_rotate_x to 0.02.
Set demo_sphere auto_rotate_y to 0.03.

Create cube named demo_cube at x 3 y 0 z 0.
Set demo_cube color to #ff6644.
Set demo_cube size to 0.9.
Set demo_cube auto_rotate_y to 0.05.

Create pyramid named demo_pyramid at x -3 y -3 z 0.
Set demo_pyramid color to #44ff88.
Set demo_pyramid size to 0.9.
Set demo_pyramid auto_rotate_y to -0.04.

Create cylinder named demo_cylinder at x 3 y -3 z 0.
Set demo_cylinder color to #ffaa44.
Set demo_cylinder size to 0.8.
Set demo_cylinder auto_rotate_x to 0.03.

Create torus named demo_torus at x 0 y 3 z 0.
Set demo_torus color to #ff44ff.
Set demo_torus size to 0.8.
Set demo_torus auto_rotate_y to 0.04.

Create text named var_display at x 0 y -50 z 0 saying "".
Set var_display color to #88ff88.
Set var_display size to 11.

Create text named list_display at x 0 y -100 z 0 saying "".
Set list_display color to #ffcc88.
Set list_display size to 11.

Create text named event_log at x 0 y -180 z 0 saying "Angis Capabilities Demo — Press Space or click to start".
Set event_log color to #8888ff.
Set event_log size to 11.

Create text named help_text at x 0 y -230 z 0 saying "Space = next  |  R = reset  |  Click = next step  |  19 categories".
Set help_text color to #666666.
Set help_text size to 9.

Set titles to ["1/19 Variables & Data Types", "2/19 Expressions & Operators", "3/19 Control Flow: If/Else/Unless", "4/19 Loops: While/For/Repeat", "5/19 Lists", "6/19 Maps & Dictionaries", "7/19 Functions & Recursion", "8/19 Blueprints & Methods", "9/19 File I/O", "10/19 Text Operations", "11/19 Math & Random", "12/19 List Comprehensions", "13/19 Custom DSL Phrases", "14/19 Python Interop", "15/19 Error Handling", "16/19 Time & Date", "17/19 Path Operations", "18/19 3D Graphics", "19/19 Events: Click / Key / Timer"].

Set descs to ["set to / add / subtract / multiply / divide | integers floats strings booleans", "plus minus times over mod | + - * / % ** | is greater than less than equals", "if / else / unless / and / or / not | contains / starts with / is between", "while / for each / repeat N times | break / continue | range from A to B", "create list / add / put / remove | sort / reverse / shuffle | first last random", "create dict / set / get / keys / values / merge | blueprints with fields", "define / call / return | recursion | parameters | yield generators", "blueprint / create instance / methods with self | inheritance", "write / read file | copy / move / delete | info / exists / glob / list dir", "split / join / replace | upper / lower / trim | length / letters / regex", "round / floor / ceil / abs | sqrt / pow / clamp | random number / item", "for each collect / filter / reduce | lambda arrow fn | map transform", "define phrase {name:type} slots | optional words | custom commands", "import python / run python: / eval python | {{py: inline}}", "try / except / finally | raise error | assert", "get current time / timestamp / todays date | date arithmetic", "get file name / ext / folder / stem | join path", "sphere cube pyramid cylinder torus | auto-rotate | colors sizes positions", "on click / when key pressed / every N ms | mouse moved | collision"].

Set total to length of titles.

Define, show_step with n:
    Get item at index n of titles as t.
    Get item at index n of descs as d.
    Set step_label text to t.
    Set code_display text to d.

on click:
    If started is false:
        Set started to true.
        show_step with 0.
        Set demo_step to 1.
    If started is true:
        If demo_step is less than total:
            show_step with demo_step.
            Set demo_step to demo_step + 1.
        If demo_step is at least total:
            Set demo_step to 0.
            show_step with 0.

When key space pressed:
    If started is false:
        Set started to true.
        show_step with 0.
        Set demo_step to 1.
    If started is true:
        If demo_step is less than total:
            show_step with demo_step.
            Set demo_step to demo_step + 1.
        If demo_step is at least total:
            Set demo_step to 0.
            show_step with 0.

When key r pressed:
    Set demo_step to 0.
    Set started to false.
    Set step_label text to "Angis: Full Language Capabilities Demo".
    Set code_display text to "19 categories | Press Space or click to begin".
    Set var_display text to "".
    Set list_display text to "".

Define, run_step:
    Set idx to demo_step - 1.
    If idx is 0:
        Set x to 42.
        Set y to 3.14.
        Set ready to true.
        Set name to "Angis".
        Turn x into text as xs.
        Turn y into text as ys.
        Turn ready into text as rds.
        Set var_display text to "int: " + xs + "  float: " + ys + "  bool: " + rds + "  str: " + name.
        Set list_display text to "Types: integer / float / string / boolean / list / map".
    If idx is 1:
        Set a to (5 + 3) * 2.
        Set b to 10 / 3.
        Set c to a is greater than 10.
        Raise 2 to power 8 as p.
        Turn a into text as as.
        Turn p into text as ps.
        Turn c into text as cs.
        Set var_display text to "(5+3)*2=" + as + "  10/3=3.33  >10:" + cs + "  2^8=" + ps.
        Set list_display text to "Operators: + - * / % ** plus minus times over mod".
    If idx is 2:
        Set score to 75.
        Set grade to "Fail".
        If score is at least 70:
            Set grade to "Pass".
        Unless score is less than 0:
            Set valid to "ok".
        Turn score into text as ss.
        Set var_display text to "score:" + ss + " grade:" + grade + " valid:" + valid.
        Set list_display text to "if/else/unless | and/or/not | contains/starts with/is between".
    If idx is 3:
        Set sum to 0.
        Set n to 1.
        While n is at most 5:
            Set sum to sum + n.
            Set n to n + 1.
        For each x in range from 1 to 4:
            Set sum to sum + x.
        Repeat 3 times:
            Set sum to sum + 10.
        Turn sum into text as ss.
        Set var_display text to "while+for+repeat sum = " + ss.
        Set list_display text to "while / for each / repeat N / break / continue / range".
    If idx is 4:
        Create list named bag with sword, shield, potion.
        Add "ring" to list bag.
        Put "helm" in bag.
        Remove shield from bag.
        Sort bag as sorted.
        Reverse sorted as rev.
        Pick random item from rev as lucky.
        Get first item of rev as fi.
        Get last item of rev as li.
        Turn rev into text as rs.
        Set var_display text to "bag: " + rs + "  lucky: " + lucky.
        Set list_display text to "first:" + fi + " last:" + li + " | add/put/remove/sort/reverse/shuffle".
    If idx is 5:
        Create dictionary named hero with name: Ada, score: 42, health: 100.
        Set hero.level to 5.
        Get score from hero as hs.
        Get keys from hero as ks.
        Turn hero into text as hs2.
        Turn ks into text as kss.
        Turn hs into text as hss.
        Set var_display text to "hero: " + hs2 + "  score: " + hss.
        Set list_display text to "keys: " + kss.
    If idx is 6:
        Call, greet with "World" as g.
        Call, add_pair with 7 and 8 as ad.
        Call, fact with 6 as ft.
        Turn ad into text as ads.
        Turn ft into text as fts.
        Set var_display text to g + "  7+8=" + ads + "  6!=" + fts.
        Set list_display text to "define/call/return | recursion | parameters | generators".
    If idx is 7:
        Create Player named mage with name: "Merlin", hp: 80, mana: 120.
        Call, mage.heal with 5 as hr.
        Turn mage.hp into text as hps.
        Turn mage.mana into text as mns.
        Set var_display text to "Merlin hp:" + hps + " mana:" + mns.
        Set list_display text to "blueprint / create instance / methods / self / field access".
    If idx is 8:
        Write "hello angis" to file "/tmp/angis_demo.txt" as wr.
        Get file name of "/tmp/angis_demo.txt" as fn.
        Get file extension of "/tmp/angis_demo.txt" as fe.
        Turn wr into text as wrs.
        Set var_display text to "write:" + wrs + " name:" + fn + " ext:" + fe.
        Set list_display text to "write/read/copy/move/delete | info/exists/glob/list dir".
    If idx is 9:
        Set sample to "  Hello Angis World!  ".
        Get uppercase of sample as up.
        Get lowercase of sample as lw.
        Get trimmed text of sample as tr.
        Split tr by space as words.
        Join words with "-" as slug.
        Replace "Angis" in tr with "ANGIS" as rp.
        Turn words into text as ws.
        Set var_display text to "slug: " + slug + "  upper: " + up.
        Set list_display text to "words: " + ws + "  replaced: " + rp.
    If idx is 10:
        Round 3.7 as rd.
        Floor 3.7 as fl.
        Ceil 3.2 as cl.
        Absolute -5 as ab.
        Calculate square root of 81 as sq.
        Raise 2 to power 10 as pw.
        Clamp 14 between 1 and 10 as cp.
        Pick random number between 1 and 100 as rn.
        Turn rd into text as rds.
        Turn sq into text as sqs.
        Turn cp into text as cps.
        Turn pw into text as pws.
        Turn rn into text as rns.
        Set var_display text to "round:" + rds + " sqrt81=" + sqs + " 2^10=" + pws.
        Set list_display text to "clamp:" + cps + " random:" + rns + " | sin/cos/tan/log/exp".
    If idx is 11:
        Set nums to [1, 2, 3, 4, 5].
        Set dbl to for each x in nums collect x * 2.
        Set sqs2 to for each x in nums collect x * x.
        Set big to [].
        For each y in nums:
            If y is greater than 2:
                Add y to list big.
        Set tot to 0.
        For each z in nums:
            Set tot to tot + z.
        Turn dbl into text as dbs.
        Turn big into text as bgs.
        Turn tot into text as tos.
        Turn sqs2 into text as sq2s.
        Set var_display text to "doubled: " + dbs + "  squares: " + sq2s.
        Set list_display text to "filtered>2: " + bgs + "  total: " + tos.
    If idx is 12:
        Create dictionary named p with score: 0.
        award 50 points to p.
        award 25 points to p.
        Turn p.score into text as pss.
        Set var_display text to "Custom DSL: award X points to Y  →  p.score=" + pss.
        Set list_display text to "define phrase | {name:type} slots | optional/alternative words".
    If idx is 13:
        import python math as math_mod.
        Run python: py_val = 42 * 2.
        Eval python math_mod.sqrt(144) as sqrt_py.
        Turn py_val into text as pys.
        Turn sqrt_py into text as sps.
        Set var_display text to "python 42*2=" + pys + "  sqrt(144)=" + sps.
        Set list_display text to "import python / run python: / eval python / {{py: inline}}".
    If idx is 14:
        Try:
            Raise error "Test error".
        Except as err:
            Set em to "Caught: " + err.
        Assert 2 + 2 is 4 else "math broken".
        Set var_display text to em + "  |  assert 2+2=4 ok".
        Set list_display text to "try/except/finally | raise error | assert | custom error types".
    If idx is 15:
        Get current time as now.
        Get timestamp as epoch.
        Get todays date as today.
        Turn epoch into text as eps.
        Set var_display text to "now: " + now + "  epoch: " + eps + "  date: " + today.
        Set list_display text to "get current time / timestamp / todays date / date arithmetic".
    If idx is 16:
        Get file name from "/tmp/folder/data.csv" as fn2.
        Get file extension from "/tmp/folder/data.csv" as fe2.
        Get folder from "/tmp/folder/data.csv" as fld.
        Get stem from "/tmp/folder/data.csv" as stm.
        Join path "/tmp" with "output.txt" as jn.
        Set var_display text to "name:" + fn2 + " ext:" + fe2 + " folder:" + fld.
        Set list_display text to "stem:" + stm + " joined:" + jn.
    If idx is 17:
        Set demo_sphere color to #ff4488.
        Set demo_cube color to #44ff88.
        Set demo_pyramid color to #ffaa44.
        Set var_display text to "3D shapes: sphere / cube / pyramid / cylinder / torus".
        Set list_display text to "auto-rotate | perspective camera | colors | sizes | positions".
    If idx is 18:
        Set var_display text to "Events: click advances steps | space=next | r=reset".
        Set list_display text to "on click / when key pressed / every N ms / mouse moved".

every 30 ms:
    If started is false:
        break.
    If demo_step is 0:
        Set event_log text to "Angis Capabilities Demo — Press Space or click to start".
        break.
    run_step.
    Set snum to demo_step.
    Turn snum into text as sn.
    Turn total into text as tn.
    Set event_log text to "Step " + sn + " of " + tn + " — Press Space or click for next".

Define, greet with name:
    Return "Hello " + name + "!".

Define, add_pair with left and right:
    Return left + right.

Define, fact with n:
    If n is at most 1:
        Return 1.
    Return n * fact(n - 1).

Define phrase award {amount} points to {target}:
    Set target.score to target.score + amount.

Blueprint Player with name: "Unknown", hp: 100, mana: 50.

Define method heal for Player with amount:
    Set self.hp to self.hp + amount.
    Turn amount into text as amt_s.
    Return self.name + " healed by " + amt_s.
```

## 12. capability_checks.angis

```angis
# Capability check demo

Check capability folder_packages as canUsePackages.
Check capability made_up_feature as canUseMadeUp.
Use capabilities has with name: math.sqrt as canUseSqrt.

Show canUsePackages.
Show canUseMadeUp.
Show canUseSqrt.
```

## 13. capability_registry.angis

```angis
# Capability registry demo

Use capabilities list as everythingAngisCanDo.
Use capabilities language as languageFeatures.
Use capabilities runtime as runtimeFeatures.
Use capabilities functions as loadedFunctions.

Show languageFeatures.
Show runtimeFeatures.
Show loadedFunctions.
```

## 14. code_anything.angis

```angis
# Can you code anything in Angis?
# Yes. This file is the answer.

import python os as os
import python json as json
import python datetime as datetime
import python math as math
import python hashlib as hashlib
import python tempfile as tempfile
import python textwrap as textwrap
import python statistics as stats
import python itertools as itertools

Say, Yes. You can code anything in natural Angis flow.

# ─── 1. Files & paths ───
Say, - - - File system - - -

Get os getcwd as here.
Show here.

Run os path join with left: here, right: "answer.txt" as path.
Show path.

Run os path exists with path: path as exists.
Show exists.

# ─── 2. JSON ───
Say, - - - JSON - - -

Run json dumps with obj: {"question": "code anything?", "answer": "yes"}, indent: 2 as pretty.
Show pretty.

# ─── 3. Math beyond hardcoded stdlib ───
Say, - - - Extended math - - -

Run math degrees with value: 3.14159 as deg.
Show deg.

Run math isclose with a: 0.1, b: 0.1, rel_tol: 0.01 as close.
Show close.

Run math comb with n: 10, k: 3 as combos.
Show combos.

# ─── 4. Statistics ───
Say, - - - Statistics - - -

Run stats mean with data: [10, 20, 30, 40, 50] as mean.
Show mean.

Run stats median with data: [10, 20, 30, 40, 50] as med.
Show med.

Run stats stdev with data: [10, 20, 30, 40, 50] as sd.
Show sd.

# ─── 5. Text processing ───
Say, - - - Text processing - - -

Run textwrap fill with text: "This is a long line that should be wrapped to a certain width", width: 30 as wrapped.
Show wrapped.

Run textwrap indent with text: "line one\nline two\nline three", prefix: ">> " as indented.
Show indented.

# ─── 6. Date/time ───
Say, - - - Date and time - - -

Run datetime datetime now as now.
Show now.

# ─── 7. System info ───
Say, - - - System - - -

Run os cpu_count as cores.
Show cores.

Run os getpid as pid.
Show pid.

# ─── 8. Hashing ───
Say, - - - Hashing - - -

import python codecs as codecs

Run codecs encode with obj: "hello from angis", encoding: "utf-8" as encoded.
Run hashlib sha256 with data: encoded as hash.
Get hash hexdigest as hexhash.
Show hexhash.

# ─── 9. Combinatorics ───
Say, - - - Combinatorics - - -

Run itertools combinations with iterable: ["a", "b", "c"], r: 2 as raw_combos.
import python builtins as builtins
Run builtins list with iterable: raw_combos as combos_list.
Show combos_list.

# ─── 10. Temp files ───
Say, - - - Temporary files - - -

Run tempfile mkstemp with suffix: ".angis" as tmp.
Get item at index 1 of tmp as tmp_path.
Show tmp_path.

# ─── Done ───
Say, Yes. You can code anything in Angis.
```

## 15. code_anything_helper.angis

```angis
# Helper module imported by code_anything_native.angis

define triple with value:
    return value * 3
```

## 16. code_anything_native.angis

```angis
# Angis-native "code anything" capability tour.
# This avoids host-language escape hatches and uses normal Angis phrases.

say "Yes. Angis can now cover the big building blocks."

# variables, math, text, lists, maps
set profile to {name: "Ada", age: 36}
put key language in profile to "Angis" as updated_profile
remove key age from updated_profile as public_profile
show public_profile

make range from 1 to 5 as numbers
extend numbers with [6, 7] as more_numbers
show more_numbers

get words of "code almost anything in Angis" as words
slugify "Code Almost Anything In Angis" as slug
reverse text "Angis" as backwards
show words
show slug
show backwards

# validation, URLs, paths, random, encoding, crypto, system info
check if "me@example.com" is an email as email_ok
parse url "https://example.com:443/path?q=1" as url_parts
resolve path "." as project_path
flip coin as coin
encode text "hello" as base64 as encoded
base64 decode encoded as decoded
hash text "hello" with sha256 as digest
get system platform as platform_name
show email_ok
show url_parts
show project_path
show coin
show encoded
show decoded
show digest
show platform_name

# file I/O, JSON, regex, identifiers
write text "hello" to file "examples/code_anything_native_note.txt" as wrote_note
append text " world" to file "examples/code_anything_native_note.txt" as appended_note
read file "examples/code_anything_native_note.txt" as note_text
parse json "[1, 2, 3]" as parsed_profile
turn parsed_profile into json as json_text
find pattern "\d+" in "abc123" as digits
replace pattern "\d+" in "abc123" with "456" as replaced_text
make uuid as identifier
show note_text
show json_text
show digits
show replaced_text
show identifier

# structured objects
blueprint Person with name: "unknown", language: "Angis"
create Person named teacher with name: "Ada", language: "Angis"
clone object teacher as teacher_copy
list object fields teacher as teacher_fields
show teacher_copy
show teacher_fields

# database
create database file "examples/code_anything_native.db" named demo_db
run query "create table if not exists notes(text text)" on demo_db
run query "delete from notes" on demo_db
run query "insert into notes(text) values ('Angis stores data')" on demo_db
run query "select text from notes" on demo_db as rows
show rows

# app/runtime/package primitives
app "Code Anything Native Demo"
create label named greeting at x 10 y 5 with text "Hello Angis"
create button named save_button at x 10 y 40 with text "Save"
create input named email at x 10 y 80 with placeholder "email"
create slider named volume at x 20 y 120 from 0 to 100 value 50
create checkbox named agree at x 20 y 160 checked with text "I agree"
when save_button clicked:
    set saved to true
create circle named ball at x 40 y 210 size 24 color blue
create rectangle named wall at x 0 y 250 width 200 height 20 color gray
build app package in folder "examples/code_anything_native_package"

# async/background work and Angis module imports
define slow_double with value:
    return value * 2
run slow_double in background with 21 as job
wait for job as doubled
use everything from module "code_anything_helper.angis" as helper
call helper_triple with 7 as tripled
show doubled
show tripled

# networking, permissions/security, and more standard-library modules
check if path "examples/code_anything_native_note.txt" is inside folder "examples" as safe_path
redact secrets in text "token=abc password=hunter2 email=a@example.com" as redacted
check if port 127.0.0.1:1 is open as port_open
get median of [3, 1, 2] as median_value
get standard deviation of [2, 4, 4, 4, 5, 5, 7, 9] as deviation
define web route get "/hello" returning "hello" as hello_route
create package manifest named "code-anything-native" version "1.0.0" as manifest
request permission file read for path "examples" as read_permission
make deployment plan for app "Code Anything Native Demo" to folder "examples/code_anything_native_deploy" as deploy_plan
test that 2 equals 2 as equality_ok
test that "Angis" contains "gis" as contains_ok
show safe_path
show redacted
show port_open
show median_value
show deviation
show hello_route
show manifest
show read_permission
show deploy_plan
show equality_ok
show contains_ok

# capability/debug introspection
show debug trace as trace
show trace

say "Done."
```

## 17. codeism_universe.angis

```angis
App, Codeism Universe Simulation.
Dark background.
Window size 600 by 700.

Set virtue to 0.
Set heaven_souls to 0.
Set hell_souls to 0.

Set s1_y to 100.
Set s2_y to 370.
Set s3_y to 340.
Set s4_y to 360.
Set s5_y to 380.
Set s6_y to 550.

Set s1_color to "gold".
Set s2_color to "gray".
Set s3_color to "gray".
Set s4_color to "gray".
Set s5_color to "gray".
Set s6_color to "red".

Create rectangle named heaven at x 0 y 0.
Set heaven width to 600.
Set heaven height to 200.
Set heaven color to gold.
Set heaven border to white.
Set heaven border_width to 2.

Create rectangle named hell at x 0 y 500.
Set hell width to 600.
Set hell height to 200.
Set hell color to darkred.
Set hell border to orange.
Set hell border_width to 2.

Create rectangle named earth at x 150 y 330.
Set earth width to 300.
Set earth height to 40.
Set earth color to green.
Set earth border to white.
Set earth border_width to 1.

Create text named title at x 200 y 215 saying "The Codeism Universe".
Set title font_size to 16.
Set title color to white.

Create text named heavenLabel at x 200 y 85 saying "Heaven: Connected to the Source".
Set heavenLabel font_size to 12.
Set heavenLabel color to white.

Create text named hellLabel at x 200 y 540 saying "Hell: Disconnected from Code".
Set hellLabel font_size to 12.
Set hellLabel color to white.

Create text named stats at x 200 y 260 saying "Virtue: 0 | Heaven: 0 | Hell: 0".
Set stats font_size to 12.
Set stats color to lightgray.

Create text named guide at x 200 y 680 saying "Click: raise souls | Space: lower souls | The Code governs all."
Set guide font_size to 10.
Set guide color to gray.

Create circle named soul1 at x 180 y 350.
Set soul1 size to 8.

Create circle named soul2 at x 220 y 370.
Set soul2 size to 8.

Create circle named soul3 at x 260 y 340.
Set soul3 size to 8.

Create circle named soul4 at x 300 y 360.
Set soul4 size to 8.

Create circle named soul5 at x 340 y 380.
Set soul5 size to 8.

Create circle named soul6 at x 380 y 345.
Set soul6 size to 8.

Set soul1 y to s1_y.
Set soul1 color to s1_color.
Set soul6 y to s6_y.
Set soul6 color to s6_color.

Add 1 to heaven_souls.
Add 1 to hell_souls.

Attach file "HeavenCode.txt" to window at x 0 y 0 z 0.
Attach file "SoulRecords.txt" to window at x 0 y 0 z 1.

on click:
    Add 1 to virtue.
    If s1_y is greater than 100:
        Set s1_y to s1_y minus 30.
    If s2_y is greater than 100:
        Set s2_y to s2_y minus 30.
    If s3_y is greater than 100:
        Set s3_y to s3_y minus 30.
    If s4_y is greater than 100:
        Set s4_y to s4_y minus 30.
    If s5_y is greater than 100:
        Set s5_y to s5_y minus 30.
    If s6_y is greater than 100:
        Set s6_y to s6_y minus 30.

on space pressed:
    Subtract 1 from virtue.
    If s1_y is less than 500:
        Set s1_y to s1_y plus 30.
    If s2_y is less than 500:
        Set s2_y to s2_y plus 30.
    If s3_y is less than 500:
        Set s3_y to s3_y plus 30.
    If s4_y is less than 500:
        Set s4_y to s4_y plus 30.
    If s5_y is less than 500:
        Set s5_y to s5_y plus 30.
    If s6_y is less than 500:
        Set s6_y to s6_y plus 30.

every 500 ms:
    Set heaven_souls to 0.
    Set hell_souls to 0.

    Set s1_color to "gray".
    If s1_y is less than 200:
        Set s1_color to "gold".
        Add 1 to heaven_souls.
    If s1_y is greater than 500:
        Set s1_color to "red".
        Add 1 to hell_souls.

    Set s2_color to "gray".
    If s2_y is less than 200:
        Set s2_color to "gold".
        Add 1 to heaven_souls.
    If s2_y is greater than 500:
        Set s2_color to "red".
        Add 1 to hell_souls.

    Set s3_color to "gray".
    If s3_y is less than 200:
        Set s3_color to "gold".
        Add 1 to heaven_souls.
    If s3_y is greater than 500:
        Set s3_color to "red".
        Add 1 to hell_souls.

    Set s4_color to "gray".
    If s4_y is less than 200:
        Set s4_color to "gold".
        Add 1 to heaven_souls.
    If s4_y is greater than 500:
        Set s4_color to "red".
        Add 1 to hell_souls.

    Set s5_color to "gray".
    If s5_y is less than 200:
        Set s5_color to "gold".
        Add 1 to heaven_souls.
    If s5_y is greater than 500:
        Set s5_color to "red".
        Add 1 to hell_souls.

    Set s6_color to "gray".
    If s6_y is less than 200:
        Set s6_color to "gold".
        Add 1 to heaven_souls.
    If s6_y is greater than 500:
        Set s6_color to "red".
        Add 1 to hell_souls.

    Set soul1 y to s1_y.
    Set soul1 color to s1_color.
    Set soul2 y to s2_y.
    Set soul2 color to s2_color.
    Set soul3 y to s3_y.
    Set soul3 color to s3_color.
    Set soul4 y to s4_y.
    Set soul4 color to s4_color.
    Set soul5 y to s5_y.
    Set soul5 color to s5_color.
    Set soul6 y to s6_y.
    Set soul6 color to s6_color.

    Set stats text to "Virtue: {virtue} | Heaven: {heaven_souls} | Hell: {hell_souls}".
```

## 18. contains_conditions.angis

```angis
# Natural contains and true/false conditions

Create list named inventory with wood, stone.
Create dictionary named player with name: Ada, score: 42.
Set, phrase to hello world.
Set, ready to true.

If inventory contains wood:
    Say, list contains.

If player has score:
    Say, map has score.

If phrase contains world:
    Say, text contains world.

If ready:
    Say, ready is true.

If shield is not in inventory:
    Say, no shield.
```

## 19. creator_runtime.angis

```angis
# Angis Creator Runtime example

App, Creator World.
Scene, 3D world.

Create player named hero at x 0 y 0 z 0.
Create image named city at x 0 y -40 z 4 from file /Users/fellflow/Desktop/Angis/assets/gta_style_city.png.
Create button named start with text Start Mission.

When key w pressed:
    Move hero forward by 1.

When key s pressed:
    Move hero backward by 1.

When key a pressed:
    Move hero left by 1.

When key d pressed:
    Move hero right by 1.

When button start clicked:
    Show text Mission started.
    Move hero forward by 2.
```

## 20. creator_runtime_v2.angis

```angis
# Angis Creator Runtime v2 example

App, Creator V2 World.
Scene, 3D world.

Create player named hero at x 0 y 0 z 0.
Create player named enemy at x 2 y 0 z 2.
Create image named city at x 0 y -40 z 4 from file /Users/fellflow/Desktop/Angis/assets/gta_style_city.png.
Create button named start with text Start Mission.

Set hero color to red.
Set hero size to 22.

Create list named inventory with key, map.
Add shield to list inventory.

When key w pressed:
    Move hero forward by 1.

When key s pressed:
    Move hero backward by 1.

When key a pressed:
    Move hero left by 1.

When key d pressed:
    Move hero right by 1.

When mouse clicked:
    Play sound click.
    Show text Mouse clicked.

Every 500 milliseconds:
    Animate enemy left by 1 every 500 milliseconds.

When hero touches enemy:
    Play sound hit.
    Show text Collision detected.

When button start clicked:
    Show text Mission started.
    Move hero forward by 2.

Save state to file /Users/fellflow/Desktop/Angis/assets/creator_state.json.
```

## 21. csv_data.angis

```angis
# Natural CSV and data actions

Read CSV file assets/items.csv as rows.
Count rows in rows as rowCount.
Get column name from rows as names.
Keep rows where name is Ada as adaRows.

Show rowCount.
Show first item of names.
Show score of first item of adaRows.
```

## 22. custom_app_words.angis

```angis
# Build an app using custom phrase-pack wording

use phrase pack phrases/app.angis

Make app Custom Words.
Make canvas.
Put text Hello from custom app wording.
Put file /Users/fellflow/Desktop/Angis/README.md at 20 80 0.
```

## 23. custom_commands.angis

```angis
# Teach Angis your own wording

Blueprint Player with name: Ada, score: 0.
Create Player named hero with name: Grace.

Define command give points with target and amount:
    Set, target.score to target.score + amount.
    Return, target.score.

Define command rename player with target and newName:
    Set, target.name to newName.

Give points with hero, 3 as firstScore.
Give points with hero, 7 as secondScore.
Rename player with hero, Lovelace.

Show, hero.name.
Show, firstScore.
Show, secondScore.
Show, hero.score.
```

## 24. cyber_dungeon.angis

```angis
# Cyber Dungeon Crawler
# A demonstration of complex logic, visuals, and natural language in Angis.

App "Cyber Dungeon"
Scene "canvas"
Window size 800 by 600.
Dark background.

# --- GAME LOGIC (Blueprints) ---

Blueprint Entity with name: "Unknown", hp: 10, max_hp: 10, attack: 2.

Blueprint Hero inherits Entity with gold: 0, level: 1.

# Initialize Hero
Create Hero named hero with name: "Lovelace", hp: 20, max_hp: 20, attack: 5.

# --- VISUALS ---

# Player Sprite
Create circle named player_sprite at x 400 y 300 z 10
Set player_sprite.color to "#38bdf8"
Set player_sprite.size to 30
Set player_sprite.textcolor to "#ffffff"

# An Enemy
Create circle named virus at x 200 y 150 z 5
Set virus.color to "#f43f5e"
Set virus.size to 25
Set virus.text to "VIRUS"

# A Treasure
Create rectangle named data_cube at x 600 y 450 z 5
Set data_cube.color to "#facc15"
Set data_cube.width to 20
Set data_cube.height to 20
Set data_cube.text to "DATA"

# --- UI & STATS ---

Show "Dungeon Initialized. Move with WASD."
Show "Hero: " + hero.name + " | HP: " + hero.hp + " | Gold: " + hero.gold

# --- CONTROLS ---

When key w pressed:
    Move player_sprite up by 15

When key s pressed:
    Move player_sprite down by 15

When key a pressed:
    Move player_sprite left by 15

When key d pressed:
    Move player_sprite right by 15

# --- INTERACTIONS ---

# Combat Logic
When player_sprite touches virus:
    Say "SYSTEM ALERT: Security Breach!"
    Set hero.hp to hero.hp - 2
    Set virus.color to "#ffffff"
    Animate virus right by 100 every 50 milliseconds
    Show "HP Left: " + hero.hp
    If hero.hp is at most 0:
        Say "CRITICAL FAILURE: Game Over"
        Set player_sprite.color to "#475569"

# Loot Logic
When player_sprite touches data_cube:
    Say "DATA ACQUIRED!"
    Set hero.gold to hero.gold + 50
    Move data_cube up by 1000  # Hide it
    Show "Total Gold: " + hero.gold

# --- MULTILINGUAL FALLBACKS ---

# Italian
mostra "Scansione completa."

# Portuguese
defina status_sistema como "Operacional"
mostre status_sistema
```

## 25. cyber_garden.angis

```angis
# Cyber Garden Demo
# This showcases natural phrasing, animations, and interactivity in Angis.

App "Cyber Garden"
Scene "canvas"
Window size 800 by 600.
Dark background.

# Natural variable assignment (newly supported)
garden_power = 100
weather = "Neon Rain"

Show "Welcome to the Cyber Garden"
Show "Garden Power: " + garden_power

# Create some animated 'plants'
Create circle named bloom1 at x 200 y 400 z 1
Set bloom1.color to "#a855f7"
Set bloom1.size to 40

Create circle named bloom2 at x 400 y 450 z 2
Set bloom2.color to "#38bdf8"
Set bloom2.size to 60

Create circle named bloom3 at x 600 y 420 z 1
Set bloom3.color to "#facc15"
Set bloom3.size to 30

# Animate them to pulse
Animate bloom1 up by 2 every 100 milliseconds
Animate bloom2 up by 1 every 150 milliseconds
Animate bloom3 up by 3 every 80 milliseconds

# Interactions
When mouse clicked:
    Say "You touched the digital soil."
    Add 1 to garden_power
    Set bloom2.color to "#f43f5e"
    Show "Power surging: " + garden_power

On key space pressed:
    Say "Rebooting the garden..."
    Set bloom1.color to "#a855f7"
    Set bloom2.color to "#38bdf8"
    Set bloom3.color to "#facc15"

# Italian fallback usage
mostra "Il giardino è vivo"
```

## 26. data_access.angis

```angis
# Angis direct data access demo

Create dictionary named player with name: Ada, score: 42.
Create list named inventory with wood, stone, iron.
Use json parse with text: [{"name":"Ada"},{"name":"Grace"}] as rows.

Show, player.name.
Show, player.score.
Show, inventory[0].
Show, rows[1].name.

For each, row in rows:
    Show, row.name.
```

## 27. data_assignment.angis

```angis
# Change real data objects with Angis wording

Create dictionary named player with name: Ada, score: 42.
Create list named inventory with wood, stone, iron.
Use json parse with text: [{"name":"Ada"},{"name":"Grace"}] as rows.

Set, player.score to 50.
Set, inventory[1] to diamond.
Set, rows[0].name to Lovelace.
Put shield in inventory.
Store potion inside inventory.
Remove shield from inventory.
Take potion out of inventory.
Put key in inventory.
Make player have health 99.
Give player level 3.
Set name of player to Grace.
Remove field level from player.
Get map has with value: player, key: level as hasLevel.

Show, player.name.
Show, player.score.
Show, player.health.
Show, hasLevel.
Show, inventory[1].
Show, inventory[3].
Show, rows[0].name.
```

## 28. debug_trace.angis

```angis
# Debug trace demo

Set, x to 1.
Add, 2 to x.
Show x.

Debug trace.
```

## 29. else_blocks.angis

```angis
# Angis else block demo

Set, score to 2.

If, score is at least 3:
    Say, winner.
Else:
    Say, keep going.

If, score is less than 3:
    Say, low score.
Otherwise:
    Say, high score.
```

## 30. expressions.angis

```angis
# Angis expression demo

Set, x to 5.
Set, y to 3.
Set, total to x * y + 10.

Show, total.

If, total is at least x + y:
    Say, expression condition works.

While, x + y is less than 12:
    Add, 1 to x.

Show, x.
```

## 31. file_actions.angis

```angis
# Natural file actions

Read file examples/hello.angis as sourceText.
Write copied text to file assets/natural-output.txt as writeResult.
Get info for file assets/natural-output.txt as fileInfo.

Show first 20 letters of sourceText.
Show writeResult.
Show name of fileInfo.
```

## 32. file_attach.angis

```angis
# Replace the path with a real local file path on your Mac.

Attach file at /Users/fellflow/Desktop/Angis/README.md.
```

## 33. file_window.angis

```angis
# File attachment shown inside an app window.

App, File Window.
Text, The attached file should appear below.
Set file attach to window at x 20 y 80 z 0 from file /Users/fellflow/Desktop/Angis/README.md.
Button, Confirm File.
```

## 34. flappy_bird.angis

```angis
# Click or press Space to move the bird up.
# The bird falls down by gravity and must avoid obstacles.

Bird on screen.
When clicked, bird goes up.
Bird falls down.
Add obstacles.
If bird hits obstacle, end game.
```

## 35. flappy_bird_3d.angis

```angis
App, Flappy Bird 3D.
Scene, true 3D.
Window size 800 by 600.
camera at x 0 y 0 z -10.
mode third person.

Set score to 0.
Set gravity to 2.
Set flap to -18.
Set bird_y to 150.
Set velocity to 0.
Set pipe_z to 15.
Set pipe_speed to 0.4.
Set game_over to false.
Set started to false.

Create sphere named bird at x 0 y 150 z 0.
Set bird color to #ffcc00.
Set bird size to 15.
Attach file "examples/duck.gif" named duck.
Set bird image to duck.

Create box named upperPipe at x 0 y -60 z 15.
Set upperPipe color to #22c55e.
Set upperPipe scale_x to 2.
Set upperPipe scale_y to 1.
Set upperPipe scale_z to 0.5.

Create box named lowerPipe at x 0 y 330 z 15.
Set lowerPipe color to #22c55e.
Set lowerPipe scale_x to 2.
Set lowerPipe scale_y to 1.
Set lowerPipe scale_z to 0.5.

Create box named ground at x 0 y 570 z 0.
Set ground color to #15803d.
Set ground scale_x to 5.
Set ground scale_y to 0.1.
Set ground scale_z to 10.

on click:
    If game_over is true:
        Set score to 0.
        Set bird_y to 150.
        Set velocity to 0.
        Set pipe_z to 15.
        Set bird y to bird_y.
        Set upperPipe z to pipe_z.
        Set lowerPipe z to pipe_z.
        Set game_over to false.
    If started is false:
        Set started to true.
    If started is true:
        If game_over is false:
            Set velocity to flap.

every 30 ms:
    If started is true:
        If game_over is false:
            Set velocity to velocity plus gravity.
            Set bird_y to bird_y plus velocity.
            Set bird y to bird_y.
            Set pipe_z to pipe_z minus pipe_speed.
            Set upperPipe z to pipe_z.
            Set lowerPipe z to pipe_z.
            If pipe_z is less than -2:
                Set pipe_z to 15.
                Add 1 to score.
            If bird_y is greater than 550:
                Set game_over to true.
                Show text "Game Over!".
            If bird_y is less than 10:
                Set game_over to true.
                Show text "Game Over!".
            If pipe_z is less than 1:
                If pipe_z is greater than -1:
                    If bird_y is less than 70:
                        Set game_over to true.
                        Show text "Game Over!".
                    If bird_y is greater than 230:
                        Set game_over to true.
                        Show text "Game Over!".
```

## 36. flappy_bird_natural.angis

```angis
App, Flappy Bird.
Scene, 2D screen.
Blue window.
Window size 400 by 600.

Set score to 0.
Set gravity to 3.
Set flap to -30.
Set bird_y to 250.
Set velocity to 0.
Set pipe_x to 400.
Set pipe_gap to 150.
Set pipe_speed to 3.
Set game_over to false.

Create circle named bird at x 180 y 250.
Set bird color to yellow.
Set bird size to 20.

Create rectangle named ground at x 0 y 580.
Set ground color to green.
Set ground width to 400.
Set ground height to 20.

Create rectangle named Top pipe at x 400 y 0 size 50 by 200.
Set Top pipe color to darkgreen.

Create rectangle named Bottom pipe at x 400 y 500 size 50 by 200.
Set Bottom pipe color to darkgreen.

Create text named scoreText at x 10 y 10 saying "Score: 0".
Set scoreText font_size to 20.
Set scoreText color to white.

on click:
    If game_over is true:
        Set score to 0.
        Set bird_y to 250.
        Set velocity to 0.
        Set pipe_x to 400.
        Set bird y to bird_y.
        Set Top pipe x to pipe_x.
        Set Bottom pipe x to pipe_x.
        Set scoreText text to "Score: 0".
        Set game_over to false.
    If game_over is false:
        Set velocity to flap.

every 30 ms:
    If game_over is false:
        Set velocity to velocity plus gravity.
        Set bird_y to bird_y plus velocity.
        Set bird y to bird_y.
        Set pipe_x to pipe_x minus pipe_speed.
        Set Top pipe x to pipe_x.
        Set Bottom pipe x to pipe_x.
        If pipe_x is less than -50:
            Set pipe_x to 450.
            Add 1 to score.
            Set scoreText text to "Score: {score}".
        If bird_y is greater than 560:
            Set game_over to true.
            Show text "Game Over!".

when bird hits Top pipe:
    Set game_over to true.
    Show text "Game Over!".

when bird hits Bottom pipe:
    Set game_over to true.
    Show text "Game Over!".
```

## 37. floppy_bird_3d.angis

```angis
App, Floppy Bird 3D.
Scene, true 3D.
Window size 800 by 600.
camera at x 0 y 0 z -8.
mode third person.

Set score to 0.
Set gravity to 0.05.
Set flap to -3.
Set gap_half to 150.
Set shift to 0.
Set bird_y to 0.
Set velocity to 0.
Set wall_speed to 0.2.
Set game_over to false.
Set started to false.

Set w1z to 30.
Set w1g to 0.
Set w2z to 70.
Set w2g to 0.
Set w3z to 110.
Set w3g to 0.
Set w4z to 150.
Set w4g to 0.

Create image named bird at x 0 y 0 z 0 using the file at "examples/duck.png".
Set bird size to 25.

Create box named w1t at x 0 y 40 z 30.
Set w1t color to #ef4444.
Set w1t scale_x to 2.5.
Set w1t scale_y to 4.
Set w1t scale_z to 0.3.

Create box named w1b at x 0 y -40 z 30.
Set w1b color to #ef4444.
Set w1b scale_x to 2.5.
Set w1b scale_y to 4.
Set w1b scale_z to 0.3.

Create box named w2t at x 0 y 40 z 70.
Set w2t color to #3b82f6.
Set w2t scale_x to 2.5.
Set w2t scale_y to 4.
Set w2t scale_z to 0.3.

Create box named w2b at x 0 y -40 z 70.
Set w2b color to #3b82f6.
Set w2b scale_x to 2.5.
Set w2b scale_y to 4.
Set w2b scale_z to 0.3.

Create box named w3t at x 0 y 40 z 110.
Set w3t color to #22c55e.
Set w3t scale_x to 2.5.
Set w3t scale_y to 4.
Set w3t scale_z to 0.3.

Create box named w3b at x 0 y -40 z 110.
Set w3b color to #22c55e.
Set w3b scale_x to 2.5.
Set w3b scale_y to 4.
Set w3b scale_z to 0.3.

Create box named w4t at x 0 y 40 z 150.
Set w4t color to #a855f7.
Set w4t scale_x to 2.5.
Set w4t scale_y to 4.
Set w4t scale_z to 0.3.

Create box named w4b at x 0 y -40 z 150.
Set w4b color to #a855f7.
Set w4b scale_x to 2.5.
Set w4b scale_y to 4.
Set w4b scale_z to 0.3.

on click:
    If game_over is true:
        Set score to 0.
        Set bird_y to 0.
        Set bird y to 0.
        Set velocity to 0.
        Set game_over to false.
        Set started to true.
        Set shift to 0.
        Set w1z to 30.
        Set w1g to 0.
        Set w2z to 70.
        Set w2g to 0.
        Set w3z to 110.
        Set w3g to 0.
        Set w4z to 150.
        Set w4g to 0.
        Set w1t z to 30.
        Set w1b z to 30.
        Set w1t y to 40.
        Set w1b y to -40.
        Set w2t z to 70.
        Set w2b z to 70.
        Set w2t y to 40.
        Set w2b y to -40.
        Set w3t z to 110.
        Set w3b z to 110.
        Set w3t y to 40.
        Set w3b y to -40.
        Set w4t z to 150.
        Set w4b z to 150.
        Set w4t y to 40.
        Set w4b y to -40.
    If started is false:
        Set started to true.
    If game_over is false:
        Set velocity to flap.

every 30 ms:
    If started is false:
        break.
    If game_over is true:
        break.
    Set velocity to velocity plus gravity.
    Set bird_y to bird_y plus velocity.
    Set bird y to bird_y.
    If bird_y is greater than 550:
        Set game_over to true.
        Show text "Game Over!".
        Set bird_y to 0.
        Set bird y to 0.
        Set velocity to 0.
    If bird_y is less than -550:
        Set game_over to true.
        Show text "Game Over!".
        Set bird_y to 0.
        Set bird y to 0.
        Set velocity to 0.
    Set w1z to w1z minus wall_speed.
    Set w2z to w2z minus wall_speed.
    Set w3z to w3z minus wall_speed.
    Set w4z to w4z minus wall_speed.
    Set w1t z to w1z.
    Set w1b z to w1z.
    Set w2t z to w2z.
    Set w2b z to w2z.
    Set w3t z to w3z.
    Set w3b z to w3z.
    Set w4t z to w4z.
    Set w4b z to w4z.
    If w1z is less than -5:
        Set w1z to 190.
        Set shift to shift plus 20.
        If shift is greater than 60:
            Set shift to 0.
        Set w1g to shift.
        Set w1t y to w1g plus gap_half.
        Set w1b y to w1g minus gap_half.
    If w2z is less than -5:
        Set w2z to 190.
        Set shift to shift plus 20.
        If shift is greater than 60:
            Set shift to 0.
        Set w2g to shift.
        Set w2t y to w2g plus gap_half.
        Set w2b y to w2g minus gap_half.
    If w3z is less than -5:
        Set w3z to 190.
        Set shift to shift plus 20.
        If shift is greater than 60:
            Set shift to 0.
        Set w3g to shift.
        Set w3t y to w3g plus gap_half.
        Set w3b y to w3g minus gap_half.
    If w4z is less than -5:
        Set w4z to 190.
        Set shift to shift plus 20.
        If shift is greater than 60:
            Set shift to 0.
        Set w4g to shift.
        Set w4t y to w4g plus gap_half.
        Set w4b y to w4g minus gap_half.
    If game_over is true:
        break.
    If w1z is less than 3:
        If w1z is greater than -3:
            If bird_y is less than w1g minus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
            If bird_y is greater than w1g plus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
    If w2z is less than 3:
        If w2z is greater than -3:
            If bird_y is less than w2g minus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
            If bird_y is greater than w2g plus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
    If w3z is less than 3:
        If w3z is greater than -3:
            If bird_y is less than w3g minus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
            If bird_y is greater than w3g plus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
    If w4z is less than 3:
        If w4z is greater than -3:
            If bird_y is less than w4g minus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
            If bird_y is greater than w4g plus gap_half:
                Set game_over to true.
                Show text "Game Over!".
                Set bird_y to 0.
                Set bird y to 0.
                Set velocity to 0.
```

## 38. for_each.angis

```angis
# Angis for-each loop demo

Create list named inventory with wood, stone, iron.

For each, item in inventory:
    Show, item.

Use json parse with text: [{"name":"Ada"},{"name":"Grace"}] as rows.

For each, row in rows:
    Show, row.
```

## 39. fortnite_style.angis

```angis
# Fortnite style app

App, Battle Royale Builder.
Scene, lobby.
Text, Drop from the sky.
Text, Choose a landing spot.
Text, Collect shields.
Text, Find weapons.
Text, Build cover.
Text, Stay inside the storm circle.
Text, Be the last player standing.

Button, Jump From Bus.
Button, Pick Up Weapon.
Button, Drink Shield.
Button, Build Wall.
Button, Build Ramp.
Button, Check Storm.
Button, Victory Royale.
```

## 40. forward_phrases.angis

```angis
# Use a phrase before defining it later

Blueprint Player with name: Ada, score: 0.
Create Player named hero with name: Grace.

Give 3 points to hero as firstScore.
Give 7 points to hero.

Define phrase give {amount} points to {target}:
    Set, target.score to target.score + amount.
    Return, target.score.

Show, hero.name.
Show, firstScore.
Show, hero.score.
```

## 41. full_system.angis

```angis
# Broader Angis system example

include shared.angis

import pygame
import database
import network
import packaging
import debug

Open database file /Users/fellflow/Desktop/Angis/assets/angis_demo.sqlite as db.
Run SQL "CREATE TABLE IF NOT EXISTS scores (name TEXT, score INTEGER)" on db.
Run SQL "DELETE FROM scores" on db.
Run SQL "INSERT INTO scores VALUES ('Ada', 42)" on db.
Run SQL "SELECT * FROM scores" on db as rows.

App, Full System Demo.
Scene, canvas.
Window size 800 by 500.

Text, This file includes another .angis file, uses SQLite, exports, packages, and can run with pygame if installed.

Create rectangle named box at x 100 y 220.
Set box color to purple.
Set box width to 120.
Set box height to 80.

Create circle named target at x 520 y 210.
Set target color to green.
Set target size to 70.

Breakpoint after setup.
Debug all.
Export app to file /Users/fellflow/Desktop/Angis/assets/full_system_export.html.
Package app to folder /Users/fellflow/Desktop/Angis/assets/full_system_package.
```

## 42. function_returns.angis

```angis
# Angis function return demo

Define, addPair with left and right:
    Return, left + right.

Define, firstName with row:
    Return, row.name.

Use json parse with text: {"name":"Ada"} as person.

Call, addPair with 4, 6 as total.
Call, firstName with person as name.

Show, total.
Show, name.
```

## 43. functions_with_parameters.angis

```angis
# Angis function parameters demo

Define, greet with name:
    Show, name.

Define, addPair with left and right:
    Set, total to left + right.
    Show, total.

Call, greet with Ada.
Call, greet with Grace.
Call, addPair with 4, 6.
```

## 44. general_language.angis

```angis
# Angis general language example

Set, score to 0.

Repeat, 3 times:
    Add, 1 to score.

If, score is 3:
    Say, score reached three.
    Show, score.

Define, greet:
    Say, hello from a function.

Call, greet.
Call, greet.
```

## 45. gta_san_andreas_image.angis

```angis
# GTA San Andreas style world with an attached picture

App, San Andreas World.
Scene, 3D world.
Text, Explore the city.
Text, Enter vehicles.
Text, Start missions.

Set file attach to window at x 0 y -40 z 4 from file /Users/fellflow/Desktop/Angis/assets/gta_style_city.png.

Button, Start Mission.
Button, Enter Vehicle.
Button, Open Map.
Button, Save Game.
```

## 46. hello.angis

```angis
# Output examples
say "hello"
print "Angis is running"
tell me "human-like phrases work"
```

## 47. inline_phrases.angis

```angis
# One-line phrase definitions

Define phrase start game means Say, started.
Define phrase note {message:text} means Show, message.

Start game.
Note hello from one line.
```

## 48. json_actions.angis

```angis
# Natural JSON actions

Parse JSON {"score": 42, "name": "Ada"} as data.
Turn data into JSON as packed.

Show score of data.

If packed contains score:
    Say, json works.
```

## 49. key_phrase_slots.angis

```angis
# Key slots let phrases control object property names

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
```

## 50. length_expressions.angis

```angis
# Natural length and count expressions

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
```

## 51. list_transforms.angis

```angis
# Natural list transforms

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
```

## 52. literal_data.angis

```angis
# List and dictionary literal data

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
```

## 53. literal_phrases.angis

```angis
# Literal phrases do not need slots

Define phrase start game:
    Say, started.

Define phrase reset everything:
    Say, reset.

Start game.
Reset, everything!
```

## 54. loading_screen.angis

```angis
# Loading screen synced to audio, then opens the app

App, Loading Demo.
Loding screen.
Scene, 3D world.

Text, App opened after loading.
Create player named hero at x 0 y 0 z 0.
Create button named start with text Start.

When button start clicked:
    Show text Started.
```

## 55. logical_conditions.angis

```angis
# Angis logical condition demo

Set, score to 4.
Set, lives to 2.

If, score is at least 3 and lives is greater than 0:
    Say, keep playing.

If, score is less than 3 or lives is 2:
    Say, backup condition.

If, not score is less than 3:
    Say, not low.
```

## 56. map_transforms.angis

```angis
# Natural map transforms

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
```

## 57. math.angis

```angis
# Math examples
add 5 and 3
what is 10 plus 4
calculate 7 * 6
give me 2 added to 9
set x to 20
divide x by 5
```

## 58. math_actions.angis

```angis
# Natural math and random actions

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
```

## 59. minecraft_style.angis

```angis
App, Minecraft 2D.
Scene, canvas.
Window size 800 by 600.

Set health to 10.
Set wood to 0.
Set stone to 0.
Set iron to 0.
Set gold to 0.
Set food to 5.

Create player named steve at x 400 y 300.
Set steve color to green.
Set steve size to 24.

Create rectangle named ground1 at x 0 y 0.
Set ground1 color to "#90EE90".
Set ground1 width to 800.
Set ground1 height to 600.

Create rectangle named treeTrunk1 at x 70 y 70.
Set treeTrunk1 color to brown.
Set treeTrunk1 width to 20.
Set treeTrunk1 height to 36.
Create circle named treeLeaf1 at x 70 y 52.
Set treeLeaf1 color to darkgreen.
Set treeLeaf1 size to 44.

Create rectangle named treeTrunk2 at x 700 y 80.
Set treeTrunk2 color to brown.
Set treeTrunk2 width to 20.
Set treeTrunk2 height to 36.
Create circle named treeLeaf2 at x 700 y 62.
Set treeLeaf2 color to darkgreen.
Set treeLeaf2 size to 44.

Create rectangle named treeTrunk3 at x 150 y 480.
Set treeTrunk3 color to brown.
Set treeTrunk3 width to 20.
Set treeTrunk3 height to 36.
Create circle named treeLeaf3 at x 150 y 462.
Set treeLeaf3 color to darkgreen.
Set treeLeaf3 size to 44.

Create rectangle named treeTrunk4 at x 630 y 470.
Set treeTrunk4 color to brown.
Set treeTrunk4 width to 20.
Set treeTrunk4 height to 36.
Create circle named treeLeaf4 at x 630 y 452.
Set treeLeaf4 color to darkgreen.
Set treeLeaf4 size to 44.

Create block named stone1 at x 340 y 140.
Set stone1 color to gray.
Set stone1 width to 28.
Set stone1 height to 28.

Create rectangle named stone2 at x 520 y 200.
Set stone2 color to gray.
Set stone2 width to 28.
Set stone2 height to 28.

Create rectangle named ironOre at x 280 y 360.
Set ironOre color to silver.
Set ironOre width to 24.
Set ironOre height to 24.

Create rectangle named goldOre at x 550 y 380.
Set goldOre color to gold.
Set goldOre width to 24.
Set goldOre height to 24.

Create rectangle named diamondOre at x 130 y 260.
Set diamondOre color to cyan.
Set diamondOre width to 24.
Set diamondOre height to 24.

Create rectangle named coalOre at x 660 y 290.
Set coalOre color to black.
Set coalOre width to 24.
Set coalOre height to 24.

Create rectangle named water1 at x 300 y 60.
Set water1 color to blue.
Set water1 width to 80.
Set water1 height to 30.
Create rectangle named water2 at x 460 y 520.
Set water2 color to blue.
Set water2 width to 70.
Set water2 height to 30.

Create circle named sheep1 at x 250 y 220.
Set sheep1 color to white.
Set sheep1 size to 20.
Create circle named sheep2 at x 550 y 270.
Set sheep2 color to lightgray.
Set sheep2 size to 20.
Create circle named cow1 at x 450 y 130.
Set cow1 color to brown.
Set cow1 size to 22.

Create rectangle named house1 at x 170 y 170.
Set house1 color to "#8B7355".
Set house1 width to 70.
Set house1 height to 60.
Create rectangle named house2 at x 175 y 175.
Set house2 color to "#A0522D".
Set house2 width to 60.
Set house2 height to 50.
Create rectangle named roof1 at x 200 y 150.
Set roof1 color to red.
Set roof1 width to 14.
Set roof1 height to 14.

Create circle named flower1 at x 100 y 160.
Set flower1 color to red.
Set flower1 size to 10.
Create circle named flower2 at x 110 y 170.
Set flower2 color to yellow.
Set flower2 size to 10.
Create circle named flower3 at x 680 y 500.
Set flower3 color to pink.
Set flower3 size to 10.
Create circle named flower4 at x 690 y 510.
Set flower4 color to red.
Set flower4 size to 10.

Create circle named zombie1 at x 80 y 440.
Set zombie1 color to red.
Set zombie1 size to 22.
Create circle named zombie2 at x 720 y 420.
Set zombie2 color to darkred.
Set zombie2 size to 22.
Create circle named creeper1 at x 500 y 500.
Set creeper1 color to lime.
Set creeper1 size to 22.

Create button named mineBtn with text Chop.
Create button named fightBtn with text Fight.
Create button named eatBtn with text Eat.
Create button named craftBtn with text Craft.
Create button named buildBtn with text Build.
Create button named statsBtn with text Stats.

When key w pressed:
    Move steve up by 10.

When key s pressed:
    Move steve down by 10.

When key a pressed:
    Move steve left by 10.

When key d pressed:
    Move steve right by 10.

When steve touches treeTrunk1:
    Show text Chopped tree! Got 2 wood.
    Move treeTrunk1 right by 300.
    Move treeLeaf1 right by 300.

When steve touches treeTrunk2:
    Show text Chopped tree! Got 2 wood.
    Move treeTrunk2 left by 300.
    Move treeLeaf2 left by 300.

When steve touches treeTrunk3:
    Show text Chopped tree! Got 2 wood.
    Move treeTrunk3 right by 300.
    Move treeLeaf3 right by 300.

When steve touches treeTrunk4:
    Show text Chopped tree! Got 2 wood.
    Move treeTrunk4 left by 300.
    Move treeLeaf4 left by 300.

When steve touches stone1:
    Show text Mined stone! Got 2 stone.
    Move stone1 down by 300.

When steve touches stone2:
    Show text Mined stone! Got 2 stone.
    Move stone2 up by 300.

When steve touches ironOre:
    Show text Found iron! Needs smelting.
    Move ironOre right by 300.

When steve touches goldOre:
    Show text Found gold! Rare!
    Move goldOre down by 300.

When steve touches diamondOre:
    Show text Found diamond! Best ore!
    Move diamondOre left by 300.

When steve touches coalOre:
    Show text Found coal! Make torches.
    Move coalOre up by 300.

When steve touches sheep1:
    Show text Baa! Sheep drops wool.
    Move sheep1 left by 80.

When steve touches sheep2:
    Show text Baa! Got more wool.
    Move sheep2 right by 80.

When steve touches cow1:
    Show text Moo! Got milk and leather.
    Move cow1 down by 80.

When steve touches zombie1:
    Show text Zombie hits you! Lost 2 health.
    Move zombie1 right by 60.

When steve touches zombie2:
    Show text Zombie attacks! Run!
    Move zombie2 left by 60.

When steve touches creeper1:
    Show text Creeper explodes! Lost 4 health.
    Move creeper1 up by 60.

When steve touches water1:
    Show text Swimming in the river.
    Move steve down by 30.

When steve touches water2:
    Show text Crossing the pond.
    Move steve up by 30.

When button mineBtn clicked:
    Show text Swing your pickaxe! Hit ores to collect.

When button fightBtn clicked:
    Show text Draw your sword! Attack zombies and creepers.

When button eatBtn clicked:
    Show text Ate some bread. Health restored.

When button craftBtn clicked:
    Show text Crafting table open. Made stone pickaxe.

When button buildBtn clicked:
    Show text Placed blocks. Built a small shelter.

When button statsBtn clicked:
    Show text Health 10 | Wood 0 | Stone 0 | Iron 0 | Gold 0.

Every 2000 milliseconds:
    Move sheep1 right by 6.

Every 2500 milliseconds:
    Move sheep2 left by 6.

Every 3000 milliseconds:
    Move cow1 right by 5.

Every 3000 milliseconds:
    Move zombie1 left by 8.

Every 3500 milliseconds:
    Move zombie2 right by 8.

Every 4000 milliseconds:
    Move creeper1 down by 7.
```

## 60. minicraft.angis

```angis
App, Minicraft.
Scene, true 3D.
Window size 900 by 650.
camera at x 0 y 4 z -10.
mode third person.

Set player_x to 0.
Set player_y to 0.
Set player_z to 0.
Set move_speed to 0.15.
Set gravity to 0.008.
Set velocity_y to 0.
Set on_ground to false.
Set selected_color to "#8B5E3C".
Set selected_name to "dirt".
Set pool_index to 0.
Set moving_fwd to false.
Set moving_back to false.
Set moving_left to false.
Set moving_right to false.

Create text named hud at x 0 y 280 z 0 saying "MINICRAFT — WASD=move  Space=jump  Click=place  Q=undo  R=reset".
Set hud color to white.
Set hud size to 11.

Create text named block_hud at x 0 y 260 z 0 saying "Block: dirt  |  1-4 to change".
Set block_hud color to #aaffaa.
Set block_hud size to 10.

Create text named pos_hud at x 0 y 240 z 0 saying "Pos: 0 0 0".
Set pos_hud color to #888888.
Set pos_hud size to 9.

Create text named ctrl at x 0 y -280 z 0 saying "1=dirt  2=grass  3=stone  4=water".
Set ctrl color to #666666.
Set ctrl size to 9.

Create box named ground at x 0 y 0 z 0.
Set ground scale_x to 8.
Set ground scale_y to 0.5.
Set ground scale_z to 8.
Set ground color to #8B5E3C.
Set ground y to -0.5.

Create box named d1 at x 0 y 0 z 0.
Set d1 scale_x to 1.
Set d1 scale_y to 1.
Set d1 scale_z to 1.
Set d1 color to #4A7C3F.
Set d1 x to -2.
Set d1 y to 0.5.
Set d1 z to -2.

Create box named d2 at x 0 y 0 z 0.
Set d2 scale_x to 1.
Set d2 scale_y to 1.
Set d2 scale_z to 1.
Set d2 color to #4A7C3F.
Set d2 x to -1.
Set d2 y to 0.5.
Set d2 z to -2.

Create box named d3 at x 0 y 0 z 0.
Set d3 scale_x to 1.
Set d3 scale_y to 1.
Set d3 scale_z to 1.
Set d3 color to #4A7C3F.
Set d3 x to -2.
Set d3 y to 0.5.
Set d3 z to -1.

Create box named t1 at x 0 y 0 z 0.
Set t1 scale_x to 1.
Set t1 scale_y to 1.
Set t1 scale_z to 1.
Set t1 color to #6B6B6B.
Set t1 x to 2.
Set t1 y to 0.5.
Set t1 z to 2.

Create box named t2 at x 0 y 0 z 0.
Set t2 scale_x to 1.
Set t2 scale_y to 1.
Set t2 scale_z to 1.
Set t2 color to #6B6B6B.
Set t2 x to 2.
Set t2 y to 1.5.
Set t2 z to 2.

Create box named t3 at x 0 y 0 z 0.
Set t3 scale_x to 1.
Set t3 scale_y to 1.
Set t3 scale_z to 1.
Set t3 color to #6B6B6B.
Set t3 x to 2.
Set t3 y to 2.5.
Set t3 z to 2.

Create box named t4 at x 0 y 0 z 0.
Set t4 scale_x to 1.
Set t4 scale_y to 1.
Set t4 scale_z to 1.
Set t4 color to #6B6B6B.
Set t4 x to -2.
Set t4 y to 0.5.
Set t4 z to 2.

Create box named t5 at x 0 y 0 z 0.
Set t5 scale_x to 1.
Set t5 scale_y to 1.
Set t5 scale_z to 1.
Set t5 color to #6B6B6B.
Set t5 x to -2.
Set t5 y to 1.5.
Set t5 z to 2.

Create box named w1 at x 0 y 0 z 0.
Set w1 scale_x to 1.
Set w1 scale_y to 0.6.
Set w1 scale_z to 1.
Set w1 color to #3C3C8B.
Set w1 x to 2.
Set w1 y to 0.5.
Set w1 z to -3.

Create box named p0 at x 0 y 0 z 0.
Set p0 scale_x to 1.
Set p0 scale_y to 1.
Set p0 scale_z to 1.
Set p0 y to -20.
Set p0 active to false.

Create box named p1 at x 0 y 0 z 0.
Set p1 scale_x to 1.
Set p1 scale_y to 1.
Set p1 scale_z to 1.
Set p1 y to -20.
Set p1 active to false.

Create box named p2 at x 0 y 0 z 0.
Set p2 scale_x to 1.
Set p2 scale_y to 1.
Set p2 scale_z to 1.
Set p2 y to -20.
Set p2 active to false.

Create box named p3 at x 0 y 0 z 0.
Set p3 scale_x to 1.
Set p3 scale_y to 1.
Set p3 scale_z to 1.
Set p3 y to -20.
Set p3 active to false.

Create box named p4 at x 0 y 0 z 0.
Set p4 scale_x to 1.
Set p4 scale_y to 1.
Set p4 scale_z to 1.
Set p4 y to -20.
Set p4 active to false.

Create box named p5 at x 0 y 0 z 0.
Set p5 scale_x to 1.
Set p5 scale_y to 1.
Set p5 scale_z to 1.
Set p5 y to -20.
Set p5 active to false.

Create box named p6 at x 0 y 0 z 0.
Set p6 scale_x to 1.
Set p6 scale_y to 1.
Set p6 scale_z to 1.
Set p6 y to -20.
Set p6 active to false.

Create box named p7 at x 0 y 0 z 0.
Set p7 scale_x to 1.
Set p7 scale_y to 1.
Set p7 scale_z to 1.
Set p7 y to -20.
Set p7 active to false.

Create box named p8 at x 0 y 0 z 0.
Set p8 scale_x to 1.
Set p8 scale_y to 1.
Set p8 scale_z to 1.
Set p8 y to -20.
Set p8 active to false.

Create box named p9 at x 0 y 0 z 0.
Set p9 scale_x to 1.
Set p9 scale_y to 1.
Set p9 scale_z to 1.
Set p9 y to -20.
Set p9 active to false.

Set place_pool to [p0, p1, p2, p3, p4, p5, p6, p7, p8, p9].
Set placed_blocks to [].

When key w pressed:
    Set moving_fwd to true.

When key w released:
    Set moving_fwd to false.

When key s pressed:
    Set moving_back to true.

When key s released:
    Set moving_back to false.

When key a pressed:
    Set moving_left to true.

When key a released:
    Set moving_left to false.

When key d pressed:
    Set moving_right to true.

When key d released:
    Set moving_right to false.

When key space pressed:
    If on_ground is true:
        Set velocity_y to -0.25.
        Set on_ground to false.

on click:
    If pool_index is less than 10:
        Get item at index pool_index of place_pool as pb.
        Round player_x as px.
        Set py to player_y - 1.
        Round py as p_y.
        Round player_z as pz.
        Set pb x to px.
        Set pb y to p_y.
        Set pb z to pz.
        Set pb color to selected_color.
        Set pb active to true.
        Set pool_index to pool_index + 1.

When key q pressed:
    Count length of placed_blocks as cnt.
    If cnt is greater than 0:
        Get last item of placed_blocks as lb.
        Set lb active to false.
        Remove lb from placed_blocks.
        Set pool_index to pool_index - 1.

When key r pressed:
    For each block in placed_blocks:
        Set block active to false.
    Set placed_blocks to [].
    Set pool_index to 0.

When key 1 pressed:
    Set selected_color to "#8B5E3C".
    Set selected_name to "dirt".
    Set block_hud text to "Block: dirt  |  1-4 to change".

When key 2 pressed:
    Set selected_color to "#4A7C3F".
    Set selected_name to "grass".
    Set block_hud text to "Block: grass  |  1-4 to change".

When key 3 pressed:
    Set selected_color to "#6B6B6B".
    Set selected_name to "stone".
    Set block_hud text to "Block: stone  |  1-4 to change".

When key 4 pressed:
    Set selected_color to "#3C3C8B".
    Set selected_name to "water".
    Set block_hud text to "Block: water  |  1-4 to change".

Every 30 ms:
    Set dx to 0.
    Set dz to 0.
    If moving_fwd is true:
        Set dz to dz - move_speed.
    If moving_back is true:
        Set dz to dz + move_speed.
    If moving_left is true:
        Set dx to dx - move_speed.
    If moving_right is true:
        Set dx to dx + move_speed.
    Set player_x to player_x + dx.
    Set player_z to player_z + dz.
    Set velocity_y to velocity_y + gravity.
    Set player_y to player_y + velocity_y.
    If player_y is greater than 0:
        Set player_y to 0.
        Set velocity_y to 0.
        Set on_ground to true.
    Set camera x to player_x.
    Set camera y to player_y + 2.
    Set camera z to player_z - 8.
    Turn player_x into text as px.
    Turn player_z into text as pz.
    Set pos_hud text to "Pos: " + px + " 0 " + pz.
```

## 61. modules/math_tools.angis

```angis
# Reusable Angis module

Define greet with name:
    Return, name.

Define double with value:
    Return, value * 2.
```

## 62. modules_app.angis

```angis
# Namespaced Angis module demo

use module modules/math_tools.angis as tools

Call, tools.greet with Ada as message.
Call, tools.double with 6 as doubled.

Show message.
Show doubled.
```

## 63. multistep_inline_phrases.angis

```angis
# One-line phrases can run multiple actions

Blueprint Player with name: Ada, score: 0.
Create Player named hero with name: Grace.

Define phrase boost {target:name} means Set, target.score to target.score + 1 and then Show, target.score.
Define phrase reset {target:name} means Set, target.score to 0 then Show, target.score.
Define phrase mark {target:name} means Set, target.score to 5; Show, target.score.

Boost hero.
Boost hero.
Reset hero.
Mark hero.
```

## 64. namespaced_phrases.angis

```angis
# Namespaced phrases let Angis grow with your wording

Define phrase app.start means Say, started.
Define phrase app.stop means Say, stopped.

App start.
app.stop.
```

## 65. natural_control_flow.angis

```angis
# Natural control-flow wording

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
```

## 66. natural_data_access.angis

```angis
# Natural data access and assignment

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
```

## 67. nested_key_phrases.angis

```angis
# Key slots can address nested object paths

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
```

## 68. object_methods.angis

```angis
# Objects can have reusable behavior

Create dictionary named player with name: Ada, health: 10.

Define method heal for player with amount:
    Set, self.health to self.health + amount.
    Return, self.health.

Define method rename for player with newName:
    Set, self.name to newName.

Call, player.heal with 5 as healed.
Call, player.rename with Lovelace.

Show, player.name.
Show, healed.
Show, player.health.
```

## 69. optional_phrase_words.angis

```angis
# Optional words make one phrase understand multiple phrasings

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
```

## 70. package_app.angis

```angis
# Folder package demo

use package packages/tools as kit

Call, kit.math.numbers.double with 6 as doubled.
Call, kit.math.numbers.triple with 5 as tripled.
Call, kit.text.names.echo with Ada as name.

Show doubled.
Show tripled.
Show name.
```

## 71. packages/tools/math/numbers.angis

```angis
# Math package module

Define double with value:
    Return, value * 2.

Define triple with value:
    Return, value * 3.
```

## 72. packages/tools/text/names.angis

```angis
# Text package module

Define echo with value:
    Return, value.
```

## 73. path_actions.angis

```angis
# Natural path actions

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
```

## 74. path_phrase_slots.angis

```angis
# Path slots capture local file paths

Define phrase attach {file:path} means Attach file at file.

Attach /Users/fellflow/Desktop/Angis/README.md.
```

## 75. phrase_library.angis

```angis
# Reusable phrase library

Define phrase note {message:text} means Show, message.
Define phrase start game means Say, started.

Define phrase set {field:key} of {target:name} to {value}:
    Set, target[field] to value.

Define phrase show {field:key} of {target:name}:
    Show, target[field].
```

## 76. phrase_templates.angis

```angis
# Teach Angis sentence shapes with slots

Blueprint Player with name: Ada, score: 0.
Create Player named hero with name: Grace.

Define phrase give {amount} points to {target}:
    Set, target.score to target.score + amount.
    Return, target.score.

Define phrase rename {target} to {newName}:
    Set, target.name to newName.

Define phrase show stats for {target}:
    Show, target.name.
    Show, target.score.

Give 3 points to hero as firstScore.
Give 7 points to hero as secondScore.
Rename hero to Lovelace.
Show stats for hero.

Show, firstScore.
Show, secondScore.
```

## 77. phrase_tree/actions/game.angis

```angis
# Nested game phrase pack

Define phrase start game means Say, started.
```

## 78. phrase_tree/ui/text.angis

```angis
# Nested UI phrase pack

Define phrase note {message:text} means Show, message.
```

## 79. phrases/app.angis

```angis
# App-building phrase pack

Define phrase make app {title:text} means App, title.
Define phrase make canvas means Scene, canvas.
Define phrase put text {message:text} means Text, message.
Define phrase put file {file:path} at {x:number} {y:number} {z:number} means Attach file file to window at x x y y z z.
```

## 80. phrases/game.angis

```angis
# Game phrase pack

use phrase pack text.angis

Define phrase start game means Say, started.
```

## 81. phrases/text.angis

```angis
# Text phrase pack

Define phrase note {message:text} means Show, message.
```

## 82. place_file_phrase.angis

```angis
# Place a file in an app window with custom wording

App, File Window.

Define phrase place {file:path} at {x:number} {y:number} {z:number} means Attach file file to window at x x y y z z.

Place /Users/fellflow/Desktop/Angis/README.md at 20 80 0.
```

## 83. point_phrase_slots.angis

```angis
# Point slots capture x y z coordinates as one value

App, File Window.

Define phrase place {file:path} at {location:point} means Attach file file to window at x location[0] y location[1] z location[2].

Place /Users/fellflow/Desktop/Angis/README.md at (20, 80, 0).
```

## 84. positive_vibes.angis

```angis
store "🌟 Welcome to Positive Vibes 🌟" as title
show title
show ""

Set day to 1.

store "you are enough" as a1
store "today is a gift" as a2
store "keep shining" as a3
store "be kind to yourself" as a4
store "you matter" as a5
store "breathe and smile" as a6
store "progress not perfection" as a7

show a1
show a2
show a3
show a4
show a5
show a6
show a7

show ""
show "= = = = = = = = = = = = = = = = ="
show "Remember: you are amazing!"
show "Keep being awesome."
show "Spread kindness everywhere you go."
show "= = = = = = = = = = = = = = = = ="

store "Be the reason someone smiles today." as bonus
show bonus
```

## 85. punctuation_phrases.angis

```angis
# Custom phrases tolerate sentence punctuation

Blueprint Player with name: Ada, score: 0.
Create Player named hero with name: Grace.

Define phrase give {amount:number} points to {target:name}:
    Set, target.score to target.score + amount.
    Return, target.score.

Give, 3 points to hero! as score.

Show, score.
Show, hero.score.
```

## 86. sentence_style.angis

```angis
# Angis IDE sentence-style test

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
```

## 87. shared.angis

```angis
Create dictionary named sharedData with level: 1, name: Demo.
```

## 88. solar_system.angis

```angis
App, Solar System.
Scene, canvas.
Window size 800 by 600.
Dark background.

Set cx to 400.
Set cy to 300.

Create circle named sun at x 383 y 283.
Set sun color to #fbbf24.
Set sun size to 34.

Create circle named mercury at x 400 y 300.
Set mercury color to #94a3b8.
Set mercury size to 8.

Create circle named venus at x 400 y 300.
Set venus color to #fb923c.
Set venus size to 12.

Create circle named earth at x 400 y 300.
Set earth color to #3b82f6.
Set earth size to 14.

Create circle named mars at x 400 y 300.
Set mars color to #ef4444.
Set mars size to 10.

Create circle named jupiter at x 400 y 300.
Set jupiter color to #f59e0b.
Set jupiter size to 22.

Create circle named saturn at x 400 y 300.
Set saturn color to #d97706.
Set saturn size to 18.

Set am to 0.
Set av to 30.
Set ae to 60.
Set ama to 90.
Set aj to 120.
Set asa to 150.

Set speed to 1.

Create text named title at x 10 y 10 saying "Solar System — press UP/DOWN to change speed".
Set title color to #94a3b8.
Set title size to 13.

Create text named info at x 10 y 570 saying "Speed: 1x".
Set info color to #64748b.
Set info size to 12.

Every 30 ms:
    calculate the sine of am as sm.
    calculate the cosine of am as cm.
    Set mercury x to cx + 50 * cm.
    Set mercury y to cy + 50 * sm.
    Set am to am + 4 * speed.

    calculate the sine of av as sv.
    calculate the cosine of av as cv.
    Set venus x to cx + 75 * cv.
    Set venus y to cy + 75 * sv.
    Set av to av + 3 * speed.

    calculate the sine of ae as se.
    calculate the cosine of ae as ce.
    Set earth x to cx + 105 * ce.
    Set earth y to cy + 105 * se.
    Set ae to ae + 2.5 * speed.

    calculate the sine of ama as sma.
    calculate the cosine of ama as cma.
    Set mars x to cx + 140 * cma.
    Set mars y to cy + 140 * sma.
    Set ama to ama + 2 * speed.

    calculate the sine of aj as sj.
    calculate the cosine of aj as cj.
    Set jupiter x to cx + 180 * cj.
    Set jupiter y to cy + 180 * sj.
    Set aj to aj + 1.5 * speed.

    calculate the sine of asa as ssa.
    calculate the cosine of asa as csa.
    Set saturn x to cx + 220 * csa.
    Set saturn y to cy + 220 * ssa.
    Set asa to asa + 1 * speed.

When key Up pressed:
    Set speed to speed + 0.5.
    If speed is greater than 5:
        Set speed to 5.
    Turn speed into text as st.
    Set info text to "Speed: " + st + "x".

When key Down pressed:
    Set speed to speed - 0.5.
    If speed is less than 0.5:
        Set speed to 0.5.
    Turn speed into text as st.
    Set info text to "Speed: " + st + "x".
```

## 89. standard_library.angis

```angis
# Angis standard library style

import pygame
import database
import network
import sound
import debug
import packaging

Create dictionary named player with health: 100, name: Ada.
Set player score to 0.

App, Standard Library Demo.
Scene, canvas.
Window size 800 by 500.

Text, Pygame-style canvas backend. Press D to move the box into the target.

Create rectangle named box at x 100 y 220.
Set box color to purple.
Set box width to 120.
Set box height to 80.

Create circle named target at x 520 y 210.
Set target color to green.
Set target size to 70.

When key d pressed:
    Move box right by 12.

When box touches target:
    Show text The objects touched.
    Play sound /Users/fellflow/Desktop/Angis/angis loading/loading-adieo.mp3.

Debug all.
Export app to file /Users/fellflow/Desktop/Angis/assets/standard_library_export.html.
```

## 90. stdlib_actions.angis

```angis
# Angis safe standard-library actions

Use math sqrt with value: 81 as root.
Use math power with base: 2, exponent: 8 as power.
Use random integer with min: 1, max: 6 as roll.
Use time now as stamp.
Use json parse with text: {"score": 42} as data.
Use json stringify with value: data as packed.
Use text uppercase with text: hello as loud.
Use text split with text: red-blue-green, by: - as parts.
Use text join with values: parts, by: / as joined.
Use list length with values: parts as partCount.
Use map keys with value: data as dataKeys.
Use file info with path: /Users/fellflow/Desktop/Angis/examples/hello.angis as fileInfo.
Use path extension with path: /Users/fellflow/Desktop/Angis/examples/hello.angis as extension.
Use capabilities list as available.

Show root.
Show power.
Show roll.
Show stamp.
Show packed.
Show loud.
Show joined.
Show partCount.
Show dataKeys.
Show extension.
Debug capabilities.
```

## 91. text_transform.angis

```angis
# Natural text transforms

Set title to hello brave world.

Split title by space as words.
Join words with dash as slug.
Replace brave in title with bright as renamed.

Show first item of words.
Show slug.
Show renamed.
```

## 92. time_actions.angis

```angis
# Natural time actions

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
```

## 93. true_3d.angis

```angis
# True 3D software-rendered scene

import std

App, True 3D Demo.
Scene, true 3D.
Window size 900 by 620.

Text, This uses Angis built-in software 3D rendering.

Create cube named core at x 0 y 0 z 0.
Set core color to blue.
Set core size to 160.

Create cube named leftTower at x -180 y 20 z 80.
Set leftTower color to purple.
Set leftTower size to 90.

Create cube named rightTower at x 180 y -20 z -40.
Set rightTower color to green.
Set rightTower size to 110.
```

## 94. typed_phrase_slots.angis

```angis
# Typed slots make custom phrases stricter

Blueprint Player with name: Ada, score: 0.
Create Player named hero with name: Grace.

Define phrase give {amount:number} points to {target:name}:
    Set, target.score to target.score + amount.
    Return, target.score.

Define phrase note {message:text}:
    Show, message.

Give 3 points to hero as firstScore.
Note hello from typed text.

Show, firstScore.
Show, hero.score.

# This would fail because amount must be a number:
# Give many points to hero.
```

## 95. ui_media.angis

```angis
# Angis UI, media, and package demo

import ui
import video
import sound
import packaging

App, Studio.
Scene, canvas.
Window size 900 by 560.
Layout, grid with 3 columns.

Text, Angis can describe controls, media, sound, and packaging with wording-code.

Create button named start at x 24 y 70 with text Start.
Create input named nameBox at x 24 y 120.
Set nameBox width to 240.
Create slider named speed at x 24 y 170.
Set speed width to 240.
Create checkbox named musicOn at x 24 y 220.

Set sound volume to 70.

When button start clicked:
    Show text Started from Angis wording-code.
```

## 96. universal_demo.angis

```angis
# Universal Angis Demo
# This demo combines Visuals, Data, Networking, and Business Logic
# using multiple languages and AI fallbacks.

# 1. VISUALS (in English)
App "Data Center"
Scene "canvas"
Window size 800 by 600.
Dark background.

Create circle hub at x 400 y 300 z 1
Set hub.color to "#38bdf8"
Set hub.size to 100

# 2. DATA & BUSINESS LOGIC (using Italian fallback/first-class)
set_language "it"
imposta inventario a []
mostra "Sistema inizializzato."

# Adding items to inventory (Business Logic)
aggiungi "Server 1" a inventario
aggiungi "Router 2" a inventario

# Heuristic assignment (AI Fallback)
numero_server = 2
mostra "Server attivi: " + numero_server

# 3. NETWORKING (using Portuguese AI Fallback)
set_language "pt"
mostre "Conectando ao banco de dados..."

# AI Heuristic for fetch (Networking)
buscar de https://api.example.com/status
mostre "Dados recebidos."

# 4. DATA (in English again)
set_language "en"
Open database "assets/angis_demo.sqlite" as db
Execute sql "CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, power INTEGER)" on db
Execute sql "INSERT INTO stats (power) VALUES (100)" on db
Show "Local database updated."

# Interaction
When hub is clicked:
    Say "Networking pulse sent!"
    Set hub.color to "#facc15"
    Animate hub up by 5 every 50 milliseconds
```

## 97. use_phrase_library.angis

```angis
# Use custom phrases from another Angis file

use phrase library phrase_library.angis

Blueprint Player with name: Ada, score: 0.
Create Player named hero with name: Grace.

Start game.
Note hello from library.
Set score of hero to 11.
Show score of hero.
```

## 98. use_phrase_pack.angis

```angis
# Use a nested phrase pack

use phrase pack phrases/game.angis

Start game.
Note nested phrase pack works.
```

## 99. use_phrase_pack_folder.angis

```angis
# Load every .angis phrase file in a folder

use phrase pack phrases

Start game.
Note folder phrase pack works.
```

## 100. use_recursive_phrase_pack.angis

```angis
# Load .angis phrase files from nested folders

use phrase pack phrase_tree

Start game.
Note recursive phrase pack works.
```

## 101. variable_mutation.angis

```angis
# Natural variable mutation

Set score to 10.
Take 2 from score.
Decrease score by 1.
Multiply score by 3.
Double score.
Divide score by 2.
Cut score in half.

Show score.
```

## 102. variables.angis

```angis
# Variable examples
set x to 5
make y equal 8
store "Ada" as name
show x
display y
tell me name
```

## 103. website_demo.angis

```angis
App, My Angis Website.
Scene, canvas.
Window size 900 by 650.

Set bg_color to #1a1a2e.
Set accent to #e94560.
Set text_color to #ffffff.
Set section_bg to #16213e.
Set card_bg to #0f3460.

Create rectangle named background at x 0 y 0.
Set background width to 900.
Set background height to 650.
Set background color to bg_color.

Create text named site_title at x 30 y 30 saying "ANGIS STUDIO".
Set site_title color to accent.
Set site_title size to 22.

Create text named nav_home at x 700 y 35 saying "Home".
Set nav_home color to text_color.
Set nav_home size to 14.

Create text named nav_projects at x 760 y 35 saying "Projects".
Set nav_projects color to text_color.
Set nav_projects size to 14.

Create text named nav_contact at x 840 y 35 saying "Contact".
Set nav_contact color to text_color.
Set nav_contact size to 14.

Create rectangle named header_line at x 0 y 65.
Set header_line width to 900.
Set header_line height to 2.
Set header_line color to accent.

Create text named hero_title at x 60 y 120 saying "Building Cool Stuff With Angis".
Set hero_title color to text_color.
Set hero_title size to 28.

Create text named hero_sub at x 60 y 165 saying "A natural language programming language that lets you build 3D games, tools, and apps in plain English."
Set hero_sub color to #aaaacc.
Set hero_sub size to 13.

Create rectangle named hero_btn at x 60 y 210.
Set hero_btn width to 140.
Set hero_btn height to 36.
Set hero_btn color to accent.
Set hero_btn border_radius to 6.

Create text named hero_btn_label at x 75 y 220 saying "Get Started".
Set hero_btn_label color to text_color.
Set hero_btn_label size to 13.

Create text named hero_btn_arrow at x 167 y 220 saying "→".
Set hero_btn_arrow color to text_color.
Set hero_btn_arrow size to 13.

Create rectangle named section1_bg at x 0 y 280.
Set section1_bg width to 900.
Set section1_bg height to 170.
Set section1_bg color to section_bg.

Create text named features_title at x 60 y 300 saying "What You Can Build".
Set features_title color to text_color.
Set features_title size to 18.

Set card_count to 3.
Set card_w to 240.
Set card_h to 100.
Set card_y_pos to 335.
Set card1_x to 60.
Set card2_x to 320.
Set card3_x to 580.

Create rectangle named card1 at x 60 y 335.
Set card1 width to card_w.
Set card1 height to card_h.
Set card1 color to card_bg.
Set card1 border_radius to 8.

Create rectangle named card2 at x 320 y 335.
Set card2 width to card_w.
Set card2 height to card_h.
Set card2 color to card_bg.
Set card2 border_radius to 8.

Create rectangle named card3 at x 580 y 335.
Set card3 width to card_w.
Set card3 height to card_h.
Set card3 color to card_bg.
Set card3 border_radius to 8.

Create text named card1_title at x 75 y 350 saying "3D Games".
Set card1_title color to accent.
Set card1_title size to 14.

Create text named card1_desc at x 75 y 377 saying "Build Flappy Bird, platformers, and more with 3D scenes, physics, and events."
Set card1_desc color to #99aacc.
Set card1_desc size to 11.

Create text named card2_title at x 335 y 350 saying "File & Data Tools".
Set card2_title color to accent.
Set card2_title size to 14.

Create text named card2_desc at x 335 y 377 saying "Read/write files, parse CSV, query SQLite, fetch HTTP APIs, and process JSON."
Set card2_desc color to #99aacc.
Set card2_desc size to 11.

Create text named card3_title at x 595 y 350 saying "AI & Text Processing".
Set card3_title color to accent.
Set card3_title size to 14.

Create text named card3_desc at x 595 y 377 saying "Keyword extraction, sentiment, summarization, and text generation — all offline."
Set card3_desc color to #99aacc.
Set card3_desc size to 11.

Create rectangle named section2_bg at x 0 y 450.
Set section2_bg width to 900.
Set section2_bg height to 200.
Set section2_bg color to bg_color.

Create text named stats_title at x 60 y 470 saying "Angis By The Numbers".
Set stats_title color to text_color.
Set stats_title size to 18.

Create text named stat1_val at x 60 y 510 saying "19+".
Set stat1_val color to accent.
Set stat1_val size to 30.

Create text named stat1_label at x 60 y 545 saying "Capability Categories".
Set stat1_label color to #99aacc.
Set stat1_label size to 11.

Create text named stat2_val at x 260 y 510 saying "140+".
Set stat2_val color to accent.
Set stat2_val size to 30.

Create text named stat2_label at x 260 y 545 saying "Phrase Patterns".
Set stat2_label color to #99aacc.
Set stat2_label size to 11.

Create text named stat3_val at x 460 y 510 saying "4".
Set stat3_val color to accent.
Set stat3_val size to 30.

Create text named stat3_label at x 460 y 545 saying "Human Languages".
Set stat3_label color to #99aacc.
Set stat3_label size to 11.

Create text named stat4_val at x 660 y 510 saying "0".
Set stat4_val color to accent.
Set stat4_val size to 30.

Create text named stat4_label at x 660 y 545 saying "Cloud Dependencies".
Set stat4_label color to #99aacc.
Set stat4_label size to 11.

Create rectangle named footer_bg at x 0 y 610.
Set footer_bg width to 900.
Set footer_bg height to 40.
Set footer_bg color to #0d0d1a.

Create text named footer_text at x 320 y 622 saying "Built with Angis — 2026 — Open source on GitHub".
Set footer_text color to #666688.
Set footer_text size to 10.

Set click_step to 0.

on click:
    Set click_step to click_step + 1.
    If click_step is 1:
        Set hero_btn_label text to "You clicked!".
        Set hero_btn color to #2ecc71.
        Set card1 color to #e94560.
        Set card1_title color to #ffffff.
    If click_step is 2:
        Set hero_btn_label text to "Click again!".
        Set hero_btn color to #ff6b81.
        Set card1 color to #0f3460.
        Set card1_title color to #e94560.
        Set card2 color to #e94560.
        Set card2_title color to #ffffff.
    If click_step is 3:
        Set hero_btn_label text to "Get Started".
        Set hero_btn color to #e94560.
        Set card2 color to #0f3460.
        Set card2_title color to #e94560.
        Set card3 color to #e94560.
        Set card3_title color to #ffffff.
    If click_step is 4:
        Set card3 color to #0f3460.
        Set card3_title color to #e94560.
        Set hero_btn_label text to "All done! Click to reset".
        Set hero_btn color to #9b59b6.
        Set click_step to 0.
```

## 104. while_loop.angis

```angis
# Angis while loop demo

Set, score to 0.

While, score is less than 5:
    Add, 1 to score.
    Show, score.

If, score is at least 5:
    Say, loop finished.
```

## 105. word_expressions.angis

```angis
# Word math works inside normal expressions

Set, x to 5.
Set, y to 7.

Set total to x plus y times 2.
Set half to total divided by 2.
Set left to total minus y.

If total is bigger than x times 3:
    Show, total.

If half is same as 9.5:
    Show, half.

Show, left.
```
