from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Chave partilhada entre as aplicações OutSystems e este servidor
    api_key: str

    # Configuração da Evolution API
    evolution_api_url: str = "http://evolution-api:8080"
    evolution_api_key: str
    evolution_instance: str = "aniversarios"
    http_timeout: int = Field(
        default=30,
        description="Timeout em segundos para chamadas à Evolution API",
    )

    # Configuração de rate limiting
    rate_limit_send: str = "30/minute"
    rate_limit_groups: str = "10/minute"

    class Config:
        env_file = ".env"


settings = Settings()
