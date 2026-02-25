"""
Minecraft Controller - выполняет команды из веб-интерфейса
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import keyboard
import time
import pyautogui

app = Flask(__name__)
CORS(app)

pyautogui.FAILSAFE = False


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


if __name__ == '__main__':
    print("=" * 50)
    print("🎮 Minecraft Controller запущен!")
    print("=" * 50)
    print("Сервер: http://localhost:5000")
    print("Открой index.html в браузере")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
