@echo off
echo ========================================
echo   Настройка брандмауэра для MC Controller
echo ========================================
echo.
echo Этот скрипт добавит правило в брандмауэр Windows
echo чтобы разрешить подключения к Flask серверу.
echo.
echo Требуются права администратора!
echo.
pause

echo.
echo Добавляю правило в брандмауэр...
echo.

netsh advfirewall firewall add rule name="MC Controller - Flask" dir=in action=allow protocol=TCP localport=5000

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo   Успешно!
    echo ========================================
    echo.
    echo Правило добавлено. Теперь попробуй подключиться с телефона.
    echo.
) else (
    echo.
    echo ========================================
    echo   Ошибка!
    echo ========================================
    echo.
    echo Запусти этот файл от имени администратора:
    echo Правый клик -> "Запуск от имени администратора"
    echo.
)

pause
