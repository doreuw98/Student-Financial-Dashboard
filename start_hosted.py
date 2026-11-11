"""Start the Render service with the hosted login settings."""

import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
import tomllib

import tomli_w


def configure_auth(source, destination):
    with source.open("rb") as config_file:
        config = tomllib.load(config_file)
    config["auth"].setdefault("client_kwargs", {})["prompt"] = "login"

    destination.parent.mkdir(exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            tomli_w.dump(config, output)
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    try:
        configure_auth(Path("/etc/secrets/secrets.toml"), Path(".streamlit/secrets.toml"))
    except (OSError, ValueError, KeyError, AttributeError, TypeError):
        sys.exit("Render Secret Files must contain a valid secrets.toml with an [auth] section.")

    os.environ["DASHBOARD_MODE"] = "hosted"
    os.execv(
        sys.executable,
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.address", "0.0.0.0",
            "--server.port", os.environ.get("PORT", "10000"),
            "--server.headless", "true",
        ],
    )


if __name__ == "__main__":
    main()
