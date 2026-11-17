# Backend — Django 5 + DRF (multi-tenant)

Voir le `README.md` à la racine du projet (démarrage, sécurité, contrat d'API, tests, limites).

    python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env        # puis renseigner SECRET_KEY
    python manage.py migrate && python manage.py seed_demo
    python manage.py runserver
    python manage.py test
