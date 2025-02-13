import streamlit as st
from typing import Dict, Any
import pandas as pd
from utils.copy_button import copy_button
from utils.common import extract_table_to_dataframe
import csv
import re


def process_text_for_display(text: str) -> str:
    """
    Обрабатывает текст для отображения на экране:
    - Преобразует блок <NewElements> в курсивный текст в формате markdown

    Args:
        text (str): Исходный текст с тегами NewElements

    Returns:
        str: Обработанный текст в формате markdown
    """

    def replace_with_italic(match: re.Match) -> str:
        # Извлекаем содержимое между тегами и оборачиваем его в markdown курсив
        content = match.group(1)
        return f"**NewElements**  \n\n{content}\n---\n"

    # Регулярное выражение для поиска содержимого между тегами NewElements
    pattern = r"<NewElements>(.*?)</NewElements>"

    # Заменяем теги на markdown курсив
    return re.sub(pattern, replace_with_italic, text, flags=re.DOTALL)


def process_text_for_copying(text: str) -> str:
    """
    Обрабатывает текст для копирования:
    - Удаляет блоки <NewElements> полностью

    Args:
        text (str): Исходный текст с тегами NewElements

    Returns:
        str: Текст без блоков NewElements
    """
    # Регулярное выражение для поиска и удаления блоков NewElements целиком
    pattern = r"<NewElements>.*?</NewElements>"

    # Удаляем блоки полностью
    return re.sub(pattern, "", text, flags=re.DOTALL)


def display_debug_panel():
    """Отображение отладочной панели"""
    if st.toggle("Debug Panel", key="debug_ctrl_toggle"):
        col0, col1, col2 = st.columns(3)
        with col0:
            if st.button("Перезапустить приложение"):
                st.rerun()

        with col1:
            if st.button("Очистить кэш обращения к api"):
                st.cache_data.clear()

        with col2:
            if st.button("Очистить внутренние переменные"):
                for key in list(st.session_state.keys()):
                    if key not in ["current_model"]:
                        del st.session_state[key]


def display_usage_stats(stats: Dict[str, Any], key_suffix: str):
    """
    Отображение статистики использования токенов и стоимости

    Parameters:
    -----------
    stats: Dict[str, Any]
        Словарь со статистикой использования
    key_suffix: str
        Суффикс для уникальных ключей виджетов
    """
    if st.toggle("Показать стоимость", key=f"cost_toggle_{key_suffix}"):
        col0, col1, col2, col3, col4 = st.columns(5)
        with col0:
            st.metric("Стоимость", f"{100*stats['full_price']:.4f} Rub")
        with col1:
            st.metric("Входные токены", stats["input_tokens"])
        with col2:
            st.metric("Выходные токены", stats["output_tokens"])
        with col3:
            st.metric("Токены создания кэша", stats["cache_create_tokens"])
        with col4:
            st.metric("Токены чтения кэша", stats["cache_read_tokens"])
        st.divider()


def display_file_upload():
    """Отображение блока загрузки файлов"""
    st.header("Загрузите файлы")
    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(
            "Исходный файл (JSON)",
            type=["json"],
            accept_multiple_files=False,
        )

    with col2:
        terms_file = st.file_uploader(
            "Словарь терминов (TXT или MD)",
            type=["txt", "md"],
            accept_multiple_files=False,
        )

    if uploaded_file is not None:
        st.session_state["uploaded_file"] = uploaded_file
        st.success("Исходный файл успешно загружен.")

    if terms_file is not None:
        st.session_state["terms_file"] = terms_file
        st.success("Словарь терминов успешно загружен.")


def display_participation_stats(df: pd.DataFrame):
    """
    Отображение статистики участия спикеров

    Parameters:
    -----------
    df: pd.DataFrame
        DataFrame со статистикой участия
    """
    st.header("Участники")
    st.bar_chart(df.set_index("Speaker"))


def display_recognition_errors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Отображение и редактирование таблицы ошибок распознавания

    Returns:
    --------
    pd.DataFrame
        Обновленная таблица ошибок
    """
    st.header("Ошибки распознавания")
    edited_df = st.data_editor(
        df,
        key="recognition_errors_editor",
    )
    return edited_df


def display_preprocessed_data():
    with st.expander("Итоги подготовки", expanded=False):
        # with st.toggle("Шаг 1"):
        tab1, tab2, tab3 = st.tabs(
            ["💬 Участники", "📚 Детали", "⚠️ Ошибки распознавания"]
        )

        with tab1:
            st.header("Участники")
            display_usage_stats(st.session_state["stats_analyze_metadata"], "tab1")

            st.bar_chart(st.session_state["df_participation"].set_index("Speaker"))
            st.session_state["topic_and_roles"] = st.text_area(
                "Введите текст",
                value=st.session_state["response_analyze_metadata"],
                height=400,
                disabled=False,
                label_visibility="collapsed",
            )
            copy_button(st.session_state["topic_and_roles"])

        with tab2:
            st.header("Детали (участники)")
            display_usage_stats(st.session_state["stats_analyze_speakers"], "tab2")
            st.markdown(st.session_state["response_analyze_speakers"])
            copy_button(st.session_state["response_analyze_speakers"])

        with tab3:
            st.header("Ошибки распознавания")
            display_usage_stats(
                st.session_state["stats_analyze_recognition_errors"], "tab3"
            )
            if "recognition_errors" not in st.session_state:
                st.session_state["recognition_errors"] = extract_table_to_dataframe(
                    st.session_state["response_analyze_recognition_errors"]
                )

            edited_df = st.data_editor(
                st.session_state["recognition_errors"],
                key="recognition_errors_editor",
            )
            st.session_state["recognition_errors"] = edited_df
            st.session_state["recognition_errors_txt"] = edited_df.to_csv(
                index=False,
                sep="|",
                quoting=csv.QUOTE_NONE,
            )
            copy_button(st.session_state["recognition_errors_txt"])


def display_summary_results(step_name: str, response: str, stats: Dict[str, Any]):
    """
    Отображение результатов шага обработки

    Parameters:
    -----------
    step_name: str
        Название шага
    response: str
        Ответ модели
    stats: Dict[str, Any]
        Статистика использования
    additional_content: Dict[str, Any], optional
        Дополнительный контент для отображения
    """
    with st.expander(step_name, expanded=False):
        st.header(step_name)
        display_usage_stats(stats, f"step_{step_name}")

        st.markdown(process_text_for_display(response))
        copy_button(process_text_for_copying(response))


def display_total_cost(total_cost: float):
    """
    Отображение общей стоимости обработки

    Parameters:
    -----------
    total_price: float
        Общая стоимость
    """
    if st.toggle("Полная стоимость", key="full_price_toggle"):
        st.header("Полная стоимость")
        st.metric("Общая стоимость", f"{100*total_cost:.4f} Rub")
