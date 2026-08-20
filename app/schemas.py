from pydantic import BaseModel, Field

class TenderSummary(BaseModel):
    contract_amount: str = Field(
        description="Полная сумма контракта. Если сумма не найдена, написать 'Не указана'."
    )
    deadlines: str = Field(
        description="Сроки выполнения работ или дата окончания контракта."
    )
    requirements: list[str] = Field(
        description="Список ключевых требований к исполнителю (опыт, лицензии, стек)."
    )
    penalties: list[str] = Field(
        description="Список штрафов, пеней и санкций за нарушение условий контракта."
    )
