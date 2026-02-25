"""
Minecraft Controller - выполняет команды из веб-интерфейса
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import keyboard
import time
import pyautogui
import threading
import pystray
from PIL import Image, ImageDraw, ImageFont
from pystray import MenuItem as item
import random
import string
import tkinter as tk
from tkinter import ttk

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

pyautogui.FAILSAFE = False

# Глобальные переменные
server_running = False
icon = None
access_code = ""
code_window = None
connected = False


def create_icon_image():
    """Создать иконку для трея"""
    # Создаем простую иконку 64x64
    image = Image.new('RGB', (64, 64), color='#3b82f6')
    dc = ImageDraw.Draw(image)
    
    # Рисуем "MC" крупным шрифтом
    try:
        # Пытаемся использовать системный шрифт
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        # Если не получилось, используем стандартный
        font = ImageFont.load_default()
    
    # Центрируем текст
    text = "MC"
    bbox = dc.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (64 - text_width) // 2
    y = (64 - text_height) // 2 - 5
    
    dc.text((x, y), text, fill='white', font=font)
    
    return image


def generate_access_code():
    """Генерировать код доступа в формате XXX-000"""
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letters}-{numbers}"


def show_code_window():
    """Показать окно с кодом доступа"""
    global code_window, access_code
    
    code_window = tk.Tk()
    code_window.title("MC Controller")
    code_window.geometry("600x400")
    code_window.configure(bg='#0f1419')
    code_window.resizable(False, False)
    code_window.overrideredirect(True)
    
    # Центрируем окно
    screen_width = code_window.winfo_screenwidth()
    screen_height = code_window.winfo_screenheight()
    x = (screen_width - 600) // 2
    y = (screen_height - 400) // 2
    code_window.geometry(f"600x400+{x}+{y}")
    
    code_window.attributes('-topmost', True)
    
    # Главный контейнер с градиентом (эмуляция)
    main_canvas = tk.Canvas(code_window, width=600, height=400, bg='#0f1419', highlightthickness=0)
    main_canvas.pack(fill='both', expand=True)
    
    # Рисуем градиентный фон
    for i in range(400):
        ratio = i / 400
        r1, g1, b1 = 15, 20, 25  # #0f1419
        r2, g2, b2 = 26, 31, 46  # #1a1f2e
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        color = f'#{r:02x}{g:02x}{b:02x}'
        main_canvas.create_line(0, i, 600, i, fill=color)
    
    # Рамка
    main_canvas.create_rectangle(2, 2, 598, 398, outline='#60a5fa', width=2)
    
    # Иконка молнии
    icon_label = tk.Label(
        code_window,
        text="⚡",
        font=("Arial", 70),
        bg='#0f1419',
        fg='#60a5fa'
    )
    icon_label.place(x=300, y=50, anchor='center')
    
    # Заголовок
    title_label = tk.Label(
        code_window,
        text="MC Controller",
        font=("Arial", 26, "bold"),
        bg='#0f1419',
        fg='#ffffff'
    )
    title_label.place(x=300, y=130, anchor='center')
    
    # Подзаголовок
    subtitle_label = tk.Label(
        code_window,
        text="Код доступа для подключения",
        font=("Arial", 12),
        bg='#0f1419',
        fg='#9ca3af'
    )
    subtitle_label.place(x=300, y=170, anchor='center')
    
    # Контейнер для кода
    code_frame = tk.Frame(code_window, bg='#1a1f2e', bd=0)
    code_frame.place(x=300, y=230, anchor='center', width=400, height=80)
    
    # Рисуем рамку вокруг кода
    code_canvas = tk.Canvas(code_frame, width=400, height=80, bg='#1a1f2e', highlightthickness=0)
    code_canvas.pack()
    code_canvas.create_rectangle(2, 2, 398, 78, outline='#60a5fa', width=1)
    
    # Код
    code_label = tk.Label(
        code_frame,
        text=access_code,
        font=("Courier New", 36, "bold"),
        bg='#1a1f2e',
        fg='#60a5fa'
    )
    code_label.place(x=200, y=40, anchor='center')
    
    # Статус
    status_label = tk.Label(
        code_window,
        text="Ожидание подключения",
        font=("Arial", 11),
        bg='#0f1419',
        fg='#6b7280'
    )
    status_label.place(x=300, y=300, anchor='center')
    
    # Индикатор (точки)
    dots_label = tk.Label(
        code_window,
        text="",
        font=("Arial", 16),
        bg='#0f1419',
        fg='#60a5fa'
    )
    dots_label.place(x=300, y=330, anchor='center')
    
    # Подсказка
    hint_label = tk.Label(
        code_window,
        text="Открой сайт и введи этот код",
        font=("Arial", 10),
        bg='#0f1419',
        fg='#4b5563'
    )
    hint_label.place(x=300, y=365, anchor='center')
    
    # Анимация точек
    def animate_dots(count=0):
        if code_window.winfo_exists():
            dots = "." * ((count % 3) + 1)
            dots_label.config(text=dots)
            code_window.after(500, lambda: animate_dots(count + 1))
    
    animate_dots()
    
    code_window.mainloop()


def send_minecraft_command(command):
    """Отправить команду в Minecraft"""
    try:
        # Открыть чат (T)
        keyboard.press_and_release('t')
        time.sleep(0.1)
        
        # Вставить команду
        pyautogui.write(command, interval=0.01)
        time.sleep(0.05)
        
        # Отправить (Enter)
        keyboard.press_and_release('enter')
        time.sleep(0.1)
        
        return True
    except Exception as e:
        print(f"Ошибка отправки команды: {e}")
        return False


@app.route('/command', methods=['POST', 'OPTIONS'])
def execute_command():
    """API endpoint для выполнения команд"""
    
    # Обработка preflight запроса
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.json
        command = data.get('command')
        code = data.get('code')
        
        if not command:
            return jsonify({'error': 'Команда не указана'}), 400
        
        # Проверка кода доступа
        if code != access_code:
            return jsonify({'error': 'Неверный код доступа'}), 403
        
        print(f"Выполняю команду: {command}")
        success = send_minecraft_command(command)
        
        if success:
            response = jsonify({'status': 'success', 'command': command})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            return jsonify({'error': 'Ошибка выполнения команды'}), 500
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    """Проверка статуса сервера"""
    return jsonify({'status': 'online', 'message': 'MC Controller работает'})


@app.route('/connect', methods=['POST', 'OPTIONS'])
def connect():
    """Проверка кода и подключение"""
    global connected, code_window
    
    # Обработка preflight запроса
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.json
        code = data.get('code')
        
        if code != access_code:
            return jsonify({'error': 'Неверный код доступа'}), 403
        
        # Успешное подключение
        connected = True
        print(f"✅ Подключение установлено!")
        
        # Закрываем окно с кодом
        if code_window and code_window.winfo_exists():
            code_window.after(100, code_window.destroy)
        
        response = jsonify({'status': 'success', 'message': 'Подключено'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return jsonify({'error': str(e)}), 500


def run_flask():
    """Запустить Flask сервер"""
    global server_running
    server_running = True
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


def on_quit(icon, item):
    """Выход из приложения"""
    global server_running
    server_running = False
    icon.stop()


def setup_tray():
    """Настроить иконку в трее"""
    global icon
    
    image = create_icon_image()
    
    menu = pystray.Menu(
        item('MC Controller', lambda: None, enabled=False),
        item('Статус: Работает', lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        item('Выход', on_quit)
    )
    
    icon = pystray.Icon("mc_controller", image, "MC Controller", menu)
    icon.run()


if __name__ == '__main__':
    # Генерируем код доступа
    access_code = generate_access_code()
    
    print("=" * 50)
    print("🎮 Minecraft Controller запущен!")
    print("=" * 50)
    print(f"Код доступа: {access_code}")
    print("Сервер: http://localhost:5000")
    print("Иконка в трее: MC Controller")
    print("Открой index.html в браузере")
    print("=" * 50)
    
    # Показываем окно с кодом в отдельном потоке
    code_thread = threading.Thread(target=show_code_window, daemon=False)
    code_thread.start()
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем иконку в трее (блокирующий вызов)
    setup_tray()

