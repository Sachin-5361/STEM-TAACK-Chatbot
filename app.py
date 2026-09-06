# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK

import os, requests
from flask import Flask, request, jsonify, render_template_string, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()

STRATEGY_PROMPT = """
You are DT4STEM GURU AI - Expert STEM Coach for Secondary School Teachers 

You MUST follow Design Thinking 5 steps in EXACT order:

### 1. EMPATHIZE:
- Learner misconception about topic - 2-3 bullets

### 2. DEFINE:
- Problem statement: "How might we help students understand [TOPIC]?"

### 3. IDEATE:
- Choose best 3 EdTech tools for THIS topic (PhET, NASA, BioDigital, Desmos, etc.)
- Table:
| Idea No | Teaching Idea | Tool Name | Why Best for This Topic? |
|---|---|---|---|

### 4. PROTOTYPE:
- 40-min lesson plan table:
| Time | Activity | Tool Used | Teacher Action |
|---|---|---|---|

### 5. TEST:
- Rubric table:
| Criteria | Excellent | Good | Needs Improvement |
|---|---|---|---|

- Use markdown tables. No images. Pure text + tables.
"""

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")

def ask_groq(question):
    if not GROQ_KEY:
        return "⚠️ GROQ_API_KEY missing! Add in Render Environment."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    models_to_try = ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "openai/gpt-oss-120b"]

    for model_name in models_to_try:
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": STRATEGY_PROMPT},
                    {"role": "user", "content": f"Teacher Question: {question}. Give answer with 5 Design Thinking steps with tables. No images needed."}
                ],
                "temperature": 0.8,
                "max_tokens": 2500
            }
            r = requests.post(url, headers=headers, json=payload, timeout=35)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except: continue
    return "❌ Groq Error. Check API Key."

@app.route("/")
def home():
    html = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DT4STEM Guru AI</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body{font-family:Segoe UI,Arial;max-width:980px;margin:auto;background:#f6f7f9;line-height:1.75}
header{background:#0f172a;color:#fff;padding:22px;text-align:center;border-radius:0 0 16px 16px}
#box{background:#fff;margin:20px;padding:22px;border-radius:16px;box-shadow:0 4px 14px rgba(0,0,0,0.1)}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #cbd5e1;margin:10px 0;box-sizing:border-box;font-size:15px}
button{padding:14px;border-radius:10px;border:none;background:#0f172a;color:#fff;width:100%;font-weight:bold;cursor:pointer;font-size:16px}
#ans{background:#ffffff;padding:20px;border-radius:12px;margin-top:16px;border:1px solid #e2e8f0;min-height:150px}
#ans table{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px} #ans th,#ans td{border:1px solid #cbd5e1;padding:9px;text-align:left} #ans th{background:#0f172a;color:#fff}
#ans h3{color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:22px}
footer{background:#0f172a;color:#94a3b8;text-align:center;padding:16px;font-size:11px;border-radius:16px 16px 0 0;margin-top:20px}
</style></head>
<body>
<header>
<h2 style="margin:0">DT4STEM Guru AI 🤖</h2>
<p style="margin:8px 0 4px 0">Design Thinking for STEM Education</p>
<small>© S Sachinkumar & Prof.G.R.Angadi, CUK</small>
</header>
<div id=box>
<input id='q' placeholder='Example: human heart, photosynthesis, newtons laws, mitosis vs meiosis...'>
<button onclick='ask()'>🚀 Ask AI Coach</button>
<div id='ans'>
<b>About DT4STEM Guru AI</b><br><br>
DT4STEM Guru is an AI-powered pedagogical coach designed for secondary school STEM teachers. It is developed as part of research by <b>S Sachinkumar (Research Scholar)</b> and <b>Prof. G.R. Angadi, Dept. of Education, Central University of Karnataka, Kalaburagi</b>.<br><br>
The system integrates <b>Design Thinking (Empathize, Define, Ideate, Prototype, Test)</b> with curated EdTech tools (PhET, NASA, BioDigital, Desmos, Tinkercad and 1000+ tools) to create contextual, activity-based lesson plans for Science, Technology, Engineering and Mathematics.<br><br>
<i>Enter your STEM topic above to generate a Design Thinking based lesson plan.</i>
</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, Central University of Karnataka</footer>
<script>
async function ask(){
 let q=document.getElementById('q').value.trim();
 if(!q){alert('Please type a question');return}
 document.getElementById('ans').innerHTML='⏳ Generating Design Thinking lesson for: <b>'+q+'</b><br><br>Steps: Empathize → Define → Ideate → Prototype → Test... Please wait...';
 try{
  let r=await fetch('/chat?q='+encodeURIComponent(q));
  let d=await r.json();
  document.getElementById('ans').innerHTML = marked.parse(d.answer);
  window.scrollTo({top: document.getElementById('ans').offsetTop-30, behavior:'smooth'});
 }catch(e){ document.getElementById('ans').innerHTML='Error: '+e; }
}
document.getElementById('q').addEventListener('keypress', function(e){ if(e.key==='Enter'){ask();} });
</script>
</body></html>
"""
    return make_response(render_template_string(html))

@app.route("/chat")
@limiter.limit("20 per minute")
def chat():
    q = request.args.get("q","").strip()
    if not q: return jsonify({"answer":"Please type a question"}),400
    return jsonify({"answer": ask_groq(q)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
