# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, CUK
import os, re, json, requests
from collections import Counter
from datetime import datetime
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template_string, make_response, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "") # You will add this in Render

def save_to_sheet(event_type, category=""):
    try:
        if not GOOGLE_SHEET_URL: return
        payload = {
            "event": event_type,
            "category": category,
            "strategy": ACTIVE["active_strategy"],
            "visits": analytics["total_visits"],
            "questions": analytics["total_questions"]
        }
        requests.post(GOOGLE_SHEET_URL, json=payload, timeout=3)
    except: pass # Don't break app if sheet fails

DEFAULT_STRATEGIES = {
    "design_thinking": "You are AI-Powered Design Thinking Coach for Secondary STEM Teachers. MUST answer in 5 steps: 1.EMPATHIZE, 2.DEFINE, 3.IDEATE, 4.PROTOTYPE, 5.TEST. End with © S Sachinkumar & Prof.G.R.Angadi, CUK",
    "tpack_ai": "You are AI-Powered TPACK Expert. Explain Content, Pedagogy, Technology integration with 1 AI tool example (like PhET, GeoGebra).",
    "nep2020": "You are NEP 2020 Aligned PD Coach for STEM Teachers.",
    "lesson_ai": "You are AI Lesson Planner for Secondary STEM. Give 40-min lesson plan with Outcomes, AI Tool, Assessment.",
    "mentoring_ai": "You are AI Mentor for STEM Teachers. Give empathy, classroom story, growth tip, action research idea."
}
ACTIVE = {"active_strategy": "design_thinking", "strategies": DEFAULT_STRATEGIES}
try:
    if os.path.exists("strategies.json"):
        with open("strategies.json","r") as f: ACTIVE = json.load(f)
except: pass

analytics = {"total_visits":0,"total_questions":0,"categories":Counter(),"daily_count":Counter()}
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"])

def is_safe(q):
    if not q or len(q)>500: return False
    if re.search(r"<script|DROP TABLE", q, re.I): return False
    return True
def get_category(q):
    q=q.lower()
    if any(w in q for w in ["physics","chemistry","bio","science"]): return "STEM Content"
    if any(w in q for w in ["pedagogy","teach","method"]): return "Pedagogy"
    if any(w in q for w in ["ai","tpack","technology"]): return "AI & TPACK"
    if any(w in q for w in ["assessment","rubric"]): return "Assessment"
    if "professional" in q: return "Professional Development"
    return "General STEM PD"

@app.route("/")
def home():
    analytics["total_visits"]+=1
    save_to_sheet("VISIT")
    active = ACTIVE["active_strategy"].upper()
    html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>STEM PD AI - CUK</title>
    <style>body{{font-family:Segoe UI;max-width:850px;margin:auto;background:#f6f7f9}} header{{background:#0f172a;color:#fff;padding:18px;text-align:center}} #box{{background:#fff;margin:20px;padding:20px;border-radius:16px;box-shadow:0 4px 12px #ddd}} input{{width:68%;padding:14px;border-radius:10px;border:1px solid #ccc}} button{{padding:14px 18px;border-radius:10px;border:none;background:#0f172a;color:#fff}} footer{{background:#0f172a;color:#fff;text-align:center;padding:20px;font-size:11px}}</style></head>
    <body><header><h2>STEM Teachers PD AI Buddy 🤖</h2><p>AI Powered | © S Sachinkumar & Prof.G.R.Angadi, CUK</p></header>
    <div id=box><small>🧠 Mode: {active}</small><br><br><input id='q' placeholder='Ask: How to teach Newton laws using AI?'><button onclick='ask()'>Ask AI</button><pre id='ans' style='white-space:pre-wrap;margin-top:20px'>AI answer will appear...</pre></div>
    <footer>COPYRIGHT © 2026<br>S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, Central University of Karnataka<br>Research: Enhancing PD of Secondary STEM Teachers by AI Powered Design Thinking Chatbot</footer>
    <script>async function ask(){{let q=document.getElementById('q').value;document.getElementById('ans').innerText='AI thinking...';let r=await fetch('/chat?q='+encodeURIComponent(q));let d=await r.json();document.getElementById('ans').innerText=d.answer;}}</script></body></html>"""
    return make_response(render_template_string(html))

@app.route("/chat")
@limiter.limit("15 per minute")
def chat():
    q=request.args.get("q","").strip()
    if not is_safe(q): return jsonify({"answer":"Invalid"}),400
    cat=get_category(q)
    analytics["total_questions"]+=1; analytics["categories"][cat]+=1; analytics["daily_count"][str(datetime.now().date())]+=1
    save_to_sheet("QUESTION", cat)
    prompt=ACTIVE["strategies"][ACTIVE["active_strategy"]]
    try:
        res=model.generate_content(prompt+f"\nTeacher Q: {q}")
        return jsonify({"answer":res.text})
    except:
        return jsonify({"answer":"AI busy, try again"}),500

@app.route("/admin")
def admin():
    if request.args.get("key")!= os.environ.get("ADMIN_KEY","admin123"): return "Unauthorized",401
    cats=dict(analytics["categories"]); days=dict(analytics["daily_count"]); active=ACTIVE["active_strategy"]
    opts="".join([f"<option value='{k}' {'selected' if k==active else ''}>{k.upper()}</option>" for k in ACTIVE["strategies"]])
    return render_template_string(f"""
    <html><head><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>body{{font-family:Segoe UI;max-width:1000px;margin:auto;padding:20px}}.card{{background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px #ddd;margin:15px 0}}</style></head>
    <body><h2>Admin - Permanent Sheet Saving ON ✅</h2>
    <div class="card" style="border:2px solid #facc15"><h3>🎮 Switch AI Strategy</h3><p>Current: <b>{active.upper()}</b></p>
    <form action="/admin/switch" method="POST"><input type="hidden" name="key" value="{request.args.get('key')}"><select name="strategy">{opts}</select><button>🚀 SWITCH</button></form>
    <p><a href='{os.environ.get("GOOGLE_SHEET_URL","")}' target='_blank' style='font-size:12px'>Sheet saving active? Check Sheet will have new rows.</a></p></div>
    <div class="card"><h3>Live Counts (This Server)</h3>Visits: {analytics["total_visits"]} | Questions: {analytics["total_questions"]}</div>
    <div class="card"><h3>Permanent Thesis Data is in Google Sheet - Even if server restarts, Sheet is safe.</h3><p>Open your Google Sheet to see all data.</p><canvas id="c"></canvas></div>
    <script>new Chart(document.getElementById('c'),{{type:'pie',data:{{labels:{list(cats.keys())},datasets:[{{data:{list(cats.values())}}}]}}}});</script></body></html>""")

@app.route("/admin/switch", methods=["POST"])
def switch_strategy():
    if request.form.get("key")!= os.environ.get("ADMIN_KEY","admin123"): return "Unauthorized",401
    ns=request.form.get("strategy")
    if ns in ACTIVE["strategies"]:
        ACTIVE["active_strategy"]=ns
        try:
            with open("strategies.json","w") as f: json.dump(ACTIVE,f)
        except: pass
        save_to_sheet(f"STRATEGY_SWITCH_TO_{ns}")
    return redirect(f"/admin?key={request.form.get('key')}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
