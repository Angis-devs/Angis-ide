import re
from dataclasses import dataclass, field

@dataclass
class Field:
    name: str
    type: str

@dataclass 
class Page:
    name: str
    route: str
    items: list = field(default_factory=list)

@dataclass
class Model:
    name: str
    fields: list[Field] = field(default_factory=list)

@dataclass
class Block:
    name: str
    color: str = "#888888"
    top: str | None = None
    drops: str | None = None

@dataclass
class GameConfig:
    world_type: str = "infinite"
    seed: str = "random"
    biomes: list = field(default_factory=list)
    player_speed: int = 8
    player_jump: int = 3

@dataclass
class Game:
    name: str
    blocks: dict[str, Block] = field(default_factory=dict)
    config: GameConfig = field(default_factory=GameConfig)

@dataclass
class App:
    name: str
    models: dict[str, Model] = field(default_factory=dict)
    pages: list[Page] = field(default_factory=list)


def parse(source: str) -> App | Game:
    app = App(name="")
    game = None
    current_model = None
    current_page = None
    current_block = None
    mode = None

    for line in source.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("--"):
            continue

        if m := re.match(r'app "([^"]+)"', stripped):
            mode = "app"
            app.name = m.group(1)
            current_model = None
            current_page = None

        elif m := re.match(r'game "([^"]+)"', stripped):
            mode = "game"
            game = Game(name=m.group(1))
            current_block = None

        elif mode == "app":
            if m := re.match(r'model (\w+)', stripped):
                current_model = Model(name=m.group(1))
                app.models[current_model.name] = current_model
                current_page = None

            elif m := re.match(r'page "([^"]+)" \[([^\]]+)\]', stripped):
                current_page = Page(name=m.group(1), route=m.group(2))
                app.pages.append(current_page)
                current_model = None

            elif current_model and (m := re.match(r'(\w+):\s*(\w+)', stripped)):
                current_model.fields.append(Field(name=m.group(1), type=m.group(2)))

            elif current_page and (m := re.match(r'(heading|text|list|form)\s+(.+?)(?:\s*->\s*(.+))?$', stripped)):
                current_page.items.append({
                    "type": m.group(1),
                    "value": m.group(2).strip(' "'),
                    "target": m.group(3).strip() if m.group(3) else None,
                })

            elif current_page and (m := re.match(r'button\s+"([^"]+)"\s*->\s*(\S+)', stripped)):
                current_page.items.append({
                    "type": "button",
                    "label": m.group(1),
                    "target": m.group(2),
                })

        elif mode == "game":
            if m := re.match(r'world type (\w+)', stripped):
                game.config.world_type = m.group(1)

            elif m := re.match(r'world seed (\w+)', stripped):
                game.config.seed = m.group(1)

            elif m := re.match(r'world biome (.+)', stripped):
                game.config.biomes = [b.strip() for b in m.group(1).split(",")]

            elif m := re.match(r'block (\w+)', stripped):
                current_block = Block(name=m.group(1))
                game.blocks[current_block.name] = current_block

            elif current_block and (m := re.match(r'color #?(\w+)', stripped)):
                c = m.group(1)
                current_block.color = f"#{c}" if not c.startswith("#") else c

            elif current_block and (m := re.match(r'top #?(\w+)', stripped)):
                c = m.group(1)
                current_block.top = f"#{c}" if not c.startswith("#") else c

            elif current_block and (m := re.match(r'drops (\w+)', stripped)):
                current_block.drops = m.group(1)

            elif m := re.match(r'player speed (\d+)', stripped):
                game.config.player_speed = int(m.group(1))

            elif m := re.match(r'player jump (\d+)', stripped):
                game.config.player_jump = int(m.group(1))

    return game if game is not None else app
