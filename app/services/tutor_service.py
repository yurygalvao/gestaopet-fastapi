"""
Serviço de Tutor (regras de negócio)
====================================

O QUE ESTE ARQUIVO FAZ
----------------------
Concentra as REGRAS DE NEGÓCIO de tutor, ou seja, o que o sistema permite ou
não permite, independente de banco ou HTTP:
- não pode existir dois tutores com o mesmo e-mail;
- buscar, atualizar ou excluir um tutor inexistente é um erro.

O QUE ESTA CAMADA NÃO FAZ
-------------------------
- Não escreve SQL: pede os dados ao repositório.
- Não conhece HTTP: em vez de devolver "404", lança NaoEncontradoError;
  o main.py é quem converte o erro em resposta HTTP.

COMO O REPOSITÓRIO CHEGA AQUI?
------------------------------
Pelo construtor (`__init__`). O serviço não cria o repositório: recebe pronto.
Isso é Injeção de Dependência. Quem monta tudo é o arquivo dependencies.py.

CICLO DE VIDA
-------------
Um objeto TutorService novo é criado a cada requisição e descartado no final.
"""

from app.core.exceptions import ConflitoError, NaoEncontradoError
from app.models.entities import Pet, Tutor
from app.repositories.tutor_repository import TutorRepository
from app.schemas.dtos import TutorCreate, TutorUpdate


class TutorService:
    def __init__(self, repo: TutorRepository) -> None:
        self.repo = repo

    def criar(self, dados: TutorCreate) -> Tutor:
        # Regra de negócio: e-mail único
        if self.repo.get_by_email(dados.email):
            raise ConflitoError(f"Já existe um tutor com o e-mail {dados.email}")
        # model_dump() transforma o schema em dicionário:
        #   {"nome": "Maria", "email": "...", "telefone": "..."}
        # e o ** "espalha" o dicionário como argumentos: Tutor(nome=..., email=...)
        return self.repo.add(Tutor(**dados.model_dump()))

    def listar(self, skip: int, limit: int) -> list[Tutor]:
        return self.repo.list(skip, limit)

    def buscar(self, tutor_id: int) -> Tutor:
        tutor = self.repo.get(tutor_id)
        if tutor is None:
            raise NaoEncontradoError(f"Tutor {tutor_id} não encontrado")
        return tutor

    def atualizar(self, tutor_id: int, dados: TutorUpdate) -> Tutor:
        tutor = self.buscar(tutor_id)  # já lança 404 se não existir
        # exclude_unset=True pega SÓ os campos que o cliente realmente enviou.
        # Se ele mandou {"nome": "Ana"}, o resultado é {"nome": "Ana"} e o
        # e-mail e o telefone continuam como estavam.
        alteracoes = dados.model_dump(exclude_unset=True)

        # Se o e-mail mudou, aplica a mesma regra de e-mail único da criação
        novo_email = alteracoes.get("email")
        if novo_email and novo_email != tutor.email and self.repo.get_by_email(novo_email):
            raise ConflitoError(f"Já existe um tutor com o e-mail {novo_email}")

        # setattr(tutor, "nome", "Ana") é o mesmo que tutor.nome = "Ana"
        for campo, valor in alteracoes.items():
            setattr(tutor, campo, valor)
        return self.repo.add(tutor)

    def excluir(self, tutor_id: int) -> None:
        # Os pets do tutor são excluídos junto (cascade definido em entities.py)
        self.repo.delete(self.buscar(tutor_id))

    def listar_pets(self, tutor_id: int) -> list[Pet]:
        return self.buscar(tutor_id).pets
