from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    group_id: str = Field(
        ...,
        description="ID do grupo WhatsApp no formato 120363XXXXXXXXX@g.us",
        examples=["120363000000000@g.us"],
    )
    message: str = Field(
        ...,
        description=(
            "Texto da mensagem. Se 'phone' for fornecido, a menção @número "
            "é inserida automaticamente no início."
        ),
        examples=["🎂 Hoje é aniversário da Ana! Parabéns! 🎉"],
    )
    phone: str | None = Field(
        default=None,
        description=(
            "Número de telemóvel do aniversariante (com ou sem +, com indicativo). "
            "Quando presente, a pessoa é mencionada no grupo e recebe notificação."
        ),
        examples=["351912345678", "+351912345678"],
    )


class SendMessageResponse(BaseModel):
    success: bool
    detail: str = ""
