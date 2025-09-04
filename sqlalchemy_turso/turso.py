import os
import urllib.parse

from sqlalchemy import util
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from turso import Connection


def _build_connection_url(url, query, secure):
    # sorting of keys is for unit test support
    query_str = urllib.parse.urlencode(sorted(query.items()))

    if not url.host:
        if query_str:
            return f"{url.database}?{query_str}"
        return url.database
    elif secure:  # yes, pop to remove
        scheme = "https"
    else:
        scheme = "http"

    if url.username and url.password:
        netloc = f"{url.username}:{url.password}@{url.host}"
    elif url.username:
        netloc = f"{url.username}@{url.host}"
    else:
        netloc = url.host

    if url.port:
        netloc += f":{url.port}"

    return urllib.parse.urlunsplit(
        (
            scheme,
            netloc,
            url.database or "",
            query_str,
            "",  # fragment
        )
    )


class SQLiteDialect_turso(SQLiteDialect_pysqlite):
    driver = "turso"
    # need to be set explicitly
    supports_statement_cache = SQLiteDialect_pysqlite.supports_statement_cache

    @classmethod
    def import_dbapi(cls):
        import turso
        from sqlite3 import Error
        # NOTE: faked attributes for the sake of sqlalchemy
        turso.paramstyle = 'qmark'
        turso.sqlite_version_info = (3, 47, 1)
        turso.Error = Error  # Add Error class that SQLAlchemy expects
        return turso

    def on_connect(self):
        import turso
        sqlite3_connect = super().on_connect()

        def connect(conn):
            # turso: there is no support for create_function()
            if isinstance(conn, Connection):
                return
            return sqlite3_connect(conn)

        return connect

    def create_connect_args(self, url):
        pysqlite_args = (
            ("uri", bool),
            ("timeout", float),
            ("isolation_level", str),
            ("detect_types", int),
            ("check_same_thread", bool),
            ("cached_statements", int),
            ("secure", bool),  # turso extra, selects between ws and wss
        )
        opts = url.query
        turso_opts = {}
        for key, type_ in pysqlite_args:
            util.coerce_kw_type(opts, key, type_, dest=turso_opts)

        if url.host:
            turso_opts["uri"] = True

        if turso_opts.get("uri", False):
            uri_opts = dict(opts)
            # here, we are actually separating the parameters that go to
            # sqlite3/pysqlite vs. those that go the SQLite URI.  What if
            # two names conflict?  again, this seems to be not the case right
            # now, and in the case that new names are added to
            # either side which overlap, again the sqlite3/pysqlite parameters
            # can be passed through connect_args instead of in the URL.
            # If SQLite native URIs add a parameter like "timeout" that
            # we already have listed here for the python driver, then we need
            # to adjust for that here.
            for key, type_ in pysqlite_args:
                uri_opts.pop(key, None)

            secure = turso_opts.pop("secure", False)
            connect_url = _build_connection_url(url, uri_opts, secure)
        else:
            connect_url = url.database or ":memory:"
            if connect_url != ":memory:":
                connect_url = os.path.abspath(connect_url)

        # Remove parameters that turso.connect() doesn't accept
        # turso.connect() only accepts the path argument
        turso_opts.pop("check_same_thread", None)
        turso_opts.pop("uri", None)
        turso_opts.pop("timeout", None)
        turso_opts.pop("isolation_level", None)
        turso_opts.pop("detect_types", None)
        turso_opts.pop("cached_statements", None)
        # Note: we already popped "secure" above

        # turso.connect() only accepts path, so we return empty dict for kwargs
        return [connect_url], {}

    def get_isolation_level(self, dbapi_connection):
        """Override to avoid PRAGMA read_uncommitted which Turso doesn't support.
        
        Turso doesn't support isolation levels, so we return None.
        """
        return None

    def get_default_isolation_level(self, dbapi_connection):
        """Override to avoid PRAGMA read_uncommitted which Turso doesn't support.
        
        Turso doesn't support isolation levels, so we return None.
        """
        return None

    def set_isolation_level(self, dbapi_connection, level):
        """Override to avoid setting isolation level which Turso doesn't support.
        
        Turso doesn't support changing isolation levels, so this is a no-op.
        """
        pass


dialect = SQLiteDialect_turso
