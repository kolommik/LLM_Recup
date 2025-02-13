import streamlit as st
from typing import Dict
from chat_strategies.chat_model_strategy import ChatModelStrategy


def render_sidebar(available_strategies: Dict[str, ChatModelStrategy]):
    """
    Отображает боковую панель с настройками.

    Parameters:
    -----------
    available_strategies : Dict[str, ChatModelStrategy]
        Словарь доступных стратегий, где ключ - имя провайдера,
        значение - инициализированная стратегия
    """
    with st.sidebar:
        st.header("Настройки")

        # Собираем все доступные модели от всех провайдеров
        all_models = []
        for strategy in available_strategies.values():
            all_models.extend(strategy.get_models())

        # Если это первая загрузка или текущая модель недоступна
        if (
            "current_model" not in st.session_state
            or st.session_state["current_model"] not in all_models
        ):
            st.session_state["current_model"] = all_models[0]

        # Выпадающий список для выбора модели LLM
        selected_model = st.selectbox(
            "Выберите модель LLM",
            all_models,
            index=all_models.index(st.session_state["current_model"]),
        )

        # Сохраняем выбранную модель в session_state
        st.session_state["current_model"] = selected_model
