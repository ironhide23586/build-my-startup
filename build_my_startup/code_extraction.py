from typing import Tuple


def extract_file_content(task_name: str, content: str) -> Tuple[str, str]:
    """Extract raw file content from LLM output that may include markdown or prose.

    Returns (clean_content, debug_info).
    """
    debug = []
    code = content or ""
    original_length = len(code)

    if not code:
        return code, "empty"

    if ("```" in code or "here is" in code.lower() or "```python" in code.lower() or "```html" in code.lower()):
        debug.append("detected_markdown")
        lines = code.split("\n")
        code_blocks = []
        current_block = []
        code_language = None
        block_index = 0
        in_code = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code:
                    if current_block:
                        code_blocks.append({
                            'lang': code_language or 'unknown',
                            'code': '\n'.join(current_block),
                            'index': block_index,
                        })
                        block_index += 1
                    current_block = []
                else:
                    code_language = stripped[3:].strip().lower()
                in_code = not in_code
                continue
            if in_code:
                current_block.append(line)

        if current_block and in_code:
            code_blocks.append({'lang': code_language or 'unknown', 'code': '\n'.join(current_block), 'index': block_index})

        if code_blocks:
            task_lang = 'python' if task_name.endswith('.py') else 'html' if task_name.endswith('.html') else None
            selected = None
            for block in code_blocks:
                if task_lang and task_lang in block['lang']:
                    selected = block
                    break
            if not selected:
                selected = max(code_blocks, key=lambda b: len(b['code']))
            if selected:
                code = selected['code']
                debug.append(f"selected_block_{selected['index']}")
    else:
        debug.append("plain_text")

    return code, ",".join(debug) + f"|orig={original_length}|final={len(code)}"


