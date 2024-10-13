from dotenv import load_dotenv
from pathlib import Path

from .generators import dummy_llm, abacus_api

__all__ = ["dummy_llm", "abacus_api"]

# Locate and load .env file from the root directory
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
