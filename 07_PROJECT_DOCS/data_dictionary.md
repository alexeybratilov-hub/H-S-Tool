# Словарь данных, начальная версия

Документ будет пополняться по мере создания SQLite-схемы.

## Основные сущности первого контура

- companies
- company_attributes
- departments
- positions
- employees
- staffing_schedules
- staffing_schedule_rows
- job_descriptions

## Обязательные принципы

1. Все корпоративные записи должны иметь company_id.
2. Все нормативные утверждения должны иметь source_id или быть помечены как отсутствующие.
3. Выводы LLM не отображаются как факты.
4. Данные разделяются на:
   - FACT
   - DATA
   - CONCLUSION
   - RECOMMENDATION
5. При отсутствии СОУТ, ОПР, подтверждённых контингентов, норм СИЗ или медицинских периодичностей документ получает статус PRELIMINARY или REQUIRES_VERIFICATION.