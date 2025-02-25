from typing import Dict, Tuple, Any, List
from chat_strategies.chat_model_strategy import ChatModelStrategy
import pandas as pd
from utils.common import calculate_speaker_participation
from concurrent.futures import ThreadPoolExecutor
import time


def process_step(
    chat_strategy: ChatModelStrategy,
    step_config: Dict[str, Any],
    content: str,
    model_name: str,
    terms_file: str = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Обработка одного шага с помощью модели

    Parameters:
    -----------
    chat_strategy: ChatModelStrategy
        Стратегия работы с моделью
    step_config: Dict[str, Any]
        Конфигурация шага
    content: str
        Входной контент
    model_name: str
        Имя модели
    terms_file: str, optional
        Содержимое файла словаря терминов

    Returns:
    --------
    Tuple[str, Dict[str, Any]]
        Ответ модели и статистика использования
    """
    system_prompt = step_config.get("prompt", "")
    temperature = step_config.get("temperature", 0.0)
    max_tokens = chat_strategy.get_output_max_tokens(model_name)

    messages = []
    # Добавляем основной контент
    messages.extend(
        [
            {"role": "user", "content": content},
            {"role": "assistant", "content": "Текст принят."},
        ]
    )
    # Добавляем словарь терминов, если он предоставлен
    if terms_file:
        messages.extend(
            [
                {"role": "user", "content": f"Словарь терминов:\n{terms_file}"},
                {"role": "assistant", "content": "Словарь терминов принят."},
            ]
        )
    # Добавляем сам вопрос (system prompt)
    messages.append({"role": "user", "content": system_prompt})

    response = chat_strategy.send_message(
        system_prompt="",
        messages=messages,
        model_name=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    stats = {
        "input_tokens": chat_strategy.get_input_tokens(),
        "output_tokens": chat_strategy.get_output_tokens(),
        "cache_create_tokens": chat_strategy.get_cache_create_tokens(),
        "cache_read_tokens": chat_strategy.get_cache_read_tokens(),
        "full_price": chat_strategy.get_full_price(),
    }

    return response, stats


def process_initial_steps(
    chat_strategy: ChatModelStrategy,
    file_content: str,
    model_name: str,
    steps: Dict[str, Any],
    terms_file: str = None,
) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]], pd.DataFrame]:
    """
    Параллельная обработка начальных шагов анализа

    Parameters:
    -----------
    chat_strategy: ChatModelStrategy
        Стратегия работы с моделью
    file_content: str
        Содержимое файла для анализа
    model_name: str
        Имя модели
    steps: Dict[str, Any]
        Конфигурация шагов
    terms_file: str, optional
        Содержимое файла словаря терминов

    Returns:
    --------
    Tuple[Dict[str, str], Dict[str, Dict[str, Any]], pd.DataFrame]
        Ответы моделей, статистика и DataFrame с участием спикеров
    """
    # Расчет участия спикеров
    speaker_participation = calculate_speaker_participation(file_content)
    df_participation = pd.DataFrame(
        list(speaker_participation.items()), columns=["Speaker", "Participation"]
    )

    responses = {}
    stats = {}

    # Первый шаг - analyze_metadata.
    # Идет отдельно, т.к. позволяет инициализировать кэш
    response, step_stats = process_step(
        chat_strategy,
        steps.get("analyze_metadata", {}),
        file_content,
        model_name,
        terms_file,
    )

    responses["analyze_metadata"] = response
    stats["analyze_metadata"] = step_stats

    # Ждем 10 секунд
    time.sleep(10)

    # Параллельное выполнение оставшихся шагов
    # Испольуя кэш
    parallel_steps = ["analyze_speakers", "analyze_recognition_errors"]

    with ThreadPoolExecutor() as executor:
        futures = {
            step_name: executor.submit(
                process_step,
                chat_strategy,
                steps.get(step_name, {}),
                file_content,
                model_name,
                terms_file,
            )
            for step_name in parallel_steps
        }

        # Сбор результатов параллельных шагов
        for step_name, future in futures.items():
            response, step_stats = future.result()
            responses[step_name] = response
            stats[step_name] = step_stats

    return responses, stats, df_participation


def process_summary_initial(
    chat_strategy: ChatModelStrategy,
    file_content: str,
    model_name: str,
    topic_roles: str,
    recognition_errors: str,
    step_config: Dict[str, Any],
    terms_file: str = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Первый этап формирования итогов steps.generate_summary
    """
    prompt = (
        step_config["prompt"]
        .replace("<<TOPIC_AND_ROLES>>", topic_roles)
        .replace("<<RECOGNITION_ERRORS>>", recognition_errors)
    )

    return process_step(
        chat_strategy,
        {"prompt": prompt, "temperature": step_config.get("temperature", 0)},
        file_content,
        model_name,
        terms_file,
    )


def process_summary_recursive(
    chat_strategy: ChatModelStrategy,
    file_content: str,
    model_name: str,
    topic_roles: str,
    recognition_errors: str,
    step_config: Dict[str, Any],
    prev_summary: str,
    terms_file: str = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Рекурсивное улучшение итогов (step5+)
    """
    prompt = (
        step_config["prompt"]
        .replace("<<TOPIC_AND_ROLES>>", topic_roles)
        .replace("<<RECOGNITION_ERRORS>>", recognition_errors)
        .replace("<<PREV_RESUME>>", prev_summary)
    )

    return process_step(
        chat_strategy,
        {"prompt": prompt, "temperature": step_config.get("temperature", 0)},
        file_content,
        model_name,
        terms_file,
    )


def process_all_summaries(
    chat_strategy: ChatModelStrategy,
    file_content: str,
    model_name: str,
    topic_roles: str,
    recognition_errors: str,
    generate_summary_config: Dict[str, Any],
    refine_summary_config: Dict[str, Any],
    iterations: int = 2,
    terms_file: str = None,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Полный процесс формирования итогов с рекурсивным улучшением

    Returns:
    --------
    List[Tuple[str, Dict[str, Any]]]
        Список кортежей (ответ, статистика) для каждой итерации
    """
    results = []

    # Первый этап (step4)
    response, stats = process_summary_initial(
        chat_strategy,
        file_content,
        model_name,
        topic_roles,
        recognition_errors,
        generate_summary_config,
        terms_file,
    )
    results.append((response, stats))

    # Рекурсивные улучшения
    prev_summary = response
    for _ in range(iterations):
        response, stats = process_summary_recursive(
            chat_strategy,
            file_content,
            model_name,
            topic_roles,
            recognition_errors,
            refine_summary_config,
            prev_summary,
            terms_file,
        )
        results.append((response, stats))
        prev_summary = response

    return results
