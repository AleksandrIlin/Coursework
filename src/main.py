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
from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import (
    analyze_cashback,
    find_person_to_person_transactions,
    investment_bank,
    search_transaction_by_mobile_phone,
    search_transactions_by_user_choice,
)
from src.views import web_page_event, web_page_event_dop, web_page_home


def main() -> Any:
    """Функция для запуска всего проекта"""
    # Главная страница
    print("\nГЛАВНАЯ\n")
    print(web_page_home(input_date_str, user_settings, api_key_currency, api_key_stocks))

    # Событие страница
    print("\nСОБЫТИЕ\n")
    print(web_page_event(input_date_str))
    print(web_page_event_dop(user_settings, api_key_currency, api_key_stocks))

    # Cтраница сервиса
    print("\nСЕРВИСЫ\n")
    cashback_analysis_result = analyze_cashback(transactions, year, month)
    investment_bank_result = investment_bank(transactions, date, limit)
    search_transactions_by_user_choice_result = search_transactions_by_user_choice(transactions, search)
    search_transaction_by_mobile_phone_result = search_transaction_by_mobile_phone(transactions)
    find_person_to_person_transactions_result = find_person_to_person_transactions(transactions)
    print(cashback_analysis_result)
    print(investment_bank_result)
    print(search_transactions_by_user_choice_result)
    print(search_transaction_by_mobile_phone_result)
    print(find_person_to_person_transactions_result)

    # Страница отчета
    print("\nОТЧЕТЫ\n")
    spending_by_category_result = spending_by_category(transactions_reports, search_reports, input_data_reports)
    spending_by_weekday_result = spending_by_weekday(transactions_reports, input_data_reports)
    spending_by_workday_result = spending_by_workday(transactions_reports, input_data_reports)
    print(spending_by_category_result)
    print(spending_by_weekday_result)
    print(spending_by_workday_result)


if __name__ == "__main__":
    main()
