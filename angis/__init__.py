from .parser import parse
from .transpiler import transpile


def build(source: str) -> str:
    app = parse(source)
    return transpile(app)
