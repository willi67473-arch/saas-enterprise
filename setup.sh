#!/usr/bin/env bash
# Installation complète (Linux / macOS / Git Bash). Prérequis : Python 3.11+, Node 18+.
#   ./setup.sh              installe tout
#   RUN_TESTS=1 ./setup.sh  lance aussi la suite de tests du backend
set -e
cd "$(dirname "$0")/backend"
PY="${PYTHON:-python3}"

"$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt

[ -f .env ] || cp .env.example .env
python - <<'PYEOF'
import pathlib, re, secrets
p = pathlib.Path(".env")
p.write_text(re.sub(r"(?m)^SECRET_KEY=\s*$", "SECRET_KEY=" + secrets.token_urlsafe(50), p.read_text()))
PYEOF

python manage.py check
python manage.py makemigrations --noinput   # sans effet si les migrations fournies sont à jour
python manage.py migrate
python manage.py seed_demo
[ -z "$RUN_TESTS" ] || python manage.py test

cd ../frontend
[ -f .env ] || cp .env.example .env
npm install

echo
echo "✔ Installation terminée."
echo "  Terminal 1 : cd backend  && source .venv/bin/activate && python manage.py runserver   (http://127.0.0.1:8000)"
echo "  Terminal 2 : cd frontend && npm run dev                                                (http://localhost:5173)"
echo "  Compte démo : admin@enterprise.ca / password"
