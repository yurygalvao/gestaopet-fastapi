"""
Conexão com o banco de dados
============================

O QUE ESTE ARQUIVO FAZ
----------------------
Prepara tudo o que a aplicação precisa para conversar com o banco:

1. `engine`        -> a conexão com o banco (sabe ONDE ele está e COMO falar com ele)
2. `SessionLocal`  -> uma "fábrica" de sessões; cada sessão é uma conversa com o banco
3. `Base`          -> classe mãe de todas as tabelas (models/entities.py herda dela)
4. `get_db()`      -> função que o FastAPI chama a cada requisição para entregar
                      uma sessão pronta e fechá-la no final

O QUE É SQLALCHEMY?
-------------------
É um ORM (Object-Relational Mapper): uma biblioteca que permite trabalhar com
o banco usando objetos Python em vez de escrever SQL na mão. Em vez de
    INSERT INTO tutores (nome, email) VALUES ('Maria', 'maria@email.com')
nós fazemos
    db.add(Tutor(nome="Maria", email="maria@email.com"))

PADRÃO DE PROJETO: Unit of Work (Unidade de Trabalho)
-----------------------------------------------------
A Session do SQLAlchemy funciona como uma lista de tudo o que mudou durante
a requisição (inserções, alterações, exclusões). Nada fica gravado de forma
definitiva até o `commit()`. Se algo der errado no meio, o `rollback()`
desfaz tudo. Ou a requisição inteira é salva, ou nada é salvo.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Cria a conexão com o banco usando o endereço das configurações.
# "check_same_thread": False é uma exigência do SQLite: por padrão ele só
# aceita ser usado pela mesma thread que o abriu, e o servidor web usa várias.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # necessário para SQLite
)

# Fábrica de sessões. Cada chamada SessionLocal() abre uma sessão nova.
# - autoflush=False: só envia as mudanças ao banco quando pedirmos (flush/commit)
# - expire_on_commit=False: depois do commit, os objetos continuam com os dados
#   em memória, então a API consegue montar a resposta sem consultar o banco de novo
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe base de todos os modelos ORM.

    Toda classe que herda de Base vira uma tabela. O SQLAlchemy guarda a lista
    dessas tabelas em Base.metadata, que o main.py usa para criá-las no banco.
    """


def get_db() -> Generator[Session, None, None]:
    """Entrega uma sessão do banco para cada requisição.

    É uma DEPENDÊNCIA COM YIELD, um recurso do FastAPI:
    - o código ANTES do `yield` roda antes do endpoint (abre a sessão);
    - no `yield`, a sessão é entregue para quem pediu (repositórios);
    - o código DEPOIS do `yield` roda quando o endpoint termina.

    Por isso esta função consegue fazer o commit no final, se tudo deu certo,
    ou o rollback, se aconteceu algum erro.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise  # repassa o erro para o FastAPI montar a resposta (404, 409...)
    finally:
        db.close()  # sempre fecha a conexão, com erro ou sem erro
