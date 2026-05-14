# Angis Descriptive Language

Angis is a minimal descriptive language that transpiles to Python. Two modes:
- **app** mode -> Flask web apps
- **game** mode -> Ursina 3D games (like Minecraft)

## File Extension
`.ang`

## Comments
`-- single line comment`

## Language Structure

### App
```
app "App Name"
  ... models and pages ...
```

### Models (data)
```
model <Name>
  <field>: <type>
  <field>: <type>
```
Types: `text`, `number`, `bool`, `list`

### Pages (views)
```
page "Page Name" [/route/path]
  heading "Title text"
  text "Paragraph text"
  list <ModelName>
  form <ModelName>
  button "Label" -> /path
  button "Label" -> save
  button "Label" -> delete
```

## Rules
- Indentation = 2 spaces (required)
- No tabs
- Model names are PascalCase
- Page names are quoted strings
- Routes use brackets like [/path/:id/edit]
- `->` maps button actions to routes or keywords (save, delete)

## Game Mode
```
game "Game Name"
  world type infinite
  world biome forest, desert, plains
  block BlockName
    color #hexcolor
    drops OtherBlock
  player speed 10
  player jump 3
```

## Transpiling
```bash
python -m angis myapp.ang out.py    # web app
python -m angis mygame.ang game.py   # 3D game
python out.py
```

## App Example
```angis
app "Notes"
  model Note
    title: text
    content: text

  page "Home" [/]
    heading "Notes App"
    text "Your personal notes"
    button "View Notes" -> /notes

  page "Notes" [/notes]
    list Note
    button "New Note" -> /notes/new
```

## Game Example (Minecraft)
```angis
game "Minecraft"
  world type infinite
  block Grass
    color #4CAF50
  block Dirt
    color #795548
  block Stone
    color #9E9E9E
  block Wood
    color #5D4037
  block Planks
    color #8D6E63
  player speed 10
  player jump 3
```
  model Note
    title: text
    content: text

  page "Home" [/]
    heading "Notes App"
    text "Your personal notes"
    button "View Notes" -> /notes

  page "Notes" [/notes]
    list Note
    button "New Note" -> /notes/new
```

## VS Code Extension
Located in `vs-code-extension/`. Install via:
- Open that folder in VS Code
- Press F5 to run extension
- Or copy to `~/.vscode/extensions/angis-<version>`
