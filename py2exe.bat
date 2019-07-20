@echo off
pip install -U pyinstaller
pyinstaller -F --add-data OLMS\static;static --add-data OLMS\templates-zh;templates --add-data OLMS\schema.sql;templates main.py -i main.ico
pause
