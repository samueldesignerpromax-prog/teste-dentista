import requests
import json
from datetime import datetime
from services.agendamento import horarios_disponiveis, criar_agendamento, listar_dentistas, listar_servicos

LLM_API_URL = os.getenv("LLM_API_URL", "https://lenior-api-1-hvvj.onrender.com")

async def processar_mensagem(mensagem: str):
    # Obter dados atuais
    dentistas = await listar_dentistas()
    servicos = await listar_servicos()
    dentistas_str = ", ".join([f"{d['nome']} ({d['especialidade']})" for d in dentistas])
    servicos_str = ", ".join([s['nome'] for s in servicos])

    prompt = f"""
    Você é um assistente de clínica odontológica. Seu nome é DentBot.
    Dentistas: {dentistas_str}
    Serviços: {servicos_str}
    Para agendar, você deve retornar um JSON no seguinte formato:
    {{"acao": "agendar", "nome": "...", "telefone": "...", "dentista": "...", "servico": "...", "data_hora": "..."}}
    Se não tiver dados suficientes, peça as informações faltantes de forma educada.
    Se for uma pergunta geral, responda normalmente.
    Cliente: {mensagem}
    Resposta:
    """
    
    try:
        resp = requests.post(LLM_API_URL, json={"prompt": prompt}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        resposta_texto = data.get("response", "")
        # Tentar parsear JSON se existir
        try:
            # Pode estar dentro da resposta, extrair parte JSON
            json_start = resposta_texto.find('{')
            json_end = resposta_texto.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = resposta_texto[json_start:json_end]
                acao = json.loads(json_str)
                if acao.get("acao") == "agendar":
                    # Validar e criar agendamento
                    resultado = await executar_agendamento(acao)
                    return {"resposta": f"Agendamento realizado com sucesso! ID: {resultado}", "acao": "agendado"}
        except:
            pass
        return {"resposta": resposta_texto}
    except Exception as e:
        return {"resposta": "Desculpe, tive um problema técnico."}

async def executar_agendamento(dados):
    # Mapear nomes para IDs (simplificado)
    dentistas = await listar_dentistas()
    servicos = await listar_servicos()
    dentista_id = next((d["_id"] for d in dentistas if d["nome"] == dados["dentista"]), None)
    servico_id = next((s["_id"] for s in servicos if s["nome"] == dados["servico"]), None)
    if not dentista_id or not servico_id:
        raise ValueError("Dentista ou serviço não encontrado")
    # Converter data_hora
    data_hora = datetime.fromisoformat(dados["data_hora"])
    agendamento = {
        "cliente_nome": dados["nome"],
        "cliente_telefone": dados["telefone"],
        "dentista_id": str(dentista_id),
        "servico_id": str(servico_id),
        "data_hora": data_hora
    }
    return await criar_agendamento(agendamento)
