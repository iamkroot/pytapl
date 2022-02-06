from typing import Generator, NamedTuple
from lark.lexer import Token
from nodes import Binding, SchemeBinding, TypeSubst, VarBinding, IdTy


class _ContextElem(NamedTuple):
    name: Token
    binding: Binding

    def __str__(self) -> str:
        if isinstance(self.binding, VarBinding):
            return f"{self.name}: {self.binding.ty}"
        elif isinstance(self.binding, SchemeBinding):
            return f"{self.name}: {self.binding}"
        else:
            return self.name


class Context:
    def __init__(self, vargen: Generator[IdTy, None, None]) -> None:
        self.data: list[_ContextElem] = []
        self.vargen = vargen

    def clone(self):
        ctx = Context(self.vargen)
        ctx.data = self.data.copy()
        return ctx

    def add_binding(self, name, binding: Binding):
        self.data.append(_ContextElem(name, binding))

    def find_binding(self, name):
        for i, binding in enumerate(reversed(self.data)):
            if binding.name == name:
                return i, binding
        raise ValueError

    def get_binding(self, idx):
        return self.data[~idx]

    def get_name(self, idx):
        return self.get_binding(idx).name

    def get_type(self, idx):
        match self.get_binding(idx).binding:
            case VarBinding(ty):
                return ty
            case SchemeBinding(ty_vars, body_ty):
                # instantiate
                from run import apply_substs_to_ty
                substs = map(lambda var: TypeSubst(var, next(self.vargen)), ty_vars)
                return apply_substs_to_ty(body_ty, list(substs))

        raise ValueError(f"Wrong binding for var {self.get_name(idx)} at {idx}")

    def has_typevar(self, ty: IdTy):
        return any(elem.binding.contains_ty(ty) for elem in self.data)

    def pop_binding(self):
        self.data.pop()

    @property
    def top(self):
        """Return most recent binding"""
        return self.data[-1]

    def __len__(self):
        return len(self.data)

    def __str__(self) -> str:
        return "Ctx[" + ", ".join(map(str, self.data)) + "]"
