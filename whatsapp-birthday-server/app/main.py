import json
import logging
from secrets import compare_digest

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import httpx
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .models import SendMessageRequest, SendMessageResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WhatsApp Birthday Server",
    description="Middleware entre OutSystems e Evolution API para envio de mensagens de aniversário.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or not compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="API Key inválida ou ausente.")
    return api_key


@app.get("/health", tags=["Sistema"])
def health():
    """Verifica se o servidor está a funcionar. Não requer autenticação."""
    return {"status": "ok"}


@app.post(
    "/send-message",
    response_model=SendMessageResponse,
    tags=["Mensagens"],
    summary="Envia mensagem de aniversário para um grupo WhatsApp",
)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    body: SendMessageRequest,
    _: str = Depends(verify_api_key),
):
    """
    Recebe o ID do grupo WhatsApp e a mensagem já formatada,
    e encaminha para a Evolution API.

    Chamar este endpoint a partir do Timer do OutSystems para cada
    aniversariante encontrado na query.
    """
    logger.info("Request recebido: POST /send-message")

    url = f"{settings.evolution_api_url}/message/sendText/{settings.evolution_instance}"
    headers = {"apikey": settings.evolution_api_key}

    # Normalizar número: remover +, espaços e hífens (ex: +351 912-345-678 → 351912345678)
    mention_number = None
    text = body.message
    if body.phone:
        mention_number = body.phone.replace("+", "").replace(" ", "").replace("-", "")
        text = f"@{mention_number} {body.message}"

    payload: dict = {"number": body.group_id, "text": text}
    if mention_number:
        # Evolution API requer o sufixo @s.whatsapp.net na lista de menções
        payload["mentioned"] = [f"{mention_number}@s.whatsapp.net"]

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        logger.error("Erro de ligação à Evolution API (send-message): %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Erro ao comunicar com o serviço de mensagens.",
        )

    if response.status_code not in (200, 201):
        logger.error(
            "Evolution API devolveu erro %s em send-message: %s",
            response.status_code,
            response.text,
        )
        raise HTTPException(
            status_code=502,
            detail="Erro ao comunicar com o serviço de mensagens.",
        )

    logger.info("Mensagem enviada com sucesso para o grupo %s", body.group_id)
    return SendMessageResponse(success=True)


@app.get(
    "/groups",
    tags=["Setup"],
    summary="Lista os grupos WhatsApp disponíveis (útil durante configuração)",
)
@limiter.limit("10/minute")
async def list_groups(request: Request, _: str = Depends(verify_api_key)):
    """
    Lista todos os grupos WhatsApp a que o número ligado pertence.
    Usar durante a configuração inicial para obter os Group IDs
    que devem ser guardados como Site Properties no OutSystems.
    """
    logger.info("Request recebido: GET /groups")

    url = (
        f"{settings.evolution_api_url}/group/fetchAllGroups"
        f"/{settings.evolution_instance}?getParticipants=false"
    )
    headers = {"apikey": settings.evolution_api_key}

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        logger.error("Erro de ligação à Evolution API (list-groups): %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Erro ao comunicar com o serviço de mensagens.",
        )

    if response.status_code not in (200, 201):
        logger.error(
            "Evolution API devolveu erro %s em list-groups: %s",
            response.status_code,
            response.text,
        )
        raise HTTPException(
            status_code=502,
            detail="Erro ao comunicar com o serviço de mensagens.",
        )

    try:
        groups = response.json()
    except (json.JSONDecodeError, Exception) as exc:
        logger.error("Erro ao fazer parse do JSON da resposta de list-groups: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Erro ao comunicar com o serviço de mensagens.",
        )

    return [
        {"id": g.get("id", ""), "name": g.get("subject", "(sem nome)")}
        for g in groups
    ]
