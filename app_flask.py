"""
  </section>
  {% endif %}

  <footer>
    Every answer shows its confidence, grounded flag and the exact passages it was generated from &mdash; nothing is hidden.<br>
    Confidence gate: retrieval score &ge; 0.35 &rarr; answer&nbsp;&middot;&nbsp;below &rarr; refusal. Runs fully offline on CPU.
  </footer>
</div>

<script>
(function(){
  var form = document.getElementById('ask-form');
  var btn = document.getElementById('ask-btn');
  var input = document.querySelector('input[name=question]');
  var loading = document.getElementById('loading');
  var elapsed = document.getElementById('elapsed');
  var timerId = null;

  form.addEventListener('submit', function(){
    if(!input.value.trim()){ return; }
    btn.disabled = true;
    btn.innerHTML = 'Thinking&hellip;';
    loading.style.display = 'block';
    var t0 = Date.now();
    timerId = setInterval(function(){
      elapsed.textContent = Math.floor((Date.now() - t0) / 1000);
    }, 250);
    loading.scrollIntoView({behavior:'smooth', block:'center'});
  });

  var chips = document.querySelectorAll('.chip');
  for(var i = 0; i < chips.length; i++){
    chips[i].addEventListener('click', function(){
      input.value = this.getAttribute('data-q');
      form.requestSubmit();
    });
  }
})();
</script>
</body>
</html>
"""

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
    return render_template_string(HTML, result=None, q="", error=None)

@app.route("/ask", methods=["POST"])
def ask():
    q = request.form.get("question", "")
    try:
        res = get_answer_via_subprocess(q)
        return render_template_string(HTML, result=res, q=q, error=None)
    except Exception as e:
        return render_template_string(HTML, result=None, q=q, error=str(e))

if __name__ == "__main__":
    print("Starting Flask UI on http://localhost:5000 - no pyarrow, no torch in main process")
    app.run(host="0.0.0.0", port=5000, debug=False)