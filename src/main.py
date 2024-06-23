from src.config import input_date_str,user_settings, api_key_currency, api_key_stocks
from src.services import page_services
from src.views import web_page_home, web_page_event, web_page_event_dop


#Главная страница
print("\nГЛАВНАЯ\n")
print(web_page_home(input_date_str, user_settings, api_key_currency, api_key_stocks))
#Событие страница
print("\nСОБЫТИЕ\n")
print(web_page_event(input_date_str))
print(web_page_event_dop(user_settings, api_key_currency, api_key_stocks))
# страница сервиса
print("\nСЕРВИСЫ\n")
print(page_services())



