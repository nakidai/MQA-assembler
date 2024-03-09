from ._asm_types import Token


class Tokenizer:
    """
    Tokenizer class, which specializes on working with mainly the individual characters of the source code.
    """

    # opposite brackets
    opposite_brackets = {"[": "]", "{": "}", "(": ")"}

    @staticmethod
    def tokenize(code: str):
        """
        Splits the input code string into a list of tokens, which then can be used to construct a token tree
        :param code: code string
        :return: list of tokens
        """

        # character pointer
        char_ptr = [-1]

        # next char function
        def next_char() -> str | None:
            char_ptr[0] += 1
            if char_ptr[0] >= len(code):
                return None
            return code[char_ptr[0]]

        # token list (not a tree yet)
        token_list: list[Token] = []

        # on which line of the code the pointer is
        line_number = 0

        # if we are inside a comment
        is_commented = False

        # token string (the accumulative string)
        token_str = ""

        # fetch each character and do some operations
        while (char := next_char()) is not None:
            # if we are inside a comment
            if char == ";":
                is_commented = True
                continue

            # if we hit a newline
            if char == "\n":
                line_number += 1
                is_commented = False
                if token_str != "":
                    token_list.append(Token(token_str, line_number))
                    token_str = ""
                token_list.append(Token("\n", line_number))
                continue

            # skip this part of the code if it's commented
            if is_commented:
                continue

            # if a character is a space or a comma
            if char == " " or char == ",":
                if token_str != "":
                    token_list.append(Token(token_str, line_number))
                    token_str = ""

            # if a character is a bracket
            elif char in "[]{}()":
                if token_str != "":
                    token_list.append(Token(token_str, line_number))
                    token_str = ""
                token_list.append(Token(char, line_number))

            # otherwise just add it to token string
            else:
                token_str += char

        if token_str != "":
            token_list.append(Token(token_str, line_number))
            token_list.append(Token("\n", line_number))

        # delete the repeating newlines
        pointer = 0
        while pointer < (len(token_list) - 1):
            if token_list[pointer] == token_list[pointer + 1] == "\n":
                token_list.pop(pointer)
                pointer -= 1
            pointer += 1

        return token_list

    @staticmethod
    def build_token_tree(token_list: list[Token]):
        """
        Builds a tree of tokens.
        This function is called recursively.
        :param token_list: list of tokens
        :return: hierarchical token structure
        """

        # token tree
        token_tree: list[list[Token] | Token] = []

        # token pointer
        token_ptr = [-1]

        # token fetching function
        def next_token() -> Token | None:
            token_ptr[0] += 1
            if token_ptr[0] >= len(token_list):
                return None
            return token_list[token_ptr[0]]

        # make a tree
        while (token := next_token()) is not None:
            # if the token is not a bracket => append & continue
            if token.token not in "[]{}()":
                token_tree.append(token)
                continue

            # if it's an opening bracket
            if token.token in "[{(":
                # local scope
                scope = []

                # bracket types
                bracket = token.token
                bracket_opposite = Tokenizer.opposite_brackets[bracket]

                # how many brackets are nested in each other
                nesting = 0

                # go through each scope token and do a recursive call when needed
                while (scope_token := next_token()) is not None:
                    if scope_token.token == bracket_opposite and nesting == 0:
                        token_tree.append(Tokenizer.build_token_tree(scope))
                        break
                    elif scope_token.token == bracket:
                        nesting += 1
                    elif scope_token.token == bracket_opposite:
                        nesting -= 1
                    scope.append(scope_token)

        return token_tree
