"""
Repositório de Tutor
====================

Herda de BaseRepository, então já tem get, list, add e delete prontos.
Aqui só acrescentamos a consulta que é específica de tutor: buscar por e-mail.
O TutorService usa essa busca para impedir e-mails duplicados.
"""

from sqlalchemy import select

from app.models.entities import Tutor
from app.repositories.base import BaseRepository


class TutorRepository(BaseRepository[Tutor]):
    model = Tutor  # informa à classe base qual tabela usar

    def get_by_email(self, email: str) -> Tutor | None:
        # Equivale a: SELECT * FROM tutores WHERE email = :email
        # scalar() devolve o primeiro resultado ou None se não achar nada
        return self.db.scalar(select(Tutor).where(Tutor.email == email))
