"""
AI-Объяснялка - FastAPI сервер (Gemini версия)

Запуск:
    uvicorn main:app --reload

API endpoints:
    POST /api/explain      - Получить объяснение темы
    GET  /api/levels       - Список доступных уровней
    GET  /                 - Главная страница

Получить API ключ: https://aistudio.google.com/app/apikey
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from gemini_client import GeminiClient, LEVEL_NAMES

app = FastAPI(
    title="AI-Объяснялка",
    description="Объясняем сложные темы простым языком с помощью Gemini AI",
    version="2.0.0",
)

# Подключаем статические файлы (фронтенд)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============ Pydantic модели ============

class ExplainRequest(BaseModel):
    topic: str
    level: str = "child"  # child, school, student, expert


class ExplainResponse(BaseModel):
    success: bool
    explanation: str
    topic: str
    level: str
    level_name: str
    model: str | None
    usage: dict


class LevelsResponse(BaseModel):
    levels: list[dict]


# ============ API Endpoints ============

@app.get("/")
async def root():
    """Главная страница - отдаём index.html"""
    return FileResponse("static/index.html")


@app.get("/api/levels", response_model=LevelsResponse)
async def get_levels():
    """Получить список доступных уровней объяснения"""
    return {
        "levels": [
            {"id": key, "name": name}
            for key, name in LEVEL_NAMES.items()
        ]
    }


@app.post("/api/explain", response_model=ExplainResponse)
async def explain_topic(request: ExplainRequest):
    """
    Отправить запрос в Gemini API и получить объяснение темы.
    
    Параметры:
        - topic: Тема для объяснения (например, "блокчейн")
        - level: Уровень сложности (child/school/student/expert)
    """
    if not request.topic or len(request.topic.strip()) < 2:
        raise HTTPException(status_code=400, detail="Тема слишком короткая")
    
    if request.level not in LEVEL_NAMES:
        raise HTTPException(
            status_code=400, 
            detail=f"Неизвестный уровень. Доступные: {list(LEVEL_NAMES.keys())}"
        )
    
    try:
        client = GeminiClient()
        result = await client.explain(request.topic.strip(), request.level)
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка API: {str(e)}")


# ============ Дополнительные endpoints для отладки ============

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "ok", "service": "ai-explainer", "provider": "gemini"}


# ============ Запуск ============

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Запуск AI-Объяснялки (Gemini версия)...")
    print("📖 Открой в браузере: http://localhost:8000")
    print("📚 API документация: http://localhost:8000/docs")
    print("")
    print("⚠️  Не забудь создать .env с GEMINI_API_KEY!")
    print("   Получить ключ: https://aistudio.google.com/app/apikey")
    print("")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
