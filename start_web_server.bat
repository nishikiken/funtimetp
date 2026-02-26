@echo off
echo ========================================
echo   Запуск веб-сервера для HTML файлов
echo ========================================
echo.
echo Сервер будет доступен по адресу:
echo http://localhost:8000
echo.
echo Для доступа с телефона используй:

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
echo http://%IP:~1%:8000
echo.
echo Открой этот адрес в браузере телефона!
echo.
echo Нажми Ctrl+C чтобы остановить сервер
echo ========================================
echo.

python -m http.server 8000

pause
