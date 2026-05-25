"""AI-powered natural language translation for Angis."""

from __future__ import annotations
import os
import json
import re
from .errors import AngisError


class AITranslator:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ANGIS_AI_KEY")
        self._cache_path = os.path.expanduser("~/.angis_ai_cache.json")
        self._cache: dict[str, str] = {
            # Italian technical fallbacks
            "mostra": 'say',
            "stampa": 'print',
            "imposta": 'set',
            "aggiungi": 'add',
            "fai": 'make',
            "tabella": 'table',
            "richiesta": 'request',
            "scarica": 'fetch',
            "carica": 'load',
            "salva": 'save',
            "progetto": 'blueprint',
            
            # Portuguese technical fallbacks
            "mostre": 'say',
            "imprima": 'print',
            "defina": 'set',
            "adicione": 'add',
            "tabela": 'table',
            "projeto": 'blueprint',
            "carregar": 'load',
            "buscar": 'fetch',
            
            # Japanese (romaji) fallbacks
            "hyoji": 'say',
            "printo": 'print',
            "settei": 'set',
            "tsuika": 'add',
        }
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path, "r") as f:
                    cached = json.load(f)
                    self._cache.update(cached)
            except Exception:
                pass

    def _save_cache(self):
        try:
            # We don't save builtins
            builtins = {
                "mostra", "stampa", "imposta", "aggiungi", "fai", "tabella", "richiesta", "scarica", "carica", "salva", "progetto",
                "mostre", "imprima", "defina", "adicione", "tabela", "projeto", "carregar", "buscar",
                "hyoji", "printo", "settei", "tsuika"
            }
            to_save = {k: v for k, v in self._cache.items() if k not in builtins}
            with open(self._cache_path, "w") as f:
                json.dump(to_save, f)
        except Exception:
            pass

    def translate(self, phrase: str) -> str | None:
        """Translate a natural language phrase into a standard Angis phrase."""
        phrase = phrase.strip().lower()
        if phrase in self._cache:
            return self._cache[phrase]
        
        # 1. Fuzzy verb matching
        for verb, translation in self._cache.items():
            if phrase.startswith(verb + " "):
                return translation + " " + phrase[len(verb):].strip()

        # 2. Heuristics for assignments and simple expressions
        set_match = re.fullmatch(r"([^\W\d]\w*)\s*(?:is|to|equal|equals|=|è|é)\s+(.+)", phrase)
        if set_match:
            return f"set {set_match.group(1)} to {set_match.group(2)}"
        
        # 3. Handle "fetch from X" variations
        fetch_match = re.search(r"(?:fetch|get|download|scarica|buscar)\s+(?:from|da|de)\s+(https?://[^\s]+)", phrase)
        if fetch_match:
            return f"fetch {fetch_match.group(1)} as data"

        # 4. Handle "save to X" variations
        save_match = re.search(r"(?:save|store|salva|guardar)\s+(.+?)\s+(?:to|in|a|em)\s+(.+)", phrase)
        if save_match:
            return f"save {save_match.group(1)} to {save_match.group(2)}"

        return None

    def learn(self, phrase: str, angis_code: str):
        """Manually teach the AI a translation."""
        self._cache[phrase.strip().lower()] = angis_code
        self._save_cache()


_INSTANCE = AITranslator()


def translate_phrase(phrase: str) -> str | None:
    return _INSTANCE.translate(phrase)


def teach_phrase(phrase: str, angis_code: str):
    _INSTANCE.learn(phrase, angis_code)
