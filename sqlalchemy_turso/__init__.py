from sqlalchemy.dialects import registry as _registry
from .aioturso import SQLiteDialect_aioturso
from .turso import SQLiteDialect_turso

__version__ = "0.1.0-pre"

_registry.register("sqlite.turso", "sqlalchemy_turso.turso", "SQLiteDialect_turso")
_registry.register(
    "sqlite.aioturso", "sqlalchemy_turso.aioturso", "SQLiteDialect_aioturso"
)
