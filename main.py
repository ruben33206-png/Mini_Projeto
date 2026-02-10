from fastapi import FastAPI, Request

app= FastAPI()

@app.get("/")
def read_root():
    return {"mensagem": "API está a funcionar!"}


@app.get("/teste")
def teste_endpoint():
    Teste = "Dado 1"
    return {"Teste": Teste}
