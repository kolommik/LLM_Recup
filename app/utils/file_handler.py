from pathlib import Path
import json
import csv


def save_uploaded_file(uploaded_file, destination: Path):
    """
    Сохраняет загруженный файл в указанное место.

    Parameters:
    - uploaded_file: Объект загруженного файла Streamlit.
    - destination (Path): Путь к файлу, куда сохранить загруженный файл.
    """
    with open(destination, "wb") as f:
        f.write(uploaded_file.getbuffer())


def read_json(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: dict, file_path: Path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def read_csv(file_path: Path) -> list:
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)


def write_csv(data: list, file_path: Path):
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)
