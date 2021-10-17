from typing import NamedTuple
from nodes import Binding, VarBinding
from contextlib import contextmanager

class _ContextElem(NamedTuple):
    name: str
    binding: Binding

    def __str__(self) -> str:
        if isinstance(self.binding, VarBinding):
            return f"{self.name}: {self.binding.ty}"
        else:
            return self.name


class Context:
    def __init__(self) -> None:
        self.data: list[_ContextElem] = []

    def clone(self):
        ctx = Context()
        ctx.data = self.data.copy()
        return ctx

    def add_binding(self, name: str, binding: Binding):
        self.data.append(_ContextElem(name, binding))

    def find_binding(self, name: str):
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
        raise ValueError(f"Wrong binding for var {self.get_name(idx)} at {idx}")

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

    @contextmanager
    def scoped_add(self, name: str, binding: Binding):
        """Add binding for the scope of the `with` block"""
        self.add_binding(name, binding)
        yield
        self.pop_binding()
