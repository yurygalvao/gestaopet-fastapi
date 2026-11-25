"""
Endpoints de Pet (a "porta de entrada" HTTP)
============================================

Mesma estrutura de routers/tutores.py (veja a explicação completa lá).

    POST   /pets                  cria um pet              -> 201, 404 ou 422
    GET    /pets                  lista pets               -> 200
    GET    /pets?especie=gato     lista só os gatos        -> 200
    GET    /pets/{pet_id}         busca um pet             -> 200 ou 404
    PATCH  /pets/{pet_id}         altera campos do pet     -> 200 ou 404
    DELETE /pets/{pet_id}         exclui o pet             -> 204 ou 404

Novidade em relação aos tutores: o filtro opcional `especie`. Como o
parâmetro tem tipo `Especie | None` e valor padrão None, o FastAPI entende
que ele vem da query string (?especie=...) e que pode ser omitido. Se o
cliente enviar uma espécie que não existe no Enum, recebe erro 422.
"""

from fastapi import APIRouter, Query, status

from app.dependencies import PetServiceDep
from app.models.entities import Especie
from app.schemas.dtos import PetCreate, PetRead, PetUpdate

router = APIRouter(prefix="/pets", tags=["Pets"])


@router.post("", response_model=PetRead, status_code=status.HTTP_201_CREATED)
def criar_pet(dados: PetCreate, service: PetServiceDep):
    return service.criar(dados)


@router.get("", response_model=list[PetRead])
def listar_pets(
    service: PetServiceDep,
    especie: Especie | None = None,  # filtro opcional: ?especie=cachorro
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return service.listar(especie, skip, limit)


@router.get("/{pet_id}", response_model=PetRead)
def buscar_pet(pet_id: int, service: PetServiceDep):
    return service.buscar(pet_id)


@router.patch("/{pet_id}", response_model=PetRead)
def atualizar_pet(pet_id: int, dados: PetUpdate, service: PetServiceDep):
    return service.atualizar(pet_id, dados)


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_pet(pet_id: int, service: PetServiceDep):
    service.excluir(pet_id)
