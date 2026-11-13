# PostgreSQL setup with pgAdmin 4

This guide creates a dedicated local role and database for PharmaPulse. Never use a production database for this POC.

## 1. Create a login role

1. Open pgAdmin 4 and connect to your PostgreSQL server.
2. Right-click **Login/Group Roles → Create → Login/Group Role**.
3. **General → Name:** `pharmapulse`
4. **Definition → Password:** choose a strong local password.
5. **Privileges → Can login?:** `Yes`
6. Click **Save**.

## 2. Create the database

1. Right-click **Databases → Create → Database**.
2. **Database:** `pharmapulse`
3. **Owner:** `pharmapulse`
4. Click **Save**.

The `pharmapulse` role owns the database, so it can create tables during Alembic migrations.

## 3. Test the connection

```powershell
psql -h localhost -p 5432 -U pharmapulse -d pharmapulse -c "SELECT current_database();"
```

Expected:

```text
 current_database
------------------
 pharmapulse
```

## 4. Configure the backend

Create `backend/.env` from the example:

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Set:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pharmapulse
DB_USER=pharmapulse
DB_PASSWORD=YOUR_PASSWORD
```

Notes:

- `DB_PASSWORD` is passed to SQLAlchemy as a raw value. Characters such as `@`, `:`, `/`, and `#` are handled automatically by `URL.create()`.
- The optional `DATABASE_URL` override takes precedence over `DB_*`. If you use it, URL-encode special password characters: `@` → `%40`, `:` → `%3A`, `/` → `%2F`, `#` → `%23`, `%` → `%25`.
- `backend/.env` is gitignored. Do not commit it.
- If your server uses another port, change `5432`.

## 5. Check the credentials

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m scripts.check_db
```

Expected:

```text
Database target
  driver:   postgresql+psycopg
  host:     localhost
  port:     5432
  database: pharmapulse
  user:     pharmapulse
  password: configured

Connection: OK
  connected as: pharmapulse
  database:     pharmapulse
  server:       PostgreSQL 18.x ...
  migration:    not applied (alembic_version table missing)
```

The command never prints the password. On failure it prints a short, sanitized reason and exits with code `1`.

| Message | Meaning |
|---|---|
| `password authentication failed for user "pharmapulse"` | Wrong password, or the role is configured differently. Reset the password in pgAdmin. |
| `role "pharmapulse" does not exist` | Wrong username or the role was not created. |
| `database "pharmapulse" does not exist` | Wrong database name or the database was not created. |
| `connection refused` | PostgreSQL is not running, or host/port is wrong. |
| `failed to resolve host` | Wrong host, or a malformed `DATABASE_URL` override. |

Alternative check with `psql`:

```powershell
psql -h localhost -p 5432 -U pharmapulse -d pharmapulse -c "SELECT current_user, current_database();"
```

`psql` prompts for the password. A successful query means the password is correct. pgAdmin 4 does not provide a reliable "test password" button for an existing role; a real connection attempt is the authoritative check.

## 6. Apply migrations

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
alembic current
```

Expected current revision:

```text
311745f27a91 (head)
```

## 7. Seed master data

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m scripts.seed
```

Expected:

```text
Seed complete: 5 brands, 4 regions, 2 anomaly rules.
```

The seed is idempotent; run it again and the counts stay the same.

## 8. Verify readiness

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

In another PowerShell window:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

Expected:

```text
status  database
------  --------
healthy available
```

## 9. Useful psql checks

List tables:

```powershell
psql -h localhost -p 5432 -U pharmapulse -d pharmapulse -c "\dt"
```

Inspect the migration history:

```powershell
psql -h localhost -p 5432 -U pharmapulse -d pharmapulse -c "SELECT * FROM alembic_version;"
```

## Security notes

- The POC has no authentication yet. Do not expose this API to the internet.
- Keep PostgreSQL bound to localhost for the POC.
- Never commit `backend/.env` or real credentials.
- Do not import patient data, prescription data, or production KAM exports.
