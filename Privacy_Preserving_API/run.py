"""
Generates fake HR data and stores it encrypted.

Run this once to populate the database before launching the dashboard.
The raw values are printed locally (client side) but never stored.
"""

import hashlib
import os
from database import init_db, get_session, Employee
from crypto.keygen import generate_key
from crypto.encryption import encrypt


# Department encoding
DEPARTMENT_MAP = {
    "HR":      1,
    "IT":      2,
    "Finance": 3,
    "Legal":   4,
}


# Fake employee data
FAKE_EMPLOYEES = [
    {"name": "Alice Martin",  "department": "IT",      "age": 29, "salary": 52000},
    {"name": "Bob Dupont",    "department": "Finance",  "age": 45, "salary": 71000},
    {"name": "Clara Schmidt", "department": "HR",       "age": 33, "salary": 48000},
    {"name": "David Lemoine", "department": "Legal",    "age": 38, "salary": 63000},
    {"name": "Eva Rossi",     "department": "IT",       "age": 26, "salary": 49000},
    {"name": "Frank Bernard", "department": "Finance",  "age": 51, "salary": 85000},
    {"name": "Grace Leroy",   "department": "HR",       "age": 41, "salary": 51000},
    {"name": "Hugo Petit",    "department": "IT",       "age": 30, "salary": 55000},
]


def hash_name(name: str) -> str:
    """Hash a name using SHA-256 — one-way, not decryptable."""
    return hashlib.sha256(name.encode()).hexdigest()[:16]


def save_key(key: int):
    """Persist the secret key to a local .env file. Never commit this."""
    with open(".env", "w") as f:
        f.write(f"SECRET_KEY={key}\n")
    print("Key saved to .env (never commit this file)")


def seed(key: int):
    """Encrypt and insert all fake employees into the database."""
    init_db()
    session = get_session()

    print(f"\n Client key (never sent to server): {key}\n")
    print(f"{'Name':<20} {'Dept':<10} {'Age':>5} {'Salary':>10}")

    for emp in FAKE_EMPLOYEES:
        print(f"{emp['name']:<20} {emp['department']:<10} {emp['age']:>5} {emp['salary']:>10}")

        record = Employee(
            name             = emp["name"],   
            name_hash        = hash_name(emp["name"]),
            department_code  = DEPARTMENT_MAP[emp["department"]],
            encrypted_age    = encrypt(emp["age"], key),
            encrypted_salary = encrypt(emp["salary"], key),
        )
        session.add(record)

    session.commit()
    session.close()

    print("\n Database seeded with encrypted records.")
    print(" Launch the dashboard: streamlit run app.py")


if __name__ == "__main__":
    key = generate_key()
    save_key(key)
    seed(key)