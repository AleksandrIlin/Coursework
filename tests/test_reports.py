import pandas as pd
from typing import List, Dict


def get_read_excel(path: str) -> List[Dict]:
    """Функция принимает путь до xlsx файла и создает список словарей с транзакциями"""
    try:
        df = pd.read_excel(path)
        logger.info('файл перекодирован в список словарей')
        return df.to_dict(orient='records')
    except Exception as e:
        print(f'Возникла ошибка {e}')
        logger.error(f'Возникла ошибка {e}')
        return []