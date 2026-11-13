"""Check database connectivity and credentials without printing secrets.

Run from the backend directory:
    python -m scripts.check_db
"""

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.database.session import engine


def _sanitize(message: str, password: str | None) -> str:
    if password:
        return message.replace(password, "***")
    return message


def main() -> None:
    url = settings.sqlalchemy_url
    print("Database target")
    print(f"  driver:   {url.drivername}")
    print(f"  host:     {url.host}")
    print(f"  port:     {url.port}")
    print(f"  database: {url.database}")
    print(f"  user:     {url.username}")
    print(f"  password: {'configured' if url.password else 'not set'}")
    print()

    try:
        with engine.connect() as connection:
            current_user, current_database, version = connection.execute(
                text("SELECT current_user, current_database(), version()")
            ).one()
    except SQLAlchemyError as exc:
        first_line = str(exc).strip().splitlines()[0]
        print("Connection: FAILED")
        print(f"  {_sanitize(first_line, url.password)}")
        print()
        print("Check the following:")
        print("  1. PostgreSQL is running and the host/port are correct.")
        print("  2. The role exists and can log in.")
        print("  3. DB_PASSWORD matches the role password exactly.")
        print("  4. The database exists and the role can connect to it.")
        raise SystemExit(1) from None

    print("Connection: OK")
    print(f"  connected as: {current_user}")
    print(f"  database:     {current_database}")
    print(f"  server:       {str(version).split(',')[0]}")

    try:
        if inspect(engine).has_table("alembic_version"):
            with engine.connect() as connection:
                revision = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one_or_none()
            print(f"  migration:    {revision or 'none'}")
        else:
            print("  migration:    not applied (alembic_version table missing)")
    except SQLAlchemyError:
        print("  migration:    could not read alembic_version")


if __name__ == "__main__":
    main()
