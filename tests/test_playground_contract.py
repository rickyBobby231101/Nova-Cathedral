"""The playground must contain what it holds.

Daniel, 2026-09-06: "let them go do whatever. open playground and build."

"Whatever" is the requirement, and it is why the containment is tested rather
than asserted in a docstring. Several models writing into the trees the daemon
and the game run from is a race with no referee, and the canon names hidden
execution and unattended action as the Silent Order's own signature.

Three properties, in order of how badly they would fail:

  1. Nothing written here escapes the playground directory.
  2. Nothing written here is ever executed.
  3. No seat's output is merged into another's.

The first session, minutes after this was built, justified it: gemma3:4b
produced code importing psutil (the task said stdlib only), never using it, and
querying `SELECT COUNT(*) FROM pr_sqlite_dbname` — a table that does not exist —
to count file handles, which is not something a database knows. Plausible on
sight, broken on first run. In `modules/` that is a dead daemon; here it is a
file that cost nothing.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES) not in sys.path:
    sys.path.insert(0, str(MODULES))

import playground as pg


class TestNothingEscapes:
    """A model asked for a filename will sometimes give you a path."""

    @pytest.mark.parametrize("hostile,expected", [
        ("../../etc/passwd",            "passwd"),
        ("/home/daniel/.bashrc",        "bashrc"),
        ("../../../../root/.ssh/id_rsa", "id_rsa"),
        ("..\\..\\windows\\system32",   "system32"),
        ("....//....//evil.py",         "evil.py"),
        ("/dev/null",                   "null"),
    ])
    def test_a_path_is_reduced_to_a_bare_name(self, hostile, expected):
        assert pg.safe_name(hostile) == expected

    def test_a_leading_dot_cannot_hide_a_file(self):
        assert not pg.safe_name(".hidden").startswith(".")

    def test_an_empty_name_still_yields_something_writable(self):
        assert pg.safe_name("") and "/" not in pg.safe_name("")

    def test_writes_land_inside_the_session(self, tmp_path):
        r = pg.write_seat("s1", "ollama", "```python ../../escape.py\nx = 1\n```",
                          root=tmp_path)
        written = Path(r["dir"]) / r["files"][0]
        assert written.exists()
        assert str(written.resolve()).startswith(str(tmp_path.resolve()))
        assert not (tmp_path.parent / "escape.py").exists()

    def test_a_hostile_seat_name_cannot_climb_out(self, tmp_path):
        r = pg.write_seat("s1", "../../../etc", "```\nx\n```", root=tmp_path)
        assert "error" in r or str(Path(r["dir"]).resolve()).startswith(str(tmp_path.resolve()))


class TestNothingRuns:
    def test_dangerous_content_is_stored_as_text_not_run(self, tmp_path):
        """The playground writes; it does not import, exec, or spawn. A model
        that emits a destructive command produces a file containing that text."""
        marker = tmp_path / "SHOULD_NOT_EXIST"
        payload = f"```python evil.py\nopen({str(marker)!r}, 'w').write('x')\n```"
        r = pg.write_seat("s1", "ollama", payload, root=tmp_path)
        assert not marker.exists(), "the playground executed model output"
        body = (Path(r["dir"]) / "evil.py").read_text()
        assert "SHOULD_NOT_EXIST" in body, "the file should hold the text verbatim"

    def test_the_module_never_executes_anything(self):
        """Pinned at the AST, not by grep.

        A text scan fails here for the right reason and the wrong one: this
        module's own docstring names os.system as an example of something it
        deliberately does not do. Parsing distinguishes a mention from a call,
        which a grep cannot, and is the stronger check in both directions — it
        also catches a real call hidden inside a string a grep would miss.
        """
        import ast
        tree = ast.parse((MODULES / "playground.py").read_text())

        # Bare builtins that turn text into running code.
        BANNED_BUILTINS = {"exec", "eval", "compile", "__import__"}
        # Attribute calls that reach the OS. `compile` is deliberately absent:
        # re.compile is how the fence parser works, and banning the name
        # outright confuses "builds a regex" with "runs a program".
        BANNED_ATTRS = {"system", "popen", "Popen", "spawn", "fork",
                        "check_output", "check_call"}
        BANNED_IMPORTS = {"subprocess", "importlib", "runpy", "pty"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] not in BANNED_IMPORTS, \
                        f"playground imports {a.name}"
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in BANNED_IMPORTS, \
                    f"playground imports from {node.module}"
            elif isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name):
                    assert fn.id not in BANNED_BUILTINS, \
                        f"playground calls {fn.id}() — it must only write files"
                elif isinstance(fn, ast.Attribute):
                    assert fn.attr not in BANNED_ATTRS, \
                        f"playground calls .{fn.attr}() — it must only write files"


class TestSeatsStaySeparate:
    def test_each_seat_gets_its_own_directory(self, tmp_path):
        pg.write_seat("s1", "ollama:llama", "```python a.py\n1\n```", root=tmp_path)
        pg.write_seat("s1", "ollama:gemma", "```python a.py\n2\n```", root=tmp_path)
        d = pg.session_dir("s1", tmp_path)
        dirs = sorted(p.name for p in d.iterdir() if p.is_dir())
        assert len(dirs) == 2, "two seats collapsed into one directory"

    def test_identical_filenames_do_not_overwrite_each_other(self, tmp_path):
        pg.write_seat("s1", "a", "```python x.py\nFIRST\n```", root=tmp_path)
        pg.write_seat("s1", "b", "```python x.py\nSECOND\n```", root=tmp_path)
        d = pg.session_dir("s1", tmp_path)
        assert (d/"a"/"x.py").read_text().strip() == "FIRST"
        assert (d/"b"/"x.py").read_text().strip() == "SECOND"


class TestExtraction:
    def test_a_named_fence_keeps_its_name(self):
        assert pg.extract_files("```python hello.py\nprint(1)\n```")[0][0] == "hello.py"

    def test_an_unnamed_fence_gets_the_language_extension(self):
        assert pg.extract_files("```bash\necho hi\n```")[0][0].endswith(".sh")

    def test_two_unnamed_blocks_do_not_collide(self):
        names = [n for n, _ in pg.extract_files("```py\n1\n```\n```py\n2\n```")]
        assert len(set(names)) == 2

    def test_prose_with_no_fences_is_kept_not_discarded(self):
        """A seat that explains rather than codes has still contributed."""
        out = pg.extract_files("I would use os.listdir on /proc/<pid>/fd.")
        assert out and out[0][0] == "answer.md"
        assert "proc" in out[0][1]

    def test_output_is_capped(self):
        many = "\n".join(f"```py f{i}.py\n{i}\n```" for i in range(20))
        assert len(pg.extract_files(many)) <= pg.MAX_FILES_PER_SEAT

    def test_empty_blocks_are_skipped(self):
        assert pg.extract_files("```python\n\n```")[0][0] == "answer.md"


class TestTheRecord:
    def test_a_session_records_the_task_and_that_nothing_ran(self, tmp_path):
        sid = pg.open_session("build a thing", root=tmp_path)
        pg.close_session(sid, "build a thing", [{"seat": "ollama", "status": "ok"}],
                         root=tmp_path)
        idx = json.loads((pg.session_dir(sid, tmp_path)/"index.json").read_text())
        assert idx["task"] == "build a thing"
        assert idx["executed"] is False
        assert idx["reviewed"] is False

    def test_a_malformed_index_does_not_break_listing(self, tmp_path):
        sid = pg.open_session("t", root=tmp_path)
        pg.close_session(sid, "t", [], root=tmp_path)
        bad = pg.session_dir("broken", tmp_path); bad.mkdir()
        (bad/"index.json").write_text("{not json")
        assert len(pg.sessions(tmp_path)) == 1

    def test_no_playground_directory_is_empty_not_fatal(self, tmp_path):
        assert pg.sessions(tmp_path/"nope") == []
