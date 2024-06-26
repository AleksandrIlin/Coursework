import json
import os
import re
from datetime import datetime
from typing import Dict, List

from src.logger import logger_setup

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path_log = os.path.join(current_dir, "../logs", "services.log")
logger = logger_setup("services", file_path_log)


def analyze_cashback(transactions: List[Dict], year: int, month: int) -> str:
    """Принимает список словарей транзакций и считает сумму кэшбека по категориям"""
    try:
        cashback_analysis: Dict = {}
        for transaction in transactions:
            transaction_date = datetime.strptime(transaction["Дата операции"], "%d.%m.%Y %H:%M:%S")
            if transaction_date.year == year and transaction_date.month == month:
                category = transaction["Категория"]
                amount = transaction["Сумма операции"]
                if amount < 0:
                    cashback_value = transaction["Кэшбэк"]
                    if cashback_value is not None and cashback_value >= 0:
                        cashback = float(cashback_value)
                    else:
                        cashback = abs(round(amount * 0.01))
                    if category in cashback_analysis:
                        cashback_analysis[category] += cashback
                    else:
                        cashback_analysis[category] = cashback
        logger.info("Посчитана сумма кэшбека по категориям")
        return json.dumps(cashback_analysis, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return ""


# принимает строку с датой гггг.мм
def investment_bank(transactions: List[Dict], date: str, limit: int) -> float | Exception:
    """Функция принимает транзакции, дату и лимит округления и считает сколько можно было отложить в инвесткопилку"""
    try:
        sum_investment_bank = float(0.0)
        user_date = datetime.strptime(date, "%Y.%m")
        for transaction in transactions:
            transaction_date = datetime.strptime(transaction["Дата операции"], "%d.%m.%Y %H:%M:%S")
            if transaction_date.year == user_date.year and transaction_date.month == user_date.month:
                amount = transaction["Сумма операции"]
                if amount < 0 and transaction["Категория"] != "Переводы" and transaction["Категория"] != "Наличные":
                    amount_ = abs(amount)  # перевел в положительное
                    total_amount = round(((amount_ + limit + 1) // limit) * limit - amount_)
                    sum_investment_bank += total_amount
        logger.info(f"Инвесткопилка за  {date} посчитана")
        return sum_investment_bank
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return e


def search_transactions_by_user_choice(transactions: List[Dict], search: str) -> str:
    """Функция выполняет поиск в транзакциях по переданной строке"""
    try:
        search_result = []
        for transaction in transactions:
            category = str(transaction.get("Категория", ""))
            description = str(transaction.get("Описание", ""))
            if search.lower() in description.lower() or search.lower() in category.lower():
                search_result.append(transaction)
        logger.info(f"Выполнен поиск по запросу {search}")
        return json.dumps(search_result, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return ""


def search_transaction_by_mobile_phone(transactions: List[Dict]) -> str:
    """Функция возвращает транзакции в описании которых есть мобильный номер"""
    try:
        mobile_pattern = re.compile(r"\+\d{1,4}")
        found_transactions = []
        for transaction in transactions:
            description = transaction.get("Описание", "")
            if mobile_pattern.search(description):
                found_transactions.append(transaction)
        logger.info("Выполнен поиск по транзакциям с номером телефона")
        return json.dumps(found_transactions, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return ""


def find_person_to_person_transactions(transactions: List[Dict]) -> str:
    """Функция вовзращает транзакции в описании которых есть имя кому или от кого выполнен перевод"""
    try:
        transfer_transactions = []
        search_pattern = re.compile(r"\b[А-ЯЁ][а-яё]*\s[А-ЯЁ]\.")
        for transaction in transactions:
            category = transaction.get("Категория", "")
            description = transaction.get("Описание", "")
            if category == "Переводы" and search_pattern.search(description):
                transfer_transactions.append(transaction)
        logger.info("Выполнен поиск по переводам физлицам")
        return json.dumps(transfer_transactions, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Возникла ошибка {e}")
        logger.error(f"Возникла ошибка {e}")
        return ""
