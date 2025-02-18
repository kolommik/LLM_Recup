import streamlit.components.v1 as components


def copy_button(text_to_copy: str, title: str = "Скопировать"):
    """
    Создает кнопку с помощью HTML и JavaScript.
    Копирует переданный текст в буфер обмена при нажатии.
    """
    html_code = f"""
    <div style="margin-top:10px;">
        <button onclick="copyToClipboard()" style="
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 4px;">
            {title}
        </button>
    </div>
    <script>
      function copyToClipboard() {{
          navigator.clipboard.writeText(`{text_to_copy}`).then(function() {{
              alert('Текст скопирован в буфер обмена!');
          }}, function(err) {{
              alert('Не удалось скопировать текст: ' + err);
          }});
      }}
    </script>
    """
    components.html(html_code, height=60)
