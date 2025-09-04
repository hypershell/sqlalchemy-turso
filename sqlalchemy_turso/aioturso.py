from sqlalchemy_turso.turso import SQLiteDialect_turso


class SQLiteDialect_aioturso(SQLiteDialect_turso):
    driver = "turso"
    supports_statement_cache = SQLiteDialect_turso.supports_statement_cache
    is_async = True


dialect = SQLiteDialect_aioturso
