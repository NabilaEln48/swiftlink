ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)

def encode_base62(number: int) -> str:
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return ALPHABET[0]
    digits: list[str] = []
    while number:
        number, remainder = divmod(number, BASE)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))
