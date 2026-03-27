"""
Encrypt and decrypt values

"""

def encrypt(value: float, key: int) -> float:
    """Encrypt a single plaintext value."""
    return value + key


def decrypt(ciphertext: float, key: int) -> float:
    """Decrypt a single ciphertext value."""
    return ciphertext - key

def decrypt_sum(encrypted_total: float, key: int, n: int) -> float:
    """
    Decrypt a sum computed by the server over n ciphertexts.

    The key was added n times during encryption, so we subtract n*key.
    """
    return encrypted_total - n * key


def decrypt_mean(encrypted_total: float, key: int, n: int) -> float:
    """
    Decrypt a mean computed by the server over n ciphertexts.
    """
    return decrypt_sum(encrypted_total, key, n) / n