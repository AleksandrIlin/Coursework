import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests_mock
from src.utils import (
    filter_transactions_by_date,
    final_processing,
    get_cards_info,
    get_exchange_rates,
    get_greeting,
    get_read_excel,
    get_stocks_cost,
    get_top_5_transactions,
    process_expenses_and_income,
    process_income,
)


def test_get_data_from_xlsx() -> None:
    test_data = [
        {
            "Дата операции": "01.06.2023 12:00:00",
            "Сумма операции": "-100.50",
            "Категория": "Покупки",
            "Описание": "Магазин",
        },
        {
            "Дата операции": "15.06.2023 18:30:00",
            "Сумма операции": "-250.00",
            "Категория": "Ресторан",
            "Описание": "Ужин",
        },
    ]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path_tests = os.path.join(current_dir, "../data", "operations.json")

    df = pd.DataFrame(test_data)

    with patch("pandas.read_excel", return_value=df):
        result = get_read_excel(file_path_tests)
        assert result == test_data


@pytest.fixture
def test_transactions() -> list:
    return [
        {
            "Дата операции": "01.06.2023 12:00:00",
            "Сумма операции": "-100.50",
            "Категория": "Покупки",
            "Описание": "Магазин",
        },
        {
            "Дата операции": "15.06.2023 18:30:00",
            "Сумма операции": "-250.00",
            "Категория": "Ресторан",
            "Описание": "Ужин",
        },
        {
            "Дата операции": "20.06.2023 10:00:00",
            "Сумма операции": "-75.00",
            "Категория": "Транспорт",
            "Описание": "Такси",
        },
        {
            "Дата операции": "05.05.2023 08:15:00",
            "Сумма операции": "-500.00",
            "Категория": "Медицина",
            "Описание": "Аптека",
        },
        {
            "Дата операции": "25.05.2023 14:45:00",
            "Сумма операции": "-120.00",
            "Категория": "Покупки",
            "Описание": "Одежда",
        },
    ]


@pytest.mark.parametrize(
    "input_date_str, expected_result",
    [
        (
            "20.06.2023",
            [
                {
                    "Дата операции": "01.06.2023 12:00:00",
                    "Сумма операции": "-100.50",
                    "Категория": "Покупки",
                    "Описание": "Магазин",
                },
                {
                    "Дата операции": "15.06.2023 18:30:00",
                    "Сумма операции": "-250.00",
                    "Категория": "Ресторан",
                    "Описание": "Ужин",
                },
                {
                    "Дата операции": "20.06.2023 10:00:00",
                    "Сумма операции": "-75.00",
                    "Категория": "Транспорт",
                    "Описание": "Такси",
                },
            ],
        ),
        (
            "15.05.2023",
            [
                {
                    "Дата операции": "05.05.2023 08:15:00",
                    "Сумма операции": "-500.00",
                    "Категория": "Медицина",
                    "Описание": "Аптека",
                },
            ],
        ),
    ],
)
def test_filter_transactions_by_date(test_transactions: list, input_date_str: str, expected_result: list) -> None:
    result = filter_transactions_by_date(test_transactions, input_date_str)
    assert result == expected_result


@patch("src.utils.datetime")
@pytest.mark.parametrize(
    "current_hour, expected_greeting",
    [
        (7, "Доброе утро"),
        (13, "Добрый день"),
        (19, "Добрый вечер"),
        (2, "Доброй ночи"),
    ],
)
def test_greeting(mock_datetime: MagicMock, current_hour: int, expected_greeting: str) -> None:
    mock_now = datetime(2023, 6, 20, current_hour, 0, 0)
    mock_datetime.now.return_value = mock_now
    result = get_greeting()
    assert result == expected_greeting


def test_get_cards_data_empty() -> None:
    transactions: list = []
    expected_result: list = []
    assert get_cards_info(transactions) == expected_result


def test_get_cards_data_single_transaction() -> None:
    transactions = [{"Номер карты": "1234", "Сумма операции": "-100.0", "Кэшбэк": "1.0", "Категория": "Продукты"}]
    expected_result = [{"last_digits": "1234", "total_spent": 100.0, "cashback": 1.0}]
    assert get_cards_info(transactions) == expected_result


def test_get_cards_data_multiple_transactions() -> None:
    transactions = [
        {"Номер карты": "1234", "Сумма операции": "-100.0", "Кэшбэк": "1.0", "Категория": "Продукты"},
        {"Номер карты": "1234", "Сумма операции": "-200.0", "Кэшбэк": "2.0", "Категория": "Продукты"},
        {"Номер карты": "5678", "Сумма операции": "-50.0", "Кэшбэк": "0.5", "Категория": "Продукты"},
    ]
    expected_result = [
        {"last_digits": "1234", "total_spent": 300.0, "cashback": 3.0},
        {"last_digits": "5678", "total_spent": 50.0, "cashback": 0.5},
    ]
    assert get_cards_info(transactions) == expected_result


def test_get_cards_data_nan_card_number() -> None:
    transactions = [
        {"Номер карты": "1234", "Сумма операции": "-100.0", "Кэшбэк": "1.0", "Категория": "Продукты"},
        {"Номер карты": "nan", "Сумма операции": "-200.0", "Кэшбэк": "2.0", "Категория": "Продукты"},
        {"Номер карты": "5678", "Сумма операции": "-50.0", "Кэшбэк": "0.5", "Категория": "Продукты"},
    ]
    expected_result = [
        {"last_digits": "1234", "total_spent": 100.0, "cashback": 1.0},
        {"last_digits": "5678", "total_spent": 50.0, "cashback": 0.5},
    ]
    assert get_cards_info(transactions) == expected_result


def test_get_cards_data_cashback() -> None:
    transactions = [
        {"Номер карты": "1234", "Сумма операции": "-100.0", "Категория": "Продукты"},
        {"Номер карты": "5678", "Сумма операции": "-50.0", "Категория": "Продукты"},
    ]
    expected_result = [
        {"last_digits": "1234", "total_spent": 100.0, "cashback": 1.0},
        {"last_digits": "5678", "total_spent": 50.0, "cashback": 0.5},
    ]
    assert get_cards_info(transactions) == expected_result


def test_get_top_5_transactions_empty() -> None:
    transactions: list = []
    expected_result: list = []
    assert get_top_5_transactions(transactions) == expected_result


def test_get_top_5_transactions_single_transaction() -> None:
    transactions = [
        {
            "Дата операции": "20.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Еда",
            "Описание": "Покупка еды",
        }
    ]
    expected_result = [{"date": "20.06.2023", "amount": "-100.0", "category": "Еда", "description": "Покупка еды"}]
    assert get_top_5_transactions(transactions) == expected_result


def test_get_top_5_transactions_multiple_transactions() -> None:
    transactions = [
        {
            "Дата операции": "20.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Еда",
            "Описание": "Покупка еды",
        },
        {
            "Дата операции": "21.06.2023 12:00:00",
            "Сумма операции": "-200.0",
            "Категория": "Транспорт",
            "Описание": "Оплата проезда",
        },
        {
            "Дата операции": "22.06.2023 12:00:00",
            "Сумма операции": "-50.0",
            "Категория": "Развлечения",
            "Описание": "Кино",
        },
        {
            "Дата операции": "23.06.2023 12:00:00",
            "Сумма операции": "-300.0",
            "Категория": "Магазины",
            "Описание": "Покупка одежды",
        },
        {
            "Дата операции": "24.06.2023 12:00:00",
            "Сумма операции": "-20.0",
            "Категория": "Кофе",
            "Описание": "Кофе на вынос",
        },
        {
            "Дата операции": "25.06.2023 12:00:00",
            "Сумма операции": "-400.0",
            "Категория": "Магазины",
            "Описание": "Покупка техники",
        },
    ]
    expected_result = [
        {"date": "25.06.2023", "amount": "-400.0", "category": "Магазины", "description": "Покупка техники"},
        {"date": "23.06.2023", "amount": "-300.0", "category": "Магазины", "description": "Покупка одежды"},
        {"date": "21.06.2023", "amount": "-200.0", "category": "Транспорт", "description": "Оплата проезда"},
        {"date": "20.06.2023", "amount": "-100.0", "category": "Еда", "description": "Покупка еды"},
        {"date": "22.06.2023", "amount": "-50.0", "category": "Развлечения", "description": "Кино"},
    ]
    assert get_top_5_transactions(transactions) == expected_result


def test_get_top_5_transactions_less_than_5() -> None:
    transactions = [
        {
            "Дата операции": "20.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Еда",
            "Описание": "Покупка еды",
        },
        {
            "Дата операции": "21.06.2023 12:00:00",
            "Сумма операции": "-200.0",
            "Категория": "Транспорт",
            "Описание": "Оплата проезда",
        },
    ]
    expected_result = [
        {"date": "21.06.2023", "amount": "-200.0", "category": "Транспорт", "description": "Оплата проезда"},
        {"date": "20.06.2023", "amount": "-100.0", "category": "Еда", "description": "Покупка еды"},
    ]
    assert get_top_5_transactions(transactions) == expected_result


def test_get_top_5_transactions_with_equal_amounts() -> None:
    transactions = [
        {
            "Дата операции": "20.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Еда",
            "Описание": "Покупка еды",
        },
        {
            "Дата операции": "21.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Транспорт",
            "Описание": "Оплата проезда",
        },
        {
            "Дата операции": "22.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Развлечения",
            "Описание": "Кино",
        },
        {
            "Дата операции": "23.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Магазины",
            "Описание": "Покупка одежды",
        },
        {
            "Дата операции": "24.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Кофе",
            "Описание": "Кофе на вынос",
        },
        {
            "Дата операции": "25.06.2023 12:00:00",
            "Сумма операции": "-100.0",
            "Категория": "Магазины",
            "Описание": "Покупка техники",
        },
    ]
    expected_result = [
        {"date": "20.06.2023", "amount": "-100.0", "category": "Еда", "description": "Покупка еды"},
        {"date": "21.06.2023", "amount": "-100.0", "category": "Транспорт", "description": "Оплата проезда"},
        {"date": "22.06.2023", "amount": "-100.0", "category": "Развлечения", "description": "Кино"},
        {"date": "23.06.2023", "amount": "-100.0", "category": "Магазины", "description": "Покупка одежды"},
        {"date": "24.06.2023", "amount": "-100.0", "category": "Кофе", "description": "Кофе на вынос"},
    ]
    assert get_top_5_transactions(transactions) == expected_result


@pytest.fixture
def api_key_currency() -> str:
    return "test_api_key"


def test_get_exchange_rates_success(api_key_currency: str) -> None:
    currencies = ["USD", "EUR"]
    expected_result = [{"currency": "USD", "rate": 75.0}, {"currency": "EUR", "rate": 90.0}]

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/USD",
            json={"conversion_rates": {"RUB": 75.0}},
        )
        mocker.get(
            f"https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/EUR",
            json={"conversion_rates": {"RUB": 90.0}},
        )

        assert get_exchange_rates(currencies, api_key_currency) == expected_result


def test_get_exchange_rates_partial_failure(api_key_currency: str) -> None:
    currencies = ["USD", "EUR"]
    expected_result = [{"currency": "USD", "rate": 75.0}, {"currency": "EUR", "rate": None}]

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/USD",
            json={"conversion_rates": {"RUB": 75.0}},
        )
        mocker.get(
            f"https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/EUR", status_code=404, text="Not Found"
        )

        assert get_exchange_rates(currencies, api_key_currency) == expected_result


def test_get_exchange_rates_all_failure(api_key_currency: str) -> None:
    currencies = ["USD", "EUR"]
    expected_result = [{"currency": "USD", "rate": None}, {"currency": "EUR", "rate": None}]

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/USD", status_code=500, text="Server Error"
        )
        mocker.get(
            f"https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/EUR", status_code=500, text="Server Error"
        )

        assert get_exchange_rates(currencies, api_key_currency) == expected_result


@pytest.fixture
def api_key_stocks() -> str:
    return "test_api_key"


def test_get_stocks_cost_success(api_key_stocks: str) -> None:
    companies = ["AAPL", "AMZN"]
    expected_result = [{"stock": "AAPL", "price": 150.0}, {"stock": "AMZN", "price": 3000.0}]

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=" f"{api_key_stocks}",
            json={"Time Series (Daily)": {"2023-06-19": {"4. close": "150.0"}}},
        )
        mocker.get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AMZN&apikey=" f"{api_key_stocks}",
            json={"Time Series (Daily)": {"2023-06-19": {"4. close": "3000.0"}}},
        )

        assert get_stocks_cost(companies, api_key_stocks) == expected_result


def test_get_stocks_cost_partial_failure(api_key_stocks: str) -> None:
    companies = ["AAPL", "AMZN"]
    expected_result = [{"stock": "AAPL", "price": 150.0}, {"stock": "AMZN", "price": None}]

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=" f"{api_key_stocks}",
            json={"Time Series (Daily)": {"2023-06-19": {"4. close": "150.0"}}},
        )
        mocker.get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AMZN&apikey=" f"{api_key_stocks}",
            status_code=404,
            text="Not Found",
        )

        assert get_stocks_cost(companies, api_key_stocks) == expected_result


def test_get_stocks_cost_all_failure(api_key_stocks: str) -> None:
    companies = ["AAPL", "AMZN"]
    expected_result = [{"stock": "AAPL", "price": None}, {"stock": "AMZN", "price": None}]

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=" f"{api_key_stocks}",
            status_code=500,
            text="Server Error",
        )
        mocker.get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AMZN&apikey=" f"{api_key_stocks}",
            status_code=500,
            text="Server Error",
        )

        assert get_stocks_cost(companies, api_key_stocks) == expected_result


# Тестирование функции process_income
def test_process_income() -> None:
    df = pd.DataFrame(
        {
            "Сумма операции": [1000, 2000, 3000, -4000, -5000],
            "Категория": ["Зарплата", "Инвестиции", "Зарплата", "Покупка акций", "Прочее"],
        }
    )
    result = process_income(df)
    assert result["total_amount"] == 15000
    assert len(result["main"]) == 3
    assert result["main"][0]["Категория"] == "Зарплата"
    assert result["main"][1]["Категория"] == "Инвестиции"


def test_process_expenses_and_income() -> None:
    # Создаем тестовые данные
    data = {
        "Дата операции": ["01.06.2024 08:00:00", "15.06.2024 12:00:00", "01.07.2024 16:30:00"],
        "Дата платежа": ["01.06.2024", "15.06.2024", "01.07.2024"],
        "Сумма": [100, 200, 300],
    }
    df = pd.DataFrame(data)

    # Сохраняем данные в Excel файл
    df.to_excel("test.xlsx", index=False)

    # Проверяем функцию
    result = process_expenses_and_income("test.xlsx", "01.06.2024", "M")

    # Ожидаем, что в результате останется только одна запись из июня
    assert len(result) == 2
    assert result["Сумма"].values[0] == 100

    # Очищаем созданный тестовый файл
    os.remove("test.xlsx")


def test_final_processing() -> None:
    result_expenses = {
        "total_amount": 1100,
        "main": [{"Категория": "Продукты", "Сумма операции": 400}, {"Категория": "Прочее", "Сумма операции": 500}],
        "transfers_and_cash": [{"Категория": "Наличные", "Сумма операции": -600}],
    }
    result_income = {
        "total_amount": 15000,
        "main": [
            {"Категория": "Зарплата", "Сумма операции": 7000},
            {"Категория": "Инвестиции", "Сумма операции": 6000},
        ],
    }
    result = final_processing(result_expenses, result_income)
    assert "1100" in result
    assert "Продукты" in result
    assert "15000" in result


test_data = {
    "Дата операции": ["01.01.2022 12:00:00", "15.02.2022 08:00:00", "20.03.2022 16:30:00"],
    "Сумма": [100, 200, 150],
    "Категория": ["Еда", "Транспорт", "Еда"],
}
transactions = pd.DataFrame(test_data)
