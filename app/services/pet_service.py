"""
Serviço de Pet (regras de negócio)
==================================

Mesma ideia do tutor_service.py, agora para pets. Regra principal:
- todo pet precisa de um tutor que EXISTA. Antes de cadastrar, o serviço
  consulta o repositório de tutores; se o tutor não existir, lança
  NaoEncontradoError (que vira 404).

Por isso este serviço recebe DOIS repositórios no construtor: o de pets e o
de tutores. Os dois usam a mesma sessão do banco, então tudo acontece dentro
da mesma transação (ver dependencies.py).
"""

from app.core.exceptions import NaoEncontradoError
from app.models.entities import Especie, Pet
from app.repositories.pet_repository import PetRepository
from app.repositories.tutor_repository import TutorRepository
from app.schemas.dtos import PetCreate, PetUpdate


class PetService:
    def __init__(self, pets: PetRepository, tutores: TutorRepository) -> None:
        self.pets = pets
        self.tutores = tutores

    def _garantir_tutor(self, tutor_id: int) -> None:
        # O "_" no início do nome é uma convenção do Python para dizer
        # "método de uso interno da classe"
        if self.tutores.get(tutor_id) is None:
            raise NaoEncontradoError(f"Tutor {tutor_id} não encontrado")

    def criar(self, dados: PetCreate) -> Pet:
        self._garantir_tutor(dados.tutor_id)  # regra: todo pet precisa de um tutor
        return self.pets.add(Pet(**dados.model_dump()))

    def listar(self, especie: Especie | None, skip: int, limit: int) -> list[Pet]:
        return self.pets.list_filtrado(especie, skip, limit)

    def buscar(self, pet_id: int) -> Pet:
        pet = self.pets.get(pet_id)
        if pet is None:
            raise NaoEncontradoError(f"Pet {pet_id} não encontrado")
        return pet

    def atualizar(self, pet_id: int, dados: PetUpdate) -> Pet:
        pet = self.buscar(pet_id)
        # Atualiza só os campos enviados pelo cliente (ver explicação em tutor_service.py)
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(pet, campo, valor)
        return self.pets.add(pet)

    def excluir(self, pet_id: int) -> None:
        self.pets.delete(self.buscar(pet_id))
