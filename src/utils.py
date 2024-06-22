import pandas as pd
import functools
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict
from src.logger import logger_setup
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "../logs", "utils.log")
logger = logger_setup("utils", file_path)


# Веб страница главное и событие
def get_read_excel(file_path_transactions: str) -> List[Dict]:
    """Функция принимает путь до xlsx файла и создает список словарей с транзакциями"""
    try:
        df = pd.read_excel(file_path_transactions)
        logger.info('файл перекодирован в список словарей')
        return df.to_dict(orient='records')
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return []


def filter_transactions_by_date(transactions: List[Dict], input_date_str: str) -> List[Dict]:  # дата дд.мм.гггг
    """Функция принимает список словарей с транзакциями и дату
        фильтрует транзакции с начала месяца, на который выпадает входящая дата по входящую дату."""
    input_date = datetime.strptime(input_date_str, '%d.%m.%Y')
    end_date = input_date + timedelta(days=1)
    start_date = datetime(end_date.year, end_date.month, 1)

    def parse_date(date_str: str):
        """Функция переводит дату из формата строки в формат datetime"""
        return datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')

    filtered_transactions = [transaction for transaction in transactions
                             if start_date <= parse_date(transaction["Дата операции"]) <= end_date]
    logger.info(f'Транзакции в списке отфильтрованы по датам от {start_date} до {end_date}')
    return filtered_transactions


def get_greeting():
    """Функция определяет время суток и возвращает приветствие в зависимости от времени"""
    now = datetime.now()
    current_hour = now.hour
    if 6 <= current_hour < 12:
        logger.info('Приветствие утра выполнено')
        return "Доброе утро"
    elif 12 <= current_hour < 18:
        logger.info('Приветствие дня выполнено')
        return "Добрый день"
    elif 18 <= current_hour < 23:
        logger.info('Приветствие вечера выполнено')
        return "Добрый вечер"
    else:
        logger.info('Приветствие ночи выполнено')
        return "Доброй ночи"


def get_cards_info(transactions: List[Dict]) -> List[Dict]:
    """Функция создает словарь с ключоми номеров карт и в значения добавляет сумму трат и сумму кэшбека"""
    card_data = {}
    for transaction in transactions:
        card_number = transaction.get('Номер карты')
        # если поле номер карты пустое операцию пропускаем т.к. непонятно к какой карте привязать трату
        if not card_number or str(card_number).strip().lower() == 'nan':
            continue
        amount = float(transaction['Сумма операции'])
        if card_number not in card_data:
            card_data[card_number] = {'total_spent': 0.0, 'cashback': 0.0}
        if amount < 0:
            card_data[card_number]['total_spent'] += abs(amount)
            cashback_value = transaction.get("Кэшбэк")
            # убираем категории переводы и наличные т.к. с них кэшбека не будет
            if transaction["Категория"] != "Переводы" and transaction["Категория"] != "Наличные":
                # рассчитываем кэшбек как 1% от траты, но если поле кешбек содержит сумму просто ее добавляем
                if cashback_value is not None:
                    cashback_amount = float(cashback_value)
                    if cashback_amount >= 0:
                        card_data[card_number]['cashback'] += cashback_amount
                    else:
                        card_data[card_number]['cashback'] += amount * -0.01
                else:
                    card_data[card_number]['cashback'] += amount * -0.01
    logger.info('кэшбек и суммы по картам посчитаны')
    cards_data = []
    for last_digits, data in card_data.items():
        cards_data.append({
            "last_digits": last_digits,
            "total_spent": round(data['total_spent'], 2),
            "cashback": round(data['cashback'], 2)})
    logger.info('получен словарь по тратам и кешбеку по каждой карте')
    return cards_data


def get_top_5_transactions(transactions: List[Dict]) -> List[Dict]:
    """Функция принимает список транзакций и выводит топ 5 операций по сумме платежа"""
    sorted_transactions = sorted(transactions, key=lambda x: abs(float(x["Сумма операции"])), reverse=True)
    top_5_sorted_transactions = []
    for transaction in sorted_transactions[:5]:
        date = datetime.strptime(transaction["Дата операции"], '%d.%m.%Y %H:%M:%S').strftime('%d.%m.%Y')
        top_5_sorted_transactions.append({
            "date": date,
            "amount": transaction["Сумма операции"],
            "category": transaction["Категория"],
            "description": transaction["Описание"]
        })
    logger.info('Выделено топ 5 больших транзакций')
    return top_5_sorted_transactions


def get_exchange_rates(currencies: List[str], api_key_currency) -> List[Dict]:
    """Функция принимает список кодов валют и возвращает список словарей с валютами и их курсами"""
    exchange_rates = []
    for currency in currencies:
        url = f'https://v6.exchangerate-api.com/v6/{api_key_currency}/latest/{currency}'
        response = requests.get(url)
        logger.info('Выполнен запрос на курс валют')
        if response.status_code == 200:
            data = response.json()
            logger.info(f'Получен ответ от api курса валют: {data}')
            ruble_cost = data["conversion_rates"]["RUB"]
            exchange_rates.append({
                "currency": currency,
                "rate": ruble_cost})
        else:
            print(f"Ошибка: {response.status_code}, {response.text}")
            logger.error(f'Ошибка api запроса {response.status_code}, {response.text}')
            exchange_rates.append({
                "currency": currency,
                "rate": None
            })
    logger.info('Курсы валют созданы')
    return exchange_rates


def get_stocks_cost(companies: List[str], api_key_stocks) -> List[Dict]:
    """Функция принимает список кодов компаний и возвращает словарь со стоимостью акций каждой переданной компании"""
    stocks_cost = []
    for company in companies:
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={company}&apikey={api_key_stocks}'
        response = requests.get(url)
        logger.info('Выполнен запрос на курс акций')
        if response.status_code == 200:
            data = response.json()
            logger.info(f'Получен ответ от api курса акций: {data}')
            time_series = data.get("Time Series (Daily)")
            if time_series:
                latest_date = max(time_series.keys())
                latest_data = time_series[latest_date]
                stock_cost = latest_data["4. close"]
                stocks_cost.append({
                    "stock": company,
                    "price": float(stock_cost)})
            else:
                print(f"Ошибка: данные для компании {company} недоступны. API ответ {data}")
                logger.error(f'Ошибка ответа: {data}')
                stocks_cost.append({
                    "stock": company,
                    "price": None})
        else:
            print(f"Ошибка: {response.status_code}, {response.text}")
            logger.error(f'Ошибка api запроса {response.status_code}, {response.text}')
            stocks_cost.append({
                "stock": company,
                "price": None})
    logger.info('Стоимость акций создана')
    return stocks_cost


# Страница сервисы
def analyze_cashback(transactions: List[Dict], year: int, month: int) -> str:
    """Принимает список словарей транзакций и считает сумму кэшбека по категориям"""
    try:
        cashback_analysis: Dict = {}
        for transaction in transactions:
            transaction_date = datetime.strptime(transaction["Дата операции"], '%d.%m.%Y %H:%M:%S')
            if transaction_date.year == year and transaction_date.month == month:
                category = transaction["Категория"]
                amount = transaction["Сумма операции"]
                if amount < 0:
                    cashback_value = transaction["Кэшбэк"]
                    if cashback_value is not None and cashback_value >= 0:
                        cashback = float(cashback_value)
                    else:
                        cashback = round(amount * -0.01, 5)
                    if category in cashback_analysis:
                        cashback_analysis[category] += cashback
                    else:
                        cashback_analysis[category] = cashback
        logger.info('Посчитана сумма кэшбека по категориям')
        return json.dumps(cashback_analysis, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return ''


# принимает строку с датой гггг.мм
def investment_bank(transactions: List[Dict], date: str, limit: int) -> float | Exception:
    """Функция принимает транзакции, дату и лимит округления и считает сколько можно было отложить в инвесткопилку"""
    try:
        sum_investment_bank = float(0.0)
        user_date = datetime.strptime(date, '%Y.%m')
        for transaction in transactions:
            transaction_date = datetime.strptime(transaction["Дата операции"], '%d.%m.%Y %H:%M:%S')
            if transaction_date.year == user_date.year and transaction_date.month == user_date.month:
                amount = transaction["Сумма операции"]
                if amount < 0 and transaction["Категория"] != "Переводы" and transaction["Категория"] != "Наличные":
                    amount_ = abs(amount)  # перевел в положительное
                    total_amount = ((amount_ + limit + 1) // limit) * limit - amount_
                    sum_investment_bank += total_amount
        logger.info(f"Инвесткопилка за  {date} посчитана")
        return sum_investment_bank
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return e


def search_transactions_by_user_choice(transactions: List[Dict], search: str) -> str:
    """Функция выполняет поиск в транзакциях по переданной строке """
    try:
        search_result = []
        for transaction in transactions:
            category = str(transaction.get('Категория', ''))
            description = str(transaction.get('Описание', ''))
            if search.lower() in description.lower() or search.lower() in category.lower():
                search_result.append(transaction)
        logger.info(f'Выполнен поиск по запросу {search}')
        return json.dumps(search_result, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return ''


def search_transaction_by_mobile_phone(transactions: List[Dict]) -> str:
    """Функция возвращает транзакции в описании которых есть мобильный номер"""
    try:
        mobile_pattern = re.compile(r'\+\d{1,4}')
        found_transactions = []
        for transaction in transactions:
            description = transaction.get('Описание', '')
            if mobile_pattern.search(description):
                found_transactions.append(transaction)
        logger.info('Выполнен поиск по транзакциям с номером телефона')
        return json.dumps(found_transactions, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return ''


def find_person_to_person_transactions(transactions: List[Dict]) -> str:
    """Функция вовзращает транзакции в описании которых есть имя кому или от кого выполнен перевод"""
    try:
        transfer_transactions = []
        search_pattern = re.compile(r'\b[А-ЯЁ][а-яё]*\s[А-ЯЁ]\.')
        for transaction in transactions:
            category = transaction.get('Категория', '')
            description = transaction.get('Описание', '')
            if category == 'Переводы' and search_pattern.search(description):
                transfer_transactions.append(transaction)
        logger.info('Выполнен поиск по переводам физлицам')
        return json.dumps(transfer_transactions, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return ''


# Страница отчеты
def report_to_file_default(func):
    """Записывает в файл результат, который возвращает функция, формирующая отчет."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        with open("function_operation_report.txt", "w") as file:
            file.write(str(result))
        logger.info(f'Записан результат работы функции {func}')
        return result
    return wrapper


def report_to_file(filename="function_operation_report.txt"):
    """Записывает в переданный файл результат, который возвращает функция, формирующая отчет."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            with open(filename, "w") as file:
                file.write(str(result))
            logger.info(f'Записан результат работы функции {func} в файл {filename}')
            return result
        return wrapper
    return decorator


# дата гггг.мм.дд
@report_to_file_default
def spending_by_category(transactions: pd.DataFrame, category: str, date=None) -> str:
    """Функция возвращает траты по заданной категории за последние три месяца
    (от переданной даты, если дата не передана берет текущую)"""
    try:
        transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'], format='%d.%m.%Y %H:%M:%S')
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%Y.%m.%d')
        start_date = date - timedelta(days=date.day - 1) - timedelta(days=3 * 30)
        filtered_transactions = transactions[(transactions['Дата операции'] >= start_date) &
                                             (transactions['Дата операции'] <= date) &
                                             (transactions['Категория'] == category)]
        grouped_transactions = filtered_transactions.groupby(pd.Grouper(key='Дата операции', freq='ME')).sum()
        logger.info(f'Траты за последние три месяца от {date} по категории {category}')
        return grouped_transactions.to_dict(orient='records')
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return ""


@report_to_file_default
def spending_by_weekday(transactions: pd.DataFrame, date=None) -> str:
    """Функция возвращает средние траты в каждый из дней недели за последние три месяца (от переданной даты)"""
    try:
        transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'], format='%d.%m.%Y %H:%M:%S')
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%Y.%m.%d')
        start_date = date - timedelta(days=date.day) - timedelta(days=3 * 30)
        filtered_transactions = transactions[(transactions['Дата операции'] >= start_date) &
                                             (transactions['Дата операции'] <= date)]
        filtered_transactions = filtered_transactions.copy()
        filtered_transactions.loc[:, 'День недели'] = filtered_transactions['Дата операции'].dt.dayofweek
        grouped_transactions = filtered_transactions.groupby('День недели')['Сумма операции'].mean()
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        grouped_transactions.index = weekdays
        result_dict = {day: grouped_transactions.get(day, 0.0) for day in weekdays}
        logger.info(f'Средние траты по дням недели начиная с {date}')
        return json.dumps(result_dict, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return ""


@report_to_file_default
def spending_by_workday(transactions: pd.DataFrame, date=None) -> str:
    """Функция выводит средние траты в рабочий и в выходной день за последние три месяца (от переданной даты)."""
    try:
        transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'], format='%d.%m.%Y %H:%M:%S')
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%Y.%m.%d')
        weekend_days = [5, 6]
        start_date = date - timedelta(days=date.day) - timedelta(days=3 * 30)
        filtered_transactions = transactions[(transactions['Дата операции'] >= start_date) &
                                             (transactions['Дата операции'] <= date)]
        filtered_transactions = filtered_transactions.copy()
        filtered_transactions['День недели'] = filtered_transactions['Дата операции'].dt.dayofweek
        filtered_transactions['Тип дня'] = 'Рабочий'
        filtered_transactions.loc[filtered_transactions['День недели'].isin(weekend_days), 'Тип дня'] = 'Выходной'
        grouped_transactions = filtered_transactions.groupby('Тип дня')['Сумма операции'].mean()
        logger.info(f'средние траты за последние три месяца от {date} по рабочим и выходным дням')
        return json.dumps(grouped_transactions.to_dict(), ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return ""
