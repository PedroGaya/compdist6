import importlib
import sys

import six

if not hasattr(six, "get_function_name"):
    six.get_function_name = lambda f: f.__name__ # type: ignore
    
for _name in ("collections_abc", "urllib", "urllib.parse", "urllib.request",
              "urllib.error", "http_cookies", "http_client", "queue",
              "configparser", "builtins", "StringIO", "cStringIO"):
    try:
        importlib.import_module(f"six.moves.{_name}")
    except ImportError:
        pass

for _key, _mod in list(sys.modules.items()):
    if _key == "six" or _key.startswith("six."):
        sys.modules["spyne.util." + _key] = _mod