import ast
import json
import re
import unittest
from pathlib import Path
from string import Formatter


class TranslationTests(unittest.TestCase):
    def test_all_messages_and_placeholders_are_available_in_both_languages(self):
        root = Path(__file__).parents[1]
        messages = json.loads((root / "languages.json").read_text(encoding="utf-8"))
        for name in ["app.py", "accounts.py", "finance.py"]:
            for node in ast.walk(ast.parse((root / name).read_text(encoding="utf-8"))):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and re.search(r"[\u3040-\u30ff\u3400-\u9fff]", node.value)
                ):
                    self.assertIn(node.value, messages, (name, node.value))
        for source, translations in messages.items():
            source_fields = {
                field for _, field, _, _ in Formatter().parse(source) if field
            }
            for language in ["en", "id"]:
                self.assertTrue(translations[language])
                fields = {
                    field
                    for _, field, _, _ in Formatter().parse(translations[language])
                    if field
                }
                self.assertEqual(fields, source_fields, (source, language))
