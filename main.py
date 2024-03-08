import os
import argparse
from src import Compiler, Tokenizer


parser = argparse.ArgumentParser(description="Compiles Mini Quantum CPU source files.")
parser.add_argument("input", type=str, help="source file")
parser.add_argument("-o", "--output", type=str, help="output file")
parser.add_argument("--json", help="creates a blueprint for Scrap Mechanic", action="store_true")
parser.add_argument("--no-byte", help="outputs the assembly code", action="store_true")
args = parser.parse_args()


def code_compile(code: str):
    """
    Compiles the given code.
    :param code: code string
    :return: instruction list
    """

    token_list = Tokenizer.tokenize(code)
    token_tree = Tokenizer.build_token_tree(token_list)
    instruction_list = Compiler.compile(token_tree)

    return instruction_list


def die(message=None):
    """
    Dies with some kind of message.
    :param message: message with which the program will do the die thing
    """

    if message is not None:
        print(f"ERROR: {message}")
    exit(1)


def main():
    # file reading
    if not os.path.isfile(args.input):
        die(f"file '{args.input}' not found")
    with open(args.input, "r", encoding="utf8") as file:
        code = file.read()

    # compilation
    instruction_list = code_compile(code)

    # file creation
    output_filename = args.output
    if output_filename is None:
        # 'compiled_{file}'
        output_filename = "compiled_" + os.path.splitext(os.path.basename(args.input))[0]

        # if '--no-byte' is True, append '.mqas' to the end of the filename
        if args.no_byte:
            output_filename += ".mqas"

        # else, append '.mqa' to the end of the filename
        else:
            output_filename += ".mqa"

    # bytecode file output (for the emulator)
    if args.no_byte:
        # write instructions to a file
        with open(output_filename, "w", encoding="utf8") as file:
            for instruction in instruction_list:
                file.write(" ".join([x.__str__() for x in instruction]) + "\n")
    else:
        # write bytes to a file
        with open(output_filename, "wb") as file:
            file.write(Compiler.get_bytecode(instruction_list))


if __name__ == '__main__':
    main()
