from app.core.config import Settings


def test_separate_fields_build_url_without_manual_encoding() -> None:
    settings = Settings(
        _env_file=None,
        database_url=None,
        db_driver="postgresql+psycopg",
        db_host="localhost",
        db_port=5432,
        db_name="pharmapulse",
        db_user="pharmapulse",
        db_password="password@123",
    )

    url = settings.sqlalchemy_url

    assert url.drivername == "postgresql+psycopg"
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "pharmapulse"
    assert url.username == "pharmapulse"
    assert url.password == "password@123"

    rendered = url.render_as_string(hide_password=False)
    assert "password%40123" in rendered
    assert "password@123" not in rendered


def test_database_url_override_takes_precedence() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://override:secret@db.example:5433/other",
        db_host="ignored-host",
        db_name="ignored-db",
        db_user="ignored-user",
        db_password="ignored-password",
    )

    url = settings.sqlalchemy_url

    assert url.host == "db.example"
    assert url.port == 5433
    assert url.database == "other"
    assert url.username == "override"
    assert url.password == "secret"


def test_blank_database_url_falls_back_to_fields() -> None:
    settings = Settings(
        _env_file=None,
        database_url="   ",
        db_host="dbhost",
        db_port=6543,
        db_name="dbname",
        db_user="dbuser",
        db_password="p@ss:word/with#chars",
    )

    url = settings.sqlalchemy_url

    assert url.host == "dbhost"
    assert url.port == 6543
    assert url.database == "dbname"
    assert url.username == "dbuser"
    assert url.password == "p@ss:word/with#chars"
