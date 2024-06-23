from typing import Any

from src.config import (
    api_key_currency,
    api_key_stocks,
    date,
    input_data_reports,
    input_date_str,
    limit,
    month,
    search,
    search_reports,
    transactions,
    transactions_reports,
    user_settings,
    year,
)
from src.reports import page_reports
from src.services import page_services
from src.views import web_page_event, web_page_event_dop, web_page_home


def main() -> Any:
    # Главная страница
    print("\nГЛАВНАЯ\n")
    print(web_page_home(input_date_str, user_settings, api_key_currency, api_key_stocks))
    # Событие страница
    print("\nСОБЫТИЕ\n")
    print(web_page_event(input_date_str))
    print(web_page_event_dop(user_settings, api_key_currency, api_key_stocks))
    # Cтраница сервиса
    print("\nСЕРВИСЫ\n")
    print(page_services(transactions, year, month, limit, search, date))
    # Страница отчета
    print("\nОТЧЕТЫ\n")
    print(page_reports(transactions_reports, search_reports, input_data_reports))


if __name__ == "__main__":
    main()
