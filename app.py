# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, CUK
# Dual AI + Rich Format: Paragraph / Table / Image / Flowchart - Based on Topic

import os, re, json, requests, random, urllib.parse
from collections import Counter
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, make_response, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google import genai
from google.genai import types

app = Flask(__name__)

print(f"DEBUG: Groq key exists? {bool(GROQ_KEY)} Length: {len(GROQ_KEY)}")
GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "").strip()
ADMIN_KEY = os.environ.get("ADMIN_KEY", "CUK_Secure_2026")

gemini_client = None
if GEMINI_KEY:
    try: gemini_client = genai.Client(api_key=GEMINI_KEY)
    except: pass

# --- RICH FORMAT STRATEGIES - OPEN TOOL + VARIED FORMAT ---
DEFAULT_STRATEGIES = {
    "design_thinking": """You are DT4STEM GURU AI, expert STEM Coach with knowledge of 1000+ EdTech tools from internet (NASA, PhET, Tinkercad, Stellarium, BioDigital, Desmos, ChemCollective, etc.).

For Teacher Question, you MUST:
1. Choose BEST format based on topic:
   - If topic is comparison (e.g., mitosis vs meiosis, acids vs bases) -> Use MARKDOWN TABLE format
   - If topic is process/cycle (e.g., photosynthesis, water cycle) -> Use BULLET + FLOWCHART (using -> arrows) + PARAGRAPH
   - If topic is definition/theory (e.g., Newton law, Pythagoras) -> Use PARAGRAPH + BULLET POINTS + EXAMPLE
   - If topic needs visual (e.g., heart, solar system, atom) -> You MUST include 1 image markdown:![diagram of {topic}](https://image.pollinations.ai/prompt/{topic} diagram educational colorful)
   - Randomly vary so answers don't look same

2. Structure in 5 steps but with rich formatting:
   **1. EMPATHIZE:** paragraph about student misconception
   **2. DEFINE:** problem statement
   **3. IDEATE:** Table or bullets with BEST tools for THIS topic from internet knowledge. Justify why tool fits THIS topic. Not fixed tools.
   **4. PROTOTYPE:** 40-min activity in table format: | Time | Activity | Tool |
   **5. TEST:** Rubric in table format

3. At end, if topic is visual, include:![{topic} educational diagram](https://image.pollinations.ai/prompt/{topic} educational diagram labeled colorful 4k)

Use markdown for tables, bold, bullets.

End with © S Sachinkumar & Prof.G.R.Angadi, CUK""",

    "tpack_ai": "You are TPACK Expert with 1000+ tools knowledge. For topic, give answer in varied format - sometimes table, sometimes paragraph, sometimes with image markdown![topic](https://image.pollinations.ai/prompt/topic educational). Choose best tools for topic from internet. Use markdown tables where useful. End with © S Sachinkumar & Prof.G.R.Angadi, CUK",
    "nep2020": "You are NEP 2020 Coach. Give answer in rich format - paragraph, table, bullets based on topic. Include image if visual topic using![topic](https://image.pollinations.ai/prompt/topic). Suggest best tools from internet. End with © S Sachinkumar & Prof.G.R.Angadi, CUK",
    "lesson_ai": "You are Lesson Planner. Give 40-min lesson with varied format: Table for timeline, paragraph for explanation, image for diagram using markdown![...](https://image.pollinations.ai/prompt/...). Choose topic-specific tools. End with © S Sachinkumar & Prof.G.R.Angadi, CUK",
    "mentoring_ai": "You are Mentor. Give answer in paragraph + bullet + table mix. Include inspirational image if relevant. End with © S Sachinkumar & Prof.G.R.Angadi, CUK"
}

ACTIVE = {"active_strategy": "design_thinking", "strategies": DEFAULT_STRATEGIES}
try:
    if os.path.exists("strategies.json"):
        with open("strategies.json","r", encoding="utf-8") as f: ACTIVE = json.load(f)
except: pass

analytics = {"total_visits":0,"total_questions":0,"categories":Counter(),"daily_count":Counter()}
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")

def save_to_sheet(event_type, category=""):
    try:
        if not GOOGLE_SHEET_URL: return
        requests.post(GOOGLE_SHEET_URL, json={"event": event_type, "category": category, "strategy": ACTIVE["active_strategy"]}, timeout=3)
    except: pass

def is_safe(q):
    if not q or len(q)>500: return False
    if re.search(r"<script|DROP TABLE", q, re.I): return False
    return True
def get_category(q): return "STEM"

# --- GROQ ---
def ask_groq_api(question, strategy_prompt):
    if not GROQ_KEY: return None
    try:
        format_instruction = random.choice([
            "Use MARKDOWN TABLE for IDEATE and PROTOTYPE sections. Include image markdown for visual topics.",
            "Use PARAGRAPH + BULLET POINTS for explanation. Include flowchart using -> arrows.",
            "Use MIXED format: paragraph intro, then table for comparison, then bullet for activity. Add image if needed.",
            "Use TABLE for 40-min activity timeline | Time | Teacher Action | Student Action | Tool | and include diagram image markdown."
        ])
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"{strategy_prompt}\n\nFORMAT INSTRUCTION: {format_instruction}\nYou know 1000+ tools. Choose best for '{question}'. For images use markdown:![{question}](https://image.pollinations.ai/prompt/{urllib.parse.quote(question + ' educational diagram colorful labeled')})"},
                {"role": "user", "content": f"Question: {question}. Give rich formatted answer with paragraph, table, and image markdown if visual. Be specific to {question}."}
            ],
            "temperature": 0.9, "max_tokens": 1800
        }
        r = requests.post(url, headers=headers, json=payload, timeout=25)
        if r.status_code == 200: return r.json()["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"Groq fail: {e}"); return None

@app.route("/")
def home():
    analytics["total_visits"]+=1; save_to_sheet("VISIT")
    active = ACTIVE["active_strategy"].upper()
    # Frontend with Markdown + Image rendering
    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DT4STEM Guru AI - Rich Format</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body{{font-family:Segoe UI,Arial;max-width:950px;margin:auto;background:#f6f7f9;line-height:1.7}}
header{{background:#0f172a;color:#fff;padding:20px;text-align:center;border-radius:0 0 16px 16px}}
#box{{background:#fff;margin:20px;padding:22px;border-radius:16px;box-shadow:0 4px 12px #ddd}}
input{{width:100%;padding:14px;border-radius:10px;border:1px solid #ccc;margin:10px 0;box-sizing:border-box}}
button{{padding:14px;border-radius:10px;border:none;background:#0f172a;color:#fff;width:100%;font-weight:bold;cursor:pointer}}
#ans{{background:#f8fafc;padding:18px;border-radius:12px;margin-top:15px;border:1px solid #e2e8f0;min-height:100px}}
#ans table{{border-collapse:collapse;width:100%;margin:12px 0}} #ans th, #ans td{{border:1px solid #cbd5e1;padding:8px;text-align:left}} #ans th{{background:#0f172a;color:#fff}}
#ans img{{max-width:100%;border-radius:10px;margin:12px 0;box-shadow:0 2px 8px #ccc}}
footer{{background:#0f172a;color:#cbd5e1;text-align:center;padding:16px;font-size:11px;border-radius:16px 16px 0 0}}
</style></head>
<body>
<header><h2 style="margin:0">DT4STEM Guru AI 🤖 Rich Format</h2><p style="margin:5px 0">Paragraph • Table • Images • Flowchart | © S Sachinkumar & Prof.G.R.Angadi, CUK</p><small>Mode: {active} | Helped: {analytics["total_questions"]} | Dual AI: Gemini + Groq</small></header>
<div id=box>
<input id='q' placeholder='Try: human heart diagram, mitosis vs meiosis table, water cycle with flowchart, newtons law...'>
<button onclick='ask()'>🚀 Ask AI Coach - Rich Answer</button>
<div id='ans'>Your rich formatted answer with paragraph, tables, and images will appear here...<br><br>Examples:<br>• <b>heart</b> → paragraph + diagram image<br>• <b>mitosis vs meiosis</b> → comparison table<br>• <b>water cycle</b> → flowchart + table<br>• <b>newtons law</b> → paragraph + table activity</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, CUK<br>Images auto-generated via Pollinations AI (Free, Open) + Knowledge from internet sources</footer>
<script>
async function ask(){{
 let q=document.getElementById('q').value; if(!q){{alert('Type question');return}}
 document.getElementById('ans').innerHTML='⏳ Generating rich answer with text + table + image for: '+q+'... Please wait 6 sec...';
 try{{
  let r=await fetch('/chat?q='+encodeURIComponent(q)); let d=await r.json();
  // Render markdown to HTML (tables + images)
  let html = marked.parse(d.answer);
  document.getElementById('ans').innerHTML = html;
  window.scrollTo(0, document.getElementById('ans').offsetTop);
 }}catch(e){{
  document.getElementById('ans').innerHTML='Error: '+e;
 }}
}}
</script>
</body></html>
"""
    return make_response(render_template_string(html))

@app.route("/chat")
@limiter.limit("20 per minute")
def chat():
    q=request.args.get("q","").strip()
    if not is_safe(q): return jsonify({"answer":"Invalid input."}),400
    analytics["total_questions"]+=1; save_to_sheet("QUESTION", get_category(q))
    strategy_prompt = ACTIVE["strategies"][ACTIVE["active_strategy"]]

    # Try Gemini
    gem_ans = ask_gemini_api(q, strategy_prompt)
    if gem_ans: return jsonify({"answer": gem_ans})

    # Try Groq
    groq_ans = ask_groq_api(q, strategy_prompt)
    if groq_ans: return jsonify({"answer": groq_ans + "\n\n---\n© S Sachinkumar & Prof.G.R.Angadi, CUK"})

    return jsonify({"answer": "Both AI keys need refresh. Add GROQ_API_KEY from https://console.groq.com/keys"}),500

@app.route("/admin")
def admin():
    if request.args.get("key")!= ADMIN_KEY: return "Unauthorized",401
    return f"Admin OK - Visits: {analytics['total_visits']} Q: {analytics['total_questions']} | Active: {ACTIVE['active_strategy']}"

@app.route("/admin/switch", methods=["POST"])
def switch_strategy():
    if request.form.get("key")!= ADMIN_KEY: return "Unauthorized",401
    ns=request.form.get("strategy")
    if ns in ACTIVE["strategies"]: ACTIVE["active_strategy"]=ns
    return redirect(f"/admin?key={request.form.get('key')}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
