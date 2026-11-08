import os
import tempfile
import urllib.request
import wave
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from piper import PiperVoice

app = FastAPI()

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "pt_BR-faber-medium.onnx"
CONFIG_PATH = BASE_DIR / "pt_BR-faber-medium.onnx.json"

MODEL_URL = (
    "https://huggingface.co/rhasspy/piper-voices/"
    "resolve/main/pt/pt_BR/faber/medium/"
    "pt_BR-faber-medium.onnx"
)

CONFIG_URL = MODEL_URL + ".json"

voice = None


class TextRequest(BaseModel):
    text: str


def download_file(url, destination):
    if not destination.exists():
        urllib.request.urlretrieve(url, destination)


@app.on_event("startup")
async def load_voice():
    global voice

    download_file(MODEL_URL, MODEL_PATH)
    download_file(CONFIG_URL, CONFIG_PATH)

    voice = PiperVoice.load(str(MODEL_PATH))


@app.get("/")
async def home():
    index = BASE_DIR / "index.html"

    if not index.exists():
        raise HTTPException(404, "index.html não encontrado.")

    return FileResponse(str(index))


@app.post("/api/tts")
async def generate_voice(data: TextRequest):
    text = data.text.strip()

    if not text:
        raise HTTPException(400, "Digite um texto.")

    if len(text) > 5000:
        raise HTTPException(400, "Limite de 5000 caracteres.")

    if voice is None:
        raise HTTPException(503, "A voz ainda está carregando.")

    temp = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    )

    filename = temp.name
    temp.close()

    try:
        with wave.open(filename, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)

        return FileResponse(
            filename,
            media_type="audio/wav",
            filename="narracao.wav"
        )

    except Exception as error:
        if os.path.exists(filename):
            os.remove(filename)

        raise HTTPException(
            500,
            f"Erro ao gerar narração: {str(error)}"
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
