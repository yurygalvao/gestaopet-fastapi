"""
Endpoints de Tutor (a "porta de entrada" HTTP)
==============================================

O QUE ESTE ARQUIVO FAZ
----------------------
Define as URLs da API relacionadas a tutores e o que acontece em cada uma.
Cada função é um ENDPOINT: a combinação de um método HTTP com um caminho.

    POST   /tutores               cria um tutor            -> 201 Created
    GET    /tutores               lista tutores            -> 200 OK
    GET    /tutores/{tutor_id}    busca um tutor           -> 200 ou 404
    PATCH  /tutores/{tutor_id}    altera campos do tutor   -> 200, 404 ou 409
    DELETE /tutores/{tutor_id}    exclui o tutor           -> 204 No Content
    GET    /tutores/{tutor_id}/pets  lista os pets dele    -> 200 ou 404

Os endpoints são FINOS de propósito: só recebem os dados e repassam ao
serviço. Nenhuma regra de negócio fica aqui.

DE ONDE VÊM OS PARÂMETROS?
--------------------------
O FastAPI descobre sozinho, olhando o tipo de cada parâmetro:
- `tutor_id: int` que aparece no caminho "/{tutor_id}" -> vem da URL
- `dados: TutorCreate` (um schema Pydantic)          -> vem do corpo JSON
- `skip: int = Query(...)`                            -> vem da query string (?skip=10)
- `service: TutorServiceDep`                          -> vem da injeção de dependência

PADRÃO DE PROJETO: Decorator
----------------------------
`@router.post(...)` é um decorator: ele pega uma função Python comum e
ACRESCENTA comportamento sem mudar o código dela. Depois de decorada, a
função passa a:
- responder no caminho e método HTTP indicados;
- ter a entrada validada pelo Pydantic (erro 422 se inválida);
- ter a saída convertida e filtrada pelo `response_model`;
- devolver o `status_code` indicado;
- aparecer na documentação automática em /docs.

O QUE É `APIRouter`?
--------------------
Um "mini app" que agrupa endpoints relacionados. Aqui ele define o prefixo
"/tutores" (que vale para todas as rotas do arquivo) e a tag "Tutores", que
agrupa essas rotas na página /docs. O main.py conecta o router ao app.
"""

from fastapi import APIRouter, Query, status

from app.dependencies import TutorServiceDep
from app.schemas.dtos import PetRead, TutorCreate, TutorRead, TutorUpdate

router = APIRouter(prefix="/tutores", tags=["Tutores"])


# response_model=TutorRead: a resposta segue o formato de TutorRead.
# O FastAPI converte o objeto Tutor do banco nesse formato automaticamente.
@router.post("", response_model=TutorRead, status_code=status.HTTP_201_CREATED)
def criar_tutor(dados: TutorCreate, service: TutorServiceDep):
    return service.criar(dados)


# Query(0, ge=0): valor padrão 0, e precisa ser maior ou igual a 0.
# Query(100, ge=1, le=100): padrão 100, entre 1 e 100 (evita pedir 1 milhão).
@router.get("", response_model=list[TutorRead])
def listar_tutores(
    service: TutorServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return service.listar(skip, limit)


@router.get("/{tutor_id}", response_model=TutorRead)
def buscar_tutor(tutor_id: int, service: TutorServiceDep):
    return service.buscar(tutor_id)


# PATCH = atualização parcial: o cliente envia só os campos que quer mudar
@router.patch("/{tutor_id}", response_model=TutorRead)
def atualizar_tutor(tutor_id: int, dados: TutorUpdate, service: TutorServiceDep):
    return service.atualizar(tutor_id, dados)


# 204 No Content: deu certo, mas não há nada para devolver no corpo
@router.delete("/{tutor_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_tutor(tutor_id: int, service: TutorServiceDep):
    service.excluir(tutor_id)


@router.get("/{tutor_id}/pets", response_model=list[PetRead])
def listar_pets_do_tutor(tutor_id: int, service: TutorServiceDep):
    return service.listar_pets(tutor_id)
