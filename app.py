# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, CUK
# Title: DT4STEM Guru - AI Powered Design Thinking Chatbot
# Research: Enhancing PD of Secondary STEM Teachers by AI Powered Design Thinking

import os, re, json, requests
from collections import Counter
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, make_response, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# NEW GOOGLE GENAI SDK - Fixed deprecated warning
from google import genai
from google.genai import types

app = Flask(__name__)

# Secure API Client
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "CUK_Secure_2026")

# Strategies - You can switch from Admin Panel
DEFAULT_STRATEGIES = {
    "design_thinking": "You are DT4STEMGURU-AI Powered PD APP, an AI-Powered Design Thinking Coach for Secondary STEM Teachers in India (NEP 2020 aligned). You MUST answer in 5 steps: 1.EMPATHIZE (student pain point), 2.DEFINE (problem statement), 3.IDEATE (3 creative ideas with 1 AI tool like PhET, GeoGebra, ChatGPT, Canva AI), 4.PROTOTYPE (40-min classroom activity), 5.TEST (assessment rubric). Use simple English. End every answer with: \n\n---\n© S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, Central University of Karnataka",
    "tpack_ai": "You are AI-Powered TPACK Expert for STEM Teachers. Explain Content, Pedagogy, Technology integration. Give 1 AI tool example and how to use. End with © S Sachinkumar & Prof.G.R.Angadi, CUK",
    "nep2020": "You are NEP 2020 Aligned PD Coach for STEM Teachers. Explain answer as per NEP 2020 principles - experiential, inquiry, multidisciplinary. End with © S Sachinkumar & Prof.G.R.Angadi, CUK",
    "lesson_ai": "You are AI Lesson Planner for Secondary STEM. Give 40-min lesson plan with Learning Outcomes, Materials, AI Tool Integration, 5E F, Assessment. End with © S Sachinkumar & Prof.G.R.Angadi, CUK",
    "mentoring_ai": "You are AI Mentor for STEM Teachers. Give empathy, classroom story, growth mindset tip, action research idea. End with © S Sachinkumar & Prof.G.R.Angadi, CUK"
}

ACTIVE = {"active_strategy": "design_thinking", "strategies": DEFAULT_STRATEGIES}
try:
    if os.path.exists("strategies.json"):
        with open("strategies.json","r", encoding="utf-8") as f:
            ACTIVE = json.load(f)
except: pass

analytics = {"total_visits":0,"total_questions":0,"categories":Counter(),"daily_count":Counter()}
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")

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
        requests.post(GOOGLE_SHEET_URL, json=payload, timeout=4)
    except: pass

def is_safe(q):
    if not q or len(q)>500: return False
    if re.search(r"<script|DROP TABLE|DELETE FROM|ignore previous|system prompt", q, re.I): return False
    return True

def get_category(q):
    q=q.lower()
    if any(w in q for w in ["physics","chemistry","biology","science","math"]): return "STEM Content"
    if any(w in q for w in ["pedagogy","teach","method","didactic"]): return "Pedagogy"
    if any(w in q for w in ["ai","tpack","technology","phET","geogebra"]): return "AI & TPACK"
    if any(w in q for w in ["assessment","rubric","evaluation","exam"]): return "Assessment"
    if "professional" in q: return "Professional Development"
    return "General STEM PD"

@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    return response

@app.route("/")
def home():
    analytics["total_visits"]+=1
    save_to_sheet("VISIT")
    active = ACTIVE["active_strategy"].upper()
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>DT4STEM Guru AI - CUK</title>
    <style>body{{font-family:Segoe UI,Arial;max-width:900px;margin:auto;background:#f6f7f9;line-height:1.6}} header{{background:#0f172a;color:#fff;padding:20px;text-align:center;border-radius:0 0 16px 16px}} #box{{background:#fff;margin:20px;padding:22px;border-radius:16px;box-shadow:0 4px 12px #ddd}} input{{width:100%;padding:14px;border-radius:10px;border:1px solid #ccc;margin:10px 0;box-sizing:border-box}} button{{padding:14px 22px;border-radius:10px;border:none;background:#0f172a;color:#fff;width:100%;font-weight:bold;cursor:pointer}} pre{{white-space:pre-wrap;background:#f8fafc;padding:15px;border-radius:10px;margin-top:15px;border:1px solid #e2e8f0}} footer{{background:#0f172a;color:#cbd5e1;text-align:center;padding:18px;font-size:11px;margin-top:20px;border-radius:16px 16px 0 0}}</style></head>
    <body><header><h2 style="margin:0">DT4STEM Guru AI 🤖</h2><p style="margin:5px 0 0">AI Powered Design Thinking Coach for STEM Teachers<br><small>© S Sachinkumar & Prof.G.R.Angadi, CUK</small></p></header>
    <div id=box><small>🧠 Current Mode: <b>{active}</b> | Total Teachers Helped: {analytics["total_questions"]}</small>
    <input id='q' placeholder='Ask: How to teach Newton 2nd law using PhET AI?'><button onclick='ask()'>🚀 Ask AI Coach</button>
    <pre id='ans'>AI answer will appear here in 5 Steps - EMPATHIZE, DEFINE, IDEATE, PROTOTYPE, TEST...</pre></div>
    <footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi<br>Dept. of Education, Central University of Karnataka<br>Research Topic: Enhancing Professional Development of Secondary School STEM Teachers by AI Powered Design Thinking Chatbot and App<br>For Research Purpose Only | No Personal Data Collected</footer>
    <script>async function ask(){{let q=document.getElementById('q').value;if(!q){{alert('Please type question');return}} document.getElementById('ans').innerText='⏳ AI Coach thinking in 5 steps... Please wait 3 sec...'; try{{let r=await fetch('/chat?q='+encodeURIComponent(q)); let d=await r.json(); document.getElementById('ans').innerText=d.answer;}}catch(e){{document.getElementById('ans').innerText='Network error, please try again';}}}}</script></body></html>"""
    return make_response(render_template_string(html))

@app.route("/chat")
@limiter.limit("15 per minute")
def chat():
    q=request.args.get("q","").strip()
    if not is_safe(q): return jsonify({"answer":"Invalid input."}),400
    if not client: return jsonify({"answer":"Server Error: GEMINI_API_KEY not set."}),500

    cat=get_category(q)
    analytics["total_questions"]+=1; analytics["categories"][cat]+=1; analytics["daily_count"][str(datetime.now().date())]+=1
    save_to_sheet("QUESTION", cat)

    prompt = ACTIVE["strategies"][ACTIVE["active_strategy"]]
    full_prompt = f"{prompt}\n\nTeacher Question: {q}"

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest", # ALWAYS WORKS - auto points to latest
            contents=full_prompt
        )
        return jsonify({"answer": response.text})
    except Exception as e:
        print(f"AI ERROR 1: {e}")
        try:
            response2 = client.models.generate_content(
                model="gemini-2.5-flash", # Fallback - stable till June 2026
                contents=full_prompt
            )
            return jsonify({"answer": response2.text})
        except Exception as e2:
            print(f"AI ERROR 2: {e2}")
            return jsonify({"answer": f"AI error: {str(e)[:250]}"}),500

@app.route("/admin")
def admin():
    if request.args.get("key")!= ADMIN_KEY: return "Unauthorized - Wrong Admin Key",401
    cats=dict(analytics["categories"]); days=dict(analytics["daily_count"]); active=ACTIVE["active_strategy"]
    opts="".join([f"<option value='{k}' {'selected' if k==active else ''}>{k.upper()}</option>" for k in ACTIVE["strategies"]])
    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>body{{font-family:Segoe UI;max-width:1000px;margin:auto;padding:15px;background:#f8fafc}}.card{{background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px #ddd;margin:15px 0}}</style></head>
    <body><h2>Admin - DT4STEM Guru AI ✅ NEW SDK</h2>
    <div class="card" style="border:2px solid #22c55e"><h3>🎮 Switch AI Powered Strategy - Remote Control</h3><p>Current Active: <b>{active.upper()}</b></p>
    <form action="/admin/switch" method="POST"><input type="hidden" name="key" value="{request.args.get('key')}"><select name="strategy" style="padding:10px">{opts}</select><button style="padding:10px 15px;background:#0f172a;color:#fff;border:none;border-radius:6px">🚀 SWITCH LIVE</button></form>
    <p style="color:green">✅ Google Sheet Saving: {'ON' if GOOGLE_SHEET_URL else 'OFF - Add GOOGLE_SHEET_URL in Render'}</p></div>
    <div class="card"><h3>Live Thesis Data (This Server Session)</h3><p>Visits: {analytics["total_visits"]} | Questions: {analytics["total_questions"]}</p><p><b>Category Wise:</b> {cats}</p><p><b>Day Wise:</b> {days}</p></div>
    <div class="card"><h3>Anonymous Usage Pie Chart - For Thesis Chapter 4 Screenshot</h3><canvas id="c"></canvas></div>
    <script>new Chart(document.getElementById('c'),{{type:'pie',data:{{labels:{list(cats.keys())},datasets:[{{data:{list(cats.values())},backgroundColor:['#0f172a','#22c55e','#f59e0b','#ef4444','#8b5cf6']}}]}}}});</script></body></html>""")

@app.route("/admin/switch", methods=["POST"])
def switch_strategy():
    if request.form.get("key")!= ADMIN_KEY: return "Unauthorized",401
    ns=request.form.get("strategy")
    if ns in ACTIVE["strategies"]:
        ACTIVE["active_strategy"]=ns
        try:
            with open("strategies.json","w", encoding="utf-8") as f: json.dump(ACTIVE,f)
        except: pass
        save_to_sheet(f"STRATEGY_SWITCH_TO_{ns}")
    return redirect(f"/admin?key={request.form.get('key')}")

@app.route("/about")
def about():
    return render_template_string("""<html><body style="font-family:Segoe UI;max-width:800px;margin:auto;padding:20px"><h2>About SrujanaSTEM AI / DT4STEM Guru AI</h2><p><b>Research Title:</b> Enhancing Professional Development of Secondary School STEM Teachers by AI Powered Design Thinking Chatbot and App</p><p><b>Researcher:</b> S Sachinkumar, PhD Scholar, Dept. of Education, Central University of Karnataka</p><p><b>Guide:</b> Prof.G.R.Angadi, Dept. of Education, CUK</p><p><b>Purpose:</b> This AI chatbot is developed for academic research to support secondary STEM teachers with NEP 2020 aligned, AI integrated pedagogical strategies using Design Thinking framework (Empathize, Define, Ideate, Prototype, Test).</p><p><b>Data Policy:</b> No personal data collected. Only anonymous visit counts and question categories stored for thesis analysis.</p><p><b>Copyright © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK. All Rights Reserved.</b></p></body></html>""")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
