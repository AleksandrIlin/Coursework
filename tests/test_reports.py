import json
from datetime import datetime

import pandas as pd
from src.reports import spending_by_category, spending_by_weekday, spending_by_workday


def test_spending_by_category() -> None:
    transactions_data = {
        "Дата операции": ["01.06.2024 12:00:00", "02.06.2024 12:00:00", "15.05.2024 08:30:00", "10.05.2024 15:45:00"],
        "Категория": ["Еда", "Транспорт", "Еда", "Транспорт"],
        "Сумма": [100, 50, 80, 70],
    }
    transactions_df = pd.DataFrame(transactions_data)

    expected_result_1 = (
        "[\n"
        "    {\n"
        '        "Дата операции": "02.06.2024 12:00:00",\n'
        '        "Категория": "Транспорт",\n'
        '        "Сумма": 50\n'
        "    },\n"
        "    {\n"
        '        "Дата операции": "10.05.2024 15:45:00",\n'
        '        "Категория": "Транспорт",\n'
        '        "Сумма": 70\n'
        "    }\n"
        "]"
    )

    expected_result = (
        "[\n"
        "    {\n"
        '        "Дата операции": "01.06.2024 12:00:00",\n'
        '        "Категория": "Еда",\n'
        '        "Сумма": 100\n'
        "    },\n"
        "    {\n"
        '        "Дата операции": "15.05.2024 08:30:00",\n'
        '        "Категория": "Еда",\n'
        '        "Сумма": 80\n'
        "    }\n"
        "]"
    )

    # Тест с передачей даты
    result = spending_by_category(transactions_df, "Еда", "2024.06.30")
    assert result.strip() == expected_result.strip()

    # Тест без передачи даты
    result = spending_by_category(transactions_df, "Транспорт")
    assert result.strip() == expected_result_1.strip()

    # Тест с некорректной категорией
    result = spending_by_category(transactions_df, "Несуществующая категория")
    assert result == "[]"


def test_spending_by_weekday() -> None:
    data = {
        "Дата операции": [
            "01.06.2024 12:00:00",
            "02.06.2024 12:00:00",
            "15.05.2024 08:30:00",
            "10.05.2024 15:45:00",
            "25.04.2024 18:20:00",
            "15.04.2024 09:10:00",
            "16.04.2024 09:10:00",
        ],
        "Сумма операции": [1000, 500, 300, 700, 400, 100, 500],
    }
    transactions = pd.DataFrame(data)
    transactions["Дата операции"].apply(lambda x: datetime.strptime(x, "%d.%m.%Y %H:%M:%S").strftime("%A")).unique()
    result_current_date = spending_by_weekday(transactions)
    expected_result_current_date = {
        "Понедельник": 100.0,
        "Вторник": 500.0,
        "Среда": 300.0,
        "Четверг": 400.0,
        "Пятница": 700.0,
        "Суббота": 1000.0,
        "Воскресенье": 500.0,
    }
    assert json.loads(result_current_date) == expected_result_current_date
    result_given_date = spending_by_weekday(transactions, "2024.06.15")
    expected_result_given_date = {
        "Понедельник": 100.0,
        "Вторник": 500.0,
        "Среда": 300.0,
        "Четверг": 400.0,
        "Пятница": 700.0,
        "Суббота": 1000.0,
        "Воскресенье": 500.0,
    }
    assert json.loads(result_given_date) == expected_result_given_date


def test_spending_by_workday() -> None:
    data = {
        "Дата операции": [
            "01.06.2024 12:00:00",
            "02.06.2024 12:00:00",
            "15.05.2024 08:30:00",
            "10.05.2024 15:45:00",
            "25.04.2024 18:20:00",
            "15.04.2024 09:10:00",
            "16.04.2024 09:10:00",
        ],
        "Сумма операции": [1000, 500, 300, 700, 400, 100, 500],
    }
    transactions = pd.DataFrame(data)
    result_current_date = spending_by_workday(transactions)
    expected_result_current_date = {
        "Рабочий": 400.0,  # Средняя сумма операций по рабочим дням
        "Выходной": 750.0,  # Средняя сумма операций по выходным дням
    }
    assert json.loads(result_current_date) == expected_result_current_date

    result_given_date = spending_by_workday(transactions, "2024.06.15")  # без даты
    expected_result_given_date = {
        "Рабочий": 400.0,  # Средняя сумма операций по рабочим дням
        "Выходной": 750.0,  # Средняя сумма операций по выходным дням
    }
    assert json.loads(result_given_date) == expected_result_given_date
