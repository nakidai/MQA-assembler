import os
import argparse
from src import Compiler


parser = argparse.ArgumentParser(description="Compiles Mini Quantum CPU source files.")
parser.add_argument("input", type=str, help="source file")
parser.add_argument("-o", "--output", type=str, help="output file")
parser.add_argument("--json", help="creates a blueprint for Scrap Mechanic", action="store_true")
parser.add_argument("--byte", help="outputs the bytecode, executable for mqe", action="store_true")
args = parser.parse_args()


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
    compiler = Compiler()
    instruction_list = compiler.compile(code)
    if instruction_list is None:
        die()

    # file creation
    output_filename = args.output
    if output_filename is None:
        # 'compiled_{file}'
        output_filename = "compiled_" + os.path.splitext(os.path.basename(args.input))[0]

        # if '--byte' is True, append '.mqa' to the end of the filename
        if args.byte:
            output_filename += ".mqa"

        # else, append '.mqas' to the end of the filename
        else:
            output_filename += ".mqas"

    # bytecode file output (for the emulator)
    if args.byte:
        # write bytes to a file
        with open(output_filename, "wb") as file:
            file.write(compiler.get_bytecode(instruction_list))
    else:
        # write instructions to a file
        with open(output_filename, "w", encoding="utf8") as file:
            for instruction in instruction_list:
                file.write(" ".join([x.__str__() for x in instruction]) + "\n")


if __name__ == '__main__':
    main()
