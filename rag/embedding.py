import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")


def embed_texts(texts: list[str]) -> list[list[float]]:
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    response = requests.post(
        HF_API_URL,
        headers=headers,
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()