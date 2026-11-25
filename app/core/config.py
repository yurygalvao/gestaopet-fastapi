"""
Configurações da aplicação
==========================

O QUE ESTE ARQUIVO FAZ
----------------------
Guarda, em um único lugar, os valores que podem mudar de um ambiente para
outro: o nome da aplicação e o endereço do banco de dados. Assim nenhum outro
arquivo precisa ter esses valores "chumbados" no código.

COMO FUNCIONA
-------------
- `Settings` herda de `BaseSettings` (biblioteca pydantic-settings).
  Cada atributo da classe é uma configuração com um valor padrão.
- Se existir uma variável de ambiente com o mesmo nome (ex.: DATABASE_URL)
  ou um arquivo `.env` na pasta do projeto, o valor de lá substitui o padrão.
  Exemplo de .env para usar PostgreSQL em produção:
      DATABASE_URL=postgresql://usuario:senha@servidor/gestaopet

PADRÃO DE PROJETO: Singleton
----------------------------
Singleton garante que exista UMA única instância de um objeto na aplicação.
Aqui isso é feito com o decorator `@lru_cache` do Python: na primeira chamada,
`get_settings()` cria o objeto `Settings` e guarda o resultado em cache; nas
chamadas seguintes, devolve o MESMO objeto, sem criar outro e sem ler o
arquivo .env de novo.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Nome exibido no topo da documentação automática (/docs)
    app_name: str = "GestãoPet API"

    # Endereço do banco. "sqlite:///./gestaopet.db" significa:
    # use o SQLite e grave tudo no arquivo gestaopet.db, na pasta atual.
    database_url: str = "sqlite:///./gestaopet.db"

    # Diz ao pydantic-settings para também procurar valores no arquivo .env
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache  # guarda o resultado: a função só executa de verdade uma vez
def get_settings() -> Settings:
    return Settings()
