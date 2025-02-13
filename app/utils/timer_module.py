# timer_module.py
import time
from functools import wraps

# Глобальная переменная для хранения времени начала выполнения программы
start_time = None


def start_global_timer():
    global start_time
    start_time = time.time()


def log_function_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_func_time = time.time()
        result = func(*args, **kwargs)
        end_func_time = time.time()
        print(
            f"Функция {func.__name__} выполнилась за {end_func_time - start_func_time:.4f} секунд"
        )
        return result

    return wrapper


def end_global_timer():
    global start_time
    if start_time is not None:
        end_time = time.time()
        print(f"Общее время выполнения программы: {end_time - start_time:.4f} секунд")
    else:
        print("Глобальный таймер не был запущен.")
