from src.utils import (analyze_cashback, find_person_to_person_transactions, investment_bank,
                          search_transaction_by_mobile_phone, search_transactions_by_user_choice)
from src.config import transactions, year, month, limit, search, date


def page_services():
    cashback_analysis_result = analyze_cashback(transactions, year, month)
    investment_bank_result = investment_bank(transactions, date, limit)
    search_transactions_by_user_choice_result = search_transactions_by_user_choice(transactions, search)
    search_transaction_by_mobile_phone_result = search_transaction_by_mobile_phone(transactions)
    find_person_to_person_transactions_result = find_person_to_person_transactions(transactions)
    print(cashback_analysis_result)
    print(investment_bank_result)
    print(search_transactions_by_user_choice_result)
    print(search_transaction_by_mobile_phone_result)
    print(find_person_to_person_transactions_result)



