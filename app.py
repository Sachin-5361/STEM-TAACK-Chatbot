# COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, CUK
import os, requests, random, urllib.parse
from flask import Flask, request, jsonify, render_template_string, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# --- YOUR PREVIOUS KEY - Same as before ---
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()

print(f"=== DT4STEM Guru AI Starting ===")
print(f"Groq Key Present: {bool(GROQ_KEY)}")

# --- STRICT DESIGN THINKING PROMPT ---
STRATEGY_PROMPT = """
You are SrujanaSTEM AI - Expert STEM Coach for Secondary Teachers in India.
You MUST follow Design Thinking 5 steps in EXACT order with HEADINGS. No step can be skipped.

STRUCTURE (MANDATORY - Use these exact headings):

### 1. EMPATHIZE:
- Who is learner? What is their misconception/confusion about [TOPIC]?
- 2-3 bullet points.

### 2. DEFINE:
- Write clear Problem Statement: "How might we help students understand [TOPIC] using [best tools]?"

### 3. IDEATE:
- You know 1000+ tools (NASA Eyes, Stellarium, BioDigital Human, ChemCollective, PhET, Desmos, Tinkercad, Merge Cube, Google Earth, etc.)
- CHOOSE BEST 3 tools specifically for THIS topic.
- MUST give in MARKDOWN TABLE format:
| Idea No | Teaching Idea | Tool Name | Why This Tool is Best for This Topic? |
|---|---|---|---|
| 1 |... |... |... |

### 4. PROTOTYPE:
- 40-min lesson plan
- MUST give in MARKDOWN TABLE format:
| Time | Activity | Tool Used | Teacher Action |
|---|---|---|---|
| 0-5 min |... |... |... |
| 5-15 min |... |... |... |

### 5. TEST:
- Assessment rubric
- MUST give in MARKDOWN TABLE format:
| Criteria | Excellent | Good | Needs Improvement |
|---|---|---|---|
|... |... |... |... |

IMAGE RULE:
- If topic is visual (heart, cell, atom, solar system, water cycle, etc.), include ONE clean diagram at top.
- Image must have NO TEXT inside. Labels will be in table below.
- After image, give Label Table: | No | Part | Function |

FORMATTING:
- Use bold headings, bullet points, and tables.
- Choose format based on topic but STEPS 1-5 are compulsory.
"""

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")

def ask_groq(question):
    if not GROQ_KEY:
        return "⚠️ **GROQ_API_KEY missing!** Add in Render > Environment > GROQ_API_KEY = gsk_... from https://console.groq.com/keys"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}

    # Working models - 2026
    models_to_try = ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "openai/gpt-oss-120b"]

    # --- CLEAN IMAGE - NO TEXT, NO GIBBERISH ---
    no_text_prompt = f"{question} anatomy clean scientific illustration, NO TEXT, NO LABELS, NO WORDS, NO LETTERS, white background, ultra detailed, textbook style, 4k"
    encoded = urllib.parse.quote(no_text_prompt)
    clean_image_url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1024&height=1024&enhance=true&nologo=true&seed={random.randint(1,99999)}"

    for model_name in models_to_try:
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": f"""{STRATEGY_PROMPT}

IMAGE MARKDOWN TO USE (if visual topic):
![{question} Clean Diagram - No Labels]({clean_image_url})

After image, give labels in table if needed. Then start with ### 1. EMPATHIZE:

MANDATORY: Follow 5 Design Thinking steps in order. Each step must have table where specified.
"""},
                    {"role": "user", "content": f"Teacher Question: {question}. Give answer with STRICT Design Thinking 5 steps (1. EMPATHIZE, 2. DEFINE, 3. IDEATE with table, 4. PROTOTYPE with table, 5. TEST with table). Include clean diagram if visual."}
                ],
                "temperature": 0.8,
                "max_tokens": 2500
            }
            r = requests.post(url, headers=headers, json=payload, timeout=35)
            if r.status_code == 200:
                print(f"Success with {model_name}")
                return r.json()["choices"][0]["message"]["content"]
            else:
                print(f"Model {model_name} failed {r.status_code}")
        except Exception as e:
            print(f"Exception {e}")
            continue

    return "❌ Groq Error: Please check GROQ_API_KEY. Generate new from https://console.groq.com/keys"

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
#ans img{max-width:100%;border-radius:14px;margin:16px 0;box-shadow:0 4px 12px rgba(0,0,0,0.15);border:1px solid #e2e8f0;display:block}
#ans h3{color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:22px}
footer{background:#0f172a;color:#94a3b8;text-align:center;padding:16px;font-size:11px;border-radius:16px 16px 0 0;margin-top:20px}
</style></head>
<body>
<header>
<h2 style="margin:0">DT4STEM Guru AI 🤖</h2>
<p style="margin:8px 0 4px 0">Design Thinking • Paragraph • Table • Clean HD Diagram</p>
<small>© S Sachinkumar & Prof.G.R.Angadi, CUK</small>
</header>
<div id=box>
<input id='q' placeholder='Example: human heart, photosynthesis, newtons laws, mitosis vs meiosis...'>
<button onclick='ask()'>🚀 Ask AI Coach</button>
<div id='ans'>
<b>How it works:</b><br>
• Answers follow <b>5 Design Thinking Steps</b>: EMPATHIZE → DEFINE → IDEATE (table) → PROTOTYPE (table) → TEST (table)<br>
• Visual topics: HD clean diagram (no blurry text) + label table<br>
• One GROQ_API_KEY works for all questions - no need to change
</div>
</div>
<footer>COPYRIGHT © 2026 S Sachinkumar & Prof.G.R.Angadi, Dept. of Education, Central University of Karnataka<br>Powered by Groq AI + Pollinations HD (No text in image)</footer>
<script>
async function ask(){
 let q=document.getElementById('q').value.trim();
 if(!q){alert('Please type a question');return}
 document.getElementById('ans').innerHTML='⏳ Generating Design Thinking lesson for: <b>'+q+'</b><br><br>Following 5 steps: Empathize, Define, Ideate, Prototype, Test... Please wait 6 sec...';
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
    answer = ask_groq(q)
    return jsonify({"answer": answer})

@app.route("/health")
def health():
    return f"OK - Groq Ready: {bool(GROQ_KEY)} - Design Thinking Mode ON"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
