"""
Ponto de entrada da aplicação
=============================

O QUE ESTE ARQUIVO FAZ
----------------------
Monta a aplicação FastAPI, juntando todas as peças:
1. cria o objeto `app` (a aplicação em si);
2. cria as tabelas no banco quando o servidor inicia (lifespan);
3. registra um middleware que mede o tempo de cada requisição;
4. registra os tratadores de erro (exceção de domínio -> resposta HTTP);
5. conecta os routers de tutores e de pets.

COMO RODAR
----------
    fastapi dev app/main.py
O comando procura a variável `app` neste arquivo e sobe um servidor em
http://127.0.0.1:8000 (o servidor por baixo é o Uvicorn). O modo "dev"
reinicia sozinho quando um arquivo é salvo.
A documentação interativa fica em http://127.0.0.1:8000/docs.

POR QUE ALGUMAS FUNÇÕES SÃO `async def`?
----------------------------------------
O FastAPI aceita funções normais (`def`) e assíncronas (`async def`).
- `async def` é usado quando a função precisa ESPERAR algo sem travar o
  servidor (aqui: `await call_next(request)` espera o restante da cadeia).
- `def` normal é usado nos endpoints porque o SQLAlchemy desta PoC é
  síncrono. O FastAPI roda essas funções em uma área separada (thread pool),
  então elas também não travam o servidor.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import ConflitoError, NaoEncontradoError
from app.db.session import Base, engine
from app.routers import pets, tutores

# Configura o log que aparece no terminal (uma linha por requisição)
logger = logging.getLogger("gestaopet")
logging.basicConfig(level=logging.INFO, format="%(message)s")


# LIFESPAN: código que roda quando o servidor LIGA (antes do yield) e quando
# ele DESLIGA (depois do yield). Aqui usamos só a parte de ligar.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria no banco todas as tabelas declaradas em models/ que ainda não
    # existem. Em projetos maiores isso é feito com migrações (Alembic).
    Base.metadata.create_all(bind=engine)
    yield


# O objeto principal. title, description e version aparecem no /docs.
app = FastAPI(
    title=get_settings().app_name,
    description="Prova de Conceito do seminário de APSI: CRUD de tutores e pets.",
    version="1.0.0",
    lifespan=lifespan,
)


# MIDDLEWARE
# ----------
# Um middleware é um código que envolve TODAS as requisições: roda antes de
# chegar ao endpoint e depois que a resposta fica pronta.
#
# PADRÃO DE PROJETO: Chain of Responsibility (Cadeia de Responsabilidade)
# A requisição passa por uma corrente de etapas. Cada etapa faz sua parte e
# chama `call_next` para entregar ao próximo elo (outro middleware ou, no
# fim, o endpoint). A resposta volta pelo mesmo caminho, na ordem inversa.
@app.middleware("http")
async def medir_tempo(request: Request, call_next):
    inicio = time.perf_counter()              # marca o horário de início
    response = await call_next(request)       # deixa a requisição seguir
    ms = (time.perf_counter() - inicio) * 1000  # quanto tempo levou, em ms
    response.headers["X-Process-Time-ms"] = f"{ms:.1f}"  # anexa à resposta
    logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, ms)
    return response


# TRATADORES DE EXCEÇÃO
# ---------------------
# Quando um serviço lança NaoEncontradoError ou ConflitoError, o FastAPI
# procura aqui uma função registrada para aquele tipo de erro e usa a
# resposta que ela devolve. Assim os serviços não precisam conhecer HTTP.
@app.exception_handler(NaoEncontradoError)
async def nao_encontrado_handler(request: Request, exc: NaoEncontradoError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflitoError)
async def conflito_handler(request: Request, exc: ConflitoError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


# Conecta os routers: a partir daqui as rotas /tutores e /pets existem
app.include_router(tutores.router)
app.include_router(pets.router)


# Rota simples na raiz, útil para conferir se a API está no ar
@app.get("/", tags=["Status"])
def status_api():
    return {"status": "ok", "docs": "/docs"}
