"""Short code generation: base62 encoding of an atomic counter.

Design choice — counter vs random string:
  - Random strings (e.g. 6 random chars) need a "generate, check collision,
    retry" loop. Under load, retries get more likely as the namespace fills.
  - An atomic Redis INCR counter guarantees uniqueness with zero retries:
    every call returns a number nobody else got. Encoding that number in
    base62 keeps codes short: 62^4 = ~14.7M links fit in 4 characters,
    62^6 = ~56.8B in 6 characters.

Trade-off: codes are sequential-ish, so they're guessable (a/b/c...).
For a teaching project that's fine; real services that need unguessable
links use random tokens instead.

Why base62 (0-9, a-z, A-Z) and not base64?
  - base64 includes '+' '/' '=' which are special in URLs and would need
    percent-encoding — defeating the point of a *short* link.
"""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode_base62(number: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return ALPHABET[0]
    digits: list[str] = []
    while number:
        number, remainder = divmod(number, BASE)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))
