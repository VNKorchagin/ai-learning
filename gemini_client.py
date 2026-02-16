"""
Клиент для работы с Gemini API (Google AI)
Новый SDK: google.genai
Документация: https://ai.google.dev/gemini-api/docs
"""
import json
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Системные промпты для разных уровней объяснения
LEVEL_PROMPTS = {
    "child": """Ты — добрый рассказчик для детей. Объясняй тему так, чтобы понял 5-летний ребёнок:
- Используй простые слова
- Приводи яркие примеры из жизни ребёнка (игрушки, животные, еда)
- Объясняй через аналогии и сравнения
- Добавь немного веселья и энтузиазма
- Максимум 200 слов""",

    "school": """Ты — школьный учитель. Объясняй тему для ученика 10-12 класса:
- Используй школьную терминологию
- Давай конкретные примеры
- Объясняй логику и связи между понятиями
- Можно использовать базовые формулы, если нужно
- 2-3 абзаца""",

    "student": """Ты — преподаватель университета. Объясняй тему для студента 2-3 курса:
- Используй профессиональную терминологию
- Раскрывай технические детали
- Объясняй принципы работы
- Приводи практические применения
- Структурированный развёрнутый ответ""",

    "expert": """Ты — эксперт в области. Дай углублённое профессиональное объяснение:
- Используй академическую и индустриальную терминологию
- Раскрывай нюансы, edge cases и компромиссы
- Упомяни современные исследования и best practices
- Обсуди ограничения и перспективы развития
- Профессиональный уровень для специалиста""",
}

LEVEL_NAMES = {
    "child": "👶 5-летний ребёнок",
    "school": "🎒 Школьник",
    "student": "🎓 Студент",
    "expert": "🔬 Эксперт",
}

# Маппинг уровней сложности к настройкам модели
LEVEL_CONFIG = {
    "child": {"temperature": 0.9, "max_tokens": 500},
    "school": {"temperature": 0.7, "max_tokens": 1000},
    "student": {"temperature": 0.6, "max_tokens": 2000},
    "expert": {"temperature": 0.5, "max_tokens": 4000},
}


class GeminiClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY не задан. Создай файл .env и добавь GEMINI_API_KEY=your_key")
        
        # Создаём клиент с API ключом
        self.client = genai.Client(api_key=self.api_key)
        
    def _get_config(self, level: str) -> types.GenerateContentConfig:
        """Создаёт конфигурацию генерации для уровня сложности."""
        config = LEVEL_CONFIG.get(level, LEVEL_CONFIG["school"])
        
        return types.GenerateContentConfig(
            temperature=config["temperature"],
            max_output_tokens=config["max_tokens"],
        )
    
    async def explain(self, topic: str, level: str) -> dict:
        """
        Отправляет запрос в Gemini API и возвращает объяснение темы.
        
        Args:
            topic: Тема для объяснения
            level: Уровень сложности (child, school, student, expert)
        
        Returns:
            dict с ответом и метаданными запроса
        """
        if level not in LEVEL_PROMPTS:
            raise ValueError(f"Неизвестный уровень: {level}. Доступные: {list(LEVEL_PROMPTS.keys())}")
        
        system_prompt = LEVEL_PROMPTS[level]
        user_prompt = f"Объясни тему: {topic}"
        
        # Формируем структуру запроса для логирования
        request_payload = {
            "model": "gemini-3-flash-preview",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "level": level,
            "generation_config": LEVEL_CONFIG[level],
        }
        
        # Формируем полный "сырой" запрос для логирования
        raw_request = {
            "model": "gemini-3-flash-preview",
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                }
            ],
            "config": {
                "temperature": LEVEL_CONFIG[level]["temperature"],
                "max_output_tokens": LEVEL_CONFIG[level]["max_tokens"],
            }
        }
        
        # Логируем сырой запрос
        print("\n" + "=" * 60)
        print("🔴 ОТПРАВКА ЗАПРОСА В GEMINI API")
        print("=" * 60)
        print(f"URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent")
        print(f"Method: POST")
        print(f"Headers: {{")
        print(f'  "Authorization": "Bearer {self.api_key[:10]}...{self.api_key[-4:]}",')
        print(f'  "Content-Type": "application/json"')
        print(f"}}")
        print("-" * 60)
        print("Body:")
        print(json.dumps(raw_request, ensure_ascii=False, indent=2))
        print("=" * 60)
        
        try:
            # Получаем конфигурацию для уровня
            config = self._get_config(level)
            
            # Формируем содержимое запроса
            contents = f"{system_prompt}\n\n{user_prompt}"
            
            # Отправляем запрос (синхронно, т.к. новый SDK не требует async для generate_content)
            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=contents,
                config=config,
            )
            
            explanation = response.text
            
            # Извлекаем информацию об использовании токенов
            usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
            
            # Формируем структуру ответа для логирования
            response_data = {
                "text": explanation[:500] + "..." if len(explanation) > 500 else explanation,
                "prompt_token_count": usage_metadata.prompt_token_count if usage_metadata else 0,
                "candidates_token_count": usage_metadata.candidates_token_count if usage_metadata else 0,
                "total_token_count": usage_metadata.total_token_count if usage_metadata else 0,
            }
            
            # Формируем полный "сырой" ответ для логирования
            raw_response = {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [{"text": explanation}]
                        },
                        "finish_reason": "STOP",
                    }
                ],
                "usage_metadata": {
                    "prompt_token_count": response_data["prompt_token_count"],
                    "candidates_token_count": response_data["candidates_token_count"],
                    "total_token_count": response_data["total_token_count"],
                },
                "model": "gemini-3-flash-preview",
            }
            
            # Логируем сырой ответ
            print("\n" + "=" * 60)
            print("🟢 ПОЛУЧЕН ОТВЕТ ОТ GEMINI API")
            print("=" * 60)
            print(json.dumps(raw_response, ensure_ascii=False, indent=2))
            print("=" * 60 + "\n")
            
            return {
                "success": True,
                "explanation": explanation,
                "topic": topic,
                "level": level,
                "level_name": LEVEL_NAMES.get(level),
                "model": "gemini-3-flash-preview",
                "usage": {
                    "prompt_tokens": response_data["prompt_token_count"],
                    "completion_tokens": response_data["candidates_token_count"],
                    "total_tokens": response_data["total_token_count"],
                },
                "raw_request": request_payload,
                "raw_response": response_data,
            }
            
        except Exception as e:
            print(f"\n❌ Ошибка Gemini API: {e}")
            raise
    
    async def stream_explain(self, topic: str, level: str) -> AsyncGenerator[str, None]:
        """
        Стриминговая версия для получения ответа по частям.
        """
        if level not in LEVEL_PROMPTS:
            raise ValueError(f"Неизвестный уровень: {level}")
        
        system_prompt = LEVEL_PROMPTS[level]
        user_prompt = f"Объясни тему: {topic}"
        
        print(f"\n[STREAM] Запрос: тема='{topic}', уровень='{level}'\n")
        
        config = self._get_config(level)
        contents = f"{system_prompt}\n\n{user_prompt}"
        
        # Стриминговый запрос
        for chunk in self.client.models.generate_content_stream(
            model="gemini-3-flash-preview",
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
