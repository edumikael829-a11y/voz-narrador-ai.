import os
import tempfile
import edge_tts

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel

app = FastAPI()

VOICE = "pt-BR-AntonioNeural"

class TextRequest(BaseModel):
    text: str

@app.get("/")
async def home():
    return FileResponse("index.html")

@app.post("/api/tts")
async def generate_voice(data: TextRequest):
    text = data.text.strip()

    if not text:
        raise HTTPException(400, "Digite um texto.")

    if len(text) > 5000:
        raise HTTPException(400, "Limite de 5000 caracteres.")

    temp = tempfile.NamedTemporaryFile(
        suffix=".mp3", delete=False
    )
    filename = temp.name
    temp.close()

    try:
        communicate = edge_tts.Communicate(
            text,
            VOICE,
            rate="-5%",
            pitch="-5Hz"
        )

        await communicate.save(filename)

        return FileResponse(
            filename,
            media_type="audio/mpeg",
            filename="narracao.mp3",
            background=BackgroundTask(os.remove, filename)
        )

    except Exception:
        if os.path.exists(filename):
            os.remove(filename)

        raise HTTPException(
            500,
            "Erro ao gerar a narração."
        )
