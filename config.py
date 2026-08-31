import os

from dotenv import load_dotenv


load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")


if not GITHUB_TOKEN:
    raise ValueError(
        "GITHUB_TOKEN is not set."
    )


if not HF_TOKEN:
    raise ValueError(
        "HF_TOKEN is not set."
    )