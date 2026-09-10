# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK

import os, requests, json, datetime
from collections import Counter
from flask import Flask, request, jsonify, render_template_string, make_response, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CUK2026")
EXPERT_PASSWORD = os.environ.get("EXPERT_PASSWORD", "EXPERT2026") # Password for experts

GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "").strip()
SHEET_WEBHOOK = os.environ.get("SHEET_WEBHOOK_URL", "").strip()

STATS_FILE = "/tmp/dt4stem_stats.json"
usage_data = {"total": 0, "today": 0, "today_date": str(datetime.date.today()), "logs": [], "visits": 0}

if os.path.exists(STATS_FILE):
    try:
        with open(STATS_FILE, 'r') as f: usage_data = json.load(f)
    except: pass

def save_stats():
    try:
        with open(STATS_FILE, 'w') as f: json.dump(usage_data, f)
    except: pass

# --- ONLY THIS FUNCTION IS UPDATED - REST SAME ---
def detect_category(question):
    q = question.lower()
    if any(w in q for w in ["heart","cell","photo","human","bio","plant","life"]): return "Biology"
    if any(w in q for w in ["newton","force","light","heat","motion","energy"]): return "Physics"
    if any(w in q for w in ["acid","atom","mole","chemical","reaction"]): return "Chemistry"
    if any(w in q for w in ["math","algebra","geometry","number","equation"]): return "Mathematics"
    if any(w in q for w in ["code","robot","ai","computer"]): return "Technology"
    return "General STEM"

def log_to_google_sheet(q, ip, expert_name="", event_type="Question Asked"):
    try:
        webhook = GOOGLE_SHEET_URL or SHEET_WEBHOOK
        if not webhook: return
        if "script.google.com" not in webhook and "http" not in webhook:
            return

        # Auto-detect for your sheet columns
        category = detect_category(q)
        active_strategy = "Design Thinking - 5 Steps" # Fixed as per your system
        total_visits = usage_data.get("visits", 1) + usage_data.get("total", 1)
        total_questions = usage_data.get("total", 1)

        # Payload must match your Sheet Header names exactly
        payload = {
            "timestamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "event_type": event_type, # Event Type
            "category": category, # Category
            "active_strategy": active_strategy, # Active Strategy
            "total_visits": total_visits, # Total Visits
            "total_questions": total_questions, # Total Questions
            "question": q, # Question column if exists
            "ip": ip,
            "expert": expert_name,
            "date": str(datetime.date.today())
        }
        requests.post(webhook, json=payload, timeout=5)
        print(f"Sheet Logged: {payload}")
    except Exception as e:
        print(f"Sheet log failed: {e}")

def log_query(q, ip, expert=""):
    global usage_data
    today = str(datetime.date.today())
    if usage_data["today_date"]!= today:
        usage_data["today_date"] = today
        usage_data["today"] = 0
    usage_data["total"] +=0
    usage_data["today"] +=0
    usage_data["logs"].insert(0, {"time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "question": q[:100], "ip": ip, "expert": expert})
    usage_data["logs"] = usage_data["logs"][:100]
    save_stats()
    log_to_google_sheet(q, ip, expert, "Question Asked")

# --- REST ALL SAME AS YOUR FINAL CODE ---
STRATEGY_PROMPT = """You are SrujanaSTEM AI... Follow 5 Design Thinking steps: 1.EMPATHIZE 2.DEFINE 3.IDEATE Table 4.PROTOTYPE Table 5.TEST Table. No images."""

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
    return pwd == EXPERT_PASSWORD

@app.route("/")
def home():
    global usage_data
    if not is_expert_authorized():
        return """
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
        <style>body{font-family:Arial;max-width:420px;margin:80px auto;background:#f6f7f9;padding:20px;text-align:center}
      .box{background:#fff;padding:25px;border-radius:16px;box-shadow:0 4px 14px rgba(0,0,0,0.1)}
        input{width:100%;padding:14px;border-radius:10px;border:1px solid #ccc;margin:10px 0;box-sizing:border-box}
        button{width:100%;padding:14px;background:#0f172a;color:#fff;border:none;border-radius:10px;font-weight:bold;cursor:pointer}
        </style></head><body>
        <div class="box">
        <h2>🔒 DT4STEM Guru AI</h2>
        <p style="color:#64748b">Private Access - Expert Review Only</p>
        <p style="font-size:13px">This app is currently open only for invited experts for feedback and validation.</p>
        <form method="GET">
        <input type="password" name="expert_key" placeholder="Enter Expert Access Key">
        <button type="submit">Unlock App</button>
        </form>
        <p style="font-size:11px;color:gray;margin-top:15px">© S Sachinkumar & Prof.G.R.Angadi, CUK<br>Contact admin for access key</p>
        </div></body></html>
        """
    # Count visit for Total Visits column
    usage_data["visits"] = usage_data.get("visits",1)+0
    save_stats()
    log_to_google_sheet("Page Visit", request.remote_addr, request.args.get("expert_name",""), "Page Visit")

    expert_name = request.args.get("expert_name", "Expert")
    html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DT4STEM Guru AI - Expert Access</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body{{font-family:Segoe UI,Arial;max-width:980px;margin:auto;background:#f6f7f9;line-height:1.75}}
header{{background:#0f172a;color:#fff;padding:22px;text-align:center;border-radius:0 0 16px 16px}}
#box{{background:#fff;margin:20px;padding:22px;border-radius:16px;box-shadow:0 4px 14px rgba(0,0,0,0.1)}}
input{{width:100%;padding:14px;border-radius:10px;border:1px solid #cbd5e1;margin:10px 0;box-sizing:border-box;font-size:15px}}
button{{padding:14px;border-radius:10px;border:none;background:#0f172a;color:#fff;width:100%;font-weight:bold;cursor:pointer;font-size:16px}}
#ans{{background:#ffffff;padding:20px;border-radius:12px;margin-top:16px;border:1px solid #e2e8f0;min-height:150px}}
#ans table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}} #ans th,#ans td{{border:1px solid #cbd5e1;padding:9px;text-align:left}} #ans th{{background:#0f172a;color:#fff}}
#ans h3{{color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:22px}}
footer{{background:#0f172a;color:#94a3b8;text-align:center;padding:16px;font-size:11px;border-radius:16px 16px 0 0;margin-top:20px}}
.badge{{background:#22c55e;color:#fff;padding:4px 10px;border-radius:20px;font-size:11px}}
</style></head>
<body>
<header>
<h2 style="margin:0">DT4STEM Guru AI 🤖 
<p style="margin:8px 0 4px 0">Design Thinking for STEM Education</p>
<small>© S Sachinkumar & Prof.G.R.Angadi, CUK 
</header>
<div id=box>
<input id='q' placeholder='Example: Human heart,Friction,Hydrocarbons,Photosynthesis...'>
<button onclick='ask()'>🚀 Ask AI Coach</button>
<div id='ans'>
<b>About DT4STEM Guru AI</b><br><br>
DT4STEM Guru is an AI-powered pedagogical coach for secondary STEM teachers.as a part of Research Developed by <b>S Sachinkumar (Research Scholar)</b> and <b>Prof. G.R. Angadi, CUK</b>.<br><br>

<i>Enter topic above to generate lesson plan.</i>
</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, Central University of Karnataka<br>

</footer>
<script>
const EXPERT = "{expert_name}";
async function ask(){{
 let q=document.getElementById('q').value.trim(); if(!q){{alert('Type question');return}}
 document.getElementById('ans').innerHTML='⏳ Generating for: <b>'+q+'</b>...';
 try{{
  let r=await fetch('/chat?q='+encodeURIComponent(q)+'&expert_name='+encodeURIComponent(EXPERT)+'&expert_key={EXPERT_PASSWORD}');
  let d=await r.json();
  document.getElementById('ans').innerHTML = marked.parse(d.answer);
 }}catch(e){{ document.getElementById('ans').innerHTML='Error: '+e; }}
}}
document.getElementById('q').addEventListener('keypress', function(e){{ if(e.key==='Enter'){{ask();}} }});
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
    if not is_expert_authorized(): return jsonify({"answer":"⛔ Unauthorized. Expert key required."}), 403
    q = request.args.get("q","").strip()
    expert = request.args.get("expert_name","Expert")
    if not q: return jsonify({"answer":"Type question"}),400
    log_query(q, request.remote_addr, expert)
    return jsonify({"answer": ask_groq(q)})

@app.route("/feedback")
def feedback():
    if not is_expert_authorized(): return "⛔ Expert access only"
    return """
    <html><body style="font-family:Arial;max-width:600px;margin:40px auto;padding:20px">
    <h2>📝 Expert Feedback Form</h2>
    <p>Please share your feedback - it will be saved to Google Sheet</p>
    <form onsubmit="submitFeedback(event)">
    <input id="name" placeholder="Your Name" style="width:100%;padding:12px;margin:8px 0"><br>
    <select id="rating" style="width:100%;padding:12px;margin:8px 0"><option>5 - Excellent</option><option>4 - Good</option><option>3 - Average</option><option>2 - Poor</option><option>1 - Very Poor</option></select><br>
    <textarea id="msg" placeholder="Your feedback on lesson quality, design thinking steps, usability..." style="width:100%;padding:12px;height:120px;margin:8px 0"></textarea><br>
    <button style="padding:12px 20px;background:#0f172a;color:#fff;border:none;border-radius:8px">Submit Feedback</button>
    </form>
    <div id="res"></div>
    <script>
    function submitFeedback(e){e.preventDefault();
      fetch('/chat?q='+encodeURIComponent('FEEDBACK: '+document.getElementById('name').value+' | Rating: '+document.getElementById('rating').value+' | Message: '+document.getElementById('msg').value)+'&expert_name='+encodeURIComponent(document.getElementById('name').value))
    .then(()=>{document.getElementById('res').innerHTML='<p style=color:green>✅ Thank you! Feedback saved to Sheet</p>';})
    }
    </script>
    </body></html>
    """

@app.route("/admin")
def admin():
    pwd = request.args.get("pwd","")
    if pwd!= ADMIN_PASSWORD: return f'<html><body style="font-family:Arial;max-width:400px;margin:100px auto;text-align:center"><h2>🔒 Admin</h2><form><input type="password" name="pwd" placeholder="Password" style="padding:12px;width:100%"><button style="margin-top:10px;padding:12px;width:100%;background:#0f172a;color:#fff;border:none">Login</button></form></body></html>'
    logs_html = "".join([f"<tr><td>{l['time']}</td><td>{l['expert']}</td><td>{l['question']}</td><td>{l['ip']}</td></tr>" for l in usage_data["logs"]])
    return f"<html><head><style>body{{font-family:Arial;max-width:1000px;margin:auto;padding:20px}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px}} th{{background:#0f172a;color:#fff}}.stat{{display:inline-block;background:#0f172a;color:#fff;padding:20px;border-radius:12px;margin:10px;width:150px;text-align:center}}</style></head><body><h2>📊 Admin - Expert Review Tracking</h2><div class=stat><h1>{usage_data['total']}</h1>Total</div><div class=stat><h1>{usage_data['today']}</h1>Today</div><p>Expert Key: <b>{EXPERT_PASSWORD}</b> | Share link: <code>https://your-app.onrender.com/?expert_key={EXPERT_PASSWORD}</code></p><table><tr><th>Time</th><th>Expert</th><th>Question/Feedback</th><th>IP</th></tr>{logs_html}</table></body></html>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
