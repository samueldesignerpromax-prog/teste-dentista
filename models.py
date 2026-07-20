from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Dentista(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nome: str
    especialidade: str

class Servico(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nome: str
    duracao_minutos: int

class Agendamento(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    cliente_nome: str
    cliente_email: Optional[str] = None
    cliente_telefone: str
    dentista_id: str  # ObjectId como string
    servico_id: str
    data_hora: datetime
    status: str = "agendado"
    criado_em: datetime = Field(default_factory=datetime.utcnow)
