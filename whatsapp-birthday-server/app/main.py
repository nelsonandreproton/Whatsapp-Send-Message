from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
import httpx

from .config import settings
from .models import SendMessageRequest, SendMessageResponse

app = FastAPI(
    title="WhatsApp Birthday Server",
    description="Middleware entre OutSystems e Evolution API para envio de mensagens de aniversário.",
    version="1.0.0",
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key != settings.api_key:
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
async def send_message(
    request: SendMessageRequest,
    _: str = Depends(verify_api_key),
):
    """
    Recebe o ID do grupo WhatsApp e a mensagem já formatada,
    e encaminha para a Evolution API.

    Chamar este endpoint a partir do Timer do OutSystems para cada
    aniversariante encontrado na query.
    """
    url = f"{settings.evolution_api_url}/message/sendText/{settings.evolution_instance}"
    headers = {"apikey": settings.evolution_api_key}

    # Normalizar número: remover +, espaços e hífens (ex: +351 912-345-678 → 351912345678)
    mention_number = None
    text = request.message
    if request.phone:
        mention_number = request.phone.replace("+", "").replace(" ", "").replace("-", "")
        text = f"@{mention_number} {request.message}"

    payload: dict = {"number": request.group_id, "text": text}
    if mention_number:
        # Evolution API requer o sufixo @s.whatsapp.net na lista de menções
        payload["mentioned"] = [f"{mention_number}@s.whatsapp.net"]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erro de ligação à Evolution API: {exc}",
        )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=f"Evolution API devolveu erro {response.status_code}: {response.text}",
        )

    return SendMessageResponse(success=True)


@app.get(
    "/groups",
    tags=["Setup"],
    summary="Lista os grupos WhatsApp disponíveis (útil durante configuração)",
)
async def list_groups(_: str = Depends(verify_api_key)):
    """
    Lista todos os grupos WhatsApp a que o número ligado pertence.
    Usar durante a configuração inicial para obter os Group IDs
    que devem ser guardados como Site Properties no OutSystems.
    """
    url = (
        f"{settings.evolution_api_url}/group/fetchAllGroups"
        f"/{settings.evolution_instance}?getParticipants=false"
    )
    headers = {"apikey": settings.evolution_api_key}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erro de ligação à Evolution API: {exc}",
        )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=f"Evolution API devolveu erro {response.status_code}: {response.text}",
        )

    groups = response.json()
    return [
        {"id": g.get("id", ""), "name": g.get("subject", "(sem nome)")}
        for g in groups
    ]
