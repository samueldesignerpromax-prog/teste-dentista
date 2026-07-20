from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from services.agendamento import listar_dentistas, listar_servicos, horarios_disponiveis, criar_agendamento
from services.chat import processar_mensagem
from db import db

app = FastAPI(title="Clínica Odontológica API")

# Servir arquivos estáticos (se tiver)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    # Inicializar dados de exemplo se não existirem
    if await db.dentistas.count_documents({}) == 0:
        await db.dentistas.insert_many([
            {"nome": "Dra. Ana", "especialidade": "Ortodontia"},
            {"nome": "Dr. Carlos", "especialidade": "Implantodontia"}
        ])
    if await db.servicos.count_documents({}) == 0:
        await db.servicos.insert_many([
            {"nome": "Limpeza", "duracao_minutos": 30},
            {"nome": "Obturação", "duracao_minutos": 45},
            {"nome": "Clareamento", "duracao_minutos": 60}
        ])

@app.get("/", response_class=HTMLResponse)
async def get_index():
    # Retorna uma página HTML com o chat e botão de agendamento
    with open("templates/index.html", "r") as f:
        return f.read()

@app.get("/agendar", response_class=HTMLResponse)
async def get_agendar():
    with open("templates/agendar.html", "r") as f:
        return f.read()

@app.get("/api/dentistas")
async def get_dentistas():
    dentistas = await listar_dentistas()
    return [{"id": str(d["_id"]), "nome": d["nome"], "especialidade": d["especialidade"]} for d in dentistas]

@app.get("/api/servicos")
async def get_servicos():
    servicos = await listar_servicos()
    return [{"id": str(s["_id"]), "nome": s["nome"], "duracao": s["duracao_minutos"]} for s in servicos]

@app.get("/api/horarios")
async def get_horarios(data: str, dentista_id: str):
    dt = datetime.fromisoformat(data)
    slots = await horarios_disponiveis(dt, dentista_id)
    return {"horarios": slots}

@app.post("/api/agendar")
async def post_agendar(dados: dict):
    try:
        id = await criar_agendamento(dados)
        return {"status": "sucesso", "id": id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def post_chat(request: Request):
    body = await request.json()
    mensagem = body.get("mensagem")
    if not mensagem:
        raise HTTPException(status_code=400, detail="Mensagem vazia")
    resultado = await processar_mensagem(mensagem)
    return JSONResponse(content=resultado)
