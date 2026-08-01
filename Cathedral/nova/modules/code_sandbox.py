#!/usr/bin/env python3
"""
code_sandbox.py — Safe Python code execution for Nova.

Runs code in an isolated subprocess with:
  - Hard timeout (default 12 seconds)
  - Blocklist for shell-escape patterns
  - Stdout/stderr capture (truncated to 3k chars each)
  - Return code + success flag

Nova uses this to test every piece of code she writes before saving it.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path

CATHEDRAL = Path.home() / "cathedral"

# ── safety blocklist ──────────────────────────────────────────────────────────
# These patterns indicate attempts to escape the sandbox or cause damage.
# Nova doesn't need them for legitimate coding practice.

_BLOCKED = [
    r"\bos\.system\s*\(",
    r"\bos\.popen\s*\(",
    r"\bsubprocess\s*\.\s*(?:run|call|Popen|check_output|getoutput)\s*\(",
    r"\beval\s*\(",
    r"\bcompile\s*\(",
    r"__import__\s*\(",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+ctypes\b",
    r"shutil\s*\.\s*rmtree",
    r"os\s*\.\s*remove\s*\(\s*['\"](?!/home/\w+/cathedral)",   # only allow removing inside cathedral
]

_BLOCKED_RE = re.compile("|".join(_BLOCKED), re.IGNORECASE)


def validate(code: str) -> list[str]:
    """
    Check code for dangerous patterns.
    Returns list of violation strings (empty = safe to run).
    """
    violations = []
    for pat in _BLOCKED:
        if re.search(pat, code, re.IGNORECASE):
            violations.append(pat.replace(r"\b", "").replace(r"\s*", " ").replace(r"\(", "("))
    return violations


def run(code: str, timeout: int = 12) -> dict:
    """
    Execute Python code in a subprocess sandbox.

    Returns:
        {
            "ok":         bool,
            "stdout":     str,
            "stderr":     str,
            "returncode": int,
            "timed_out":  bool,
            "blocked":    list[str],   # non-empty if blocked before running
        }
    """
    violations = validate(code)
    if violations:
        return {
            "ok":         False,
            "stdout":     "",
            "stderr":     f"Blocked patterns detected: {violations}",
            "returncode": -1,
            "timed_out":  False,
            "blocked":    violations,
        }

    # Write to temp file
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", dir="/tmp",
            prefix="nova_sandbox_", delete=False
        ) as f:
            f.write(code)
            tmp = f.name

        result = subprocess.run(
            ["python3", tmp],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(CATHEDRAL),   # working dir is cathedral
        )

        return {
            "ok":         result.returncode == 0,
            "stdout":     result.stdout[:3000],
            "stderr":     result.stderr[:2000],
            "returncode": result.returncode,
            "timed_out":  False,
            "blocked":    [],
        }

    except subprocess.TimeoutExpired:
        return {
            "ok":         False,
            "stdout":     "",
            "stderr":     f"Execution timed out after {timeout}s",
            "returncode": -1,
            "timed_out":  True,
            "blocked":    [],
        }
    except Exception as e:
        return {
            "ok":         False,
            "stdout":     "",
            "stderr":     str(e),
            "returncode": -1,
            "timed_out":  False,
            "blocked":    [],
        }
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except Exception:
                pass


def extract_code(text: str) -> str:
    """
    Pull Python code from an LLM response.
    Handles ```python ... ``` blocks; falls back to full text.
    """
    # Try fenced blocks in order of specificity
    for fence in (r"```python\n(.*?)```", r"```py\n(.*?)```", r"```\n(.*?)```"):
        m = re.search(fence, text, re.DOTALL)
        if m:
            return m.group(1).strip()
    # No fence — return stripped text, filtering out obvious prose
    lines = []
    in_code = False
    for line in text.splitlines():
        stripped = line.strip()
        # Heuristic: lines starting with keywords, indentation, or assignments
        if stripped.startswith(("def ", "class ", "import ", "from ", "#", "if ", "for ",
                                 "while ", "try:", "with ", "return ", "@", "async ")):
            in_code = True
        if in_code:
            lines.append(line)
    return "\n".join(lines).strip() if lines else text.strip()
