from fastapi import FastAPI, UploadFile, File, HTTPException, status
from app.schemas import TenderSummary
from app.services import extract_text_from_pdf, analyze_tender_text

app = FastAPI(
    title="Умный суммаризатор тендеров",
    description="API для автоматического анализа PDF-документации госзакупок с помощью ИИ",
    version="1.0.0"
)

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
