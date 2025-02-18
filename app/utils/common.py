import json
import pandas as pd
from collections import defaultdict


def calculate_speaker_participation(json_text):
    # Парсинг JSON
    data = json.loads(json_text)

    # Словарь для хранения количества слов каждого спикера
    speaker_word_count = defaultdict(int)

    # Общее количество слов
    total_words = 0

    # Обработка каждого сообщения
    for entry in data:
        speaker = entry["speaker"]
        message = entry["message"]

        # Разделение сообщения на слова
        words = message.split()

        # Подсчет слов для текущего спикера
        speaker_word_count[speaker] += len(words)

        # Обновление общего количества слов
        total_words += len(words)

    # Вычисление процента участия каждого спикера
    speaker_percentage = {
        speaker: (count / total_words) * 100
        for speaker, count in speaker_word_count.items()
    }

    # Сортировка по проценту участия по убыванию
    sorted_speaker_percentage = dict(
        sorted(speaker_percentage.items(), key=lambda item: item[1], reverse=True)
    )

    return sorted_speaker_percentage


def extract_table_to_dataframe(input_text):
    """
    Извлекает таблицу из текста и возвращает pandas DataFrame.
    Если таблица не найдена или произошла ошибка, возвращает пустой DataFrame.

    :param input_text: Текст, содержащий таблицу.
    :return: pandas DataFrame или пустой DataFrame в случае ошибки.
    """
    try:
        # Находим начало таблицы (первая строка с заголовками)
        table_start = input_text.find("| Исходный текст")
        if table_start == -1:
            # Пробуем найти альтернативный вариант заголовка
            table_start = input_text.find("| **Исходный текст")
            if table_start == -1:
                # Если таблица не найдена, возвращаем пустой DataFrame
                return pd.DataFrame()

        # Находим конец таблицы (пустая строка или конец текста)
        table_end = input_text.find("\n\n", table_start)
        if table_end == -1:
            table_end = len(input_text)  # Если пустой строки нет, берем до конца текста

        # Извлекаем табличную часть
        table_text = input_text[table_start:table_end].strip()

        # Разделяем табличный текст на строки
        lines = table_text.split("\n")

        # Извлекаем заголовки
        headers = [header.strip() for header in lines[0].split("|") if header.strip()]

        # Извлекаем данные
        data = []
        for line in lines[
            2:
        ]:  # Пропускаем первую строку (заголовки) и вторую (разделитель)
            row = [cell.strip() for cell in line.split("|") if cell.strip()]
            if len(row) == len(
                headers
            ):  # Проверяем, что строка соответствует заголовкам
                data.append(row)

        # Создаем DataFrame
        df = pd.DataFrame(data, columns=headers)
        return df

    except Exception as e:
        # В случае любой ошибки возвращаем пустой DataFrame
        print(f"Ошибка при обработке таблицы: {e}")
        return pd.DataFrame()
