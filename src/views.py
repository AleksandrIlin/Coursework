import json
import os
from typing import Any

from dotenv import load_dotenv
from src.utils import (
    filter_transactions_by_date,
    final_processing,
    get_cards_info,
    get_exchange_rates,
    get_greeting,
    get_read_excel,
    get_stocks_cost,
    get_top_5_transactions,
    process_expenses,
    process_expenses_and_income,
    process_income,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "../data", "operations.xls")

with open("../data/user_settings.json", "r") as file:
    user_settings = json.load(file)
load_dotenv()
api_key_currency = os.getenv("API_KEY_CURRENCY")
api_key_stocks = os.getenv("API_KEY_STOCKS")


def web_page_home(input_date_str: Any, user_settings: dict, api_key_currency: Any, api_key_stocks: Any) -> Any:
    """Основная функция для генерации JSON-ответа, главной страницы"""
    transactions = get_read_excel(file_path)
    filtered_transactions = filter_transactions_by_date(transactions, input_date_str)
    cards_data = get_cards_info(filtered_transactions)
    exchange_rates = get_exchange_rates(user_settings["user_currencies"], api_key_currency)
    stocks_cost = get_stocks_cost(user_settings["user_stocks"], api_key_stocks)
    top_transactions = get_top_5_transactions(filtered_transactions)
    greetings = get_greeting()
    user_data = {
        "greeting": greetings,
        "cards": cards_data,
        "top_transactions": top_transactions,
        "exchange_rates": exchange_rates,
        "stocks": stocks_cost,
    }
    return json.dumps(user_data, ensure_ascii=False, indent=4)


def web_page_event(input_date_str: Any) -> str:
    """Функция вывода страницы события"""
    df = process_expenses_and_income(file_path, input_date_str)
    result_expenses = process_expenses(df)
    result_income = process_income(df)
    result_final = final_processing(result_expenses, result_income)
    return result_final


def web_page_event_dop(user_settings: dict, api_key_currency: Any, api_key_stocks: Any) -> Any:
    """Дополнительная функция к странице событие для вывода json ответа по акциям и валютам"""
    exchange_rates = get_exchange_rates(user_settings["user_currencies"], api_key_currency)
    stocks_cost = get_stocks_cost(user_settings["user_stocks"], api_key_stocks)
    user_data = {"exchange_rates": exchange_rates, "stocks": stocks_cost}
    return json.dumps(user_data, ensure_ascii=False, indent=4)
