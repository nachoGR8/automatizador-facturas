import re

_CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_DNI = re.compile(r"^\d{8}[A-Z]$")
_NIE = re.compile(r"^[XYZ]\d{7}[A-Z]$")
_CIF = re.compile(r"^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$")


def _control_letter(number: int) -> str:
    return _CONTROL_LETTERS[number % 23]


def _double_digit_sum(digit: int) -> int:
    doubled = digit * 2
    return doubled // 10 + doubled % 10


def _cif_control_is_valid(cif: str) -> bool:
    digits = [int(char) for char in cif[1:8]]
    odd_positions = sum(_double_digit_sum(digit) for digit in digits[0::2])
    even_positions = sum(digits[1::2])
    control_digit = (10 - (odd_positions + even_positions) % 10) % 10
    # El control puede ser el dígito o su letra equivalente (J, A, B, ... I)
    return cif[8] in (str(control_digit), "JABCDEFGHI"[control_digit])


def is_valid_nif(nif: str) -> bool:
    nif = nif.upper().replace(" ", "").replace("-", "")
    if _DNI.match(nif):
        return _control_letter(int(nif[:8])) == nif[8]
    if _NIE.match(nif):
        # X, Y, Z se sustituyen por 0, 1, 2 antes de calcular la letra
        number = int(str("XYZ".index(nif[0])) + nif[1:8])
        return _control_letter(number) == nif[8]
    if _CIF.match(nif):
        return _cif_control_is_valid(nif)
    return False
