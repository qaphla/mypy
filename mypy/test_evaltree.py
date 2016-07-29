from mypy.evaltree import Evaluator
from mypy.parse import parse
from mypy.options import Options
from mypy.nodes import IntExpr
from mypy.types import LiteralType

evaluator = Evaluator({"x": LiteralType('builtins.int', IntExpr(1))})
def print_nodes(file: str) -> None:
    mypy_file = parse(file, "ASD", None, Options())
    for d in mypy_file.defs:
        print(d.expr.accept(evaluator))

def test_evaltree():
    f = "1 + 2\n3 - 4\nlambda x: x + 1"
    print_nodes(f)
