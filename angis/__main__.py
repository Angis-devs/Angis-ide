import sys
from . import build
from .parser import parse, Game
from .transpiler_game import transpile as transpile_game


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m angis <file.ang> [output.py]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        source = f.read()

    ast = parse(source)

    if isinstance(ast, Game):
        output = transpile_game(ast)
    else:
        output = build(source)

    out_path = sys.argv[2] if len(sys.argv) > 2 else "output.py"
    with open(out_path, "w") as f:
        f.write(output)

    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
