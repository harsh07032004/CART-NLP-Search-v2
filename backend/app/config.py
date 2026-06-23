from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "ecommerce"
    ES_HOST: str = "http://localhost:9200"
    ES_INDEX: str = "products"

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env"),
        "extra": "ignore",
    }


settings = Settings()
