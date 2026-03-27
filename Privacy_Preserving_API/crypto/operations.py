"""

Only encrypted values here

"""

from typing import List


def encrypted_sum(ciphertexts: List[float]) -> float:
    """
    Sum a list of ciphertexts.

    Result = (x1 + x2 + ... + xn) + n * key
    The client will correct for the n*key offset during decryption
    """
    return sum(ciphertexts)


def encrypted_mean(ciphertexts: List[float]) -> tuple[float, int]:
    """
    Compute the mean of encrypted values.

    Returns the raw encrypted sum AND the count, because the client
    needs both to decrypt correctly:
        true_mean = (encrypted_sum - n * key) / n
    """
    n = len(ciphertexts)
    return encrypted_sum(ciphertexts), n