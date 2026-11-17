@echo off
REM Installation complète (Windows). Prérequis : Python 3.11+, Node 18+.
REM   setup.bat            installe tout
REM   set RUN_TESTS=1 & setup.bat   lance aussi les tests du backend
cd /d "%~dp0backend"
python -m venv .venv || goto :err
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || goto :err

if not exist .env copy .env.example .env
python -c "import pathlib,re,secrets; p=pathlib.Path('.env'); p.write_text(re.sub(r'(?m)^SECRET_KEY=\s*$', 'SECRET_KEY='+secrets.token_urlsafe(50), p.read_text()))"

python manage.py check || goto :err
python manage.py makemigrations --noinput || goto :err
python manage.py migrate || goto :err
python manage.py seed_demo || goto :err
if defined RUN_TESTS python manage.py test || goto :err

cd ..\frontend
if not exist .env copy .env.example .env
call npm install || goto :err

echo.
echo Installation terminee.
echo   Terminal 1 : cd backend ^&^& .venv\Scripts\activate ^&^& python manage.py runserver   (http://127.0.0.1:8000)
echo   Terminal 2 : cd frontend ^&^& npm run dev                                            (http://localhost:5173)
echo   Compte demo : admin@enterprise.ca / password
exit /b 0
:err
echo Echec de l'installation.
exit /b 1
