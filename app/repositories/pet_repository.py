"""
Repositório de Pet
==================

Herda de BaseRepository (get, list, add, delete) e acrescenta duas consultas
específicas de pet:
- list_filtrado: lista pets, filtrando por espécie se o cliente pedir
  (usada em GET /pets?especie=gato);
- list_by_tutor: lista os pets de um tutor.
"""

from sqlalchemy import select

from app.models.entities import Especie, Pet
from app.repositories.base import BaseRepository


class PetRepository(BaseRepository[Pet]):
    model = Pet

    def list_filtrado(
        self, especie: Especie | None = None, skip: int = 0, limit: int = 100
    ) -> list[Pet]:
        # Monta a consulta aos poucos: começa com "todos os pets"...
        stmt = select(Pet)
        # ...e só acrescenta o WHERE se a espécie foi informada
        if especie is not None:
            stmt = stmt.where(Pet.especie == especie)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)))

    def list_by_tutor(self, tutor_id: int) -> list[Pet]:
        # Equivale a: SELECT * FROM pets WHERE tutor_id = :tutor_id
        return list(self.db.scalars(select(Pet).where(Pet.tutor_id == tutor_id)))
