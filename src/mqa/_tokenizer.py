from ._asm_types import Token
from typing import Any


# class Tokenizer:
#     def __init__(self, code: str):
#         """
#         The main tokenizer class.
#         It spits the code into tokens
#         """
#
#         # code string and token tree
#         self._code: str = code
#         self._token_tree: list[Token | Any] | None = None
#
#         # tokenize the code
#         self._tokenize()
#
#     @property
#     def token_tree(self) -> list[Token | Any]:
#         return self._token_tree
#
#     def _tokenize(self):
#         """
#         Spaghetti code that assembles the code!
#         I know it's stupid, but I don't know how to make it better
#         :return: none
#         """
#
#         # separate the code into tokens
#         self._separate_tokens()
#
#         # delete comments
#         self._delete_comments()
#
#         # delete duplicate newlines
#         self._remove_newlines()
#
#         # create a token tree
#         self._token_tree = self._build_token_tree(self._token_tree)
#
#     def _separate_tokens(self):
#         """
#         Separates the tokens
#         :return: none
#         """
#
#         # create token string
#         token = ""
#
#         # initialize token list
#         self._token_tree = []
#
#         # initialize character pointer to 0
#         char_ptr = 0
#         code_line = 1
#         while char_ptr < len(self._code):
#             # get next character
#             char = self._code[char_ptr]
#             char_ptr += 1
#
#             # code line
#             if char == "\n":
#                 code_line += 1
#
#             # spaces between things
#             if char == " " and token != "":
#                 self._token_tree.append(Token(token, code_line))
#                 token = ""
#
#             # new lines
#             elif char in "\n," and token != "":
#                 self._token_tree.append(Token(token, code_line))
#                 self._token_tree.append(Token(char, code_line))
#                 token = ""
#
#             # brackets
#             elif char in "({[]})":
#                 if token != "":
#                     self._token_tree.append(Token(token, code_line))
#                     token = ""
#                 self._token_tree.append(Token(char, code_line))
#
#             # odd case with brackets
#             elif char == "\n" and len(self._token_tree) > 0:
#                 if self._token_tree[-1].token in "({[]})":
#                     self._token_tree.append(Token(char, code_line))
#
#             # anything else
#             elif char != " " and char != "\n":
#                 token += char
#
#         # if there is still a token at the end of the file
#         if token:
#             self._token_tree.append(Token(token, code_line))
#             self._token_tree.append(Token("\n", code_line))
#
#     def _delete_comments(self):
#         """
#         Removes the comments to not clutter the token list
#         :return: none
#         """
#
#         # create new token list
#         new_token_list = []
#         commented = False
#         for token in self._token_tree:
#             # deletus everything after the ';'
#             if token == ";":
#                 commented = True
#                 continue
#
#             # if the newline is found, it's not a comment anymore
#             elif token == "\n":
#                 commented = False
#
#             # if the thing is not commented, then put it on the new token list
#             if not commented:
#                 new_token_list.append(token)
#
#         # yes
#         self._token_tree = new_token_list
#
#     def _build_token_tree(self, token_list: list[Token]):
#         """
#         Builds the token tree
#         :param token_list: yes
#         :return: none
#         """
#
#         # the token tree
#         tree = []
#
#         # current token index
#         index = 0
#         while index < len(token_list):
#             # fetch current token
#             token = token_list[index]
#             index += 1
#
#             # when we find an opening bracket, create a new scope
#             if str(token) in "({[":
#                 scope = []
#                 nesting = 0
#                 prev_index = token_list[index].traceback
#                 while index < len(token_list):
#                     # fetch inner scope token
#                     token = token_list[index]
#                     index += 1
#
#                     # if another opening bracket of same type is found => increment the nesting variable
#                     # break out of the loop only when the nesting is 0 and the closing bracket is found
#                     if str(token) in "]})" and nesting == 0:
#                         tree.append(self._build_token_tree(scope))
#                         break
#                     elif str(token) in "]})":
#                         nesting -= 1
#                     elif str(token) in "({[":
#                         nesting += 1
#
#                     # append tokens to the local scope
#                     scope.append(token)
#
#                 # if the end of the code was reached => die.
#                 else:
#                     raise SyntaxError(f"No closing bracket was found; line {prev_index}")
#             else:
#                 # append tokens to the global scope
#                 tree.append(token)
#         # return the token tree (or a local scope)
#         return tree
#
#     def _remove_newlines(self):
#         """
#         Removes duplicate newlines
#         :return: none
#         """
#
#         # set index to 0
#         index = 0
#         while index < len(self._token_tree)-1:
#             # if there are 2 newlines in a row, delete the first one
#             if self._token_tree[index] == "\n" and self._token_tree[index + 1] == "\n":
#                 self._token_tree.pop(index)
#
#             # otherwise go to the next index
#             else:
#                 index += 1


class Tokenizer:
    @staticmethod
    def tokenize(code: str):
        # character pointer
        dummy = [-1]

        # next char function
        def next_char(offset=1) -> str | None:
            dummy[0] += offset
            if dummy[0] >= len(code):
                return None
            return code[dummy[0]]

        # token list (not a tree yet)
        token_list: list[Token] = []

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
                is_commented = False
                if token_str != "":
                    token_list.append(Token(token_str, dummy[0]))
                    token_str = ""
                token_list.append(Token("\n", dummy[0]))
                continue

            # skip this part of the code if it's commented
            if is_commented:
                continue

            # if a character is a space or a comma
            if char == " " or char == ",":
                if token_str != "":
                    token_list.append(Token(token_str, dummy[0]))
                    token_str = ""

            # if a character is a bracket
            elif char in "[]{}()":
                if token_str != "":
                    token_list.append(Token(token_str, dummy[0]))
                    token_str = ""
                token_list.append(Token(char, dummy[0]))

            # otherwise just add it to token string
            else:
                token_str += char

        # delete the repeating newlines
        pointer = 0
        while pointer < (len(token_list) - 1):
            if token_list[pointer] == token_list[pointer + 1] == "\n":
                token_list.pop(pointer)
                pointer -= 1
            pointer += 1

        return token_list
