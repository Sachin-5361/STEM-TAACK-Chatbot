# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK
import os, requests, random, urllib.parse
from flask import Flask, request, jsonify, render_template_string, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()

print(f"=== DT4STEM Guru AI Starting ===")
print(f"Groq Key Present: {bool(GROQ_KEY)}")
if GROQ_KEY:
    print("✅ Groq Ready - 1000 answers/day free")

STRATEGY_PROMPT = """You are SrujanaSTEM AI, expert STEM Coach for Secondary Teachers in India.
You know 1000+ EdTech tools from internet (NASA, Stellarium, BioDigital, ChemCollective, Desmos, Tinkercad, etc.).

For Teacher Question, you MUST:
- Choose BEST format based on topic:
    * Comparison (mitosis vs meiosis) = MARKDOWN TABLE
    * Process (water cycle) = FLOWCHART using -> arrows + TABLE
    * Visual (heart, solar system, atom) = PARAGRAPH + IMAGE markdown:![diagram](https://image.pollinations.ai/prompt/TOPIC educational diagram colorful labeled)
    * Theory = PARAGRAPH + BULLETS + TABLE
- Choose BEST tools for THIS topic from internet. Not fixed.
- Structure:
  **1. EMPATHIZE:** student misconception
  **2. DEFINE:** problem
  **3. IDEATE:** | Idea | Tool | Why best |
  **4. PROTOTYPE:** | Time | Activity | Tool |
  **5. TEST:** rubric table
- Use markdown tables. If visual, MUST include image markdown.
End with © S Sachinkumar & Prof.G.R.Angadi, CUK"""

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")

def ask_groq(question):
    if not GROQ_KEY:
        return "⚠️ GROQ_API_KEY not found! Add in Render Environment: GROQ_API_KEY = gsk_... from https://console.groq.com/keys"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    models_to_try = ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "openai/gpt-oss-120b"]

    format_type = random.choice([
        "Use MARKDOWN TABLE for IDEATE and PROTOTYPE. Include image markdown for visual topics.",
        "Use PARAGRAPH + BULLETS + TABLE mixed format.",
        "Use TABLE for comparison and FLOWCHART with -> arrows."
    ])

    image_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(question + ' educational diagram colorful labeled 4k')}"

    for model_name in models_to_try:
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": f"{STRATEGY_PROMPT}\nFORMAT: {format_type}\nFor image use:![{question}]({image_url})"},
                    {"role": "user", "content": f"Question: {question}. Give rich formatted unique answer."}
                ],
                "temperature": 0.9, "max_tokens": 2000
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except: continue

    return "❌ Groq Error. Check GROQ_API_KEY in Render."

@app.route("/")
def home():
    html = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DT4STEM Guru AI</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body{font-family:Segoe UI,Arial;max-width:950px;margin:auto;background:#f6f7f9;line-height:1.7}
header{background:#0f172a;color:#fff;padding:20px;text-align:center;border-radius:0 0 16px 16px}
#box{background:#fff;margin:20px;padding:22px;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,0.1)}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #ccc;margin:10px 0;box-sizing:border-box;font-size:15px}
button{padding:14px;border-radius:10px;border:none;background:#0f172a;color:#fff;width:100%;font-weight:bold;cursor:pointer;font-size:15px}
#ans{background:#f8fafc;padding:18px;border-radius:12px;margin-top:15px;border:1px solid #e2e8f0;min-height:120px}
#ans table{border-collapse:collapse;width:100%;margin:12px 0} #ans th,#ans td{border:1px solid #cbd5e1;padding:8px;text-align:left} #ans th{background:#0f172a;color:#fff}
#ans img{max-width:100%;border-radius:12px;margin:14px 0;box-shadow:0 2px 10px rgba(0,0,0,0.2);border:1px solid #ddd}
footer{background:#0f172a;color:#cbd5e1;text-align:center;padding:16px;font-size:11px;border-radius:16px 16px 0 0}
</style></head>
<body>
<header>
<h2 style="margin:0">DT4STEM Guru AI 🤖</h2>
<p style="margin:6px 0">Paragraph • Table • Images • Flowchart | Rich Format</p>
<small>© S Sachinkumar & Prof.G.R.Angadi, CUK</small>
</header>
<div id=box>
<input id='q' placeholder='Try: human heart diagram, mitosis vs meiosis table, water cycle...'>
<button onclick='ask()'>🚀 Ask AI Coach</button>
<div id='ans'>Your rich answer with paragraph + table + image will appear here...</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, CUK</footer>
<script>
async function ask(){
 let q=document.getElementById('q').value.trim(); if(!q){alert('Type question');return}
 document.getElementById('ans').innerHTML='⏳ Generating rich answer for: <b>'+q+'</b>... Please wait 5 sec...';
 try{
  let r=await fetch('/chat?q='+encodeURIComponent(q));
  let d=await r.json();
  document.getElementById('ans').innerHTML = marked.parse(d.answer);
  window.scrollTo({top: document.getElementById('ans').offsetTop-20, behavior:'smooth'});
 }catch(e){ document.getElementById('ans').innerHTML='Error: '+e; }
}
</script>
</body></html>
"""
    return make_response(render_template_string(html))

@app.route("/chat")
@limiter.limit("20 per minute")
def chat():
    q = request.args.get("q","").strip()
    if not q: return jsonify({"answer":"Please type a question"}),400
    answer = ask_groq(q)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
