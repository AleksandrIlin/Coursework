from typing import Any

from src.utils import spending_by_category, spending_by_weekday, spending_by_workday


def page_reports(transactions_reports: Any, search_reports: Any, input_data_reports: Any) -> Any:
    spending_by_category_result = spending_by_category(transactions_reports, search_reports, input_data_reports)
    spending_by_weekday_result = spending_by_weekday(transactions_reports, input_data_reports)
    spending_by_workday_result = spending_by_workday(transactions_reports, input_data_reports)
    print(spending_by_category_result)
    print(spending_by_weekday_result)
    print(spending_by_workday_result)
