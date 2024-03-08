from .asm_types import *
from .mqis import *


class Compiler(InstructionSet):
    @staticmethod
    def die(message: str, traceback: int, exception):
        raise exception(f"{message}\n  line {traceback}")

    @classmethod
    def process_scope_macros(cls, token_tree: list[list[Token] | Token]) -> dict[str, dict[int, Macro]]:
        """
        Returns a table of this scope's macros (with macro overloading). Modifies the token tree to delete
        already defined macros.
        Not recursive
        :param token_tree: tree of tokens
        :return: table of macros
        """

        # macros
        macros: dict[str, dict[int, Macro]] = {}

        # token pointer
        token_ptr = [-1]

        # token fetching function
        def next_token() -> list[Token] | Token | None:
            token_ptr[0] += 1
            if token_ptr[0] >= len(token_tree):
                return None
            return token_tree[token_ptr[0]]

        # go through each token and make macros
        while (token := next_token()) is not None:
            # skip sub-lists
            if isinstance(token, list):
                continue

            # macro
            if token.token == "macro":
                # load all macro things
                macro_name = next_token()
                macro_args = next_token()
                macro_body = next_token()

                # get rid of macro define
                token_ptr[0] -= 3
                token_tree.pop(token_ptr[0])
                token_tree.pop(token_ptr[0])
                token_tree.pop(token_ptr[0])
                token_tree.pop(token_ptr[0])

                # check if macro name is a token, and not a string
                if not isinstance(macro_name, Token):
                    raise SyntaxError("Expected a macro name")

                # check if macro args is a list of tokens, and not just a token
                if not isinstance(macro_args, list):
                    raise SyntaxError("Expected a '('")

                # check if macro body is a list of tokens
                if not isinstance(macro_body, list):
                    raise SyntaxError("Expected a '{'")

                # check if macro is already present
                if macro_name.token in macros:
                    # check if macros have same amount of arguments
                    if macros[macro_name.token].get(len(macro_args)) is not None:
                        print(f"WARN: You are overloading a macro '{macro_name}' with the same number of arguments")
                else:
                    macros[macro_name.token] = {}

                # add new macro
                macros[macro_name.token][len(macro_args)] = Macro(
                    name=macro_name.token,
                    args=macro_args,
                    body=cls.compile(macro_body, "macro")
                )

        return macros

    @classmethod
    def process_scope_labels(cls, token_tree: list[list[Token] | Token]) -> dict[str, Label]:
        """
        Returns a table of labels. Modifies the token tree to preserve unique labels
        Not recursive
        :param token_tree: 
        :return:
        """

        # table of labels
        labels: dict[str, Label] = {}

        # token pointer
        token_ptr = [-1]

        # token fetching function
        def next_token() -> list[Token] | Token | None:
            token_ptr[0] += 1
            if token_ptr[0] >= len(token_tree):
                return None
            return token_tree[token_ptr[0]]

        # go through tokens and find labels
        while (token := next_token()) is not None:
            # skip sub-lists
            if isinstance(token, list):
                continue

            # check if it's a label
            if token.token[-1] == ":":
                label_name = token.token[:-1]
                if label_name in labels:
                    print(f"WARN: redefining existing label '{label_name}'")

                label_class = Label(label_name, token.traceback)
                labels[label_name] = label_class

                # this may cause problems (?)
                token_tree[token_ptr[0]] = label_class

        # reset token pointer
        token_ptr[0] = -1

        # go through tokens and process label pointers
        while (token := next_token()) is not None:
            # skip sub-lists
            if isinstance(token, list):
                continue

            if token.token[0] == "$":
                if not token.token[1].isdigit():
                    if token.token[1:] not in labels:
                        raise NameError(f"Undefined label '{token}'")
                    token_tree[token_ptr[0]] = labels[token.token[1:]]

        return labels

    @classmethod
    def compile(cls, token_tree: list[list[Token] | Token], scope="main") -> list[list[Token | Argument]]:
        """
        Compiles the token_tree.
        :param token_tree: tree of tokens
        :param scope: scope which is being compiled. Default = main
        :return: list of instructions
        """

        # labels and macros
        labels = cls.process_scope_labels(token_tree)
        macros = cls.process_scope_macros(token_tree)

        # instruction list
        instruction_list = []

        # token pointer
        token_ptr = [-1]

        # token fetching function
        def next_token() -> list[Token] | Token | None:
            token_ptr[0] += 1
            if token_ptr[0] >= len(token_tree):
                return None
            return token_tree[token_ptr[0]]

        # go through tokens and compile the code
        while (token := next_token()) is not None:
            # labels
            if isinstance(token, Label):
                instruction_list.append(token)
                continue

            # if it's a newline
            if token.token == "\n":
                continue

            # instruction mnemonic token
            if token.token in cls.instruction_set:
                instruction_word = [token]
                while (instruction_token := next_token()).token != "\n":
                    instruction_word.append(instruction_token)
                instruction_list.append(instruction_word)

            # macros
            elif token.token in macros:
                macro_name = token.token
                macro_args = next_token()

                # check if macro_args is an instance of a list
                if not isinstance(macro_args, list):
                    raise SyntaxError(f"Expected a '('")

                # check if a macro with this name exists
                if macro_name not in macros:
                    raise NameError(f"Undefined macro '{macro_name}'")

                # check if macro with the same number of args is present
                if macros[macro_name].get(len(macro_args)) is None:
                    raise TypeError(f"Macro '{macro_name}' with this amount of arguments "
                                    f"({len(macro_args)}) doesn't exist")

                macro = macros[macro_name][len(macro_args)].__copy__()
                macro.put_args(*macro_args)
                instruction_list += macro.body

            # otherwise raise a name error
            else:
                raise NameError(f"Undefined instruction word '{token}'")

        # if we are processing the macro => we are done here
        if scope != "main":
            return instruction_list

        # otherwise => final step of compilation
        instruction_list: list[list[Token | Argument] | Label]

        # label pointers
        # label id -> label index in the instruction list
        label_pointer: dict[int, int] = {}

        # instruction pointer
        instruction_ptr = [-1]

        # instruction fetching function
        def next_instruction() -> list[Token | Argument] | Label | None:
            instruction_ptr[0] += 1
            if instruction_ptr[0] >= len(instruction_list):
                return None
            return instruction_list[instruction_ptr[0]]

        # go through all instructions, find & remove labels
        while (instruction := next_instruction()) is not None:
            if isinstance(instruction, Label):
                label_pointer[id(instruction)] = instruction_ptr[0]
                instruction_list.pop(instruction_ptr[0])
                instruction_ptr[0] -= 1

        # reset instruction pointer
        instruction_ptr[0] = -1

        # go through all instructions and finalize the compilation
        while (instruction := next_instruction()) is not None:
            for token_idx, token in enumerate(instruction):
                # skip mnemonics
                if token_idx == 0:
                    continue

                # if it's a label pointer
                if isinstance(token, Label):
                    instruction[token_idx] = Argument(label_pointer[id(token)], AsmTypes.INTEGER)
                    continue

                # some kind of pointer
                if token.token[0] == "$":
                    if token.token[1].isdigit():
                        instruction[token_idx] = Argument(int(token.token[1:]), AsmTypes.POINTER)
                else:
                    instruction[token_idx] = Argument(int(token.token), AsmTypes.INTEGER)

        return instruction_list

    @classmethod
    def get_bytecode(cls, instruction_list: list[list[Token | Argument]]) -> bytes:
        """
        Translates the instruction list into bytes
        :param instruction_list: list of instructions
        :return: bytes
        """

        # list of instruction bytes
        byte_code: bytes = bytes()

        for instruction in instruction_list:
            # decode the instruction
            opcode = cls.instruction_set[instruction[0].token]

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
            byte_code += bytes([value_high, value_low])

        return byte_code
