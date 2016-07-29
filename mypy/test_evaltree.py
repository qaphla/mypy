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
    expressions = ["1 + 2",
                   "3 < 4",
                   "lambda x: x + 1",
                   "lambda x: x < 3",
                   "-7"]
    f = "\n".join(expressions)
    print_nodes(f)
