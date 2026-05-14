from .parser import Game


HEX_COLORS = {
    "grass": "#4CAF50", "dirt": "#795548", "stone": "#9E9E9E",
    "cobblestone": "#757575", "wood": "#5D4037", "planks": "#8D6E63",
    "leaves": "#388E3C", "sand": "#FDD835", "water": "#2196F3",
    "snow": "#FAFAFA", "ice": "#B3E5FC", "bedrock": "#212121",
    "brick": "#C62828", "gold": "#FFD700", "diamond": "#00BCD4",
    "iron": "#B0BEC5", "coal": "#37474F", "redstone": "#D32F2F",
    "obsidian": "#1A1A2E", "netherrack": "#660000",
}


def hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"Vec3({r/255:.3f},{g/255:.3f},{b/255:.3f})"


def transpile(game: Game) -> str:
    blocks = list(game.blocks.values())
    if not blocks:
        return "# No blocks defined"

    color_map = {}
    for b in blocks:
        c = HEX_COLORS.get(b.name.lower(), b.color)
        color_map[b.name] = hex_to_rgb(c)

    color_entries = "\n".join(
        f'    "{b.name.lower()}": {color_map[b.name]},' for b in blocks
    )

    block_names = [f'"{b.name.lower()}"' for b in blocks]

    terrain = "\n".join(
        f'        Voxel(position=Vec3(x, 0, z), kind="{b.name.lower()}")'
        for b in blocks[:1]
    )

    return f"""from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

app = Ursina()

BLOCK_COLORS = {{
{color_entries}
}}

BLOCK_KINDS = [{', '.join(block_names)}]
current_kind = BLOCK_KINDS[0]


class Voxel(Button):
    def __init__(self, position=(0, 0, 0), kind="dirt"):
        self.kind = kind
        col = BLOCK_COLORS.get(kind, Vec3(0.5, 0.5, 0.5))
        super().__init__(
            parent=scene,
            position=position,
            model="cube",
            texture="white_cube",
            color=Color(*col, 1),
            highlight_color=Color(*col * 1.2, 1),
        )

    def input(self, key):
        if self.hovered:
            if key == "left mouse down":
                Voxel(position=self.position + mouse.normal, kind=current_kind)
            if key == "right mouse down":
                destroy(self)


def update():
    global current_kind
    for i, kind in enumerate(BLOCK_KINDS):
        if held_keys[str(i + 1)]:
            current_kind = kind


class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent=scene, model="sphere", texture="sky_default",
            scale=500, double_sided=True,
        )


player = FirstPersonController()
player.speed = {game.config.player_speed}
player.jump_height = {game.config.player_jump}
Sky()

for x in range(-10, 11):
    for z in range(-10, 11):
{terrain}

app.run()
"""
