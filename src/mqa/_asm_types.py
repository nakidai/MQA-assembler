from enum import Enum
from typing import Any


class AsmTypes(Enum):
    """
    Argument (class) types
    """

    INTEGER = 1
    POINTER = 2


class Token:
    def __init__(self, token: str, code_line: int):
        """
        Token class for the proper traceback.
        Acts mostly as just a string
        :param token: just a string
        :param code_line: line at which the token was defined
        """

        self._token: str = token
        self._code_line: int = code_line

    @property
    def token(self) -> str:
        return self._token

    @property
    def traceback(self) -> int:
        return self._code_line

    def __contains__(self, item):
        return item in self._token

    def __eq__(self, other):
        return self._token == other

    def __len__(self):
        return len(self._token)

    def __repr__(self):
        return self._token.__repr__()

    def __str__(self):
        return self._token


class Label(Token):
    """
    Acts exactly the same way the token does,
    Just a little bit special
    """


class Macro:
    def __init__(self, name: str, args: list[Token], body: list):
        """
        Macro token, used in precompilation
        :param name: name of the macro
        :param args: arguments of the macro
        :param body: instructions composing the macro
        """

        self.name: str = name
        self.args: list[Token] = [x for x in args if x != ","]
        self.argn: int = len(self.args)
        self.body: list[list[Token] | Label | Macro] = body

    def put_args(self, *args: Token):
        """
        Puts the arguments in the corresponding places
        :param args: arguments to the macro
        :returns: self
        :raises TypeError: when the amount of arguments does not match
        """

        if len(args) != self.argn:
            raise TypeError()

        for instruction in self.body:
            if isinstance(instruction, (Label, Macro)):
                continue
            for token_idx, tok in enumerate(instruction):
                # the first token must be an instruction word
                if token_idx == 0:
                    continue
                for arg_idx, arg in enumerate(self.args):
                    if tok == arg:
                        instruction[token_idx] = args[arg_idx]
        self.args = args
        return self

    def __copy__(self):
        return Macro(self.name, self.args, self.body)

    def __repr__(self):
        return f"{{{self.name}({self.args})}}"


class Argument:
    def __init__(self, value: Any, type_: AsmTypes):
        """
        Contains a value (anything), and type
        :param value: argument value
        :param type_: argument type
        """

        self.value = value
        self.type = type_

    def __repr__(self):
        if self.type is AsmTypes.INTEGER:
            return f"{self.value}"
        elif self.type is AsmTypes.POINTER:
            return f"${self.value}"
