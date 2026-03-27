"""
keygen.py — Secret key generation for the encryption scheme.

The key is a large random integer known only to the client.
The server never sees it — that's the whole point.
"""

import secrets

# Larger keys are harder to brute-force, for our test we will go with 10^6 
KEY_SPACE = 10**6


def generate_key() -> int:
    """
    Generate a random secret integer key.

    Returns a random integer in [1, KEY_SPACE).
    We use `secrets` instead of `random` because counterintuitively not so random
    """
    return secrets.randbelow(KEY_SPACE) + 1  # +1 to avoid key = 0