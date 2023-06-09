import os
import secrets

from dotenv import load_dotenv

load_dotenv(verbose=True)


class EnvSettings:
    @staticmethod
    def env() -> str:
        return os.getenv("ENV", "dev")

    @staticmethod
    def flask_server_host() -> str:
        return "0.0.0.0"

    @staticmethod
    def flask_server_port() -> int:
        return 9300

    @staticmethod
    def is_production():
        return EnvSettings.env() == "prod"

    @staticmethod
    def minio_endpoint():
        return os.getenv("MINIO_ENDPOINT", None)

    @staticmethod
    def minio_secure():
        secure = os.getenv("MINIO_SECURE", "False")
        return secure.upper() != "FALSE"

    @staticmethod
    def minio_access_key():
        return os.getenv("MINIO_ACCESS_KEY", "")

    @staticmethod
    def minio_secret_key():
        return os.getenv("MINIO_SECRET_KEY", "")

    # Registry endpoint config
    @staticmethod
    def registry_endpoint():
        return os.getenv("REGISTRY_ENDPOINT", "")

    @staticmethod
    def external_url():
        return os.getenv("EXTERNAL_URL", "")

    @staticmethod
    def adapter_id():
        return os.getenv("ADAPTER_ID", "")

    # AIMMS config
    @staticmethod
    def aimms_exe_path():
        return os.getenv("AIMMS_EXE_PATH", "")

    @staticmethod
    def aimms_model_path():
        return os.getenv("AIMMS_MODEL_PATH", "")

    @staticmethod
    def aimms_procedure():
        return os.getenv("AIMMS_PROCEDURE", "")

    # TEACOS config
    @staticmethod
    def teacos_API_url():
        return os.getenv("TEACOS_API_URL", "")

    @staticmethod
    def teacos_user():
        return os.getenv("TEACOS_USER", "")

    @staticmethod
    def teacos_pw():
        return os.getenv("TEACOS_PASSWORD", "")

    @staticmethod
    def teacos_env():
        return os.getenv("TEACOS_ENV", "")

    @staticmethod
    def db_host():
        return os.getenv("DATABASE_HOST", "")

    @staticmethod
    def db_name():
        return os.getenv("DATABASE_NAME", "")

    @staticmethod
    def db_user():
        return os.getenv("DATABASE_USER", "")

    @staticmethod
    def db_password():
        return os.getenv("DATABASE_PASSWORD", "")


class Config(object):
    """Generic config for all environments."""

    SECRET_KEY = secrets.token_urlsafe(16)

    API_TITLE = "MMvIB AIMMS Adapter REST API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/openapi"
    OPENAPI_SWAGGER_UI_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_URL = (
        "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )

    API_SPEC_OPTIONS = {
        "info": {
            "description": "This REST API allows to orchestrate an AIMMS-based model",
            "termsOfService": "https://www.tno.nl",
            "contact": {"email": "ewoud.werkman@tno.nl"},
            "license": {"name": "TBD", "url": "https://www.tno.nl"},
        }
    }


class ProdConfig(Config):
    ENV = "prod"
    DEBUG = False
    FLASK_DEBUG = False


class DevConfig(Config):
    ENV = "dev"
    DEBUG = True
    FLASK_DEBUG = True
