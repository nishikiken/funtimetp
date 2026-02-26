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
import pyperclip

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
    
    # Получаем локальный IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    code_window = tk.Tk()
    code_window.title("MC Controller")
    code_window.geometry("400x280")
    code_window.configure(bg='#1a1f2e')
    code_window.resizable(False, False)
    code_window.overrideredirect(True)
    
    # Центрируем окно
    screen_width = code_window.winfo_screenwidth()
    screen_height = code_window.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 280) // 2
    code_window.geometry(f"400x280+{x}+{y}")
    
    code_window.attributes('-topmost', True)
    code_window.attributes('-alpha', 0.95)  # Полупрозрачность
    
    # Создаем скругленные углы через Canvas
    canvas = tk.Canvas(code_window, width=400, height=280, bg='#0f1419', highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    
    # Рисуем скругленный прямоугольник
    def round_rectangle(x1, y1, x2, y2, radius=20, **kwargs):
        points = [x1+radius, y1,
                  x1+radius, y1,
                  x2-radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1+radius,
                  x1, y1]
        return canvas.create_polygon(points, **kwargs, smooth=True)
    
    # Фон
    round_rectangle(10, 10, 390, 270, radius=20, fill='#1a1f2e', outline='#60a5fa', width=2)
    
    # Текст сверху
    canvas.create_text(200, 40, text="Введите этот код на сайте", 
                      font=("Arial", 13), fill='#9ca3af')
    
    # Код (большой)
    canvas.create_text(200, 110, text=access_code, 
                      font=("Courier New", 42, "bold"), fill='#60a5fa')
    
    # Разделитель
    canvas.create_line(50, 160, 350, 160, fill='#2d3142', width=1)
    
    # IP адрес для телефона
    canvas.create_text(200, 190, text="Адрес для телефона:", 
                      font=("Arial", 10), fill='#6b7280')
    canvas.create_text(200, 215, text=f"http://{local_ip}:5000", 
                      font=("Courier New", 11, "bold"), fill='#10b981')
    
    # Статус
    canvas.create_text(200, 250, text="Ожидание подключения...", 
                      font=("Arial", 9), fill='#4b5563')
    
    code_window.mainloop()


def send_minecraft_command(command):
    """Отправить команду в Minecraft"""
    try:
        # Открыть чат (T)
        keyboard.press_and_release('t')
        time.sleep(0.2)
        
        # Копируем команду в буфер обмена
        pyperclip.copy(command)
        time.sleep(0.1)
        
        # Вставляем через Ctrl+V
        keyboard.press_and_release('ctrl+v')
        time.sleep(0.1)
        
        # Отправить (Enter)
        keyboard.press_and_release('enter')
        time.sleep(0.3)
        
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


@app.route('/')
def index():
    """Главная страница"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return jsonify({'error': 'index.html not found'}), 404


@app.route('/<path:filename>')
def serve_static(filename):
    """Раздача статических файлов"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Определяем тип контента
        if filename.endswith('.js'):
            return content, 200, {'Content-Type': 'application/javascript'}
        elif filename.endswith('.css'):
            return content, 200, {'Content-Type': 'text/css'}
        elif filename.endswith('.html'):
            return content, 200, {'Content-Type': 'text/html'}
        else:
            return content
    except:
        return jsonify({'error': f'{filename} not found'}), 404


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

