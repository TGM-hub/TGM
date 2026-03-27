"""
app.py -- Streamlit dashboard for exploring encrypted HR data.

The recruiter can query the encrypted database directly and request
decrypted analytics via the API. Raw values are never stored.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import sqlalchemy
from dotenv import load_dotenv
from crypto.encryption import decrypt_mean, decrypt_sum

load_dotenv()
KEY = int(os.getenv("SECRET_KEY"))
DB_PATH = "hr_encrypted.db"


def run_query(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


def get_decrypted_df() -> pd.DataFrame:
    df = run_query("SELECT * FROM employees")
    df["encrypted_age"]    = df["encrypted_age"].apply(lambda x: int(x - KEY))
    df["encrypted_salary"] = df["encrypted_salary"].apply(lambda x: int(x - KEY))
    df = df.rename(columns={
        "encrypted_age":    "age",
        "encrypted_salary": "salary",
    })
    df = df.drop(columns=["name_hash"])
    return df


# Page config
st.set_page_config(page_title="Privacy-Preserving HR Analytics", layout="wide")
st.title("Privacy-Preserving HR Analytics")
st.caption("Encrypted data is stored in the database. Only the client can decrypt results.")

# Section 1 -- Raw encrypted table
st.header("Encrypted database")
st.caption("This is what the server sees. Salaries and ages are unreadable without the key.")
df_encrypted = run_query("SELECT * FROM employees")
df_encrypted = df_encrypted.drop(columns=["name"])
st.dataframe(df_encrypted, width="stretch")

# Section 2 -- SQL explorer
st.header("SQL explorer")
st.caption("Run any SELECT query against the encrypted database.")

default_query = "SELECT * FROM employees"
default_query_decrypted = "SELECT * FROM employees"

col1, col2 = st.columns(2)
with col1:
    sql_encrypted = st.text_area("Encrypted query", value=default_query, height=100)
with col2:
    sql_decrypted = st.text_area("Decrypted query", value=default_query_decrypted, height=100)

if st.button("Run query"):
    try:
        encrypted_result = run_query(sql_encrypted)
        if "name" in encrypted_result.columns:
            encrypted_result = encrypted_result.drop(columns=["name"])
        st.subheader("Encrypted result")
        st.dataframe(encrypted_result, width="stretch")

        st.subheader("Decrypted equivalent")
        st.caption("Same query, run against the decrypted table.")
        decrypted_df = get_decrypted_df()

        engine_mem = sqlalchemy.create_engine("sqlite:///:memory:")
        with engine_mem.connect() as conn:
            decrypted_df.to_sql("employees", conn, index=False)
            decrypted_result = pd.read_sql_query(sql_decrypted, conn)

        st.dataframe(decrypted_result, width="stretch")

    except Exception as e:
        st.error(f"Query error: {e}")