"""Japanese source text with English/Indonesian translations."""

import json
from pathlib import Path

import streamlit as st

MESSAGES = json.loads(
    (Path(__file__).parent / "languages.json").read_text(encoding="utf-8")
)


def t(message, **values):
    language = st.session_state.get("language", "ja")
    translated = MESSAGES.get(message, {}).get(language, message)
    return translated.format(**values) if values else translated
