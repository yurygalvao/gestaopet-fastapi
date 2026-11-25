"""
Schemas Pydantic (o formato dos dados que entram e saem da API)
===============================================================

O QUE ESTE ARQUIVO FAZ
----------------------
Define o "contrato" da API: quais campos o cliente precisa enviar e quais
campos ele recebe de volta. Cada operação tem seu próprio schema:

    XxxCreate  -> o que o cliente envia para CRIAR (POST)
    XxxUpdate  -> o que o cliente envia para ATUALIZAR (PATCH); tudo opcional
    XxxRead    -> o que a API DEVOLVE (inclui o id gerado pelo banco)

O QUE É PYDANTIC?
-----------------
Biblioteca de validação de dados baseada nos tipos do Python. Quando um
endpoint recebe `dados: TutorCreate`, o FastAPI usa o Pydantic para:
1. ler o JSON enviado pelo cliente;
2. conferir se cada campo tem o tipo certo e respeita as regras
   (ex.: `min_length=1` impede nome vazio; `EmailStr` exige um e-mail válido);
3. se algo estiver errado, devolver automaticamente o erro 422 explicando
   qual campo falhou, sem que a gente escreva nenhum `if`.
Esses mesmos schemas geram a documentação da página /docs.

PADRÃO DE PROJETO: DTO (Data Transfer Object)
---------------------------------------------
DTO é um objeto que só serve para TRANSPORTAR dados entre camadas, sem regra
de negócio. Separar os DTOs dos modelos do banco (models/entities.py) traz
segurança e flexibilidade: por exemplo, o cliente não consegue enviar um `id`
ao criar um tutor, porque TutorCreate não tem esse campo.

HERANÇA ENTRE SCHEMAS
---------------------
Para não repetir campos, usamos herança:
    PetBase   (nome, especie, raca, data_nascimento)
     ├── PetCreate  = PetBase + tutor_id
     └── PetRead    = PetBase + id + tutor_id
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import Especie


# ---------- Pet ----------
class PetBase(BaseModel):
    # Field(...) acrescenta regras de validação e exemplos para o /docs
    nome: str = Field(min_length=1, max_length=80, examples=["Rex"])
    especie: Especie  # só aceita "cachorro", "gato" ou "outro"
    raca: str | None = Field(default=None, max_length=60, examples=["Vira-lata"])
    data_nascimento: date | None = None  # formato esperado: "2020-05-17"


class PetCreate(PetBase):
    tutor_id: int  # obrigatório: todo pet precisa de um tutor


class PetUpdate(BaseModel):
    # Todos os campos são opcionais (None): o cliente envia só o que quer mudar.
    # Ex.: PATCH /pets/1 com {"nome": "Rex II"} altera apenas o nome.
    nome: str | None = Field(default=None, min_length=1, max_length=80)
    especie: Especie | None = None
    raca: str | None = Field(default=None, max_length=60)
    data_nascimento: date | None = None


class PetRead(PetBase):
    # from_attributes=True permite criar este schema a partir de um objeto do
    # SQLAlchemy (lendo pet.id, pet.nome...), não só a partir de um dicionário.
    model_config = ConfigDict(from_attributes=True)

    id: int
    tutor_id: int


# ---------- Tutor ----------
class TutorBase(BaseModel):
    nome: str = Field(min_length=1, max_length=100, examples=["Maria Silva"])
    email: EmailStr  # valida o formato do e-mail (precisa ter @, domínio etc.)
    telefone: str | None = Field(default=None, max_length=20, examples=["82999990000"])


class TutorCreate(TutorBase):
    pass  # igual ao TutorBase; existe para deixar a intenção clara


class TutorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    telefone: str | None = Field(default=None, max_length=20)


class TutorRead(TutorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pets: list[PetRead] = []  # a resposta já traz a lista de pets do tutor
