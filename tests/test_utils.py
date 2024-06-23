from datetime import datetime
from unittest.mock import patch
import os
import json

import pandas as pd
import pytest
import requests_mock

from src.utils import (filter_transactions_by_date, get_cards_info, get_read_excel, get_exchange_rates,
                       get_stocks_cost, get_top_5_transactions, get_greeting, spending_by_category, spending_by_weekday,
                       spending_by_workday, analyze_cashback, find_person_to_person_transactions, investment_bank,
                       search_transaction_by_mobile_phone, search_transactions_by_user_choice)


def test_get_data_from_xlsx():
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
def test_transactions():
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
def test_filter_transactions_by_date(test_transactions, input_date_str, expected_result):
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
def test_greeting(mock_datetime, current_hour, expected_greeting):
    mock_now = datetime(2023, 6, 20, current_hour, 0, 0)
    mock_datetime.now.return_value = mock_now
    result = get_greeting()
    assert result == expected_greeting


def test_get_cards_data_empty():
    transactions = []
    expected_result = []
    assert get_cards_info(transactions) == expected_result


def test_get_cards_data_single_transaction():
    transactions = [{"Номер карты": "1234", "Сумма операции": "-100.0", "Кэшбэк": "1.0", "Категория": "Продукты"}]
    expected_result = [{"last_digits": "1234", "total_spent": 100.0, "cashback": 1.0}]
    assert get_cards_info(transactions) == expected_result


def test_get_cards_data_multiple_transactions():
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


def test_get_cards_data_nan_card_number():
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


def test_get_cards_data_cashback():
    transactions = [
        {"Номер карты": "1234", "Сумма операции": "-100.0", "Категория": "Продукты"},
        {"Номер карты": "5678", "Сумма операции": "-50.0", "Категория": "Продукты"},
    ]
    expected_result = [
        {"last_digits": "1234", "total_spent": 100.0, "cashback": 1.0},
        {"last_digits": "5678", "total_spent": 50.0, "cashback": 0.5},
    ]
    assert get_cards_info(transactions) == expected_result


def test_get_top_5_transactions_empty():
    transactions = []
    expected_result = []
    assert get_top_5_transactions(transactions) == expected_result


def test_get_top_5_transactions_single_transaction():
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


def test_get_top_5_transactions_multiple_transactions():
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


def test_get_top_5_transactions_less_than_5():
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


def test_get_top_5_transactions_with_equal_amounts():
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
def api_key_currency():
    return "test_api_key"


def test_get_exchange_rates_success(api_key_currency):
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


def test_get_exchange_rates_partial_failure(api_key_currency):
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


def test_get_exchange_rates_all_failure(api_key_currency):
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
def api_key_stocks():
    return "test_api_key"


def test_get_stocks_cost_success(api_key_stocks):
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


def test_get_stocks_cost_partial_failure(api_key_stocks):
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


def test_get_stocks_cost_all_failure(api_key_stocks):
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


@pytest.mark.parametrize("category, date, expected_result", [
    ('Еда', None, [{'Категория': 'Еда', 'Сумма': 700},
                   {'Категория': 'Еда', 'Сумма': 500},
                   {'Категория': 'Еда', 'Сумма': 1000}]),
    ('Еда', '2024.06.15', [{'Категория': 'Еда', 'Сумма': 700},
                           {'Категория': 'Еда', 'Сумма': 500},
                           {'Категория': 'Еда', 'Сумма': 1000}])
])
def test_spending_by_category(category, date, expected_result):
    data = {
        'Дата операции': ['01.06.2024 12:00:00', '15.05.2024 08:30:00', '10.05.2024 15:45:00', '25.04.2024 18:20:00',
                          '15.04.2024 09:10:00'],
        'Категория': ['Еда', 'Еда', 'Транспорт', 'Еда', 'Транспорт'],
        'Сумма': [1000, 500, 300, 700, 400]
    }
    transactions = pd.DataFrame(data)
    result = spending_by_category(transactions, category, date)
    assert result == expected_result


def test_spending_by_weekday():
    data = {
        'Дата операции': ['01.06.2024 12:00:00', '02.06.2024 12:00:00', '15.05.2024 08:30:00', '10.05.2024 15:45:00',
                          '25.04.2024 18:20:00',
                          '15.04.2024 09:10:00', '16.04.2024 09:10:00'],
        'Сумма операции': [1000, 500, 300, 700, 400, 100, 500]
    }
    transactions = pd.DataFrame(data)
    transactions['Дата операции'].apply(
        lambda x: datetime.strptime(x, '%d.%m.%Y %H:%M:%S').strftime('%A')).unique()
    result_current_date = spending_by_weekday(transactions)
    expected_result_current_date = {
        "Понедельник": 100.0,
        "Вторник": 500.0,
        "Среда": 300.0,
        "Четверг": 400.0,
        "Пятница": 700.0,
        "Суббота": 1000.0,
        "Воскресенье": 500.0
    }
    assert json.loads(result_current_date) == expected_result_current_date
    result_given_date = spending_by_weekday(transactions, '2024.06.15')
    expected_result_given_date = {
        "Понедельник": 100.0,
        "Вторник": 500.0,
        "Среда": 300.0,
        "Четверг": 400.0,
        "Пятница": 700.0,
        "Суббота": 1000.0,
        "Воскресенье": 500.0
    }
    assert json.loads(result_given_date) == expected_result_given_date


def test_spending_by_workday():
    data = {
        'Дата операции': ['01.06.2024 12:00:00', '02.06.2024 12:00:00', '15.05.2024 08:30:00', '10.05.2024 15:45:00',
                          '25.04.2024 18:20:00', '15.04.2024 09:10:00', '16.04.2024 09:10:00'],
        'Сумма операции': [1000, 500, 300, 700, 400, 100, 500]
    }
    transactions = pd.DataFrame(data)
    result_current_date = spending_by_workday(transactions)
    expected_result_current_date = {
        "Рабочий": 400.0,  # Средняя сумма операций по рабочим дням
        "Выходной": 750.0  # Средняя сумма операций по выходным дням
    }
    assert json.loads(result_current_date) == expected_result_current_date

    result_given_date = spending_by_workday(transactions, '2024.06.15')  # без даты
    expected_result_given_date = {
        "Рабочий": 400.0,  # Средняя сумма операций по рабочим дням
        "Выходной": 750.0  # Средняя сумма операций по выходным дням
    }
    assert json.loads(result_given_date) == expected_result_given_date


@pytest.mark.parametrize("transactions, year, month, expected_output", [
    (
            [
                {"Дата операции": "15.05.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -1000,
                 "Кэшбэк": 10},
                {"Дата операции": "15.05.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -2000,
                 "Кэшбэк": None},
                {"Дата операции": "15.05.2023 12:34:56", "Категория": "Развлечения", "Сумма операции": -500,
                 "Кэшбэк": 5},
                {"Дата операции": "15.04.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -1000,
                 "Кэшбэк": 10},
            ],
            2023,
            5,
            json.dumps({
                "Продукты": 30.0,
                "Развлечения": 5.0
            }, ensure_ascii=False, indent=4)
    ),
    (
            [
                {"Дата операции": "15.06.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -1000,
                 "Кэшбэк": None},
                {"Дата операции": "15.06.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -2000,
                 "Кэшбэк": 20},
                {"Дата операции": "15.06.2023 12:34:56", "Категория": "Развлечения", "Сумма операции": -500,
                 "Кэшбэк": 5},
                {"Дата операции": "15.04.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -1000,
                 "Кэшбэк": 10},
            ],
            2023,
            6,
            json.dumps({
                "Продукты": 30.0,
                "Развлечения": 5.0
            }, ensure_ascii=False, indent=4)
    ),
    (
            [
                {"Дата операции": "15.07.2023 12:34:56", "Категория": "Транспорт", "Сумма операции": -1500,
                 "Кэшбэк": 15},
                {"Дата операции": "15.07.2023 12:34:56", "Категория": "Транспорт", "Сумма операции": -500,
                 "Кэшбэк": None},
                {"Дата операции": "15.07.2023 12:34:56", "Категория": "Развлечения", "Сумма операции": -500,
                 "Кэшбэк": 5},
                {"Дата операции": "15.04.2023 12:34:56", "Категория": "Транспорт", "Сумма операции": -1000,
                 "Кэшбэк": 10},
            ],
            2023,
            7,
            json.dumps({
                "Транспорт": 20.0,
                "Развлечения": 5.0
            }, ensure_ascii=False, indent=4)
    )
])
def test_analyze_cashback(transactions, year, month, expected_output):
    result = analyze_cashback(transactions, year, month)
    assert result == expected_output


@pytest.mark.parametrize("transactions, date, limit, expected_output", [
    (
            [
                {"Дата операции": "15.05.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -1712},
                {"Дата операции": "16.05.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -3456},
                {"Дата операции": "17.05.2023 12:34:56", "Категория": "Развлечения", "Сумма операции": -789},
                {"Дата операции": "18.04.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -300},
            ],
            "2023.05",
            50,
            93
    ),
    (
            [
                {"Дата операции": "15.06.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -1024},
                {"Дата операции": "16.06.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -2024},
                {"Дата операции": "17.06.2023 12:34:56", "Категория": "Развлечения", "Сумма операции": -3050},
                {"Дата операции": "18.06.2023 12:34:56", "Категория": "Транспорт", "Сумма операции": -1500},
            ],
            "2023.06",
            100,
            302
    ),
    (
            [
                {"Дата операции": "15.07.2023 12:34:56", "Категория": "Транспорт", "Сумма операции": -1725},
                {"Дата операции": "16.07.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -150},
                {"Дата операции": "17.07.2023 12:34:56", "Категория": "Развлечения", "Сумма операции": -345},
                {"Дата операции": "18.07.2023 12:34:56", "Категория": "Продукты", "Сумма операции": -675},
            ],
            "2023.07",
            25,
            80
    )
])
def test_investment_bank(transactions, date, limit, expected_output):
    result = investment_bank(transactions, date, limit)
    assert result == expected_output


@pytest.mark.parametrize("transactions, search, expected_output", [
    (
            [
                {"Категория": "Продукты", "Описание": "Покупка в магазине", "Сумма операции": -1000},
                {"Категория": "Развлечения", "Описание": "Кинотеатр", "Сумма операции": -500},
                {"Категория": "Транспорт", "Описание": "Такси", "Сумма операции": -300},
            ],
            "магазин",
            json.dumps([
                {"Категория": "Продукты", "Описание": "Покупка в магазине", "Сумма операции": -1000}
            ], ensure_ascii=False, indent=4)
    ),
    (
            [
                {"Категория": "Продукты", "Описание": "Покупка в магазине", "Сумма операции": -1000},
                {"Категория": "Развлечения", "Описание": "Кинотеатр", "Сумма операции": -500},
                {"Категория": "Транспорт", "Описание": "Такси", "Сумма операции": -300},
            ],
            "кино",
            json.dumps([
                {"Категория": "Развлечения", "Описание": "Кинотеатр", "Сумма операции": -500}
            ], ensure_ascii=False, indent=4)
    ),
    (
            [
                {"Категория": "Продукты", "Описание": "Покупка в магазине", "Сумма операции": -1000},
                {"Категория": "Развлечения", "Описание": "Кинотеатр", "Сумма операции": -500},
                {"Категория": "Транспорт", "Описание": "Такси", "Сумма операции": -300},
            ],
            "транспорт",
            json.dumps([
                {"Категория": "Транспорт", "Описание": "Такси", "Сумма операции": -300}
            ], ensure_ascii=False, indent=4)
    ),
    (
            [
                {"Категория": "Продукты", "Описание": "Покупка в магазине", "Сумма операции": -1000},
                {"Категория": "Развлечения", "Описание": "Кинотеатр", "Сумма операции": -500},
                {"Категория": "Транспорт", "Описание": "Такси", "Сумма операции": -300},
            ],
            "Продукты",
            json.dumps([
                {"Категория": "Продукты", "Описание": "Покупка в магазине", "Сумма операции": -1000}
            ], ensure_ascii=False, indent=4)
    ),
])
def test_search_transactions_by_user_choice(transactions, search, expected_output):
    result = search_transactions_by_user_choice(transactions, search)
    assert result == expected_output


def test_search_transaction_by_mobile_phone():
    transactions = [
        {"Описание": "Я МТС +7 921 11-22-33", "Сумма операции": -1000},
        {"Описание": "Тинькофф Мобайл +7 995 555-55-55", "Сумма операции": -1500},
        {"Описание": "Магазин", "Сумма операции": -500},
        {"Описание": "МТС Mobile +7 981 333-44-55", "Сумма операции": -2000},
        {"Описание": "Оплата по карте", "Сумма операции": -300}
    ]

    expected_output = json.dumps([
        {"Описание": "Я МТС +7 921 11-22-33", "Сумма операции": -1000},
        {"Описание": "Тинькофф Мобайл +7 995 555-55-55", "Сумма операции": -1500},
        {"Описание": "МТС Mobile +7 981 333-44-55", "Сумма операции": -2000}
    ], ensure_ascii=False, indent=4)

    result = search_transaction_by_mobile_phone(transactions)
    assert result == expected_output


def test_find_person_to_person_transactions():
    transactions = [
        {"Категория": "Переводы", "Описание": "Перевод Сергей А.", "Сумма операции": -1000},
        {"Категория": "Переводы", "Описание": "Перевод Навид Б.", "Сумма операции": -1500},
        {"Категория": "Магазин", "Описание": "Покупка в магазине", "Сумма операции": -500},
        {"Категория": "Переводы", "Описание": "Перевод Вероника Э.", "Сумма операции": -2000},
        {"Категория": "Переводы", "Описание": "Перевод Игорь С.", "Сумма операции": -300},
        {"Категория": "Переводы", "Описание": "Перевод Денис.", "Сумма операции": -700}
    ]

    expected_output = json.dumps([
        {"Категория": "Переводы", "Описание": "Перевод Сергей А.", "Сумма операции": -1000},
        {"Категория": "Переводы", "Описание": "Перевод Навид Б.", "Сумма операции": -1500},
        {"Категория": "Переводы", "Описание": "Перевод Вероника Э.", "Сумма операции": -2000},
        {"Категория": "Переводы", "Описание": "Перевод Игорь С.", "Сумма операции": -300}
    ], ensure_ascii=False, indent=4)

    result = find_person_to_person_transactions(transactions)
    assert result == expected_output
