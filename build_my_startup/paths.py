import os
from typing import Tuple


def default_app_paths(script_file: str) -> Tuple[str, str, str]:
    """Compute standard app paths given a builder script file.

    Returns (OUTPUT_DIR, TEMPLATES_DIR, STATIC_DIR).
    OUTPUT_DIR points to ../generated relative to the script.
    """
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(script_file)))
    output_dir = os.path.join(app_root, "generated")
    templates_dir = os.path.join(output_dir, "templates")
    static_dir = os.path.join(output_dir, "static")
    return output_dir, templates_dir, static_dir


