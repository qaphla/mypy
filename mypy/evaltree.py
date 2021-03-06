"""Contains an evaluator for AST expressions in a given context."""

from typing import cast, Dict, List, Tuple, Callable, Union, Optional

from mypy.types import (
    Type, AnyType, CallableType, Overloaded, NoneTyp, Void, TypeVarDef,
    TupleType, Instance, TypeVarId, TypeVarType, ErasedType, UnionType,
    LiteralType, PartialType, DeletedType, UnboundType, UninhabitedType, TypeType
)
from mypy.nodes import (
    Argument, NameExpr, RefExpr, Var, FuncDef, OverloadedFuncDef, TypeInfo, CallExpr,
    Node, MemberExpr, IntExpr, StrExpr, BytesExpr, UnicodeExpr, FloatExpr,
    OpExpr, UnaryExpr, IndexExpr, CastExpr, RevealTypeExpr, TypeApplication, ListExpr,
    TupleExpr, DictExpr, FuncExpr, SuperExpr, SliceExpr, Context, NodeVisitor, Expression,
    ListComprehension, GeneratorExpr, SetExpr, MypyFile, Decorator,
    ConditionalExpr, ComparisonExpr, TempNode, SetComprehension,
    DictionaryComprehension, ComplexExpr, EllipsisExpr,
    TypeAliasExpr, BackquoteExpr, PromoteExpr, ARG_POS, ARG_NAMED, ARG_STAR2,
)
from mypy.nodes import function_type
from mypy import nodes
import mypy.checker
from mypy import types
from mypy.sametypes import is_same_type
from mypy.erasetype import replace_meta_vars
from mypy.messages import MessageBuilder
from mypy import messages
from mypy.infer import infer_type_arguments, infer_function_type_arguments
from mypy import join
from mypy.subtypes import is_subtype, is_equivalent
from mypy import applytype
from mypy import erasetype
from mypy.checkmember import analyze_member_access, type_object_type
from mypy.semanal import self_type
from mypy.constraints import get_actual_type
from mypy.checkstrformat import StringFormatterChecker
from mypy.expandtype import expand_type
import mypy.checkexpr

from mypy import experiments


def evaluate_condition(condition_expr: FuncExpr,
                       condition_args: Dict[str, LiteralType],
                       messages: Optional[MessageBuilder]
                       ) -> bool:
    condition_body = condition_expr.expr()
    evaluator = Evaluator(condition_args)
    result = condition_body.accept(evaluator)

    assert isinstance(result, IntExpr)
    return bool(result.value)


class Evaluator(NodeVisitor[Expression]):

    def __init__(self, var_ctx: Dict[str, LiteralType]):
        self.var_ctx = var_ctx

    # Constant expressions

    def visit_int_expr(self, expr: IntExpr) -> Expression:
        return expr

    def visit_str_expr(self, expr: StrExpr) -> Expression:
        return expr

    def visit_bytes_expr(self, expr: BytesExpr) -> Expression:
        return expr

    def visit_unicode_expr(self, expr: UnicodeExpr) -> Expression:
        return expr

    def visit_float_expr(self, expr: FloatExpr) -> Expression:
        return expr

    def visit_complex_expr(self, expr: ComplexExpr) -> Expression:
        return expr

    # qwer

    def visit_name_expr(self, expr: NameExpr) -> Expression:
        value = self.var_ctx[expr.name].value
        if value is None:
            raise Exception
        return value

    def visit_member_expr(self, expr: MemberExpr) -> Expression:
        raise NotImplemented

#    def visit_yield_from_expr(self, expr: YieldFromExpr) -> Expression:
#        pass

#    def visit_yield_expr(self, expr: YieldExpr) -> Expression:
#        pass

    def visit_call_expr(self, expr: CallExpr) -> Expression:
        pass

    def visit_op_expr(self, expr: OpExpr) -> Expression:
        left = expr.left.accept(self)
        right = expr.right.accept(self)
        op = expr.op

        # Up-cast to the larger numeric type (or string, for +)
        if op == '+':
            op_type = 0
            fn = lambda l, r: l + r
        elif op == '-':
            op_type = 0
            fn = lambda l, r: l - r
        elif op == '*':
            op_type = 0
            fn = lambda l, r: l * r
        elif op == '/':
            op_type = 0
            fn = lambda l, r: l / r

        # int, float, complex -> complex
        elif op == '**':
            op_type = 1
            fn = lambda l, r: l ** r

        # int, int -> int or float, float -> float
        elif op == '//':
            op_type = 2
            fn = lambda l, r: l // r

        # int ops -- int, int -> int
        elif op == '%':
            op_type = 3
            fn = lambda l, r: l % r
        elif op == '&':
            op_type = 3
            fn = lambda l, r: l & r
        elif op == '|':
            op_type = 3
            fn = lambda l, r: l | r
        elif op == '^':
            op_type = 3
            fn = lambda l, r: l ^ r
        elif op == '<<':
            op_type = 3
            fn = lambda l, r: l << r
        elif op == '>>':
            op_type = 3
            fn = lambda l, r: l >> r

        elif op == '<':
            op_type = 4
            fn = lambda l, r: l < r
        elif op == '>':
            op_type = 4
            fn = lambda l, r: l > r
        elif op == '<=':
            op_type = 4
            fn = lambda l, r: l <= r
        elif op == '>=':
            op_type = 4
            fn = lambda l, r: l >= r

        elif op == '==':
            op_type = 5
            fn = lambda l, r: l == r
        elif op == '!=':
            op_type = 5
            fn = lambda l, r: l != r
        # TODO(sinan) HACK!
        elif op == 'in':
            op_type = 6
            fn = lambda l, r: l in r
        elif op == 'not in':
            op_type = 6
            fn = lambda l, r: l not in r
        else:
            raise NotImplemented

        if op_type == 0:
            if isinstance(right, ListExpr):
                if isinstance(left, ListExpr):
                    return ListExpr(fn(left.items, right.items))
                else:
                    return ListExpr(fn(left.value, right.items))
            elif isinstance(right, TupleExpr):
                if isinstance(left, TupleExpr):
                    return TupleExpr(fn(left.items, right.items))
                else:
                    return TupleExpr(fn(left.value, right.items))
            elif isinstance(right, StrExpr):
                return StrExpr(fn(left.value, right.value))
            elif isinstance(left, ComplexExpr) or isinstance(right, ComplexExpr):
                return ComplexExpr(fn(left.value, right.value))
            elif isinstance(left, FloatExpr) or isinstance(right, FloatExpr):
                return FloatExpr(fn(left.value, right.value))
            else:
                assert isinstance(left, IntExpr) and isinstance(right, IntExpr)
                return IntExpr(fn(left.value, right.value))
        elif op_type == 1:
            assert isinstance(left, IntExpr) or isinstance(left, FloatExpr) or isinstance(left, ComplexExpr)
            assert isinstance(right, IntExpr) or isinstance(right, FloatExpr) or isinstance(right, ComplexExpr)
            return ComplexExpr(fn(left.value, right.value))
        elif op_type == 2:
            if isinstance(left, IntExpr) and isinstance(right, IntExpr):
                return IntExpr(fn(left.value, right.value))
            elif isinstance(left, FloatExpr) and (isinstance(right, FloatExpr) or isinstance(right, IntExpr)):
                return FloatExpr(fn(left.value, right.value))
            elif isinstance(right, FloatExpr) and isinstance(right, IntExpr):
                return FloatExpr(fn(left.value, right.value))
            else:
                raise NotImplemented
        elif op_type == 3:
            assert isinstance(left, IntExpr)
            assert isinstance(right, IntExpr)
            return IntExpr(fn(left.value, right.value))
        elif op_type == 4:
            assert isinstance(left, IntExpr) or isinstance(left, FloatExpr)
            assert isinstance(right, IntExpr) or isinstance(right, FloatExpr)
            return IntExpr(int(fn(left.value, right.value)))
        elif op_type == 5:
            assert isinstance(left, IntExpr) or isinstance(left, FloatExpr) or isinstance(left, ComplexExpr) or isinstance(left, StrExpr)
            assert isinstance(right, IntExpr) or isinstance(right, FloatExpr) or isinstance(right, ComplexExpr) or isinstance(right, StrExpr)
            return IntExpr(int(fn(left.value, right.value)))
        elif op_type == 6:
            assert(isinstance(left, StrExpr) and isinstance(right, StrExpr))
            return IntExpr(int(fn(left.value, right.value)))
        else:
            assert False

    def visit_comparison_expr(self, expr: ComparisonExpr) -> Expression:
        results = []
        for index in range(len(expr.operators)):
            left, right = expr.operands[index], expr.operands[index + 1]
            operator = expr.operators[index]
            opExpr = OpExpr(operator, left, right)
            result = opExpr.accept(self)
            results.append(result)
        # Do the and of all comparisons
        for r in results:
            if not isinstance(r, IntExpr):
                raise Exception
            if r.value == 0:
                return IntExpr(0)
        return IntExpr(1)

    def visit_cast_expr(self, expr: CastExpr) -> Expression:
        pass

    def visit_reveal_type_expr(self, expr: RevealTypeExpr) -> Expression:
        pass

    def visit_super_expr(self, expr: SuperExpr) -> Expression:
        pass

    def visit_unary_expr(self, expr: UnaryExpr) -> Expression:
        rhs = expr.expr.accept(self)
        if expr.op == '-':
            if (not isinstance(rhs, IntExpr)) and (not isinstance(rhs, FloatExpr)):
                raise Exception
            rhs.value = -rhs.value
        if expr.op == '~':
            if not isinstance(rhs, IntExpr):
                raise Exception
            rhs.value = ~rhs.value
        return rhs

    def visit_list_expr(self, expr: ListExpr) -> Expression:
        return ListExpr([item.accept(self) for item in expr.items])

    def visit_dict_expr(self, expr: DictExpr) -> Expression:
        return DictExpr([(l.accept(self), r.accept(self)) for (l, r) in expr.items])

    def visit_tuple_expr(self, expr: TupleExpr) -> Expression:
        return TupleExpr([item.accept(self) for item in expr.items])

    def visit_set_expr(self, expr: SetExpr) -> Expression:
        return SetExpr([item.accept(self) for item in expr.items])

    def visit_index_expr(self, expr: IndexExpr) -> Expression:
        base = expr.base.accept(self)
        index = expr.index.accept(self)
        # Currently this only supports indexing using base types (and probably not all of those).
        # TODO: Support indexing with more types.
        assert isinstance(base, ListExpr) or isinstance(base, Tuple) or isinstance(base, DictExpr)
        assert isinstance(index, IntExpr) or isinstance(index, FloatExpr) or isinstance(index, StrExpr)
        return base.items[index.value]

    def visit_type_application(self, expr: TypeApplication) -> Expression:
        pass

    def visit_func_expr(self, expr: FuncExpr) -> Expression:
        body = expr.expr()
        return body.accept(self)

    def visit_list_comprehension(self, expr: ListComprehension) -> Expression:
        pass

    def visit_set_comprehension(self, expr: SetComprehension) -> Expression:
        pass

    def visit_dictionary_comprehension(self, expr: DictionaryComprehension) -> Expression:
        pass

    def visit_generator_expr(self, expr: GeneratorExpr) -> Expression:
        pass

    def visit_slice_expr(self, expr: SliceExpr) -> Expression:
        pass

    def visit_conditional_expr(self, expr: ConditionalExpr) -> Expression:
        pass

    def visit_backquote_expr(self, expr: BackquoteExpr) -> Expression:
        pass

    def visit_type_alias_expr(self, expr: TypeAliasExpr) -> Expression:
        pass

    def visit__promote_expr(self, expr: PromoteExpr) -> Expression:
        pass

    def visit_temp_node(self, expr: TempNode) -> Expression:
        pass
