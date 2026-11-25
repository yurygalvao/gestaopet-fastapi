"""
Testes automatizados
====================

O QUE ESTE ARQUIVO FAZ
----------------------
Verifica automaticamente se a API se comporta como esperado: CRUD completo,
erros de validação (422), recurso inexistente (404), e-mail duplicado (409)
e exclusão em cascata.

COMO RODAR
----------
    pytest -v
O pytest encontra sozinho as funções que começam com `test_` e executa cada
uma. Se algum `assert` falhar, o teste aparece como FAILED.

COMO OS TESTES FUNCIONAM SEM O SERVIDOR NO AR?
----------------------------------------------
O `TestClient` do FastAPI simula as requisições HTTP direto na aplicação,
sem precisar subir o servidor. `client.post("/tutores", json={...})`
funciona como se alguém tivesse chamado a API de verdade.

BANCO SEPARADO PARA TESTES (Injeção de Dependência na prática)
--------------------------------------------------------------
Os testes não podem sujar o banco real. Por isso criamos um SQLite EM
MEMÓRIA ("sqlite://"), que some quando os testes terminam, e mandamos o
FastAPI usá-lo no lugar do banco real:

    app.dependency_overrides[get_db] = get_db_teste

Essa linha diz: "toda vez que algum endpoint pedir get_db, use get_db_teste".
Nenhum arquivo da aplicação precisou ser alterado. Essa é a grande vantagem
da injeção de dependência.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app

# Banco em memória. StaticPool faz todas as conexões usarem o MESMO banco
# em memória (sem isso, cada conexão veria um banco vazio diferente).
engine_teste = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTeste = sessionmaker(bind=engine_teste, autoflush=False, expire_on_commit=False)


def get_db_teste():
    """Cópia de get_db (db/session.py), mas usando o banco de teste."""
    db = SessionTeste()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# FIXTURE: preparação que o pytest executa antes de cada teste que a pede
# (todo teste que tem o parâmetro `client`). O código depois do `yield` é a
# limpeza, que roda depois do teste. Cada teste começa com o banco vazio.
@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine_teste)      # cria as tabelas
    app.dependency_overrides[get_db] = get_db_teste  # troca o banco
    with TestClient(app) as c:
        yield c                                      # o teste roda aqui
    app.dependency_overrides.clear()                 # desfaz a troca
    Base.metadata.drop_all(bind=engine_teste)        # apaga as tabelas


def criar_tutor(client, email="maria@email.com"):
    """Função auxiliar: cadastra um tutor e devolve o JSON da resposta."""
    r = client.post("/tutores", json={"nome": "Maria", "email": email, "telefone": "82999990000"})
    assert r.status_code == 201
    return r.json()


def test_status(client):
    # A rota raiz responde?
    assert client.get("/").json()["status"] == "ok"


def test_crud_tutor(client):
    # CREATE
    tutor = criar_tutor(client)
    assert tutor["id"] > 0 and tutor["pets"] == []

    # READ (um e todos)
    assert client.get(f"/tutores/{tutor['id']}").json()["nome"] == "Maria"
    assert len(client.get("/tutores").json()) == 1

    # UPDATE parcial: só o nome muda
    r = client.patch(f"/tutores/{tutor['id']}", json={"nome": "Maria Souza"})
    assert r.status_code == 200 and r.json()["nome"] == "Maria Souza"

    # DELETE e confirmação de que sumiu
    assert client.delete(f"/tutores/{tutor['id']}").status_code == 204
    assert client.get(f"/tutores/{tutor['id']}").status_code == 404


def test_email_duplicado_retorna_409(client):
    # Regra de negócio do TutorService
    criar_tutor(client)
    r = client.post("/tutores", json={"nome": "Outra", "email": "maria@email.com"})
    assert r.status_code == 409


def test_validacao_retorna_422(client):
    # Nome vazio e e-mail inválido: o Pydantic barra antes de chegar ao serviço
    r = client.post("/tutores", json={"nome": "", "email": "nao-e-email"})
    assert r.status_code == 422


def test_crud_pet(client):
    tutor = criar_tutor(client)
    r = client.post(
        "/pets",
        json={"nome": "Rex", "especie": "cachorro", "raca": "Vira-lata", "tutor_id": tutor["id"]},
    )
    assert r.status_code == 201
    pet = r.json()

    # O pet aparece na lista do tutor e o filtro por espécie funciona
    assert client.get(f"/tutores/{tutor['id']}/pets").json()[0]["nome"] == "Rex"
    assert len(client.get("/pets", params={"especie": "cachorro"}).json()) == 1
    assert client.get("/pets", params={"especie": "gato"}).json() == []

    r = client.patch(f"/pets/{pet['id']}", json={"nome": "Rex II"})
    assert r.json()["nome"] == "Rex II"

    assert client.delete(f"/pets/{pet['id']}").status_code == 204
    assert client.get(f"/pets/{pet['id']}").status_code == 404


def test_pet_sem_tutor_retorna_404(client):
    # Regra de negócio do PetService: o tutor precisa existir
    r = client.post("/pets", json={"nome": "Mimi", "especie": "gato", "tutor_id": 999})
    assert r.status_code == 404


def test_excluir_tutor_exclui_pets(client):
    # cascade="all, delete-orphan" em models/entities.py
    tutor = criar_tutor(client)
    pet = client.post("/pets", json={"nome": "Mimi", "especie": "gato", "tutor_id": tutor["id"]}).json()
    client.delete(f"/tutores/{tutor['id']}")
    assert client.get(f"/pets/{pet['id']}").status_code == 404
