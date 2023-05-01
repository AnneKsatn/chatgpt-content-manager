@echo off

call %~dp0venv\Scripts\activate
@echo %cd%
@echo %~dp0venv\Scripts\activate


set TOKEN=6221451779:AAEJCJEy1qcJxTj5xBkUobCnPxrHin4GuJs

python telegram_bot.py

pause