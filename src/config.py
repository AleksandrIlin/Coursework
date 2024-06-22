import os

from dotenv import load_dotenv

from src.utils import get_read_excel

load_dotenv()
api_key_currency = os.getenv("API_KEY_CURRENCY")
api_key_stocks = os.getenv("API_KEY_STOCKS")
input_date_str = "20.03.2020"
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "../data", "operations.xls")
transactions = get_read_excel(file_path)
year = 2018
month = 6
date = "2018.06"
limit = 50
search = "Перевод"
