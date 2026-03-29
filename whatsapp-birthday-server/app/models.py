import re

from pydantic import BaseModel, Field, field_validator


class SendMessageRequest(BaseModel):
    group_id: str = Field(
        ...,
        description="ID do grupo WhatsApp no formato 120363XXXXXXXXX@g.us",
        examples=["120363000000000@g.us"],
    )
    message: str = Field(
        ...,
        max_length=4096,
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

    @field_validator("group_id")
    @classmethod
    def validate_group_id(cls, v: str) -> str:
        if not re.fullmatch(r"^[0-9]+@g\.us$", v):
            raise ValueError(
                "group_id inválido. Formato esperado: 120363XXXXXXXXX@g.us"
            )
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.fullmatch(r"^[+]?[0-9]{7,15}$", cleaned):
            raise ValueError(
                "Número de telemóvel inválido. Use apenas dígitos com indicativo de país."
            )
        return cleaned


class SendMessageResponse(BaseModel):
    success: bool
