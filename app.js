// Состояние приложения
let selectedAnki = null;
let privilege = localStorage.getItem('privilege') || 'player';
let isRunning = false;
let cooldownEnd = null;
let accessCode = localStorage.getItem('accessCode') || '';
let isConnected = false;

// Константы
const COOLDOWNS = {
  player: 150, // 2:30 в секундах
  prince: 60   // 1:00 в секундах
};

// Инициализация
window.addEventListener('DOMContentLoaded', () => {
  loadPrivilege();
  checkCooldown();
  setInterval(updateCooldownDisplay, 1000);
  
  // Проверяем наличие кода
  if (!accessCode) {
    showCodeModal();
  } else {
    // Проверяем подключение
    checkConnection();
  }
  
  setupCodeInputs();
});

// Настройка полей ввода кода
function setupCodeInputs() {
  const inputs = ['letter1', 'letter2', 'letter3', 'digit1', 'digit2', 'digit3'];
  
  inputs.forEach((id, index) => {
    const input = document.getElementById(id);
    if (!input) return;
    
    // Автофокус на первое поле
    if (index === 0) {
      setTimeout(() => input.focus(), 300);
    }
    
    input.addEventListener('input', (e) => {
      let value = e.target.value.toUpperCase();
      
      // Для букв - только буквы
      if (index < 3) {
        value = value.replace(/[^A-Z]/g, '');
      } else {
        // Для цифр - только цифры
        value = value.replace(/[^0-9]/g, '');
      }
      
      e.target.value = value;
      
      // Автопереход на следующее поле
      if (value && index < inputs.length - 1) {
        document.getElementById(inputs[index + 1]).focus();
      }
      
      // Автоотправка при заполнении всех полей
      if (index === inputs.length - 1 && value) {
        setTimeout(submitCode, 100);
      }
    });
    
    // Backspace - переход на предыдущее поле
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !e.target.value && index > 0) {
        document.getElementById(inputs[index - 1]).focus();
      }
      
      // Enter - отправка
      if (e.key === 'Enter') {
        submitCode();
      }
    });
    
    // Вставка кода из буфера
    input.addEventListener('paste', (e) => {
      e.preventDefault();
      const pastedText = e.clipboardData.getData('text').toUpperCase().replace(/[^A-Z0-9]/g, '');
      
      if (pastedText.length >= 6) {
        document.getElementById('letter1').value = pastedText[0] || '';
        document.getElementById('letter2').value = pastedText[1] || '';
        document.getElementById('letter3').value = pastedText[2] || '';
        document.getElementById('digit1').value = pastedText[3] || '';
        document.getElementById('digit2').value = pastedText[4] || '';
        document.getElementById('digit3').value = pastedText[5] || '';
        setTimeout(submitCode, 100);
      }
    });
  });
}

// Показать модальное окно для ввода кода
function showCodeModal() {
  document.getElementById('codeModal').style.display = 'flex';
  setTimeout(() => {
    const firstInput = document.getElementById('letter1');
    if (firstInput) firstInput.focus();
  }, 300);
}

// Проверка подключения
async function checkConnection() {
  try {
    const response = await fetch('http://localhost:5000/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: accessCode })
    });
    
    if (response.ok) {
      isConnected = true;
      addLog('✅ Подключено к MC Controller', 'success');
    } else {
      // Неверный код - запрашиваем заново
      accessCode = '';
      localStorage.removeItem('accessCode');
      showCodeModal();
    }
  } catch (error) {
    addLog('⚠️ MC Controller не запущен', 'error');
  }
}

// Отправить код
async function submitCode() {
  const letter1 = document.getElementById('letter1').value;
  const letter2 = document.getElementById('letter2').value;
  const letter3 = document.getElementById('letter3').value;
  const digit1 = document.getElementById('digit1').value;
  const digit2 = document.getElementById('digit2').value;
  const digit3 = document.getElementById('digit3').value;
  
  const code = `${letter1}${letter2}${letter3}-${digit1}${digit2}${digit3}`;
  const errorMsg = document.getElementById('errorMessage');
  
  if (code.length < 7 || code.includes('-undefined')) {
    errorMsg.textContent = 'Заполни все поля';
    return;
  }
  
  try {
    // Проверяем код на сервере
    const response = await fetch('http://localhost:5000/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code })
    });
    
    if (response.ok) {
      // Сохраняем код
      accessCode = code;
      localStorage.setItem('accessCode', code);
      isConnected = true;
      
      // Закрываем модальное окно
      document.getElementById('codeModal').style.display = 'none';
      addLog('✅ Подключено к MC Controller', 'success');
    } else {
      errorMsg.textContent = 'Неверный код доступа';
      // Очищаем поля
      ['letter1', 'letter2', 'letter3', 'digit1', 'digit2', 'digit3'].forEach(id => {
        document.getElementById(id).value = '';
      });
      document.getElementById('letter1').focus();
    }
  } catch (error) {
    errorMsg.textContent = 'Сервер недоступен. Запусти mc_controller.py';
  }
}

// Переключение настроек
function toggleSettings() {
  const panel = document.getElementById('settingsPanel');
  panel.classList.toggle('active');
}

// Установка привилегии
function setPrivilege(priv) {
  privilege = priv;
  localStorage.setItem('privilege', priv);
  
  document.querySelectorAll('.privilege-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.querySelector(`[data-privilege="${priv}"]`).classList.add('active');
  
  addLog(`Привилегия изменена: ${priv === 'player' ? 'Игрок' : 'Князь'}`, 'info');
}

// Загрузка привилегии
function loadPrivilege() {
  document.querySelectorAll('.privilege-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.querySelector(`[data-privilege="${privilege}"]`).classList.add('active');
}

// Выбор анки
function selectAnki(num) {
  if (isRunning) return;
  
  selectedAnki = num;
  
  document.querySelectorAll('.anki-btn').forEach(btn => {
    btn.classList.remove('selected');
  });
  event.target.classList.add('selected');
  
  addLog(`Выбрана анка: ${num}`, 'info');
}

// Запуск последовательности
async function startSequence() {
  if (isRunning) return;
  if (!selectedAnki) {
    addLog('Выбери анку!', 'error');
    return;
  }
  
  // Проверка кулдауна
  if (cooldownEnd && Date.now() < cooldownEnd) {
    addLog('Подожди окончания кулдауна!', 'error');
    return;
  }
  
  isRunning = true;
  updateButtonState();
  
  try {
    // 1. Телепорт на анку
    addLog(`Телепорт на анку ${selectedAnki}...`, 'info');
    await sendCommand(`/an${selectedAnki}`);
    await sleep(1000);
    
    // 2. RTP
    addLog('Телепорт в случайную точку...', 'info');
    await sendCommand('/rtp small');
    await sleep(2000);
    
    // 3. Near
    addLog('Проверка сущностей...', 'info');
    await sendCommand('/near max');
    
    addLog('✅ Последовательность завершена!', 'success');
    
    // Установка кулдауна
    const cooldownSeconds = COOLDOWNS[privilege];
    cooldownEnd = Date.now() + (cooldownSeconds * 1000);
    localStorage.setItem('cooldownEnd', cooldownEnd);
    
  } catch (error) {
    addLog(`❌ Ошибка: ${error.message}`, 'error');
  } finally {
    isRunning = false;
    updateButtonState();
  }
}

// Отправка команды на сервер
async function sendCommand(command) {
  try {
    const response = await fetch('http://localhost:5000/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        command: command,
        code: accessCode 
      })
    });
    
    if (response.status === 403) {
      // Неверный код - переподключаемся
      accessCode = '';
      localStorage.removeItem('accessCode');
      isConnected = false;
      showCodeModal();
      throw new Error('Неверный код доступа');
    }
    
    if (!response.ok) {
      throw new Error('Ошибка отправки команды');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    if (error.message === 'Failed to fetch' || error.message.includes('NetworkError')) {
      throw new Error('Сервер недоступен. Запусти mc_controller.py');
    }
    throw error;
  }
}

// Проверка кулдауна при загрузке
function checkCooldown() {
  const saved = localStorage.getItem('cooldownEnd');
  if (saved) {
    cooldownEnd = parseInt(saved);
    if (Date.now() >= cooldownEnd) {
      cooldownEnd = null;
      localStorage.removeItem('cooldownEnd');
    }
  }
}

// Обновление отображения кулдауна
function updateCooldownDisplay() {
  const info = document.getElementById('cooldownInfo');
  
  if (cooldownEnd && Date.now() < cooldownEnd) {
    const remaining = Math.ceil((cooldownEnd - Date.now()) / 1000);
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    info.textContent = `⏱️ Кулдаун: ${minutes}:${seconds.toString().padStart(2, '0')}`;
    updateButtonState();
  } else {
    info.textContent = '';
    if (cooldownEnd) {
      cooldownEnd = null;
      localStorage.removeItem('cooldownEnd');
      updateButtonState();
    }
  }
}

// Обновление состояния кнопки
function updateButtonState() {
  const btn = document.getElementById('startBtn');
  const btnText = document.getElementById('btnText');
  
  if (isRunning) {
    btn.disabled = true;
    btnText.textContent = '⏳ Выполняется...';
  } else if (cooldownEnd && Date.now() < cooldownEnd) {
    btn.disabled = true;
    btnText.textContent = '⏱️ Кулдаун';
  } else {
    btn.disabled = false;
    btnText.textContent = '🚀 Начать';
  }
}

// Добавление записи в лог
function addLog(message, type = 'info') {
  const logContent = document.getElementById('logContent');
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  
  const time = new Date().toLocaleTimeString('ru-RU');
  entry.textContent = `[${time}] ${message}`;
  
  logContent.appendChild(entry);
  logContent.scrollTop = logContent.scrollHeight;
  
  // Ограничение количества записей
  while (logContent.children.length > 50) {
    logContent.removeChild(logContent.firstChild);
  }
}

// Утилита задержки
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
