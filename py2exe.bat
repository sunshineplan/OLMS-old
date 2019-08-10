curl https://code.jquery.com/jquery-3.4.1.min.js -so OLMS\static\jquery.js --create-dirs
curl https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css -so OLMS\static\bootstrap.css --create-dirs
curl https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css.map -so OLMS\static\bootstrap.min.css.map --create-dirs
@translation.py
pip install -U pyinstaller
pyinstaller -F --add-data OLMS\static;static --add-data OLMS\templates-zh;templates --add-data OLMS\schema.sql;templates main.py -i main.ico
pause
