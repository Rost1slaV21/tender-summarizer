import os
import fitz  # PyMuPDF
from openai import AsyncOpenAI
from app.schemas import TenderSummary

# Инициализируем клиент. Он автоматически подтянет OPENAI_API_KEY из среды.
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "your-key-here"),
    base_url=os-getenv("OPENAI_BASE_URL", "https://openai.com")
)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Извлекает текст из PDF-файла."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    
    # Ограничиваем текст первыми ~15000 символов, чтобы не выйти за контекстное окно
    # и не тратить лишние токены на тестовом задании.
    return text[:15000]

async def analyze_tender_text(text: str) -> TenderSummary:
    """Отправляет текст в LLM и возвращает валидированный Pydantic-объект."""
    
    prompt = (
        "Ты — профессиональный юрист и эксперт по государственным закупкам. "
        "Проанализируй текст тендерной документации и извлеки из него ключевые параметры. "
        "Ты должен вернуть ответ СТРОГО в формате JSON, соответствующем схеме.\n"
        f"Текст тендера:\n{text}"
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",  # Самый дешевый и быстрый вариант
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs strict JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}  # Гарантирует, что на выходе будет JSON
    )

    raw_json = response.choices.message.content
    
    # Валидируем полученный от LLM сырой JSON через нашу Pydantic модель
    return TenderSummary.model_validate_json(raw_json)
