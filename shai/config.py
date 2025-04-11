import os
from functools import cached_property

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def env_import(key: str):
    """
    Import a specific environment variable.
    """
    var = os.getenv(key)
    if not var:
        raise ValueError(f"{key} must be provided.")
    return var


class Config:
    """
    Configuration class to access environment variables.
    """

    @cached_property
    def api_key(self) -> str:
        return env_import("API_KEY")

    @cached_property
    def base_url(self) -> str:
        return env_import("BASE_URL")

    @cached_property
    def model(self) -> str:
        return env_import("MODEL")
