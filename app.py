# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK
# GROQ ONLY - No Gemini - Rich Format: Paragraph + Table + Image
import os, re, json, requests, random, urllib.parse
from collections import Counter
from flask import Flask, request, jsonify, render_template_string, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# --- ONLY GROQ KEY NEEDED ---
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "").strip()

print(f"Startup - Groq Key Present: {bool(GROQ_KEY)} Length: {len(GROQ_KEY) if GROQ_KEY else 0}")
if GROQ_KEY:
    print("✅ Groq Ready - One key = 14,400 answers/day, no need to change per answer")

STRATEGY_PROMPT = """You are SrujanaSTEM AI, STEM Coach for Secondary Teachers in India. You know 1000+ tools from internet (NASA, PhET, Stellarium, BioDigital, ChemCollective, Desmos, Tinkercad, LabXchange, etc.).

For each Teacher Question:
1. Choose BEST format based on topic:
   - Comparison (mitosis vs meiosis, acids vs bases) = MARKDOWN TABLE
   - Process (water cycle, photosynthesis) = FLOWCHART using -> + TABLE
   - Visual (heart, solar system, atom) = PARAGRAPH + IMAGE markdown:![diagram](https://image.pollinations.ai/prompt/TOPIC educational diagram colorful labeled)
   - Theory = PARAGRAPH + BULLETS + TABLE

2. Choose BEST tools for THIS topic from internet knowledge. Not fixed. Example: Space=Stellarium/NASA Eyes, Chemistry=ChemCollective/MolView, Biology=BioDigital/HHMI, Maths=Desmos/Mathigon. Justify why.

3. Structure:
**1. EMPATHIZE:** student misconception paragraph
**2. DEFINE:** problem
**3. IDEATE:** table with | Idea | Tool | Why best for THIS topic |
**4. PROTOTYPE:** 40-min activity table | Time | Activity | Tool |
**5. TEST:** rubric table

Use markdown tables, bold, bullets. If visual topic, MUST include image markdown.

End with © S Sachinkumar & Prof.G.R.Angadi, CUK"""

analytics = {"visits":0, "questions":0}
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")

def ask_groq(question):
    if not GROQ_KEY:
        return "⚠️ GROQ_API_KEY not found in Render Environment. Go to Render > Environment > Add GROQ_API_KEY = gsk_... > Save Changes > Redeploy."
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        format_type = random.choice([
            "Use MARKDOWN TABLE for IDEATE and PROTOTYPE",
            "Use PARAGRAPH + BULLETS + TABLE mixed",
            "Use TABLE for comparison and include image",
            "Use FLOWCHART with -> arrows + TABLE for activity"
        ])
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"{STRATEGY_PROMPT}\nFORMAT INSTRUCTION: {format_type}. For image use:![{question}](https://image.pollinations.ai/prompt/{urllib.parse.quote(question + ' educational diagram colorful labeled 4k')})"},
                {"role": "user", "content": f"Teacher Question: {question}. Give rich formatted unique answer specific to this topic with table and image if needed."}
            ],
            "temperature": 0.9,
            "max_tokens": 2000
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            print(f"Groq Error {r.status_code}: {r.text[:400]}")
            if r.status_code == 401:
                return f"❌ Invalid GROQ_API_KEY. Your key {GROQ_KEY[:10]}... is wrong. Get new from https://console.groq.com/keys"
            elif r.status_code == 429:
                return "⚠️ Free limit reached (14,400/day). Wait 1 minute and try again."
            return f"Groq API Error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        print(f"Exception: {e}")
        return f"Error: {e}"

@app.route("/")
def home():
    analytics["visits"]+=1
    html = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DT4STEM Guru AI - Groq Only</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body{font-family:Segoe UI;max-width:950px;margin:auto;background:#f6f7f9;line-height:1.7}
header{background:#0f172a;color:#fff;padding:20px;text-align:center;border-radius:0 0 16px 16px}
#box{background:#fff;margin:20px;padding:22px;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,0.1)}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #ccc;margin:10px 0;box-sizing:border-box;font-size:15px}
button{padding:14px;border-radius:10px;border:none;background:#0f172a;color:#fff;width:100%;font-weight:bold;cursor:pointer;font-size:15px}
#ans{background:#f8fafc;padding:18px;border-radius:12px;margin-top:15px;border:1px solid #e2e8f0;min-height:120px}
#ans table{border-collapse:collapse;width:100%;margin:12px 0} #ans th,#ans td{border:1px solid #cbd5e1;padding:8px;text-align:left} #ans th{background:#0f172a;color:#fff}
#ans img{max-width:100%;border-radius:10px;margin:14px 0;box-shadow:0 2px 10px #ccc}
footer{background:#0f172a;color:#cbd5e1;text-align:center;padding:16px;font-size:11px;border-radius:16px 16px 0 0}
.badge{display:inline-block;background:#10b981;color:#fff;padding:4px 10px;border-radius:20px;font-size:11px}
</style></head>
<body>
<header>
<h2 style="margin:0">DT4STEM Guru AI 🤖</h2>
<p style="margin:6px 0">Rich Format: Paragraph • Table • Images • Flowchart</p>
<span class="badge">GROQ ONLY - No Gemini Needed - 14,400 Q/day Free</span><br>
<small>© S Sachinkumar & Prof.G.R.Angadi, CUK | Helped: {{qcount}}</small>
</header>
<div id=box>
<input id='q' placeholder='Try: human heart diagram / mitosis vs meiosis / water cycle flowchart / black holes...'>
<button onclick='ask()'>🚀 Ask AI Coach</button>
<div id='ans'>Your rich answer will appear here with:<br>
• <b>Paragraph</b> for theory<br>
• <b>Table</b> for comparison (mitosis vs meiosis)<br>
• <b>Image</b> for diagram (heart, solar system)<br>
• <b>Flowchart</b> for process (water cycle)<br><br>
One GROQ_API_KEY works for all questions - No need to change API per answer!</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, CUK<br>Images via Pollinations AI (Free) | Knowledge from 1000+ EdTech tools</footer>
<script>
async function ask(){
 let q=document.getElementById('q').value.trim(); if(!q){alert('Type question');return}
 document.getElementById('ans').innerHTML='⏳ Generating rich answer (paragraph + table + image) for: <b>'+q+'</b>... Please wait 5 sec...';
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
    return make_response(render_template_string(html, qcount=analytics["questions"]))

@app.route("/chat")
@limiter.limit("20 per minute")
def chat():
    q=request.args.get("q","").strip()
    if not q: return jsonify({"answer":"Please type question"}),400
    analytics["questions"]+=1
    answer = ask_groq(q)
    return jsonify({"answer": answer})

@app.route("/about")
def about(): return "DT4STEM Guru AI - Groq Only - CUK Research 2026"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
