from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Chave partilhada entre as aplicações OutSystems e este servidor
    api_key: str

    # Configuração da Evolution API
    evolution_api_url: str = "http://evolution-api:8080"
    evolution_api_key: str
    evolution_instance: str = "aniversarios"

    class Config:
        env_file = ".env"


settings = Settings()
