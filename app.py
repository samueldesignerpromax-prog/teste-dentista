from flask import Flask, render_template, request, jsonify
from models import db, Dentista, Servico, Agendamento
from datetime import datetime
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# URL da sua API LLM
LLM_API_URL = "https://lenior-api-1-hvvj.onrender.com"

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para página de agendamento
@app.route('/agendar')
def agendar():
    dentistas = Dentista.query.all()
    servicos = Servico.query.all()
    return render_template('agendar.html', dentistas=dentistas, servicos=servicos)

# API para listar horários disponíveis (exemplo)
@app.route('/api/horarios', methods=['GET'])
def horarios_disponiveis():
    # Lógica para buscar horários livres (exemplo simplificado)
    # Aqui você pode implementar uma verificação de agendamentos existentes
    data = request.args.get('data')
    dentista_id = request.args.get('dentista_id')
    # Retorna uma lista de horários (strings)
    horarios = ['09:00', '09:30', '10:00', '10:30', '11:00', '14:00', '14:30', '15:00']
    return jsonify(horarios)

# API para criar agendamento
@app.route('/api/agendar', methods=['POST'])
def criar_agendamento():
    dados = request.json
    novo = Agendamento(
        cliente_nome=dados['nome'],
        cliente_email=dados.get('email'),
        cliente_telefone=dados.get('telefone'),
        dentista_id=dados['dentista_id'],
        servico_id=dados['servico_id'],
        data_hora=datetime.fromisoformat(dados['data_hora'])
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'status': 'sucesso', 'id': novo.id})

# ================= CHATBOT =================
@app.route('/api/chat', methods=['POST'])
def chat():
    mensagem_usuario = request.json.get('mensagem')
    if not mensagem_usuario:
        return jsonify({'erro': 'Mensagem vazia'}), 400

    # Construir o prompt com contexto
    prompt = f"""
    Você é um assistente virtual de uma clínica odontológica. 
    Seu nome é "DentBot". Você ajuda os clientes a agendar consultas, 
    escolher dentistas e serviços, e tira dúvidas sobre procedimentos.

    Regras:
    - Seja educado e claro.
    - Se o cliente pedir para agendar, peça o nome, telefone, serviço desejado e data/horário.
    - Para sugerir horários, você pode listar opções padrão (ex: 9h, 10h, 14h, 15h) ou perguntar a preferência.
    - Você tem acesso a uma lista de dentistas: [lista com nomes e especialidades].
    - Serviços disponíveis: [lista de serviços].

    Cliente: {mensagem_usuario}
    Assistente:
    """

    # Chamar a API LLM
    try:
        # Supondo que a API espere um JSON com {"prompt": ...} e retorne {"response": ...}
        response = requests.post(LLM_API_URL, json={'prompt': prompt}, timeout=10)
        response.raise_for_status()
        dados_resposta = response.json()
        resposta_llm = dados_resposta.get('response', 'Desculpe, não entendi. Pode repetir?')
    except Exception as e:
        resposta_llm = "Estou com problemas técnicos. Tente novamente mais tarde."

    return jsonify({'resposta': resposta_llm})

# Inicializar banco (criar tabelas)
with app.app_context():
    db.create_all()
    # Inserir dados de exemplo se estiver vazio
    if not Dentista.query.first():
        d1 = Dentista(nome='Dra. Ana', especialidade='Ortodontia')
        d2 = Dentista(nome='Dr. Carlos', especialidade='Implantodontia')
        db.session.add_all([d1, d2])
        db.session.commit()
    if not Servico.query.first():
        s1 = Servico(nome='Limpeza', duracao_minutos=30)
        s2 = Servico(nome='Obturação', duracao_minutos=45)
        s3 = Servico(nome='Clareamento', duracao_minutos=60)
        db.session.add_all([s1, s2, s3])
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
