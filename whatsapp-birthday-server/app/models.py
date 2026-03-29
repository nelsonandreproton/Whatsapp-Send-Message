from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    group_id: str = Field(
        ...,
        description="ID do grupo WhatsApp no formato 120363XXXXXXXXX@g.us",
        examples=["120363000000000@g.us"],
    )
    message: str = Field(
        ...,
        description="Texto da mensagem a enviar",
        examples=["🎂 Hoje é aniversário da Ana! Parabéns! 🎉"],
    )


class SendMessageResponse(BaseModel):
    success: bool
    detail: str = ""
