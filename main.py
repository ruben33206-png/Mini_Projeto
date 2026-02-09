from fastapi import FastAPI, Request

app= FastAPI()

@app.get("/")
def read_root():
    return {"mensagem": "API está a funcionar!"}