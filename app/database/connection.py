"""Conexión a PostgreSQL con SQLAlchemy.

Importante: este módulo NUNCA crea tablas. El esquema (`sensores`,
`sensor_magnitudes`, `mediciones`) ya existe en la base suministrada por el
docente; la aplicación solo lo consulta y escribe mediciones.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Clase base de todos los modelos ORM."""


def build_database_url() -> str | URL:
    """Arma la URL de conexión.

    Prioridad: `DATABASE_URL` completa; si no existe se usan las variables
    separadas (`URL.create` escapa correctamente caracteres especiales en la
    contraseña).
    """
    settings = get_settings()
    if settings.database_url:
        return settings.database_url

    faltan = [
        nombre
        for nombre, valor in (
            ("DB_HOST", settings.db_host),
            ("DB_NAME", settings.db_name),
            ("DB_USER", settings.db_user),
            ("DB_PASSWORD", settings.db_password),
        )
        if not valor
    ]
    if faltan:
        raise RuntimeError(f"Faltan variables de entorno de la base de datos: {', '.join(faltan)}")

    return URL.create(
        drivername="postgresql+psycopg2",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Crea el engine una sola vez (carga perezosa para facilitar los tests)."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(build_database_url(), pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def configure_engine(engine: Engine) -> None:
    """Permite inyectar un engine (usado por las pruebas con SQLite)."""
    global _engine, _SessionLocal
    _engine = engine
    _SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición, siempre cerrada."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def verificar_conexion() -> None:
    """Falla rápido si no hay conexión (Actividad 1, paso 7)."""
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
