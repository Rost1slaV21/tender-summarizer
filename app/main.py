from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse
from app.schemas import TenderSummary
from app.services import extract_text_from_pdf, analyze_tender_text

app = FastAPI(
    title="Умный суммаризатор тендеров",
    description="API для автоматического анализа PDF-документации госзакупок с помощью ИИ",
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>AI Tender Summarizer</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 50px auto; padding: 0 20px; background: #f5f5f7; color: #1d1d1f; }
            h1 { text-align: center; color: #0071e3; }
            .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; }
            form { display: flex; flex-direction: column; align-items: center; gap: 15px; }
            input[type="file"] { border: 2px dashed #0071e3; padding: 20px; width: 100%; box-sizing: border-box; border-radius: 8px; text-align: center; background: #f0f7ff; cursor: pointer; }
            button { background: #0071e3; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 8px; cursor: pointer; transition: background 0.2s; width: 100%; }
            button:hover { background: #005bb5; }
            pre { background: #1e1e1e; color: #7ec699; padding: 20px; border-radius: 8px; overflow-x: auto; font-size: 14px; white-space: pre-wrap; word-wrap: break-word; }
            .loading { display: none; color: #86868b; text-align: center; font-style: italic; margin-top: 15px; }
        </style>
    </head>
    <body>
        <h1>📄 Умный суммаризатор тендеров</h1>
        <div class="card">
            <form id="uploadForm">
                <input type="file" name="file" accept=".pdf" required>
                <button type="submit">Анализировать контракт</button>
            </form>
            <div id="loadingText" class="loading">🤖 ИИ анализирует документ... Пожалуйста, подождите (локальная обработка может занять некоторое время).</div>
        </div>
        
        <div class="card" id="resultCard" style="display: none;">
            <h3>Результат анализа:</h3>
            <pre id="jsonResult"></pre>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const loadingText = document.getElementById('loadingText');
                const resultCard = document.getElementById('resultCard');
                const jsonResult = document.getElementById('jsonResult');
                
                loadingText.style.display = 'block';
                resultCard.style.display = 'none';
                
                try {
                    const response = await fetch('/api/v1/summarize', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        jsonResult.textContent = JSON.stringify(data, null, 2);
                    } else {
                        jsonResult.textContent = JSON.stringify({ error: data.detail || 'Ошибка сервера' }, null, 2);
                    }
                } catch (err) {
                    jsonResult.textContent = JSON.stringify({ error: 'Не удалось связаться с сервером' }, null, 2);
                } finally {
                    loadingText.style.display = 'none';
                    resultCard.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """

@app.post(
    "/api/v1/summarize", 
    response_model=TenderSummary, 
    status_code=status.HTTP_200_OK,
    summary="Анализ PDF-тендера"
)
async def summarize_tender(file: UploadFile = File(...)):
    """
    Принимает на вход PDF-файл тендерной документации,
    извлекает текст и с помощью LLM делает краткую выжимку.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Разрешено загружать только файлы с расширением .pdf"
        )
    
    try:
        file_bytes = await file.read()
        
        # Извлекаем текст
        tender_text = extract_text_from_pdf(file_bytes)
        
        if not tender_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Не удалось извлечь текст из PDF. Возможно, файл содержит только изображения."
            )
            
        # Запрашиваем аналитику у LLM
        summary = await analyze_tender_text(tender_text)
        return summary
        
    except Exception as e:
        # В реальном продакшене здесь должно быть логирование (loguru/logging)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при обработке ИИ: {str(e)}"
        )