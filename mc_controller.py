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
from PIL import Image, ImageDraw
from pystray import MenuItem as item

app = Flask(__name__)
CORS(app)

pyautogui.FAILSAFE = False

# Глобальные переменные
server_running = False
icon = None


def create_icon_image():
    """Создать иконку для трея"""
    # Создаем простую иконку 64x64
    image = Image.new('RGB', (64, 64), color='#1a1d29')
    dc = ImageDraw.Draw(image)
    
    # Рисуем круг
    dc.ellipse([8, 8, 56, 56], fill='#60a5fa', outline='#a78bfa', width=3)
    
    # Рисуем "MC"
    dc.text((18, 22), "MC", fill='white')
    
    return image


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
        
        if not command:
            return jsonify({'error': 'Команда не указана'}), 400
        
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
    print("=" * 50)
    print("🎮 Minecraft Controller запущен!")
    print("=" * 50)
    print("Сервер: http://localhost:5000")
    print("Иконка в трее: MC Controller")
    print("Открой index.html в браузере")
    print("=" * 50)
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем иконку в трее (блокирующий вызов)
    setup_tray()

