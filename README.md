# SaaS Enterprise — backend Django REST Framework + frontend React

API multi-tenant (Django 5 + DRF, authentification par jeton Bearer) et frontend React 18 / Vite / Tailwind
**inchangé** (identique octet pour octet à la version Laravel : le contrat d'API est respecté à la lettre).

## Démarrage rapide

Prérequis : **Python 3.11+** et **Node 18+**.

```bash
./setup.sh                 # Windows : setup.bat   (RUN_TESTS=1 ./setup.sh pour lancer aussi les tests)
```

Puis deux terminaux :

```bash
cd backend  && source .venv/bin/activate && python manage.py runserver     # API  → http://127.0.0.1:8000
cd frontend && npm run dev                                                  # SPA  → http://localhost:5173
```

Le script crée le virtualenv, installe les dépendances, génère `SECRET_KEY` dans `.env`, applique les migrations
(les forfaits FREE / PRO / ENTERPRISE sont créés par une migration de données) et charge les données de démo.
SQLite par défaut ; PostgreSQL/MySQL via `DB_ENGINE` dans `.env` (installer alors `psycopg` ou `mysqlclient`).

### Comptes de démonstration (mot de passe `password`)

| E-mail | Rôle | Tenant |
|---|---|---|
| admin@enterprise.ca | SUPER_ADMIN | Enterprise Démo Inc. (ENTERPRISE) |
| manager@enterprise.ca | MANAGER | idem |
| user@enterprise.ca | USER | idem |
| claire@autre.fr | SUPER_ADMIN | **Autre Société SARL** (FREE) — sert à vérifier l'isolation |

`python manage.py seed_demo --flush` recrée la démo.

## Arborescence

```
backend/
  config/         settings, urls, wsgi/asgi
  core/           contexte de tenant (ContextVar), manager scopé, authentification, permissions,
                  format d'erreurs, dashboard, tests/
  tenants/        Plan, Tenant, TenantInvitation + migration des forfaits + commande seed_demo
  accounts/       User (connexion par e-mail), AuthToken, login/logout/me/team, CRUD /users
  billing/        plans, inscription d'entreprise, invitations, abonnement
  business/       Client, Employee, Product, Service
  projects/       Project, Task, Kanban (déplacement avec réindexation)
  timetracking/   TimeEntry (un chronomètre actif par utilisateur)
  notifications/  Notification
frontend/         React (inchangé)
```

## Sécurité : décisions clés

- **Isolation par tenant** : `TenantOwnedModel.objects` filtre *toujours* sur le tenant courant et renvoie **un résultat vide**
  s'il n'y en a pas (échec fermé). `unscoped` est réservé aux scripts. Le tenant est posé après l'authentification par
  `TenantContextMixin` (`ContextVar`), **uniquement** depuis l'utilisateur : l'en-tête `X-Tenant-ID`, l'URL ou le corps sont ignorés.
  À la création, le tenant est assigné automatiquement. Un objet d'un autre tenant répond **404** (jamais 403).
- **Unicité par tenant** : `UniqueConstraint(tenant, identifiant|matricule|code)` en base + validation dans les serializers.
- **Jetons** : aléatoires, **stockés hachés (SHA-256)**, expiration 7 jours, révoqués au `/logout` et au changement de mot de passe.
  Les jetons d'invitation sont eux aussi hachés et à usage unique (mise à jour conditionnelle atomique).
- **Rôles** : classes de permission dédiées (`IsAdminRole`, `IsManagerRole`, `ManagerWriteOnly`). Le rôle SUPER_ADMIN n'est jamais
  attribuable via l'API ; seul le propriétaire peut modifier son compte (un ADMIN ne peut pas le détourner) ; on ne se supprime/suspend pas soi-même.
- **Anti brute-force** : 10 requêtes/minute sur login, inscription et acceptation d'invitation (réponse 429).
- **Chronomètre** : contrainte unique partielle en base (un seul `is_running` par utilisateur), même en cas de requêtes concurrentes.

## Contrat d'API (préfixe `/api`, sans slash final)

Erreurs : validation → **422** `{"message", "errors": {champ: [..]}}` ; autres → `{"message"}`. Listes = tableaux JSON simples ;
montants = nombres JSON ; datetimes ISO 8601 UTC (`...Z`).

| Route | Qui |
|---|---|
| `POST /login` · `POST /tenants/register` · `POST /invitations/accept` · `GET /invitations/{token}` · `GET /plans` | public |
| `POST /logout` · `GET /me` · `GET /team` · `GET /dashboard` · `GET /billing` · `/projects…` · `/tasks…` · `/time-entries…` · `/notifications…` | tout utilisateur connecté |
| `GET /clients` `/products` `/services` | tous les rôles |
| `POST/PUT/DELETE` clients, produits, services · **tout** `/employees` | MANAGER, ADMIN, SUPER_ADMIN |
| `/users` · `GET /tenants/invitations` · `POST /tenants/invite` · `POST /billing/subscribe` | ADMIN, SUPER_ADMIN |
| `DELETE /projects/{id}` | MANAGER et au-dessus |

## Tests

```bash
cd backend && python manage.py test        # 69 tests (unittest/DRF), aucune dépendance supplémentaire
```

Couverture : isolation entre deux tenants (liste, détail → 404, création, en-tête ignoré, échec fermé), permissions par rôle,
quotas (utilisateurs, invitations en attente, projets), invitations à usage unique, inscription, abonnement, Kanban (réindexation
des deux colonnes), un seul chronomètre actif, durées positives, jetons (expiration, révocation, hachage), anti brute-force,
format d'erreurs 422, nombres JSON, dates UTC.

## Ce qui a été vérifié — et ce qui ne l'a PAS été

| Vérifié (analyse statique, hors exécution) | Résultat |
|---|---|
| Compilation de tous les fichiers Python (74) | OK |
| Noms indéfinis et imports internes cassés (vérificateur AST maison, pas pyflakes) | 0 problème |
| Cycles d'imports entre modules | aucun |
| Modèles ⇄ migrations (mêmes modèles, champs, contraintes, index) | 0 écart |
| Chaque appel API du frontend (47 distincts) a une route Django | oui |
| Frontend identique à l'original | oui (diff vide) |

| **NON exécuté** (Django/DRF indisponibles dans l'environnement de rédaction, pas de réseau) | |
|---|---|
| `python manage.py check`, `makemigrations --check`, `migrate` | jamais lancés |
| Les 69 tests | écrits, **jamais exécutés** |
| L'application en fonctionnement, le build React | jamais lancés |

**Migrations** : elles ont été *générées par un script à partir du code des modèles* (pas par `makemigrations`).
`setup.sh`/`setup.bat` lancent `makemigrations --noinput` avant `migrate` : si la moindre divergence existait, Django générerait
lui-même la migration corrective. Lancez `python manage.py test` après l'installation : si un test échoue, c'est probablement un
détail d'exécution que l'analyse statique ne pouvait pas voir — signalez-le avec la trace.

## Limites connues

- **Paiement** : le changement de forfait est en mode démonstration (aucun paiement). Pour Stripe, remplacer `SubscribeView` par une session Checkout + webhook.
- **E-mails** : les invitations renvoient un lien à copier ; aucun e-mail n'est envoyé (configurer `EMAIL_*` et envoyer le lien).
- **Temps réel** : pas de WebSocket (Django Channels non inclus) ; le frontend interroge périodiquement l'API (Kanban 8 s, notifications 15 s).
- **Pas d'interface d'administration Django** (`django.contrib.admin` volontairement absent) ni de `createsuperuser` : les comptes se créent par l'API ou `seed_demo`.
- **Production** : `DEBUG=False`, `ALLOWED_HOSTS`, HTTPS (et `SECURE_*`), base PostgreSQL/MySQL, serveur WSGI (gunicorn/uwsgi) ; le cache de limitation de débit est en mémoire locale (un cache partagé type Redis est préférable avec plusieurs processus).
- Suppression d'un utilisateur : ses projets sont réattribués à l'auteur de la suppression ; ses entrées de temps et notifications sont supprimées.
- Une violation d'unicité en concurrence stricte (deux créations simultanées du même identifiant) lèverait une erreur 500 au lieu d'un 422 (la base reste cohérente).
# SaaS Enterprise – Plateforme de gestion d'entreprise

\<p align="center">   \<strong>Plateforme SaaS moderne de gestion d'entreprise développée avec Django et React.\</strong> \</p>

\<p align="center">   \<img src="[https://img.shields.io/badge/Backend-Django-092E20?logo=django&logoColor=white](https://img.shields.io/badge/Backend-Django-092E20?logo=django\&logoColor=white)" />   \<img src="[https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react\&logoColor=black)" />   \<img src="[https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white](https://img.shields.io/badge/Language-Python-3776AB?logo=python\&logoColor=white)" />   \<img src="[https://img.shields.io/badge/JavaScript-ES6%2B-F7DF1E?logo=javascript&logoColor=black](https://img.shields.io/badge/JavaScript-ES6%2B-F7DF1E?logo=javascript\&logoColor=black)" />   \<img src="[https://img.shields.io/badge/Architecture-REST%20API-blue](https://img.shields.io/badge/Architecture-REST%20API-blue)" /> \</p>

## Présentation du projet

**SaaS Enterprise** est une application web de gestion d'entreprise conçue selon une architecture séparant le frontend et le backend.

La plateforme repose sur Django pour la gestion des données, des traitements métier et des API REST, tandis que React assure l'interface utilisateur et l'expérience interactive.

L'objectif est de proposer une solution centralisée, évolutive et sécurisée permettant de gérer différentes activités d'une entreprise.

## Architecture technique

| Partie                           | Technologies                  |
| -------------------------------- | ----------------------------- |
| Backend                          | Python, Django                |
| API                              | Django REST Framework         |
| Frontend                         | React                         |
| Gestion des dépendances frontend | npm                           |
| Base de données                  | Selon la configuration Django |
| Communication                    | API REST / HTTP               |
| Environnement backend            | Python Virtual Environment    |

## Fonctionnalités et modules

Le backend est organisé en plusieurs applications métier :

- **Accounts** : gestion des comptes utilisateurs.
- **Billing** : gestion de la facturation.
- **Business** : gestion des activités de l'entreprise.
- **Core** : fonctionnalités centrales de la plateforme.
- **Notifications** : gestion des notifications.
- **Projects** : gestion des projets.
- **Tenants** : gestion des organisations et des espaces clients.
- **Timetracking** : suivi du temps de travail.
- **Dashboard** : accès aux données du tableau de bord.

*Les fonctionnalités effectivement disponibles dépendent de l'implémentation de chaque module.*

## Structure du projet

```text
saas-enterprise/
│
├── backend/
│   ├── accounts/
│   ├── billing/
│   ├── business/
│   ├── config/
│   ├── core/
│   ├── notifications/
│   ├── projects/
│   ├── tenants/
│   ├── timetracking/
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

## Installation et configuration

### 1. Prérequis

Installer les outils suivants :

- Python 3.14 ou version compatible avec les dépendances du projet.
- Node.js et npm.
- Git.
- Un éditeur de code comme Visual Studio Code.

### 2. Récupérer le projet

```bash
git clone https://github.com/TON-PSEUDO/saas-enterprise.git
cd saas-enterprise
```

### 3. Configuration du backend Django

Accéder au backend :

```bash
cd backend
```

Créer un environnement virtuel :

```bash
py -m venv .venv
```

Activer l'environnement sous Windows PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```bash
py -m pip install -r requirements.txt
```

Créer le fichier d'environnement :

```powershell
Copy-Item .env.example .env
```

Ouvrir `.env` et renseigner les variables nécessaires :

```env
SECRET_KEY=YOUR_SECRET_KEY
DEBUG=True
```

Compléter également les paramètres de base de données si le projet les exige.

Appliquer les migrations :

```bash
py manage.py migrate
```

Démarrer le serveur Django :

```bash
py manage.py runserver
```

Backend :

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 4. Configuration du frontend React

Ouvrir un deuxième terminal :

```bash
cd frontend
```

Installer les dépendances :

```bash
npm install
```

Démarrer le serveur frontend :

```bash
npm run dev
```

Frontend :

[http://localhost:5173/](http://localhost:5173/)

*L'adresse exacte dépend du serveur de développement configuré dans le projet.*

## API Backend

Les routes API sont accessibles à partir du préfixe :

```text
http://127.0.0.1:8000/api/
```

Route du tableau de bord :

```text
http://127.0.0.1:8000/api/dashboard
```

Les endpoints peuvent nécessiter une authentification et des paramètres spécifiques.

## Sécurité

Le projet utilise une configuration par variables d'environnement.

Bonnes pratiques :

- Ne jamais publier le fichier `.env`.
- Ne jamais exposer les clés secrètes.
- Protéger les accès utilisateurs.
- Valider les données reçues par les API.
- Configurer CORS selon les origines autorisées.
- Utiliser HTTPS en production.
- Désactiver le mode DEBUG en production.

## Développement

Pour contribuer au projet :

1. Créer une branche de développement.
2. Effectuer les modifications.
3. Tester les fonctionnalités.
4. Soumettre les changements.

Exemple :

```bash
git checkout -b feature/nouvelle-fonctionnalite
git add .
git commit -m "Add new feature"
git push origin feature/nouvelle-fonctionnalite
```

## Perspectives d'évolution

- Renforcement de la gestion des rôles et permissions.
- Amélioration du système multi-tenant.
- Développement des fonctionnalités avancées de facturation.
- Intégration de tableaux de bord analytiques.
- Mise en place de tests automatisés.
- Conteneurisation avec Docker.
- Déploiement cloud et intégration CI/CD.

## Auteur

**William Diogne Kamgang**

Projet personnel de développement Full Stack et d'architecture d'applications SaaS.

## Licence

Ce projet est destiné à des fins d'apprentissage, de développement et de démonstration professionnelle. Les conditions de réutilisation peuvent être définies dans un fichier LICENSE.

