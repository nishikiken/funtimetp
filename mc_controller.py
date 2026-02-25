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
CORS(app)

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
    code_window.geometry("500x300")
    code_window.configure(bg='#0f1419')
    code_window.resizable(False, False)
    code_window.overrideredirect(True)  # Borderless
    
    # Центрируем окно
    screen_width = code_window.winfo_screenwidth()
    screen_height = code_window.winfo_screenheight()
    x = (screen_width - 500) // 2
    y = (screen_height - 300) // 2
    code_window.geometry(f"500x300+{x}+{y}")
    
    # Делаем окно поверх всех
    code_window.attributes('-topmost', True)
    
    # Рамка с градиентом (эмуляция через border)
    main_frame = tk.Frame(code_window, bg='#60a5fa', bd=2)
    main_frame.pack(fill='both', expand=True, padx=2, pady=2)
    
    inner_frame = tk.Frame(main_frame, bg='#0f1419')
    inner_frame.pack(fill='both', expand=True)
    
    # Иконка и заголовок
    header_frame = tk.Frame(inner_frame, bg='#0f1419')
    header_frame.pack(pady=(30, 10))
    
    icon_label = tk.Label(
        header_frame,
        text="⚡",
        font=("Arial", 40),
        bg='#0f1419',
        fg='#60a5fa'
    )
    icon_label.pack()
    
    title_label = tk.Label(
        header_frame,
        text="MC Controller",
        font=("Arial", 20, "bold"),
        bg='#0f1419',
        fg='#ffffff'
    )
    title_label.pack()
    
    # Текст
    info_label = tk.Label(
        inner_frame,
        text="Код доступа для подключения:",
        font=("Arial", 11),
        bg='#0f1419',
        fg='#9ca3af'
    )
    info_label.pack(pady=(10, 15))
    
    # Код в красивой рамке
    code_container = tk.Frame(inner_frame, bg='#1a1f2e', bd=0)
    code_container.pack(pady=10, padx=60)
    
    code_inner = tk.Frame(code_container, bg='#1a1f2e')
    code_inner.pack(padx=20, pady=15)
    
    code_label = tk.Label(
        code_inner,
        text=access_code,
        font=("Courier New", 32, "bold"),
        bg='#1a1f2e',
        fg='#60a5fa',
        letterspace=3
    )
    code_label.pack()
    
    # Статус
    status_label = tk.Label(
        inner_frame,
        text="Ожидание подключения...",
        font=("Arial", 10),
        bg='#0f1419',
        fg='#6b7280'
    )
    status_label.pack(pady=(15, 0))
    
    # Индикатор загрузки (анимация точек)
    dots_label = tk.Label(
        inner_frame,
        text="",
        font=("Arial", 14),
        bg='#0f1419',
        fg='#60a5fa'
    )
    dots_label.pack()
    
    # Анимация точек
    def animate_dots(count=0):
        if code_window.winfo_exists():
            dots = "." * (count % 4)
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


@app.route('/command', methods=['POST'])
def execute_command():
    """API endpoint для выполнения команд"""
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
            return jsonify({'status': 'success', 'command': command})
        else:
            return jsonify({'error': 'Ошибка выполнения команды'}), 500
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def status():
    """Проверка статуса сервера"""
    return jsonify({'status': 'online', 'message': 'MC Controller работает'})


@app.route('/connect', methods=['POST'])
def connect():
    """Проверка кода и подключение"""
    global connected, code_window
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
        
        return jsonify({'status': 'success', 'message': 'Подключено'})
        
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

