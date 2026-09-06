# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK

import os, requests, json, datetime
from collections import Counter
from flask import Flask, request, jsonify, render_template_string, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CUK2026")

# --- YOUR EXISTING GOOGLE SHEET ENV - Kept Same ---
GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "").strip() # Your old setting
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "").strip() # if you use ID
SHEET_WEBHOOK = os.environ.get("SHEET_WEBHOOK_URL", "").strip() # any other name you used

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

def log_to_google_sheet(question, ip):
    """Your old Google Sheet logging - kept exactly as you added"""
    try:
        # Try all possible ENV names you might have added
        webhook_url = GOOGLE_SHEET_URL or SHEET_WEBHOOK or GOOGLE_SHEET_ID
        if not webhook_url:
            return # No sheet configured, skip

        # If it's a full Google Apps Script URL
        if "script.google.com" in webhook_url or "http" in webhook_url:
            payload = {
                "timestamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "question": question,
                "ip": ip,
                "date": str(datetime.date.today())
            }
            requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        print(f"Sheet log failed (but app continues): {e}")

def log_query(q, ip):
    global usage_data
    today = str(datetime.date.today())
    if usage_data["today_date"]!= today:
        usage_data["today_date"] = today
        usage_data["today"] = 0
    usage_data["total"] += 1
    usage_data["today"] += 1
    usage_data["logs"].insert(0, {
        "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "question": q[:100],
        "ip": ip
    })
    usage_data["logs"] = usage_data["logs"][:100]
    save_stats()

    # Also log to your Google Sheet - OLD SETTING STILL WORKS
    log_to_google_sheet(q, ip)

STRATEGY_PROMPT = """
You are SrujanaSTEM AI - Expert STEM Coach.
MUST follow 5 Design Thinking steps:
1. EMPATHIZE: misconception bullets
2. DEFINE: problem statement
3. IDEATE: Table | Idea No | Teaching Idea | Tool Name | Why Best? |
4. PROTOTYPE: Table | Time | Activity | Tool | Teacher Action |
5. TEST: Table | Criteria | Excellent | Good | Needs Improvement |
No images. Text + tables only.
"""

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
<input id='q' placeholder='Example: human heart, photosynthesis, newtons laws...'>
<button onclick='ask()'>🚀 Ask AI Coach</button>
<div id='ans'>
<b>About DT4STEM Guru AI</b><br><br>
DT4STEM Guru is an AI-powered pedagogical coach designed for secondary school STEM teachers. It is developed as part of research by <b>S Sachinkumar (Research Scholar)</b> and <b>Prof. G.R. Angadi, Dept. of Education, Central University of Karnataka, Kalaburagi</b>.<br><br>
The system integrates <b>Design Thinking (Empathize, Define, Ideate, Prototype, Test)</b> with curated EdTech tools to create contextual, activity-based lesson plans.<br><br>
<i>Enter your STEM topic above to generate a Design Thinking based lesson plan.</i>
</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, Central University of Karnataka</footer>
<script>
async function ask(){
 let q=document.getElementById('q').value.trim(); if(!q){alert('Type question');return}
 document.getElementById('ans').innerHTML='⏳ Generating lesson for: <b>'+q+'</b>...';
 try{
  let r=await fetch('/chat?q='+encodeURIComponent(q));
  let d=await r.json();
  document.getElementById('ans').innerHTML = marked.parse(d.answer);
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
    log_query(q, request.remote_addr) # Logs to BOTH local + Google Sheet
    return jsonify({"answer": ask_groq(q)})

@app.route("/admin")
def admin():
    pwd = request.args.get("pwd", "")
    if pwd!= ADMIN_PASSWORD:
        return f"""
        <html><body style="font-family:Arial;max-width:400px;margin:100px auto;text-align:center">
        <h2>🔒 Admin Login</h2>
        <form><input type="password" name="pwd" placeholder="Password" style="padding:12px;width:100%;border-radius:8px;border:1px solid #ccc">
        <button style="margin-top:10px;padding:12px;width:100%;background:#0f172a;color:#fff;border:none;border-radius:8px">Login</button></form>
        <p style="font-size:11px;color:gray">Sheet Connected: {'Yes ✅' if (GOOGLE_SHEET_URL or SHEET_WEBHOOK) else 'No'} | Default pwd: CUK2026</p></body></html>
        """
    popular = Counter([l["question"].lower() for l in usage_data["logs"]]).most_common(5)
    logs_html = "".join([f"<tr><td>{l['time']}</td><td>{l['question']}</td><td>{l['ip']}</td></tr>" for l in usage_data["logs"]])
    return f"""
    <html><head><title>Admin</title><style>
    body{{font-family:Arial;max-width:1000px;margin:auto;background:#f6f7f9;padding:20px}}
  .card{{background:#fff;padding:20px;border-radius:12px;margin:15px 0;}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px}} th{{background:#0f172a;color:#fff}}
  .stat{{display:inline-block;background:#0f172a;color:#fff;padding:20px;border-radius:12px;margin:10px;width:180px;text-align:center}}
    </style></head><body>
    <h2>📊 DT4STEM Admin Dashboard</h2>
    <p>Total: {usage_data['total']} | Today: {usage_data['today']} | Google Sheet: {'Connected ✅' if (GOOGLE_SHEET_URL or SHEET_WEBHOOK) else 'Not Configured'}</p>
    <div class="stat"><h1>{usage_data['total']}</h1>Total</div>
    <div class="stat"><h1>{usage_data['today']}</h1>Today</div>
    <div class="card"><h3>🔥 Popular</h3><ul>{"".join([f"<li>{q} - {c}</li>" for q,c in popular])}</ul></div>
    <div class="card"><h3>📝 Recent Logs (Local + Sheet)</h3><table><tr><th>Time</th><th>Question</th><th>IP</th></tr>{logs_html}</table></div>
    <a href="/" style="background:#0f172a;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none">Go to App</a>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
