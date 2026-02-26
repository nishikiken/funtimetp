// Состояние приложения
let selectedAnki = null;
let privilege = localStorage.getItem('privilege') || 'player';
let isRunning = false;
let ankiCooldowns = JSON.parse(localStorage.getItem('ankiCooldowns') || '{}'); // {101: timestamp, 102: timestamp, ...}
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
  updateAllAnkiStates();
  setInterval(updateAllAnkiStates, 1000);
  
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
  const server = localStorage.getItem('serverIP') || 'http://localhost:5000';
  
  try {
    const response = await fetch(`${server}/connect`, {
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
  console.log('submitCode вызвана');
  
  const letter1 = document.getElementById('letter1')?.value || '';
  const letter2 = document.getElementById('letter2')?.value || '';
  const letter3 = document.getElementById('letter3')?.value || '';
  const digit1 = document.getElementById('digit1')?.value || '';
  const digit2 = document.getElementById('digit2')?.value || '';
  const digit3 = document.getElementById('digit3')?.value || '';
  
  const code = `${letter1}${letter2}${letter3}-${digit1}${digit2}${digit3}`;
  const errorMsg = document.getElementById('errorMessage');
  
  console.log('Код:', code);
  
  if (code.length < 7 || !letter1 || !letter2 || !letter3 || !digit1 || !digit2 || !digit3) {
    errorMsg.textContent = 'Заполни все поля';
    console.log('Не все поля заполнены');
    return;
  }
  
  // Получаем сервер - если открыто через http://IP:5000, используем его
  const currentHost = window.location.hostname;
  const currentPort = window.location.port || '5000';
  const server = `http://${currentHost}:${currentPort}`;
  
  console.log('Подключаюсь к:', server);
  errorMsg.textContent = 'Подключаюсь...';
  
  try {
    const response = await fetch(`${server}/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code })
    });
    
    console.log('Ответ получен:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('Успех:', data);
      
      // Сохраняем код и сервер
      accessCode = code;
      localStorage.setItem('accessCode', code);
      localStorage.setItem('serverIP', server);
      isConnected = true;
      
      // Закрываем модальное окно
      document.getElementById('codeModal').style.display = 'none';
      addLog('✅ Подключено к MC Controller', 'success');
    } else {
      const error = await response.json();
      console.log('Ошибка:', error);
      errorMsg.textContent = error.error || 'Неверный код доступа';
      
      // Очищаем поля
      ['letter1', 'letter2', 'letter3', 'digit1', 'digit2', 'digit3'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
      });
      document.getElementById('letter1')?.focus();
    }
  } catch (error) {
    console.error('Ошибка подключения:', error);
    errorMsg.textContent = 'Не удалось подключиться: ' + error.message;
  }
}

// Показать поле для ввода IP
function showIPInput() {
  const errorMsg = document.getElementById('errorMessage');
  const existingInput = document.getElementById('ipInput');
  
  if (existingInput) return;
  
  const ipContainer = document.createElement('div');
  ipContainer.style.marginTop = '15px';
  
  const ipInput = document.createElement('input');
  ipInput.id = 'ipInput';
  ipInput.type = 'text';
  ipInput.placeholder = 'Например: 192.168.1.3:5000';
  ipInput.style.cssText = `
    width: 100%;
    padding: 10px;
    background: rgba(15, 20, 25, 0.6);
    border: 2px solid rgba(96, 165, 250, 0.3);
    border-radius: 8px;
    color: #ffffff;
    font-size: 14px;
    text-align: center;
    margin-bottom: 10px;
  `;
  
  const ipBtn = document.createElement('button');
  ipBtn.textContent = 'Подключиться к этому IP';
  ipBtn.style.cssText = `
    width: 100%;
    padding: 10px;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border: none;
    border-radius: 8px;
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
  `;
  
  ipBtn.onclick = async () => {
    const ip = ipInput.value.trim();
    if (!ip) return;
    
    const server = ip.startsWith('http') ? ip : `http://${ip}`;
    localStorage.setItem('serverIP', server);
    
    // Пробуем подключиться
    try {
      const response = await fetch(`${server}/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: accessCode })
      });
      
      if (response.ok) {
        isConnected = true;
        document.getElementById('codeModal').style.display = 'none';
        addLog('✅ Подключено к MC Controller', 'success');
      } else {
        errorMsg.textContent = 'Неверный код или IP адрес';
      }
    } catch (error) {
      errorMsg.textContent = 'Не удалось подключиться к этому IP';
    }
  };
  
  ipContainer.appendChild(ipInput);
  ipContainer.appendChild(ipBtn);
  errorMsg.parentElement.appendChild(ipContainer);
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
  
  // Проверяем кулдаун этой анки
  const cooldownEnd = ankiCooldowns[num];
  if (cooldownEnd && Date.now() < cooldownEnd) {
    const remaining = Math.ceil((cooldownEnd - Date.now()) / 1000);
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    addLog(`⏱️ Анка ${num} на кулдауне: ${minutes}:${seconds.toString().padStart(2, '0')}`, 'error');
    return;
  }
  
  selectedAnki = num;
  
  document.querySelectorAll('.anki-btn').forEach(btn => {
    btn.classList.remove('selected');
  });
  event.target.classList.add('selected');
  
  addLog(`✅ Выбрана анка: ${num}`, 'info');
}

// Запуск последовательности
async function startSequence() {
  if (isRunning) return;
  if (!selectedAnki) {
    addLog('❌ Выбери анку!', 'error');
    return;
  }
  
  // Проверка кулдауна выбранной анки
  const cooldownEnd = ankiCooldowns[selectedAnki];
  if (cooldownEnd && Date.now() < cooldownEnd) {
    addLog('⏱️ Эта анка на кулдауне!', 'error');
    return;
  }
  
  isRunning = true;
  updateButtonState();
  
  const currentAnki = selectedAnki;
  
  try {
    // 1. Телепорт на анку
    addLog(`📍 Телепорт на анку ${currentAnki}...`, 'info');
    await sendCommand(`/an${currentAnki}`);
    await sleep(1000);
    
    // 2. RTP
    addLog('🌍 Телепорт в случайную точку...', 'info');
    await sendCommand('/rtp small');
    await sleep(2000);
    
    // 3. Near
    addLog('👁️ Проверка сущностей...', 'info');
    await sendCommand('/near max');
    
    addLog('✅ Последовательность завершена!', 'success');
    
    // Установка кулдауна для этой анки
    const cooldownSeconds = COOLDOWNS[privilege];
    ankiCooldowns[currentAnki] = Date.now() + (cooldownSeconds * 1000);
    localStorage.setItem('ankiCooldowns', JSON.stringify(ankiCooldowns));
    
    // Обновляем состояние кнопки анки
    updateAnkiState(currentAnki);
    
  } catch (error) {
    addLog(`❌ Ошибка: ${error.message}`, 'error');
  } finally {
    isRunning = false;
    updateButtonState();
    selectedAnki = null;
    document.querySelectorAll('.anki-btn').forEach(btn => {
      btn.classList.remove('selected');
    });
  }
}

// Отправка команды на сервер
async function sendCommand(command) {
  const server = localStorage.getItem('serverIP') || 'http://localhost:5000';
  
  try {
    const response = await fetch(`${server}/command`, {
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
      throw new Error('Сервер недоступен. Проверь подключение');
    }
    throw error;
  }
}

// Проверка кулдауна при загрузке
function checkCooldown() {
  // Очищаем старые кулдауны
  const now = Date.now();
  for (const anki in ankiCooldowns) {
    if (ankiCooldowns[anki] < now) {
      delete ankiCooldowns[anki];
    }
  }
  localStorage.setItem('ankiCooldowns', JSON.stringify(ankiCooldowns));
}

// Обновление состояния всех анок
function updateAllAnkiStates() {
  checkCooldown();
  
  document.querySelectorAll('.anki-btn').forEach(btn => {
    const anki = parseInt(btn.textContent);
    updateAnkiState(anki);
  });
}

// Обновление состояния конкретной анки
function updateAnkiState(anki) {
  const btn = Array.from(document.querySelectorAll('.anki-btn')).find(b => parseInt(b.textContent) === anki);
  if (!btn) return;
  
  const cooldownEnd = ankiCooldowns[anki];
  
  if (cooldownEnd && Date.now() < cooldownEnd) {
    const remaining = Math.ceil((cooldownEnd - Date.now()) / 1000);
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    
    btn.classList.add('cooldown');
    btn.disabled = true;
    btn.setAttribute('data-cooldown', `${minutes}:${seconds.toString().padStart(2, '0')}`);
  } else {
    btn.classList.remove('cooldown');
    btn.disabled = false;
    btn.removeAttribute('data-cooldown');
    
    // Удаляем из списка кулдаунов
    if (ankiCooldowns[anki]) {
      delete ankiCooldowns[anki];
      localStorage.setItem('ankiCooldowns', JSON.stringify(ankiCooldowns));
    }
  }
}

// Обновление отображения кулдауна
function updateCooldownDisplay() {
  // Эта функция больше не нужна, но оставим для совместимости
  updateAllAnkiStates();
}

// Обновление состояния кнопки
function updateButtonState() {
  const btn = document.getElementById('startBtn');
  const btnText = document.getElementById('btnText');
  
  if (isRunning) {
    btn.disabled = true;
    btnText.textContent = '⏳ Выполняется...';
  } else if (!selectedAnki) {
    btn.disabled = true;
    btnText.textContent = 'Выбери анку';
  } else {
    btn.disabled = false;
    btnText.textContent = 'Начать';
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
