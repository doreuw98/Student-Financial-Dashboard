"""Profiles for users authenticated by Streamlit's configured OIDC provider."""

import hashlib
import json
import os
import time

from accounts import LANGUAGES
from cloud_database import CloudDatabase
from finance import database


def data_directory(local_path):
    mode = os.environ.get("DASHBOARD_MODE", "local")
    if mode == "local":
        return local_path
    if mode != "hosted":
        raise ValueError("Invalid DASHBOARD_MODE.")
    dsn = os.environ.get("DASHBOARD_DATABASE_URL", "")
    if not dsn.startswith(("postgresql://", "postgres://")):
        raise ValueError("Hosted mode requires DASHBOARD_DATABASE_URL.")
    return CloudDatabase(dsn)


def identity(claims):
    issuer, subject = claims.get("iss"), claims.get("sub")
    expires_at = claims.get("exp")
    if (
        claims.get("email_verified") is not True
        or not isinstance(expires_at, int) or expires_at <= time.time()
        or not isinstance(issuer, str) or not issuer
        or not isinstance(subject, str) or not subject
    ):
        return None
    # Use the immutable provider identity, never the email or display name.
    key = json.dumps([issuer, subject]).encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def profile(path, claims, language):
    user_id = identity(claims)
    if user_id is None:
        return None
    with database(path, initialize=True) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS hosted_profiles "
            "(id TEXT PRIMARY KEY, language TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO hosted_profiles VALUES (?, ?) ON CONFLICT(id) DO NOTHING",
            (user_id, language),
        )
        row = connection.execute(
            "SELECT language FROM hosted_profiles WHERE id=?", (user_id,)
        ).fetchone()
    return {
        "id": user_id,
        "display_name": claims.get("nickname") or claims.get("name") or "",
        "language": row["language"],
    }


def set_language(path, user_id, language):
    if language not in LANGUAGES:
        raise ValueError("Unsupported language.")
    with database(path) as connection:
        connection.execute(
            "UPDATE hosted_profiles SET language=? WHERE id=?", (language, user_id)
        )
