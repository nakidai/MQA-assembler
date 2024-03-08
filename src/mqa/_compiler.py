from .asm_types import *
from .mqis import *


class Compiler:
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
    def compile(cls, token_tree: list[list[Token] | Token], scope="main"):
        """
        Compiles the token_tree.
        :param token_tree: tree of tokens
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
            if token.token in InstructionSet.instruction_set:
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
        label_pointer: dict[int, int] = {id(x): idx for idx, x in enumerate(instruction_list) if isinstance(x, Label)}

        # label offset
        label_offset = 0

        # instruction pointer
        instruction_ptr = [-1]

        # instruction fetching function
        def next_instruction() -> list[Token | Argument] | Label | None:
            instruction_ptr[0] += 1
            if instruction_ptr[0] >= len(instruction_list):
                return None
            return instruction_list[instruction_ptr[0]]

        # go through all instructions and finalize the compilation
        while (instruction := next_instruction()) is not None:
            if isinstance(instruction, Label):
                instruction_list.pop(instruction_ptr[0])
                instruction_ptr[0] -= 1
                continue

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
