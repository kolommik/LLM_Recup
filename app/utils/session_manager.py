import streamlit as st
import uuid
import datetime
from pathlib import Path


def initialize_session():
    """
    Инициализирует необходимые переменные в session_state.
    """
    if "session_id" not in st.session_state:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        st.session_state["session_id"] = f"{timestamp}_{unique_id}"

    default_states = {
        "processing_option": "gpt-4",
        "uploaded_file": None,
        "terms_file": None,
        "prepared": False,
        "participants": "",
        "finalized": False,
        "results": "",
    }

    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_folder() -> Path:
    """
    Возвращает путь к временной папке текущей сессии.
    """
    base_path = Path("Data/tmp")
    session_folder = base_path / st.session_state["session_id"]
    session_folder.mkdir(parents=True, exist_ok=True)
    return session_folder
