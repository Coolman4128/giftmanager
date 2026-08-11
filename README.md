# Gift Manager

## Run locally (Windows PowerShell)

Python 3.12 is recommended. From this project directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Then open <http://127.0.0.1:8000/>. Register an account, log in, and create or
join a family to use the gift list.

The local setup uses SQLite and development-only defaults, so no `.env` file is
required. For deployment, configure at least:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
DATABASE_URL=postgresql://user:password@host:5432/database
ALLOWED_HOSTS=.example.com
```
