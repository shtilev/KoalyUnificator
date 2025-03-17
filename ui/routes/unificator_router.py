from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from db.get_db_session import get_db
from sqlalchemy.orm import Session
from core.unificator import get_unification_name
import faiss
from transformers import AutoTokenizer, AutoModel
import torch
import os
from db.get_db_session import get_db
from sqlalchemy.orm import Session
import json


router = APIRouter()
templates = Jinja2Templates(directory="ui/templates")


class EmbeddingModel:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.squeeze().numpy()


embedder = EmbeddingModel()

# ==== Завантаження індексу ====
INDEX_FILE = "models/index.faiss"
MAPPING_FILE = "models/mapping.json"

if not os.path.exists(INDEX_FILE) or not os.path.exists(MAPPING_FILE):
    raise FileNotFoundError("❌ Індекс або мапінг не знайдено!")

# Завантажуємо індекс
index = faiss.read_index(INDEX_FILE)
print(f"✅ Індекс завантажено з файлу: {INDEX_FILE}")

# Завантажуємо мапінг
with open(MAPPING_FILE, "r", encoding="utf-8") as f:
    text_to_label = json.load(f)
text_to_label = {int(k): v for k, v in text_to_label.items()}
print(f"✅ Мапінг завантажено з файлу: {MAPPING_FILE}")


@router.get("/unificator", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("unificator.html", {"request": request})



@router.post("/unificator", response_class=HTMLResponse)
async def process_unification_name(
        request: Request,
        db: Session = Depends(get_db),
        synonym: str = Form(...),
        threshold: float = Form(...),

):
    try:
        # Перевірка порогу схожості, якщо потрібно
        if not (0 <= threshold <= 100):
            raise HTTPException(status_code=400, detail="Поріг повинен бути між 0 і 100.")

        # Отримання результату функції уніфікації
        result = get_unification_name(db, synonym, threshold)

        # Повертаємо результат у шаблон
        return templates.TemplateResponse(
            "unificator.html",
            {"request": request, "result": result}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unificator_faiss", response_class=HTMLResponse)
async def search_faiss(
    request: Request,
    query: str = Form(...)
):
    try:
        query_vector = embedder.get_embedding(query).astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_vector)

        distances, indices = index.search(query_vector, 1)

        closest_index = int(indices[0][0])
        confidence = float(distances[0][0])

        if confidence > 0.7:
            result = text_to_label.get(closest_index, "Невідомий аналіз")
        else:
            result = "Невідомий аналіз"

        faiss_result = {"result": result, "confidence": confidence}

        return templates.TemplateResponse(
            "unificator.html",
            {"request": request, "faiss_result": faiss_result}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
