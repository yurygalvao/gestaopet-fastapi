"""
Modelos ORM (as tabelas do banco)
=================================

O QUE ESTE ARQUIVO FAZ
----------------------
Descreve as tabelas do banco de dados como classes Python. Cada classe é uma
tabela e cada atributo é uma coluna:

    tutores                          pets
    ---------------------            ---------------------------
    id        (chave primária)       id               (chave primária)
    nome                             nome
    email     (único)                especie          (cachorro/gato/outro)
    telefone  (opcional)             raca             (opcional)
                                     data_nascimento  (opcional)
                                     tutor_id         (chave estrangeira -> tutores.id)

Relacionamento: um tutor tem vários pets (1:N); cada pet pertence a um tutor.

COMO LER A SINTAXE
------------------
    nome: Mapped[str] = mapped_column(String(100))
    ^^^^  ^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^
    |     |             detalhes da coluna no banco (texto de até 100 caracteres)
    |     tipo no Python (str = texto). `str | None` quer dizer "pode ficar vazio"
    nome do atributo = nome da coluna

PADRÃO DE PROJETO: Data Mapper
------------------------------
Estas classes são objetos Python comuns: NÃO têm métodos como `save()` ou
`delete()`. Quem traduz um objeto para uma linha da tabela (e vice-versa) é a
Session do SQLAlchemy (ver db/session.py). O objeto não sabe que existe banco.

O contrário disso é o padrão Active Record, usado no Laravel (Eloquent) e no
Ruby on Rails, em que o próprio objeto sabe se gravar: `$pet->save()`.
"""

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Especie(str, enum.Enum):
    """Lista fechada de espécies aceitas.

    Usar Enum impede valores inválidos: se alguém enviar "dinossauro", o
    FastAPI devolve erro 422 antes mesmo de chegar ao banco.
    """

    cachorro = "cachorro"
    gato = "gato"
    outro = "outro"


class Tutor(Base):
    __tablename__ = "tutores"  # nome da tabela no banco

    id: Mapped[int] = mapped_column(primary_key=True)  # gerado automaticamente
    nome: Mapped[str] = mapped_column(String(100))
    # unique=True: o banco não aceita dois tutores com o mesmo e-mail
    # index=True: cria um índice para buscar por e-mail mais rápido
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    telefone: Mapped[str | None] = mapped_column(String(20))

    # Não é uma coluna: é o "atalho" para acessar os pets do tutor (tutor.pets).
    # - back_populates="tutor": liga com o atributo `tutor` da classe Pet
    # - cascade="all, delete-orphan": ao excluir o tutor, os pets dele também
    #   são excluídos (não sobra pet sem dono)
    # - lazy="selectin": carrega os pets junto com o tutor, em uma consulta extra
    pets: Mapped[list["Pet"]] = relationship(
        back_populates="tutor", cascade="all, delete-orphan", lazy="selectin"
    )


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    especie: Mapped[Especie] = mapped_column(Enum(Especie))
    raca: Mapped[str | None] = mapped_column(String(60))
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    # Chave estrangeira: guarda o id do tutor dono deste pet
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutores.id"))

    # Atalho para o objeto Tutor completo (pet.tutor.nome, por exemplo)
    tutor: Mapped[Tutor] = relationship(back_populates="pets")
