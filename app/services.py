import os
import fitz  # PyMuPDF
from openai import AsyncOpenAI
from app.schemas import TenderSummary

# Инициализируем клиент. Он автоматически подтянет OPENAI_API_KEY из среды.
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Извлекает весь текст из PDF-файла без ограничений по объему."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    
    return text

async def analyze_tender_text(text: str) -> TenderSummary:
    """Отправляет текст в LLM и возвращает валидированный Pydantic-объект."""
    
    prompt = (
        "Ты — профессиональный юрист. Проанализируй текст тендера и извлеки параметры.\n"
        "Ты обязан вернуть ответ СТРОГО в формате JSON с четырьмя ключами. "
        "НЕ придумывай свои разделы (section_1, point_1 и т.д.). Использовать только эти 4 ключа!\n\n"
        "СТРУКТУРА ОТВЕТА (ШАБЛОН JSON):\n"
        "{\n"
        '  "contract_amount": "строка с суммой",\n'
        '  "deadlines": "строка со сроками",\n'
        '  "requirements": ["требование 1", "требование 2"],\n'
        '  "penalties": ["штраф 1", "штраф 2"]\n'
        "}\n\n"
        f"ТЕКСТ ТЕНДЕРА ДЛЯ АНАЛИЗА:\n{text}"
    )

    response = await client.chat.completions.create(
        model="llama3",  
        messages=[
            {"role": "system", "content": "You are a data extraction tool. You must ONLY output a flat JSON matching the requested keys. Do not chat or add nested blocks."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}  
    )

    raw_json = response.choices[0].message.content
    
    # Валидируем полученный от LLM сырой JSON через нашу Pydantic модель
    return TenderSummary.model_validate_json(raw_json)
