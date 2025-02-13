import streamlit as st
import json
from chat_strategies.chat_model_strategy import ChatModelStrategy
from typing import Dict, Any
from ui.processing_steps import process_initial_steps, process_all_summaries
from ui.display_components import (
    display_debug_panel,
    display_file_upload,
    display_summary_results,
    display_total_cost,
    display_preprocessed_data,
)

RECURSIVE_SUMMARY_ITERATIONS_CNT = 3  # Количество итераций для рекурсивного промптинга


def render_main_interface(chat_strategy: ChatModelStrategy, steps: Dict[str, Any]):
    """
    Отрисовка основного интерфейса приложения

    Parameters:
    -----------
    chat_strategy: ChatModelStrategy
        Стратегия работы с моделью
    steps: Dict[str, Any]
        Конфигурация шагов обработки
    """
    st.title("LLM Recup")
    st.info(f"Текущая модель: {st.session_state['current_model']}")

    # Отладочная панель
    display_debug_panel()

    # Загрузка файлов
    display_file_upload()

    # Подготовка
    button1_title = (
        "✅ Подготовка" if "response1" in st.session_state else "⚪ Подготовка"
    )
    if st.button(button1_title):
        # Чтение файлов
        uploaded_file = st.session_state["uploaded_file"]
        content = json.loads(uploaded_file.getvalue().decode("utf-8"))
        file_content = json.dumps(content, ensure_ascii=False, indent=2)

        # Обработка начальных шагов
        responses, stats, df_participation = process_initial_steps(
            chat_strategy, file_content, st.session_state["current_model"], steps
        )

        # Названия шагов
        steps_list = [
            "analyze_metadata",
            "analyze_speakers",
            "analyze_recognition_errors",
        ]

        # Инициализация стоимости
        if "total_cost" not in st.session_state:
            st.session_state["total_cost"] = 0.0

        # Обновление стоимости
        st.session_state["total_cost"] += sum(
            stats[step]["full_price"] for step in steps_list
        )

        # Сохранение результатов
        st.session_state.update(
            {
                "file_content": file_content,
                "df_participation": df_participation,
                **{f"response_{i}": responses[i] for i in steps_list},
                **{f"stats_{i}": stats[i] for i in steps_list},
            }
        )

    # Отображение результатов начальных шагов
    if "response_analyze_metadata" in st.session_state:
        display_preprocessed_data()

    # Обработка и отображение результатов
    if "response_analyze_metadata" in st.session_state and st.button("Итоги"):
        summaries = process_all_summaries(
            chat_strategy,
            st.session_state["file_content"],
            st.session_state["current_model"],
            st.session_state["response_analyze_metadata"],
            st.session_state["response_analyze_recognition_errors"],
            steps.get("generate_summary", {}),
            steps.get("refine_summary", {}),
            iterations=RECURSIVE_SUMMARY_ITERATIONS_CNT,
        )

        # Сохраняем все итерации в session_state
        for i, (response, stats) in enumerate(summaries):
            st.session_state[f"summary{i}_response"] = response
            st.session_state[f"summary{i}_stats"] = stats
            st.session_state["total_cost"] += stats["full_price"]

    # Отображение всех итераций итогов
    for i in range(0, RECURSIVE_SUMMARY_ITERATIONS_CNT):
        if f"summary{i}_response" in st.session_state:
            display_summary_results(
                f"Итоги {i}",
                st.session_state[f"summary{i}_response"],
                st.session_state[f"summary{i}_stats"],
            )

    # Отображение общей стоимости
    if "total_cost" in st.session_state:
        display_total_cost(st.session_state["total_cost"])
