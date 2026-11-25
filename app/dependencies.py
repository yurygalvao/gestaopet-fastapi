"""
Injeção de dependência (a "fiação" da aplicação)
================================================

O QUE ESTE ARQUIVO FAZ
----------------------
Ensina o FastAPI a MONTAR os objetos que os endpoints precisam. Os endpoints
apenas declaram "preciso de um TutorService" e o FastAPI resolve o resto:

    get_db()                 abre a sessão do banco
       │
       ▼
    get_tutor_repository()   cria TutorRepository(sessão)
       │
       ▼
    get_tutor_service()      cria TutorService(repositório)
       │
       ▼
    endpoint criar_tutor(service=...)   recebe tudo pronto

PADRÃO DE PROJETO: Injeção de Dependência / Inversão de Controle
----------------------------------------------------------------
- Injeção de Dependência: um objeto RECEBE o que precisa (pelo construtor ou
  parâmetro) em vez de criar sozinho. O TutorService não faz
  `TutorRepository(...)`: recebe o repositório pronto.
- Inversão de Controle: quem decide QUANDO e COMO criar os objetos não é o
  nosso código, é o framework. Nós só descrevemos as receitas (as funções
  abaixo) e o FastAPI executa na hora certa.

COMO O FASTAPI SABE O QUE CHAMAR?
---------------------------------
Pelo `Depends(...)`. Quando um parâmetro é declarado como
    repo: Annotated[TutorRepository, Depends(get_tutor_repository)]
o FastAPI entende: "para preencher `repo`, chame get_tutor_repository()".
E se essa função também tiver um Depends, ele resolve esse primeiro, e assim
por diante, em cadeia.

`Annotated[Tipo, Depends(...)]` junta duas informações:
- o TIPO do parâmetro (para o editor e para a leitura do código);
- a RECEITA de como obter o valor (para o FastAPI).

DETALHE IMPORTANTE: CACHE POR REQUISIÇÃO
----------------------------------------
Dentro de UMA requisição, o FastAPI executa cada dependência uma única vez e
reaproveita o resultado. O PetService precisa de dois repositórios, e os dois
pedem get_db, mas a sessão aberta é a MESMA. Por isso tudo acontece em uma
única transação.

VANTAGEM NOS TESTES
-------------------
Como os objetos são montados pelo framework, dá para trocar uma peça sem
mexer no resto. Em tests/test_api.py trocamos get_db por um banco em memória
com uma linha: app.dependency_overrides[get_db] = get_db_teste
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.pet_repository import PetRepository
from app.repositories.tutor_repository import TutorRepository
from app.services.pet_service import PetService
from app.services.tutor_service import TutorService

# Apelido: "uma Session obtida via get_db". Evita repetir a expressão inteira.
DbSession = Annotated[Session, Depends(get_db)]


def get_tutor_repository(db: DbSession) -> TutorRepository:
    return TutorRepository(db)


def get_pet_repository(db: DbSession) -> PetRepository:
    return PetRepository(db)


def get_tutor_service(
    repo: Annotated[TutorRepository, Depends(get_tutor_repository)],
) -> TutorService:
    return TutorService(repo)


def get_pet_service(
    pets: Annotated[PetRepository, Depends(get_pet_repository)],
    tutores: Annotated[TutorRepository, Depends(get_tutor_repository)],
) -> PetService:
    return PetService(pets, tutores)


# Apelidos usados nos routers. Com eles, um endpoint só escreve
# `service: TutorServiceDep` para receber o serviço montado.
TutorServiceDep = Annotated[TutorService, Depends(get_tutor_service)]
PetServiceDep = Annotated[PetService, Depends(get_pet_service)]
