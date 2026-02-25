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
    code_window.title("MC Controller - Код доступа")
    code_window.geometry("400x250")
    code_window.configure(bg='#1a1d29')
    code_window.resizable(False, False)
    code_window.overrideredirect(True)  # Borderless
    
    # Центрируем окно
    screen_width = code_window.winfo_screenwidth()
    screen_height = code_window.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 250) // 2
    code_window.geometry(f"400x250+{x}+{y}")
    
    # Делаем окно поверх всех
    code_window.attributes('-topmost', True)
    
    # Заголовок
    title_label = tk.Label(
        code_window,
        text="🎮 MC Controller",
        font=("Arial", 18, "bold"),
        bg='#1a1d29',
        fg='#ffffff'
    )
    title_label.pack(pady=(20, 10))
    
    # Текст
    info_label = tk.Label(
        code_window,
        text="Твой код доступа:",
        font=("Arial", 12),
        bg='#1a1d29',
        fg='#a0a0a0'
    )
    info_label.pack(pady=(0, 10))
    
    # Код
    code_frame = tk.Frame(code_window, bg='#2d3142', bd=0)
    code_frame.pack(pady=10, padx=40, fill='x')
    
    code_label = tk.Label(
        code_frame,
        text=access_code,
        font=("Courier New", 24, "bold"),
        bg='#2d3142',
        fg='#60a5fa',
        pady=15
    )
    code_label.pack()
    
    # Кнопка
    def close_window():
        code_window.destroy()
    
    btn = tk.Button(
        code_window,
        text="Понял",
        font=("Arial", 12, "bold"),
        bg='#60a5fa',
        fg='#ffffff',
        activebackground='#3b82f6',
        activeforeground='#ffffff',
        bd=0,
        padx=40,
        pady=10,
        cursor='hand2',
        command=close_window
    )
    btn.pack(pady=20)
    
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

