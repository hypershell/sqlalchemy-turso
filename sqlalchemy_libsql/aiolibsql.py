from sqlalchemy_libsql.libsql import SQLiteDialect_libsql


class SQLiteDialect_aiolibsql(SQLiteDialect_libsql):
    driver = "libsql"
    supports_statement_cache = SQLiteDialect_libsql.supports_statement_cache
    is_async = True


dialect = SQLiteDialect_aiolibsql
