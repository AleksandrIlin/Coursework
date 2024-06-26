import functools
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd
from src.logger import logger_setup

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path_log = os.path.join(current_dir, "../logs", "reports.log")
logger = logger_setup("reports", file_path_log)


# Страница отчеты
def report_to_file_default(func: Any) -> Any:
    """Записывает в файл результат, который возвращает функция, формирующая отчет."""

    @functools.wraps(func)
    def wrapper(*args: tuple, **kwargs: dict) -> Any:
        result = func(*args, **kwargs)
        with open("function_operation_report.txt", "w") as file:
            file.write(str(result))
        logger.info(f"Записан результат работы функции {func}")
        return result

    return wrapper


def report_to_file(filename: str = "function_operation_report.txt") -> Any:
    """Записывает в переданный файл результат, который возвращает функция, формирующая отчет."""

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        def wrapper(*args: tuple, **kwargs: dict) -> Any:
            result = func(*args, **kwargs)
            with open(filename, "w") as file:
                file.write(str(result))
            logger.info(f"Записан результат работы функции {func} в файл {filename}")
            return result

        return wrapper

    return decorator


# дата гггг.мм.дд
@report_to_file_default
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str | datetime] = None) -> str:
    """Функция возвращает траты по заданной категории за последние три месяца
    (от переданной даты, если дата не передана берет текущую)"""
    try:
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, "%Y.%m.%d")
        start_date = date - timedelta(days=date.day - 1) - timedelta(days=3 * 30)
        filtered_transactions = transactions[
            (transactions["Дата операции"] >= start_date)
            & (transactions["Дата операции"] <= date)
            & (transactions["Категория"] == category)
        ]
        result = filtered_transactions.to_dict(orient="records")
        for record in result:
            record["Дата операции"] = record["Дата операции"].strftime("%d.%m.%Y %H:%M:%S")
        formatted_result = json.dumps(result, ensure_ascii=False, indent=4)
        return formatted_result
    except Exception as e:
        print(f"Возникла ошибка {e}")

        return ""


@report_to_file_default
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str | datetime] = None) -> str:
    """Функция возвращает средние траты в каждый из дней недели за последние три месяца (от переданной даты)"""
    try:
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, "%Y.%m.%d")
        start_date: datetime = date - timedelta(days=date.day) - timedelta(days=3 * 30)
        filtered_transactions = transactions[
            (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= date)
        ]
        filtered_transactions = filtered_transactions.copy()
        filtered_transactions.loc[:, "День недели"] = filtered_transactions["Дата операции"].dt.dayofweek
        grouped_transactions = filtered_transactions.groupby("День недели")["Сумма операции"].mean()
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        grouped_transactions.index = weekdays
        result_dict = {day: grouped_transactions.get(day, 0.0) for day in weekdays}
        logger.info(f"Средние траты по дням недели начиная с {date}")
        return json.dumps(result_dict, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return ""


@report_to_file_default
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str | datetime] = None) -> Any:
    """Функция выводит средние траты в рабочий и в выходной день за последние три месяца (от переданной даты)."""
    try:
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, "%Y.%m.%d")
        weekend_days = [5, 6]
        start_date: str | datetime = date - timedelta(days=date.day) - timedelta(days=3 * 30)
        filtered_transactions = transactions[
            (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= date)
        ]
        filtered_transactions = filtered_transactions.copy()
        filtered_transactions["День недели"] = filtered_transactions["Дата операции"].dt.dayofweek
        filtered_transactions["Тип дня"] = "Рабочий"
        filtered_transactions.loc[filtered_transactions["День недели"].isin(weekend_days), "Тип дня"] = "Выходной"
        grouped_transactions = filtered_transactions.groupby("Тип дня")["Сумма операции"].mean()
        logger.info(f"средние траты за последние три месяца от {date} по рабочим и выходным дням")
        return json.dumps(grouped_transactions.to_dict(), ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return ""
