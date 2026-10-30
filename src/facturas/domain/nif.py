import re

_CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_DNI = re.compile(r"^\d{8}[A-Z]$")
_NIE = re.compile(r"^[XYZ]\d{7}[A-Z]$")


def _control_letter(number: int) -> str:
    return _CONTROL_LETTERS[number % 23]


def is_valid_nif(nif: str) -> bool:
    nif = nif.upper().replace(" ", "").replace("-", "")
    if _DNI.match(nif):
        return _control_letter(int(nif[:8])) == nif[8]
    if _NIE.match(nif):
        # X, Y, Z se sustituyen por 0, 1, 2 antes de calcular la letra
        number = int(str("XYZ".index(nif[0])) + nif[1:8])
        return _control_letter(number) == nif[8]
    return False
