"""
Repositório base (acesso a dados genérico)
==========================================

O QUE ESTE ARQUIVO FAZ
----------------------
Reúne as operações básicas de banco que servem para qualquer tabela:
buscar por id, listar, adicionar e excluir. Os repositórios de Tutor e de
Pet herdam desta classe e ganham essas operações prontas.

PADRÃO DE PROJETO: Repository
-----------------------------
O repositório é o ÚNICO lugar que fala com o banco. A camada de serviço pede
"me dê o tutor 3" (`repo.get(3)`) sem saber como isso é feito: se os dados
vêm de SQLite, PostgreSQL ou até de uma lista em memória. Vantagens:
- as regras de negócio ficam livres de SQL e mais fáceis de ler;
- trocar o banco ou a forma de consulta não exige mexer nos serviços;
- nos testes, dá para usar um banco diferente sem mudar as regras.

O QUE É `Generic[ModelT]`?
--------------------------
É um recurso de tipagem do Python para escrever uma classe que funciona com
vários tipos. `ModelT` é um "tipo coringa":
    BaseRepository[Tutor]  -> get() devolve um Tutor
    BaseRepository[Pet]    -> get() devolve um Pet
Assim o CRUD é escrito UMA vez e o editor ainda sabe o tipo certo de cada retorno.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import Base

# Tipo coringa: pode ser qualquer classe que herde de Base (Tutor, Pet...)
ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    # Cada repositório filho informa qual tabela ele usa (ex.: model = Tutor)
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        # A sessão chega pronta pelo construtor (injeção de dependência).
        # O repositório não abre nem fecha conexão: só usa a que recebeu.
        self.db = db

    def get(self, id: int) -> ModelT | None:
        """Busca pela chave primária. Devolve None se não existir."""
        return self.db.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelT]:
        """Lista registros com paginação.

        skip = quantos pular; limit = quantos trazer no máximo.
        Equivale a: SELECT * FROM tabela LIMIT {limit} OFFSET {skip}
        """
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt))

    def add(self, obj: ModelT) -> ModelT:
        """Adiciona (ou atualiza) um objeto na sessão."""
        self.db.add(obj)
        # flush() envia o INSERT/UPDATE ao banco AGORA, dentro da transação,
        # mas sem confirmar (o commit fica para o final da requisição).
        # Isso faz o banco gerar o id, que precisamos devolver na resposta.
        self.db.flush()
        # refresh() relê o objeto do banco para trazer os valores atualizados
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        """Marca o objeto para exclusão e envia o DELETE ao banco."""
        self.db.delete(obj)
        self.db.flush()
