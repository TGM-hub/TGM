# Privacy-Preserving Analytics API

> Compute statistics on sensitive data without the server ever seeing raw values.

![dashboard](Streamlit_privacy.gif)

---

## How it works

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database

    Client->>Client: generate secret key
    Client->>Client: encrypt(salary, key)
    Client->>Database: store ciphertexts
    API->>API: compute sum/mean on ciphertexts
    API->>Client: return encrypted result
    Client->>Client: decrypt(result, key)
```

The server computes on data it cannot read. Only the client holds the key.

The encryption scheme is additive:

```
encrypt(x)      = x + key
decrypt(sum, n) = sum - n * key
mean            = decrypt(sum, n) / n
```

---

## Project structure

```
crypto/         pure encryption logic, no external dependencies
api/            fastapi server, operates on ciphertexts only
database.py     sqlalchemy models and sqlite connection
run.py          seed script, encrypts and stores fake HR records
app.py          streamlit dashboard, decryption happens client-side
```

---

## Quick start

Clone the repo and install dependencies:

```bash
pip install -r requirements.txt
```

Seed the database with encrypted HR records:

```bash
python run.py
```

Start the API server:

```bash
uvicorn api.main:app --reload
```

Launch the dashboard:

```bash
streamlit run app.py
```

---

## Tech stack

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.33-FF4B4B)
![SQLite](https://img.shields.io/badge/SQLite-embedded-003B57)

---

## Important note

This project uses a simplified educational encryption scheme.
It demonstrates the architecture and principles of homomorphic encryption
but is not intended for production use.
