from datetime import datetime
from db import db
from models import Agendamento, Dentista, Servico
from bson import ObjectId

async def listar_dentistas():
    cursor = db.dentistas.find()
    return await cursor.to_list(length=100)

async def listar_servicos():
    cursor = db.servicos.find()
    return await cursor.to_list(length=100)

async def horarios_disponiveis(data: datetime, dentista_id: str):
    # Implementação real: buscar agendamentos existentes e gerar slots livres
    # Exemplo: slots padrão das 9h às 17h com intervalo de 30min
    slots = []
    start = data.replace(hour=9, minute=0, second=0, microsecond=0)
    end = data.replace(hour=17, minute=0, second=0, microsecond=0)
    current = start
    while current < end:
        slots.append(current.isoformat())
        current += timedelta(minutes=30)
    # Filtrar ocupados (simplificado)
    ocupados = await db.agendamentos.find({
        "dentista_id": dentista_id,
        "data_hora": {"$gte": start, "$lt": end}
    }).to_list(length=100)
    ocupados_set = {a["data_hora"].isoformat() for a in ocupados}
    livres = [s for s in slots if s not in ocupados_set]
    return livres

async def criar_agendamento(dados: dict):
    agendamento = Agendamento(**dados)
    result = await db.agendamentos.insert_one(agendamento.dict(by_alias=True, exclude={"id"}))
    return str(result.inserted_id)
