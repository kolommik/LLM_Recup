import streamlit as st
from dotenv import load_dotenv, find_dotenv
import toml
import os
from chat_strategies.openai_strategy import OpenAIChatStrategy
from chat_strategies.anthropic_strategy import AnthropicChatStrategy
from chat_strategies.deepseeker_strategy import DeepseekerChatStrategy
from chat_strategies.chat_model_strategy import ChatModelStrategy
from utils.session_manager import initialize_session
from ui.sidebar import render_sidebar
from ui.main_interface import render_main_interface
import logging
from typing import Dict

# -----------------------------
# Настройка логирования
# -----------------------------
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# -----------------------------
# Конфигурация страницы
# -----------------------------
st.set_page_config(page_title="LLM Recup", layout="wide")


def initialize_available_strategies() -> Dict[str, ChatModelStrategy]:
    """
    Инициализирует все доступные стратегии на основе наличия API ключей
    """
    load_dotenv(find_dotenv())
    strategies = {}

    # OpenAI
    if openai_key := os.environ.get("OPENAI_API_KEY"):
        strategies["openai"] = OpenAIChatStrategy(openai_key)

    # Anthropic
    if anthropic_key := os.environ.get("ANTHROPIC_API_KEY"):
        strategies["anthropic"] = AnthropicChatStrategy(anthropic_key)

    # Deepseeker
    if deepseeker_key := os.environ.get("DEEPSEEKER_API_KEY"):
        strategies["deepseeker"] = DeepseekerChatStrategy(deepseeker_key)

    return strategies


# -----------------------------
# Загрузка конфигурационного файла
# -----------------------------
@st.cache_data
def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
    return config


config = load_config("config.toml")
steps = config.get("steps", {})

# -----------------------------
# Инициализация сессионных переменных
# -----------------------------
initialize_session()

# -----------------------------
# Инициализация доступных стратегий
# -----------------------------
available_strategies = initialize_available_strategies()

if not available_strategies:
    st.error("No API keys found. Please configure at least one provider.")
    st.stop()

# -----------------------------
# Боковая панель "Настройки"
# -----------------------------
render_sidebar(available_strategies)

# -----------------------------
# Определение текущей стратегии
# -----------------------------
current_model = st.session_state["current_model"]
current_strategy = next(
    (
        strategy
        for strategy in available_strategies.values()
        if current_model in strategy.get_models()
    ),
    None,
)

if not current_strategy:
    st.error(f"No strategy found for model {current_model}")
    st.stop()

# -----------------------------
# Основной интерфейс
# -----------------------------
render_main_interface(current_strategy, steps)
