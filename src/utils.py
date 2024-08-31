import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import requests
from src.logger import logger_setup

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path_log = os.path.join(current_dir, "../logs", "utils.log")
logger = logger_setup("utils", file_path_log)


# Веб страница главное
def get_read_excel(file_path: str) -> List[Dict]:
    """Функция принимает путь до xlsx файла и создает список словарей с транзакциями"""
    try:
        df = pd.read_excel(file_path)
        logger.info("файл перекодирован в список словарей")
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return []


def filter_transactions_by_date(transactions: List[Dict], input_date_str: str) -> List[Dict]:  # дата дд.мм.гггг
    """Функция принимает список словарей с транзакциями и дату
    фильтрует транзакции с начала месяца, на который выпадает входящая дата по входящую дату."""
    input_date = datetime.strptime(input_date_str, "%d.%m.%Y")
    end_date = input_date + timedelta(days=1)
    start_date = datetime(end_date.year, end_date.month, 1)

    def parse_date(date_str: str) -> datetime:
        """Функция переводит дату из формата строки в формат datetime"""
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")

    filtered_transactions = [
        transaction
        for transaction in transactions
        if start_date <= parse_date(transaction["Дата операции"]) <= end_date
    ]
    logger.info(f"Транзакции в списке отфильтрованы по датам от {start_date} до {end_date}")
    return filtered_transactions


def get_greeting() -> str:
    """Функция определяет время суток и возвращает приветствие в зависимости от времени"""
    now = datetime.now()
    current_hour = now.hour
    if 6 <= current_hour < 12:
        logger.info("Приветствие утра выполнено")
        return "Доброе утро"
    elif 12 <= current_hour < 18:
        logger.info("Приветствие дня выполнено")
        return "Добрый день"
    elif 18 <= current_hour < 23:
        logger.info("Приветствие вечера выполнено")
        return "Добрый вечер"
    else:
        logger.info("Приветствие ночи выполнено")
        return "Доброй ночи"


def get_cards_info(transactions: List[Dict]) -> List[Dict]:
    """Функция создает словарь с ключоми номеров карт и в значения добавляет сумму трат и сумму кэшбека"""
    card_data = {}
    for transaction in transactions:
        card_number = transaction.get("Номер карты")
        # если поле номер карты пустое операцию пропускаем т.к. непонятно к какой карте привязать трату
        if not card_number or str(card_number).strip().lower() == "nan":
            continue
        amount = float(transaction["Сумма операции"])
        if card_number not in card_data:
            card_data[card_number] = {"total_spent": 0.0, "cashback": 0.0}
        if amount < 0:
            card_data[card_number]["total_spent"] += abs(amount)
            cashback_value = transaction.get("Кэшбэк")
            # убираем категории переводы и наличные т.к. с них кэшбека не будет
            if transaction["Категория"] != "Переводы" and transaction["Категория"] != "Наличные":
                # рассчитываем кэшбек как 1% от траты, но если поле кешбек содержит сумму просто ее добавляем
                if cashback_value is not None:
                    cashback_amount = float(cashback_value)
                    if cashback_amount >= 0:
                        card_data[card_number]["cashback"] += cashback_amount
                    else:
                        card_data[card_number]["cashback"] += amount * -0.01
                else:
                    card_data[card_number]["cashback"] += amount * -0.01
    logger.info("кэшбек и суммы по картам посчитаны")
    cards_data = []
    for last_digits, data in card_data.items():
        cards_data.append(
            {
                "last_digits": last_digits,
                "total_spent": round(data["total_spent"], 2),
                "cashback": round(data["cashback"], 2),
            }
        )
    logger.info("получен словарь по тратам и кешбеку по каждой карте")
    return cards_data


def get_top_5_transactions(transactions: List[Dict]) -> List[Dict]:
    """Функция принимает список транзакций и выводит топ 5 операций по сумме платежа"""
    sorted_transactions = sorted(transactions, key=lambda x: abs(float(x["Сумма операции"])), reverse=True)
    top_5_sorted_transactions = []
    for transaction in sorted_transactions[:5]:
        date = datetime.strptime(transaction["Дата операции"], "%d.%m.%Y %H:%M:%S").strftime("%d.%m.%Y")
        top_5_sorted_transactions.append(
            {
                "date": date,
                "amount": transaction["Сумма операции"],
                "category": transaction["Категория"],
                "description": transaction["Описание"],
            }
        )
    logger.info("Выделено топ 5 больших транзакций")
    return top_5_sorted_transactions


# Страница событие
def process_expenses(df: pd.DataFrame) -> dict[str, Any]:
    """Функция в котором траты по категориям отсортированы по убыванию"""
    # Сумма расходов
    total_expenses = round(df["Сумма операции"].apply(lambda x: abs(x)).sum(), 0)

    # Траты по категориям
    grouped = df.groupby("Категория").agg({"Сумма операции": "sum"})
    main_categories = grouped.nlargest(7, "Сумма операции")
    other_categories_sum = grouped[~grouped.index.isin(main_categories.index)].sum()
    main_categories.loc["Остальное"] = other_categories_sum
    main_categories = main_categories.reset_index().to_dict(orient="records")

    # Траты на наличные и переводы
    transfers_and_cash = (
        df[df["Категория"].isin(["Переводы", "Наличные"])]
        .groupby("Категория")
        .agg({"Сумма операции": "sum"})
        .reset_index()
        .to_dict(orient="records")
    )
    result_expenses = {
        "total_amount": total_expenses,
        "main": main_categories,
        "transfers_and_cash": transfers_and_cash,
    }

    return result_expenses


def process_income(df: pd.DataFrame) -> dict:
    """Функция принимает список словарей сортирует его по убыванию и выводит общую сумму,
    топ 3 категории по убываниб с выводом категории и кэшбэка"""
    # Сумма поступлений
    total_income = round(df["Сумма операции"].apply(lambda x: abs(x)).sum(), 0)

    # Поступления по категориям
    main_categories = (
        df.groupby("Категория")
        .agg({"Сумма операции": "sum"})
        .nlargest(3, "Сумма операции")
        .reset_index()
        .to_dict(orient="records")
    )
    result_income = {"total_amount": total_income, "main": main_categories}

    return result_income


def process_expenses_and_income(file_path: Any, date_str: Any, range_type: str = "M") -> pd.DataFrame:
    """Функция принимающая на вход строку с датой и второй необязательный параметр — диапазон данных"""
    # Чтение данных из файла
    df = pd.read_excel(file_path)

    # Приведение дат к нужному формату
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], format="%d.%m.%Y")

    # Определение начальной и конечной даты
    date = datetime.strptime(date_str, "%d.%m.%Y")
    if range_type == "W":
        start_date = date - timedelta(days=date.weekday())
        end_date = start_date + timedelta(days=6)
    elif range_type == "M":
        start_date = datetime(date.year, date.month, 1)
        end_date = datetime(date.year, date.month, pd.Period(date, "M").days_in_month)
    elif range_type == "Y":
        start_date = datetime(date.year, 1, 1)
        end_date = datetime(date.year, 12, 31)
    elif range_type == "ALL":
        start_date = datetime(2000, 1, 1)
        end_date = date
    else:
        raise ValueError("Invalid range type")

    # Фильтрация данных по дате
    df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

    return df


def final_processing(result_expenses: Any, result_income: Any) -> str:
    """Функция возвращающая Json_ответ"""
    result_final = {"expenses": result_expenses, "income": result_income}

    return json.dumps(result_final, ensure_ascii=False, indent=4)


# Общие функции страницы главной и события
def get_exchange_rates(currencies: List[str], api_key_currency: str) -> List[Dict]:
    """Функция принимает список кодов валют и возвращает список словарей с валютами и их курсами"""
    exchange_rates = []
    for currency in currencies:
        url = f"https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/{currency}"
        response = requests.get(url)
        logger.info("Выполнен запрос на курс валют")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получен ответ от api курса валют: {data}")
            ruble_cost = data["conversion_rates"]["RUB"]
            exchange_rates.append({"currency": currency, "rate": ruble_cost})
        else:
            print(f"Ошибка: {response.status_code}, {response.text}    1")
            logger.error(f"Ошибка api запроса {response.status_code}, {response.text}")
            exchange_rates.append({"currency": currency, "rate": None})
    logger.info("Курсы валют созданы")
    return exchange_rates


def get_stocks_cost(companies: List[str], api_key_stocks: str) -> List[Dict]:
    """Функция принимает список кодов компаний и возвращает словарь со стоимостью акций каждой переданной компании"""
    stocks_cost = []
    for company in companies:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={company}&apikey={api_key_stocks}"
        response = requests.get(url)
        logger.info("Выполнен запрос на курс акций")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получен ответ от api курса акций: {data}")
            time_series = data.get("Time Series (Daily)")
            if time_series:
                latest_date = max(time_series.keys())
                latest_data = time_series[latest_date]
                stock_cost = latest_data["4. close"]
                stocks_cost.append({"stock": company, "price": float(stock_cost)})
            else:
                print(f"Ошибка: данные для компании {company} недоступны. API ответ {data}")
                logger.error(f"Ошибка ответа: {data}")
                stocks_cost.append({"stock": company, "price": None})
        else:
            print(f"Ошибка: {response.status_code}, {response.text}    2")
            logger.error(f"Ошибка api запроса {response.status_code}, {response.text}")
            stocks_cost.append({"stock": company, "price": None})
    logger.info("Стоимость акций создана")
    return stocks_cost
