# main.py (TEMP TEST)
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "up"}

@app.get("/")
def root():
    return {"ok": True}
