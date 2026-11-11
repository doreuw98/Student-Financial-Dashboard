"""PostgreSQL storage for hosted profiles and isolated account ledgers."""

from contextlib import contextmanager
from dataclasses import dataclass, field


def storage_error_code(error, stage):
    """Classify failures without exposing database credentials or SQL values."""
    if error.sqlstate:
        return f"{stage}:SQLSTATE-{error.sqlstate}"
    message = str(error).lower()
    for fragment, code in (
        ("password authentication failed", "AUTHENTICATION"),
        ("certificate verify failed", "TLS-CERTIFICATE"),
        ("could not translate host name", "DNS"),
        ("name or service not known", "DNS"),
        ("timeout", "TIMEOUT"),
        ("channel binding", "CHANNEL-BINDING"),
    ):
        if fragment in message:
            return f"{stage}:{code}"
    return f"{stage}:CONNECTION"


@dataclass(frozen=True)
class CloudDatabase:
    dsn: str = field(repr=False)
    schema: str = "dashboard_profiles"

    def ledger(self, user_id, mode):
        prefix = "demo" if mode == "demo" else "user"
        return CloudDatabase(self.dsn, f"{prefix}_{user_id[:56]}")

    @contextmanager
    def connect(self, *, initialize=False):
        import psycopg
        from psycopg import sql
        from psycopg.rows import dict_row

        stage = "connect"
        try:
            with psycopg.connect(
                self.dsn, row_factory=dict_row, connect_timeout=10,
                sslmode="verify-full", sslrootcert="system",
            ) as connection:
                stage = "schema"
                if initialize:
                    connection.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                        (self.schema,),
                    )
                    connection.execute(
                        sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.schema))
                    )
                connection.execute(
                    sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(self.schema))
                )
                stage = "query"
                yield CloudConnection(connection)
        except psycopg.Error as error:
            code = storage_error_code(error, stage)
            raise OSError(f"Cloud storage could not complete the request. [{code}]") from None


class CloudConnection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, statement, parameters=()):
        # Only fixed application SQL reaches this adapter; values remain bound.
        return self.connection.execute(statement.replace("?", "%s"), parameters)
