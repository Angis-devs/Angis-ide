"""Optional real pygame backend for Angis apps."""

from __future__ import annotations

from .errors import AngisRuntimeError
from .ir import AppSpec


def run_pygame_app(app: AppSpec) -> None:
    try:
        import pygame
    except ImportError as exc:
        raise AngisRuntimeError("pygame is not installed for this Python. Install it, then run: python3 -m angis pygame file.angis") from exc

    pygame.init()
    screen = pygame.display.set_mode((app.width, app.height))
    pygame.display.set_caption(app.title)
    clock = pygame.time.Clock()
    objects = [obj for obj in app.objects or []]
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((248, 250, 252))
        for obj in objects:
            props = obj.properties or {}
            color = _pygame_color(str(props.get("color", "#2563eb")))
            width = int(props.get("width", props.get("size", 48))) if isinstance(props.get("width", props.get("size", 48)), (int, float)) else 48
            height = int(props.get("height", props.get("size", 48))) if isinstance(props.get("height", props.get("size", 48)), (int, float)) else 48
            rect = pygame.Rect(obj.x, obj.y, width, height)
            if obj.kind in {"circle", "ball", "player", "enemy"}:
                pygame.draw.ellipse(screen, color, rect)
            else:
                pygame.draw.rect(screen, color, rect)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


def _pygame_color(value: str) -> tuple[int, int, int]:
    names = {
        "red": (220, 38, 38),
        "green": (22, 163, 74),
        "blue": (37, 99, 235),
        "purple": (147, 51, 234),
        "black": (17, 24, 39),
        "white": (255, 255, 255),
    }
    if value.lower() in names:
        return names[value.lower()]
    if value.startswith("#") and len(value) == 7:
        return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)
    return 37, 99, 235
