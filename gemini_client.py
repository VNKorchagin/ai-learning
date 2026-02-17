"""
Клиент для работы с Gemini API (Google AI)
Новый SDK: google.genai
Документация: https://ai.google.dev/gemini-api/docs
"""
import asyncio
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

# Маппинг уровней сложности к температуре
LEVEL_TEMPERATURE = {
    "child": 0.9,
    "school": 0.7,
    "student": 0.6,
    "expert": 0.5,
}


class GeminiClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY не задан. Создай файл .env и добавь GEMINI_API_KEY=your_key")
        
        # Создаём клиент с API ключом
        self.client = genai.Client(api_key=self.api_key)
        
    def _build_system_prompt(self, level: str, format_description: str, explicit_stop: bool, stop_sequence: str) -> str:
        """Собирает полный системный промпт с учётом настроек."""
        parts = [LEVEL_PROMPTS[level]]
        
        # Добавляем описание формата, если есть
        if format_description:
            parts.append(f"\n\nДополнительные требования к формату ответа:\n{format_description}")
        
        # Добавляем явную инструкцию о завершении
        if explicit_stop:
            if stop_sequence:
                parts.append(f"\n\nВАЖНО: Закончи свой ответ фразой \"{stop_sequence}\".")
            else:
                parts.append("\n\nВАЖНО: Закончи свой ответ чётко и полностью. Не обрывай мысль на полуслове.")
        
        return "\n".join(parts)
    
    def _get_config(self, level: str, max_tokens: int, stop_sequence: str) -> types.GenerateContentConfig:
        """Создаёт конфигурацию генерации."""
        temperature = LEVEL_TEMPERATURE.get(level, 0.7)
        
        # Формируем список стоп-последовательностей
        stop_sequences = []
        if stop_sequence:
            stop_sequences.append(stop_sequence)
        
        return types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            stop_sequences=stop_sequences if stop_sequences else None,
        )
    
    async def explain(
        self, 
        topic: str, 
        level: str,
        format_description: str = "",
        max_tokens: int = 2000,
        stop_sequence: str = "",
        explicit_stop: bool = True,
    ) -> dict:
        """
        Отправляет запрос в Gemini API и возвращает объяснение темы.
        
        Args:
            topic: Тема для объяснения
            level: Уровень сложности (child, school, student, expert)
            format_description: Дополнительное описание формата ответа
            max_tokens: Максимальное количество токенов
            stop_sequence: Стоп-слово для остановки генерации
            explicit_stop: Добавить явную инструкцию о завершении
        
        Returns:
            dict с ответом и метаданными запроса
        """
        if level not in LEVEL_PROMPTS:
            raise ValueError(f"Неизвестный уровень: {level}. Доступные: {list(LEVEL_PROMPTS.keys())}")
        
        # Собираем системный промпт
        system_prompt = self._build_system_prompt(level, format_description, explicit_stop, stop_sequence)
        user_prompt = f"Объясни тему: {topic}"
        
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
                "temperature": LEVEL_TEMPERATURE.get(level, 0.7),
                "max_output_tokens": max_tokens,
                "stop_sequences": [stop_sequence] if stop_sequence else [],
            }
        }
        
        # Формируем метаданные настроек для ответа
        settings = {
            "format_description": format_description,
            "max_tokens": max_tokens,
            "stop_sequence": stop_sequence,
            "explicit_stop": explicit_stop,
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
            # Получаем конфигурацию
            config = self._get_config(level, max_tokens, stop_sequence)
            
            # Формируем содержимое запроса
            contents = f"{system_prompt}\n\n{user_prompt}"
            
            # Отправляем запрос (в отдельном потоке, чтобы не блокировать event loop)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-3-flash-preview",
                contents=contents,
                config=config,
            )
            
            explanation = response.text
            
            # Убираем стоп-последовательность из ответа, если она есть
            if stop_sequence and explanation.endswith(stop_sequence):
                explanation = explanation[:-len(stop_sequence)].rstrip()
            
            # Извлекаем информацию об использовании токенов
            usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
            
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
                    "prompt_token_count": usage_metadata.prompt_token_count if usage_metadata else 0,
                    "candidates_token_count": usage_metadata.candidates_token_count if usage_metadata else 0,
                    "total_token_count": usage_metadata.total_token_count if usage_metadata else 0,
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
                    "prompt_tokens": raw_response["usage_metadata"]["prompt_token_count"],
                    "completion_tokens": raw_response["usage_metadata"]["candidates_token_count"],
                    "total_tokens": raw_response["usage_metadata"]["total_token_count"],
                },
                "settings": settings,
                "raw_request": raw_request,
                "raw_response": raw_response,
            }
            
        except Exception as e:
            print(f"\n❌ Ошибка Gemini API: {e}")
            raise
    
    async def stream_explain(
        self, 
        topic: str, 
        level: str,
        format_description: str = "",
        max_tokens: int = 2000,
        stop_sequence: str = "",
        explicit_stop: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Стриминговая версия для получения ответа по частям.
        """
        if level not in LEVEL_PROMPTS:
            raise ValueError(f"Неизвестный уровень: {level}")
        
        system_prompt = self._build_system_prompt(level, format_description, explicit_stop, stop_sequence)
        user_prompt = f"Объясни тему: {topic}"
        
        print(f"\n[STREAM] Запрос: тема='{topic}', уровень='{level}'\n")
        
        config = self._get_config(level, max_tokens, stop_sequence)
        contents = f"{system_prompt}\n\n{user_prompt}"
        
        # Стриминговый запрос в отдельном потоке
        queue = asyncio.Queue()
        
        def generate_stream():
            try:
                for chunk in self.client.models.generate_content_stream(
                    model="gemini-3-flash-preview",
                    contents=contents,
                    config=config,
                ):
                    if chunk.text:
                        asyncio.run_coroutine_threadsafe(queue.put(chunk.text), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)
        
        loop = asyncio.get_event_loop()
        
        # Запускаем генерацию в отдельном потоке
        import threading
        thread = threading.Thread(target=generate_stream)
        thread.start()
        
        # Читаем chunks из очереди
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
        
        thread.join()
