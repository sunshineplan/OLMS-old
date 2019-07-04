@echo off
pip install pyinstaller -U > nul
pyinstaller -F --add-data OLMS\templates-zh;templates --add-data OLMS\schema.sql;templates main.py -i main.ico
pause
