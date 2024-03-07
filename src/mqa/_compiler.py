from ._tokenizer import Tokenizer
from ._asm_types import *
from ._mqis import *


class Compiler(InstructionSet):
    def __init__(self):
        """
        Main compiler class, which does all the compilation steps.
        """

        self.macros: dict[str, list[Macro]] = {}

        self.traceback: int = 0
        self.traceback_name: str = ""

    def get_bytecode(self, instruction_list: list[list[Token | Argument]]):
        """
        Will convert the list of instructions to bytecode
        :param instruction_list: list of instruction words
        :return: bytes
        """

        # list of instruction bytes
        new_instruction_list: bytes = bytes()

        for instruction in instruction_list:
            # decode the instruction
            opcode = self.instruction_set[instruction[0].token]

            # if the instruction has any arguments (ex. LRA 10, argument 10)
            # decode data and memory_flag
            if len(instruction) > 1:
                data = instruction[1].value
                memory_flag = 1 if instruction[1].type is AsmTypes.POINTER else 0

            # else, data and memory_flag are 0
            else:
                data = 0
                memory_flag = 0

            # instruction consists of 3 parts
            # memory_flag   - 1 bit
            # data          - 8 bits
            # opcode        - 7 bits
            # ==========================
            # total         - 16 bits

            # make instruction one 16 bit value
            value = (memory_flag << 15) + (data << 7) + opcode

            # bytes are 8 bits, so, split the value into 2 bytes
            value_high = (value & 0b1111_1111_0000_0000) >> 8
            value_low = value & 0b0000_0000_1111_1111

            # append 2 bytes to the list
            new_instruction_list += bytes([value_high, value_low])

        return new_instruction_list

    def compile(self, code: str) -> list[list[Token | Argument]]:
        """
        Wrapper for the 'self._compile' method
        :param code: code that needs compilation
        :return:
        """

        # make a token tree
        token_tree = Tokenizer.build_token_tree(
            Tokenizer.tokenize(code)
        )

        try:
            compiled = self._compile(token_tree)
        except Exception as exc:
            print(f"Compiler exited due to following error:\n"
                  f"{type(exc).__name__}: {exc}; line {self.traceback} in '{self.traceback_name}'")
            return None
        return compiled

    def _is_macro_unique(self, name: Token | str, argn: int) -> bool:
        """
        :return: true if macro is unique, false if macro is not unique
        """

        if isinstance(name, Token):
            name = name.token
        if name in self.macros:
            for macro in self.macros[name]:
                if argn == macro.argn:
                    return False
        return True

    def _get_macro(self, name: Token | str, argn: int, copy=True) -> Macro:
        """
        Returns macro body with the given name and the amount of arguments
        :param name: macro name
        :param argn: number of arguments the macro has
        :param copy: if the macro is a copy. Default=True
        :return: macro body
        """

        if isinstance(name, Token):
            name = name.token

        if name in self.macros:
            for macro in self.macros[name]:
                if argn == macro.argn:
                    if copy:
                        return macro.__copy__()
                    else:
                        return macro

    def _raise_exception(self, exception: BaseException, traceback: int, name: str):
        """
        Raises an exception
        Sets the traceback and the name
        :param exception: exception which will be raised
        :param traceback: line traceback
        :param name: scope traceback
        :return:
        """

        self.traceback = traceback
        self.traceback_name = name
        raise exception

    def _append_macro(self, name: Token | str, args: list[Token], body: list[list[Token] | Label]) -> None:
        """
        Appends a new macro, if and only if it is a unique one
        """

        if isinstance(name, Token):
            name = name.token
        if name in self.macros:
            for macro in self.macros[name]:
                if len(args) == macro.argn:
                    macro.args = args
                    macro.body = body
                    return
        else:
            self.macros[name] = []
        self.macros[name].append(
            Macro(
                name=name,
                args=args,
                body=body
            )
        )

    @staticmethod
    def _make_labels(instruction_list: list[list[Token] | Label]):
        """
        Modifies the list of instruction words
        Creates labels, and moves their references to the correct places
        :param instruction_list: list of instructions
        """

        labels: dict[str, Label] = dict()

        # instruction pointer
        dummy = [-1]

        # function that will retrieve the next instruction for the list of instructions
        def next_instruction() -> list[Token] | Label | None:
            dummy[0] += 1
            if dummy[0] >= len(instruction_list):
                return None
            return instruction_list[dummy[0]]

        # create labels
        while (instruction := next_instruction()) is not None:
            # skip other instruction words
            if not isinstance(instruction, Label):
                continue

            # labels
            if instruction.token not in labels:
                # add the Label itself (same label, not a copy of it)
                labels[instruction.token] = instruction

        # reset the instruction pointer
        dummy[0] = -1

        # put the labels in correct places
        while (instruction := next_instruction()) is not None:
            # skip labels
            if isinstance(instruction, Label):
                continue

            # iterate through instruction tokens and replace each '$label' with reference to the label
            for token_idx, token in enumerate(instruction):
                if token.token[1:] in labels:
                    instruction[token_idx] = labels[token.token[1:]]

    def _compile_instructions(self, instruction_list: list[list[Token] | Label]) -> list[list[Token | Argument]]:
        """
        Compile method, but on instruction words rather than the token tree
        :param instruction_list: list of instructions
        :return: list of instructions, but compiled
        """

        # new instruction list
        new_instruction_list: list[list[Token] | Label] = []

        # labels
        labels: dict[int, int] = dict()

        # instruction pointer
        dummy = [-1]

        # function that will retrieve the next instruction for the list of instructions
        def next_instruction() -> list[Token] | Label | None:
            dummy[0] += 1
            if dummy[0] >= len(instruction_list):
                return None
            return instruction_list[dummy[0]]

        # offset due to labels being removed
        label_offset = 0

        # go through all the instructions, and find all labels
        while (instruction := next_instruction()) is not None:
            # skip all non label instructions
            if not isinstance(instruction, Label):
                new_instruction_list.append(instruction)
                continue

            # labels
            labels[id(instruction)] = dummy[0] - label_offset
            label_offset += 1

        # move the new instruction list to old one
        instruction_list: list[list[Token | Argument]] = new_instruction_list

        # reset the instruction pointer
        dummy[0] = -1

        # replace references with addresses of where to jump
        while (instruction := next_instruction()) is not None:
            # loop through tokens in the instruction word
            # there should be no Labels or Macros, so no additional checks needed
            for token_idx, token in enumerate(instruction):
                # we check if token is in labels (if it IS the same exact thing)
                if id(token) in labels:
                    instruction[token_idx] = Argument(labels[id(token)], AsmTypes.INTEGER)
                    continue

                # skip mnemonics
                if token_idx == 0:
                    continue

                # replace arguments
                try:
                    if token.token[0] == "$":
                        instruction[token_idx] = Argument(int(token.token[1:]), AsmTypes.POINTER)
                    else:
                        instruction[token_idx] = Argument(int(token.token), AsmTypes.INTEGER)
                except ValueError as exc:
                    self._raise_exception(
                        exc,
                        traceback=token.traceback,
                        name="main"
                    )

        return instruction_list

    def _compile(self, token_tree: list[Token | list], _scope="main") -> list[list[Token] | Label | Argument]:
        """
        Compile method
        It's called RECURSIVELY (I keep forgetting about that part)
        This method is called on all scopes (main, or the macro scopes)
        :param token_tree: tree of tokens
        :param _scope: if it's the main scope, or a macro scope (microscope hehe)
        :return: compiled list of instructions
        """

        instruction_list: list[list[Token] | Label] = []

        # braindead coding :sunglasses:
        dummy = [-1]

        def next_token() -> Token | list | None:
            dummy[0] += 1
            if dummy[0] >= len(token_tree):
                return None
            return token_tree[dummy[0]]

        # go through tokens to define all macros first (to not cause any errors)
        while (token := next_token()) is not None:
            if isinstance(token, list):
                continue

            # macros
            if token == "macro":
                macro_name = next_token()
                if not isinstance(macro_name, Token):
                    self._raise_exception(
                        SyntaxError(f"incorrect macro name '{macro_name}'"),
                        traceback=token.traceback,
                        name=_scope)

                macro_args = next_token()
                if not isinstance(macro_args, list):
                    self._raise_exception(
                        SyntaxError("expected an argument list"),
                        traceback=token.traceback,
                        name=_scope)
                macro_args = [x for x in macro_args if x != ","]

                macro_body = next_token()
                if not isinstance(macro_body, list):
                    self._raise_exception(
                        SyntaxError("expected a '{'"),
                        traceback=token.traceback,
                        name=_scope)

                macro_compiler = Compiler()
                macro_body = macro_compiler._compile(macro_body, macro_name.token)
                self._append_macro(macro_name, macro_args, macro_body)

                for name, macro in macro_compiler.macros.items():
                    for overload_macro in macro:
                        if not self._is_macro_unique(name, overload_macro.argn):
                            self._raise_exception(
                                Exception("cyclic macro"),
                                traceback=token.traceback,
                                name=_scope)
                        self._append_macro(name, overload_macro.args, overload_macro.body)

        # reset the token pointer
        dummy[0] = -1

        # make macros, labels and instruction words
        while (token := next_token()) is not None:
            if isinstance(token, list):
                continue

            # skip macro definitions
            if token == "macro":
                next_token()
                next_token()
                next_token()
                continue

            # instructions
            if token.token in self.instruction_set:
                instruction_word = [token]
                while (tok := next_token()) != "\n":
                    instruction_word.append(tok)
                instruction_list.append(instruction_word)

            # macros
            elif token.token in self.macros:
                # macro name
                macro_name = token.token

                # list of arguments to the macro
                macro_args = next_token()
                if not isinstance(macro_args, list):
                    raise SyntaxError()
                macro_args = [x for x in macro_args if x != ","]

                # get the macro and append it to the list of instructions
                macro = self._get_macro(macro_name, len(macro_args))

                # put arguments into the macro
                macro.put_args(*macro_args)

                # put label references
                self._make_labels(macro.body)

                # add macro body to the list of instructions
                instruction_list += macro.body

                # note: this code kind of stinks :(

            # labels
            elif token.token[-1] == ":":
                instruction_list.append(
                    Label(token.token[:-1], token.traceback)
                )

        # if we are in the main scope
        if _scope == "main":
            self._make_labels(instruction_list)
            return self._compile_instructions(instruction_list)

        # if we are in the macro scope
        else:
            return instruction_list
