# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK

import os, requests, json, datetime
from collections import Counter
from flask import Flask, request, jsonify, render_template_string, make_response, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CUK2026")
EXPERT_PASSWORD = os.environ.get("EXPERT_PASSWORD", "CUKExpert@2026")
GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "").strip()
SHEET_WEBHOOK = os.environ.get("SHEET_WEBHOOK_URL", "").strip()

STATS_FILE = "/tmp/dt4stem_stats.json"
usage_data = {"total": 0, "today": 0, "today_date": str(datetime.date.today()), "logs": []}
if os.path.exists(STATS_FILE):
    try:
        with open(STATS_FILE, 'r') as f: usage_data = json.load(f)
    except: pass

def save_stats():
    try:
        with open(STATS_FILE, 'w') as f: json.dump(usage_data, f)
    except: pass

def log_query(q, ip, expert=""):
    global usage_data
    today = str(datetime.date.today())
    if usage_data["today_date"]!= today:
        usage_data["today_date"] = today; usage_data["today"]=0
    usage_data["total"]+=1; usage_data["today"]+=1
    usage_data["logs"].insert(0, {"time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "question": q[:100], "ip": ip, "expert": expert})
    usage_data["logs"]=usage_data["logs"][:100]; save_stats()
    try:
        webhook = GOOGLE_SHEET_URL or SHEET_WEBHOOK
        if webhook and ("script.google.com" in webhook or "http" in webhook):
            requests.post(webhook, json={"timestamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "question": q, "ip": ip, "expert": expert}, timeout=5)
    except: pass

STRATEGY_PROMPT = """You are SrujanaSTEM AI... Follow 5 Design Thinking steps: 1.EMPATHIZE 2.DEFINE 3.IDEATE Table 4.PROTOTYPE Table 5.TEST Table."""
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")

def ask_groq(question):
    if not GROQ_KEY: return "⚠️ GROQ_API_KEY missing!"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    for model in ["openai/gpt-oss-20b", "llama-3.1-8b-instant"]:
        try:
            payload = {"model": model, "messages": [{"role": "system", "content": STRATEGY_PROMPT}, {"role": "user", "content": question}], "temperature": 0.8, "max_tokens": 2500}
            r = requests.post(url, headers=headers, json=payload, timeout=35)
            if r.status_code == 200: return r.json()["choices"][0]["message"]["content"]
        except: continue
    return "❌ Groq Error."

def is_expert_authorized():
    pwd = request.args.get("expert_key", "") or request.cookies.get("expert_auth", "")
    # If no expert password set, make public for Google indexing
    if not EXPERT_PASSWORD or EXPERT_PASSWORD=="": return True
    return pwd == EXPERT_PASSWORD

@app.route("/")
def home():
    # Private mode check - but allow Googlebot
    user_agent = request.headers.get('User-Agent','').lower()
    is_googlebot = 'googlebot' in user_agent or 'google' in user_agent

    if not is_expert_authorized() and not is_googlebot:
        return """
        <html><head><meta name="robots" content="noindex"><meta name="viewport" content="width=device-width, initial-scale=1">
        <style>body{font-family:Arial;max-width:420px;margin:80px auto;background:#f6f7f9;padding:20px;text-align:center}
      .box{background:#fff;padding:25px;border-radius:16px;box-shadow:0 4px 14px rgba(0,0,0,0.1)}
        input{width:100%;padding:14px;border-radius:10px;border:1px solid #ccc;margin:10px 0;box-sizing:border-box}
        button{width:100%;padding:14px;background:#0f172a;color:#fff;border:none;border-radius:10px;font-weight:bold;cursor:pointer}
        </style></head><body><div class="box"><h2>🔒 DT4STEM Guru AI</h2><p>Private Access - Expert Review Only</p><form method="GET"><input type="password" name="expert_key" placeholder="Expert Access Key"><button>Unlock</button></form></div></body></html>
        """

    expert_name = request.args.get("expert_name", "Guest")
    html = f"""
<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DT4STEM Guru AI - Design Thinking for STEM Education | CUK</title>
<meta name="description" content="DT4STEM Guru AI is an AI-powered pedagogical coach for secondary STEM teachers developed by S Sachinkumar & Prof. G.R. Angadi, Central University of Karnataka. Generates Design Thinking based lesson plans with EdTech tools.">
<meta name="keywords" content="DT4STEM Guru AI, Design Thinking STEM, STEM education India, S Sachinkumar, Prof G R Angadi, CUK, Central University Karnataka, AI lesson planner, PhET, STEM coach">
<meta name="author" content="S Sachinkumar & Prof.G.R.Angadi, Central University of Karnataka">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://dt4stem-guru.onrender.com/">
<meta property="og:title" content="DT4STEM Guru AI - Design Thinking for STEM">
<meta property="og:description" content="AI Coach for STEM Teachers - Empathize, Define, Ideate, Prototype, Test - By CUK Researchers">
<meta property="og:type" content="website">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "EducationalApplication",
  "name": "DT4STEM Guru AI",
  "description": "AI-powered Design Thinking coach for STEM teachers",
  "author": [{{"@type":"Person","name":"S Sachinkumar"}},{{"@type":"Person","name":"Prof. G.R. Angadi"}}],
  "publisher": {{"@type":"Organization","name":"Central University of Karnataka"}}
}}
</script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body{{font-family:Segoe UI,Arial;max-width:980px;margin:auto;background:#f6f7f9;line-height:1.75}}
header{{background:#0f172a;color:#fff;padding:22px;text-align:center;border-radius:0 0 16px 16px}}
#box{{background:#fff;margin:20px;padding:22px;border-radius:16px;box-shadow:0 4px 14px rgba(0,0,0,0.1)}}
input{{width:100%;padding:14px;border-radius:10px;border:1px solid #cbd5e1;margin:10px 0;box-sizing:border-box;font-size:15px}}
button{{padding:14px;border-radius:10px;border:none;background:#0f172a;color:#fff;width:100%;font-weight:bold;cursor:pointer;font-size:16px}}
#ans{{background:#ffffff;padding:20px;border-radius:12px;margin-top:16px;border:1px solid #e2e8f0;min-height:150px}}
#ans table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}} #ans th,#ans td{{border:1px solid #cbd5e1;padding:9px;text-align:left}} #ans th{{background:#0f172a;color:#fff}}
footer{{background:#0f172a;color:#94a3b8;text-align:center;padding:16px;font-size:11px;border-radius:16px 16px 0 0;margin-top:20px}}
</style></head>
<body>
<header>
<h1 style="margin:0;font-size:22px">DT4STEM Guru AI 🤖</h1>
<p style="margin:8px 0 4px 0">Design Thinking for STEM Education | AI Lesson Planner for Teachers</p>
<small>© S Sachinkumar & Prof.G.R.Angadi, Department of Education, Central University of Karnataka</small>
</header>
<div id=box>
<h2 style="font-size:16px;color:#0f172a">AI-Powered Design Thinking Coach for Secondary STEM Teachers in India</h2>
<input id='q' placeholder='Type STEM topic: human heart, photosynthesis, newtons laws...'>
<button onclick='ask()'>🚀 Ask AI Coach</button>
<div id='ans'>
<b>About DT4STEM Guru AI</b><br><br>
<b>DT4STEM Guru AI</b> is an AI-powered pedagogical coach designed for secondary school STEM teachers. It is developed as part of research by <b>S Sachinkumar (Research Scholar)</b> and <b>Prof. G.R. Angadi, Dept. of Education, Central University of Karnataka, Kalaburagi</b>.<br><br>
The system integrates <b>Design Thinking (Empathize, Define, Ideate, Prototype, Test)</b> with curated EdTech tools (PhET, NASA Eyes, BioDigital, Desmos, Tinkercad) to create contextual, activity-based lesson plans for Science, Technology, Engineering and Mathematics.<br><br>
<i>Enter your STEM topic above to generate a Design Thinking based lesson plan.</i>
</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, Central University of Karnataka, Kalaburagi, India<br>DT4STEM Guru AI - Design Thinking for STEM Education</footer>
<script>
async function ask(){{
 let q=document.getElementById('q').value.trim(); if(!q){{alert('Type question');return}}
 document.getElementById('ans').innerHTML='⏳ Generating...';
 try{{
  let r=await fetch('/chat?q='+encodeURIComponent(q)+'&expert_key={EXPERT_PASSWORD}');
  let d=await r.json();
  document.getElementById('ans').innerHTML = marked.parse(d.answer);
 }}catch(e){{ document.getElementById('ans').innerHTML='Error: '+e; }}
}}
document.cookie = "expert_auth={EXPERT_PASSWORD}; path=/; max-age=86400";
</script>
</body></html>
"""
    resp = make_response(render_template_string(html))
    resp.set_cookie("expert_auth", EXPERT_PASSWORD, max_age=86400)
    return resp

@app.route("/chat")
@limiter.limit("20 per minute")
def chat():
    if not is_expert_authorized(): return jsonify({"answer":"⛔ Private mode - expert key required"}),403
    q = request.args.get("q","").strip()
    if not q: return jsonify({"answer":"Type question"}),400
    log_query(q, request.remote_addr, request.args.get("expert_name",""))
    return jsonify({"answer": ask_groq(q)})

# --- SEO FILES FOR GOOGLE ---
@app.route("/sitemap.xml")
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://dt4stem-guru.onrender.com/</loc><priority>1.0</priority></url>
<url><loc>https://dt4stem-guru.onrender.com/admin</loc><priority>0.3</priority></url>
</urlset>"""
    return Response(xml, mimetype='application/xml')

@app.route("/robots.txt")
def robots():
    txt = """User-agent: *
Allow: /
Sitemap: https://dt4stem-guru.onrender.com/sitemap.xml
"""
    return Response(txt, mimetype='text/plain')

@app.route("/admin")
def admin():
    pwd = request.args.get("pwd","")
    if pwd!= ADMIN_PASSWORD: return '<html><body style="font-family:Arial;max-width:400px;margin:100px auto;text-align:center"><h2>Admin</h2><form><input type="password" name="pwd" placeholder="Password" style="padding:12px;width:100%"><button style="margin-top:10px;padding:12px;width:100%;background:#0f172a;color:#fff">Login</button></form></body></html>'
    logs_html = "".join([f"<tr><td>{l['time']}</td><td>{l['expert']}</td><td>{l['question']}</td></tr>" for l in usage_data["logs"]])
    return f"<html><body style='font-family:Arial;max-width:1000px;margin:auto;padding:20px'><h2>📊 Admin</h2><p>Total: {usage_data['total']} | Today: {usage_data['today']}</p><table border=1 style='border-collapse:collapse;width:100%'><tr><th>Time</th><th>Expert</th><th>Question</th></tr>{logs_html}</table></body></html>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
