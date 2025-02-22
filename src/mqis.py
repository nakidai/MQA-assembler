class InstructionSet:
    """
    A set of compiler instructions;
    This file was generated.
    """

    instruction_set: dict[str, int] = {
        'NOP': 0,
        'LRA': 1,
        'SRA': 2,
        'CALL': 3,
        'RET': 4,
        'JMP': 5,
        'JMPP': 6,
        'JMPZ': 7,
        'JMPN': 8,
        'JMPC': 9,
        'CCF': 10,
        'LRP': 11,
        'CCP': 12,
        'CRP': 13,
        'AND': 16,
        'OR': 17,
        'XOR': 18,
        'NOT': 19,
        'LSC': 20,
        'RSC': 21,
        'CMP': 22,
        'CMPU': 23,
        'ADC': 32,
        'SBC': 33,
        'INC': 34,
        'DEC': 35,
        'ABS': 36,
        'MUL': 37,
        'DIV': 38,
        'MOD': 39,
        'TSE': 40,
        'TCE': 41,
        'ADD': 42,
        'SUB': 43,
        'RPL': 44,
        'UI': 48,
        'UO': 49,
        'UOC': 50,
        'UOCR': 51,
        'PRW': 112,
        'PRR': 113,
        'INT': 126,
        'HALT': 127,
    }
