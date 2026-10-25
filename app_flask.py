"""
Stage 15 - Flask UI (redesigned) - NO pyarrow, NO streamlit, NO torch in UI process.
The UI process never imports torch or pyarrow; the child process (src.cli_answer) does.

2026-10 redesign: the page now lives in templates/index.html (card layout,
suggestion chips, loading state, confidence badges, source score bars).

Run: python app_flask.py
Then open http://localhost:5000
"""
from flask import Flask, request, render_template
import subprocess
import sys
import json
from pathlib import Path

app = Flask(__name__)


def get_answer_via_subprocess(question: str) -> dict:
    """UI process stays clean (no torch/pyarrow); the child process does the ML.
    Timeout 180 s: first question loads the model, generation is CPU-only."""
    cmd = [sys.executable, "-m", "src.cli_answer", question]
    project_root = Path(__file__).parent
    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"Subprocess failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    # last line is JSON
    line = result.stdout.strip().splitlines()[-1]
    return json.loads(line)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", result=None, q="", error=None)


@app.route("/ask", methods=["POST"])
def ask():
    q = request.form.get("question", "")
    try:
        res = get_answer_via_subprocess(q)
        return render_template("index.html", result=res, q=q, error=None)
    except Exception as e:
        return render_template("index.html", result=None, q=q, error=str(e))


if __name__ == "__main__":
    print("Starting Flask UI on http://localhost:5000 - no pyarrow, no torch in main process")
    app.run(host="0.0.0.0", port=5000, debug=False)