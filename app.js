// Состояние приложения
let selectedAnki = null;
let privilege = localStorage.getItem('privilege') || 'player';
let isRunning = false;
let cooldownEnd = null;

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
});

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
      body: JSON.stringify({ command })
    });
    
    if (!response.ok) {
      throw new Error('Ошибка отправки команды');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    throw new Error('Сервер недоступен. Запусти mc_controller.py');
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
