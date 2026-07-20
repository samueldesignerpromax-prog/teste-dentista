from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from datetime import datetime
from models import db, Dentista, Servico, Agendamento

# Inicializa o Flask
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Configuração do banco de dados (usa variável de ambiente DATABASE_URL)
# Se não definida, fallback para SQLite local (apenas desenvolvimento)
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    # Fallback para SQLite (não recomendado para Vercel)
    database_url = 'sqlite:///database.db'
else:
    # Se for PostgreSQL, a Vercel costuma usar 'postgres://', mas SQLAlchemy espera 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# URL da API LLM (pode ser variável de ambiente)
LLM_API_URL = os.environ.get('LLM_API_URL', 'https://lenior-api-1-hvvj.onrender.com')

# Criar tabelas (se não existirem) e inserir dados iniciais
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

# Rotas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agendar')
def agendar():
    dentistas = Dentista.query.all()
    servicos = Servico.query.all()
    return render_template('agendar.html', dentistas=dentistas, servicos=servicos)

@app.route('/api/horarios', methods=['GET'])
def horarios_disponiveis():
    # Exemplo simples - você pode implementar lógica real
    horarios = ['09:00', '09:30', '10:00', '10:30', '11:00', '14:00', '14:30', '15:00']
    return jsonify(horarios)

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

@app.route('/api/chat', methods=['POST'])
def chat():
    mensagem_usuario = request.json.get('mensagem')
    if not mensagem_usuario:
        return jsonify({'erro': 'Mensagem vazia'}), 400

    # Obter listas para contexto
    dentistas = Dentista.query.all()
    lista_dentistas = ', '.join([f"{d.nome} ({d.especialidade})" for d in dentistas])
    servicos = Servico.query.all()
    lista_servicos = ', '.join([s.nome for s in servicos])

    prompt = f"""
    Você é o assistente virtual "DentBot" de uma clínica odontológica.
    Dentistas disponíveis: {lista_dentistas}.
    Serviços disponíveis: {lista_servicos}.
    Seja educado, claro e ajude o cliente a agendar uma consulta.
    Peça nome, telefone, serviço desejado e data/horário.
    Cliente: {mensagem_usuario}
    Assistente:
    """

    try:
        response = requests.post(LLM_API_URL, json={'prompt': prompt}, timeout=10)
        response.raise_for_status()
        dados_resposta = response.json()
        resposta_llm = dados_resposta.get('response', 'Desculpe, não entendi. Pode repetir?')
    except Exception as e:
        resposta_llm = "Estou com problemas técnicos. Tente novamente mais tarde."

    return jsonify({'resposta': resposta_llm})

# Handler para a Vercel (exporta a aplicação)
app.debug = False
