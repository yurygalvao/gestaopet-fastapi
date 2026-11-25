"""
Exceções de domínio
===================

O QUE ESTE ARQUIVO FAZ
----------------------
Define os tipos de erro que podem acontecer nas REGRAS DE NEGÓCIO do sistema,
como "tutor não encontrado" ou "e-mail já cadastrado".

POR QUE NÃO USAR DIRETO OS ERROS HTTP?
--------------------------------------
A camada de serviço (pasta services/) não deve saber que existe HTTP. Ela só
diz "isso não existe" ou "isso viola uma regra". Quem traduz esses erros para
códigos HTTP é o main.py:

    NaoEncontradoError  ->  404 Not Found
    ConflitoError       ->  409 Conflict

Vantagem: se um dia as mesmas regras forem usadas por outro tipo de interface
(um script, uma fila de mensagens), elas continuam funcionando sem mudança.
"""


class NaoEncontradoError(Exception):
    """Lançada quando um tutor ou pet procurado não existe no banco."""


class ConflitoError(Exception):
    """Lançada quando uma regra de negócio é violada (ex.: e-mail duplicado)."""
