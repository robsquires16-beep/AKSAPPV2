
import os
import base64
import random
import re
from typing import Dict, List

from flask import Flask, request, render_template_string, jsonify
from openai import OpenAI

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>AKS Marketing Post Builder</title>
  <style>
    body{margin:0;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#07070c;color:#f5f5f7}
    .wrap{max-width:860px;margin:0 auto;padding:18px}
    .card{background:linear-gradient(180deg,#121525,#0b0c14);border:1px solid rgba(255,255,255,.08);border-radius:24px;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,.35);margin-bottom:18px}
    h1,h2{margin:0 0 12px}
    h1{font-size:40px;line-height:1.05}
    h2{font-size:24px}
    p{line-height:1.45;color:#d7d7de}
    label{display:block;margin:14px 0 8px;font-weight:700}
    input,select,textarea,button{font:inherit}
    input,select,textarea{width:100%;box-sizing:border-box;padding:16px;border-radius:18px;border:1px solid rgba(255,255,255,.12);background:#0f1322;color:#fff}
    button{width:100%;padding:18px 20px;border:none;border-radius:22px;font-weight:800;cursor:pointer}
    .primary{background:linear-gradient(180deg,#ff5454,#e61f2f);color:#fff}
    .secondary{background:#151a2e;color:#fff;border:1px solid rgba(255,255,255,.12)}
    .pill{display:inline-block;padding:12px 18px;border-radius:999px;background:#141a30;border:1px solid rgba(255,255,255,.08);margin:6px 6px 0 0}
    .muted{color:#b7b7c4}
    .row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
    @media (max-width:720px){.row{grid-template-columns:1fr}}
    pre{white-space:pre-wrap;word-wrap:break-word;background:#0b0f1b;border-radius:20px;padding:18px;border:1px solid rgba(255,255,255,.08)}
    .logo{font-size:40px;font-weight:900;letter-spacing:.5px}
    .logo .red{color:#ff3131}
    .small{font-size:14px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="logo"><span>AKS</span> <span class="red">Marketing</span> Post Builder</div>
    <p>Upload a vehicle photo, detect the vehicle with AI, then generate a Facebook post in your AKS style.</p>
  </div>

  <form class="card" method="post" enctype="multipart/form-data" action="/generate">
    <div class="row">
      <div>
        <label>Upload photo</label>
        <input type="file" name="photo" accept="image/*" required>
      </div>
      <div>
        <label>Location</label>
        <input type="text" name="location" placeholder="Crewe" value="Crewe">
      </div>
    </div>

    <div class="row">
      <div>
        <label>Vehicle</label>
        <input type="text" name="vehicle_override" placeholder="Leave blank to use AI detection">
      </div>
      <div>
        <label>Service type</label>
        <select name="service_type">
          <option value="spare key">Spare key</option>
          <option value="lost key">Lost key</option>
          <option value="van key">Van key</option>
          <option value="diagnostics / coding">Diagnostics / coding</option>
          <option value="emergency lockout">Emergency lockout</option>
          <option value="general promo">General promo</option>
        </select>
      </div>
    </div>

    <div class="row">
      <div>
        <label>Offer / promo text</label>
        <input type="text" name="offer_text" placeholder="Same-day service available">
      </div>
      <div>
        <label>Phone</label>
        <input type="text" name="phone" value="07842 524607">
      </div>
    </div>

    <label>Areas covered</label>
    <input type="text" name="areas" value="Crewe, Cheshire, Stoke-on-Trent, Nantwich, Winsford, Middlewich, Northwich, Sandbach">

    <div style="margin-top:14px">
      <button class="primary" type="submit">Generate Facebook Post</button>
    </div>
  </form>

  {% if result %}
  <div class="card">
    <h2>Detection</h2>
    <div class="pill">🚗 Vehicle: {{ result.vehicle }}</div>
    <div class="pill">🧠 Confidence: {{ result.confidence }}</div>
    {% if result.clues %}<p class="small muted">Clues: {{ result.clues }}</p>{% endif %}
  </div>

  <div class="card">
    <h2>Facebook Post</h2>
    <pre id="postText">{{ result.post }}</pre>
    <button class="secondary" onclick="copyPost()" type="button">Copy post</button>
  </div>
  {% endif %}
</div>
<script>
function copyPost(){
  const t=document.getElementById('postText');
  navigator.clipboard.writeText(t.innerText);
  alert('Post copied');
}
</script>
</body>
</html>
"""

BRAND_HINTS = [
    "Vauxhall","Ford","Mercedes","Mercedes-Benz","BMW","Audi","Volkswagen","VW","Peugeot",
    "Citroen","Citroën","Renault","Nissan","Toyota","Kia","Hyundai","Land Rover","Skoda",
    "SEAT","Fiat","Honda","Mini","Dacia","Volvo","Mazda"
]

MODEL_HINTS = [
    "Adam","Corsa","Astra","Vivaro","Combo","Movano","Transit","Transit Custom","Ranger",
    "Focus","Fiesta","Sprinter","A Class","A-Class","Discovery Sport","Discovery","Berlingo",
    "Partner","Doblo","Polo","Golf","Transporter","Sportage","Relay","Boxer","Vito","A3","A4"
]

def get_client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    return OpenAI(api_key=key)

def image_to_data_url(file_storage) -> str:
    content = file_storage.read()
    file_storage.stream.seek(0)
    mime = file_storage.mimetype or "image/jpeg"
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime};base64,{encoded}"

def safe_openai_text(client: OpenAI, prompt: str, image_data_url: str) -> str:
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": image_data_url},
            ],
        }],
        temperature=0.1,
    )
    return (getattr(resp, "output_text", "") or "").strip()

def parse_detection_text(text: str) -> Dict[str, str]:
    # Try JSON-ish extraction first
    out = {"make": "", "model": "", "year": "", "body_type": "", "confidence": "low", "clues": ""}
    pairs = re.findall(r'"?(make|model|year|body_type|confidence|clues)"?\s*:\s*"?(.*?)"?(?:,|\n|$)', text, re.I)
    for k, v in pairs:
        out[k.lower()] = v.strip().strip('"')
    if not pairs:
        for field in out.keys():
            m = re.search(field + r"\s*[:\-]\s*(.+)", text, re.I)
            if m:
                out[field] = m.group(1).strip().strip('"')
    out["confidence"] = out["confidence"].lower() if out["confidence"] else "low"
    return out

def normalize_vehicle(make: str, model: str, year: str) -> str:
    parts = []
    if year and re.fullmatch(r"(19|20)\d{2}", year):
        parts.append(year)
    if make:
        make = make.replace("Mercedes-Benz", "Mercedes").replace("Citroën", "Citroen").strip()
        parts.append(make)
    if model and model.lower() not in {make.lower() if make else ""}:
        parts.append(model.strip())
    return " ".join([p for p in parts if p]).strip() or "Vehicle"

def heuristic_vehicle_from_text(text: str) -> str:
    text_l = text.lower()
    year = ""
    y = re.search(r"(19|20)\d{2}", text)
    if y:
        year = y.group(0)
    brand = next((b for b in BRAND_HINTS if b.lower() in text_l), "")
    model = next((m for m in MODEL_HINTS if m.lower() in text_l), "")
    return normalize_vehicle(brand, model, year)

def consensus_detect(image_data_url: str) -> Dict[str, str]:
    client = get_client()
    if not client:
        return {
            "vehicle": "Vehicle",
            "confidence": "low",
            "clues": "AI detection unavailable",
            "make": "", "model": "", "year": "", "body_type": ""
        }

    prompts = [
        """Identify the main vehicle in this image for an automotive locksmith job.
Return ONLY lines in this format:
make: ...
model: ...
year: ...
body_type: ...
confidence: high|medium|low
clues: short explanation
Be conservative. If unsure, leave model blank rather than guessing.""",
        """You are checking a customer job photo for a UK auto key business.
Identify the visible vehicle make, likely model, likely year range if visible, body type, and confidence.
Prefer make-only over a risky model guess.
Return:
make: ...
model: ...
year: ...
body_type: ...
confidence: high|medium|low
clues: ..."""
    ]

    parsed: List[Dict[str, str]] = []
    raw_texts = []
    for prompt in prompts:
        try:
            txt = safe_openai_text(client, prompt, image_data_url)
            raw_texts.append(txt)
            parsed.append(parse_detection_text(txt))
        except Exception:
            continue

    if not parsed:
        return {
            "vehicle": "Vehicle",
            "confidence": "low",
            "clues": "AI detection unavailable",
            "make": "", "model": "", "year": "", "body_type": ""
        }

    makes = [p.get("make", "") for p in parsed if p.get("make")]
    models = [p.get("model", "") for p in parsed if p.get("model")]
    years = [p.get("year", "") for p in parsed if p.get("year")]
    bodies = [p.get("body_type", "") for p in parsed if p.get("body_type")]
    confs = [p.get("confidence", "low") for p in parsed]

    make = makes[0] if makes else ""
    if len(set([m.lower() for m in makes])) > 1:
        # disagreement: drop to safest make present in first pass
        make = makes[0]

    model = models[0] if models else ""
    if len(set([m.lower() for m in models])) > 1:
        # disagreement on model: suppress model
        model = ""

    year = years[0] if years else ""
    body = bodies[0] if bodies else ""
    if "high" in confs and make and (model or year):
        confidence = "high"
    elif make:
        confidence = "medium" if model or year else "low"
    else:
        confidence = "low"

    vehicle = normalize_vehicle(make, model if confidence != "low" else "", year if confidence == "high" else "")
    clues = " | ".join([t[:120] for t in raw_texts if t])[:260]

    # Safer fallback if only low confidence
    if vehicle == "Vehicle":
        vehicle = heuristic_vehicle_from_text(clues)

    return {
        "vehicle": vehicle if vehicle else "Vehicle",
        "confidence": confidence,
        "clues": clues or "Conservative fallback used",
        "make": make, "model": model, "year": year, "body_type": body
    }

def clean_vehicle_for_tags(vehicle: str) -> List[str]:
    return [w for w in re.split(r"[^A-Za-z0-9]+", vehicle) if len(w) > 2]

def smart_hashtags(vehicle: str, location: str, service_type: str) -> str:
    base = [
        "#AutoKeyServices", "#CarKeyReplacement", "#SpareCarKey", "#AutoLocksmith",
        "#CarLocksmith", "#KeyProgramming", "#VehicleKeys", "#LostCarKeys", "#AKSAutoKeys"
    ]
    local = [f"#{location.replace(' ', '')}", "#Crewe", "#Cheshire", "#Nantwich", "#Sandbach"]
    service_map = {
        "spare key": ["#SpareKey", "#CarKeyCutting"],
        "lost key": ["#LostCarKey", "#ReplacementKey"],
        "van key": ["#VanKeys", "#CommercialVehicleKeys"],
        "diagnostics / coding": ["#VehicleDiagnostics", "#Coding"],
        "emergency lockout": ["#LockedOut", "#EmergencyLocksmith"],
        "general promo": ["#LocalBusiness", "#AutoKeys"],
    }
    tags = base + local + service_map.get(service_type, [])
    tags += [f"#{w}" for w in clean_vehicle_for_tags(vehicle)[:3]]
    unique = []
    for t in tags:
        if t not in unique:
            unique.append(t)
    return " ".join(unique[:12])

def varied_intro(vehicle: str, location: str, service_type: str) -> str:
    choices = [
        f"🔑 {vehicle} sorted in {location} by AKS Auto Key Services.",
        f"✅ Another {vehicle} job completed in {location}.",
        f"🚗 We recently carried out work on this {vehicle} in {location}.",
        f"🔧 Another customer sorted with a {vehicle} job in {location}.",
    ]
    if service_type == "lost key":
        choices += [
            f"🚨 Lost key situation sorted on this {vehicle} in {location}.",
            f"🔑 Customer back on the road after a lost key job on this {vehicle} in {location}.",
        ]
    return random.choice(choices)

def service_block(service_type: str, vehicle: str) -> str:
    mapping = {
        "spare key": "We carried out:\n✅ Spare key cutting & programming\n✅ Remote / transponder setup\n✅ Fully tested and working perfectly",
        "lost key": "We carried out:\n✅ Lost key replacement\n✅ New key supplied & programmed\n✅ Fully tested and ready to go",
        "van key": "We carried out:\n✅ Van key cutting & programming\n✅ Remote / transponder setup\n✅ Fully tested and working perfectly",
        "diagnostics / coding": "We carried out:\n✅ Diagnostic work / coding\n✅ System checks & setup\n✅ Fully tested and working correctly",
        "emergency lockout": "We carried out:\n✅ Rapid vehicle entry support\n✅ Key / lock assessment\n✅ Fast assistance to get things moving again",
        "general promo": "We carried out:\n✅ Vehicle key services\n✅ Remote / transponder support\n✅ Fast turnaround and testing",
    }
    return mapping.get(service_type, mapping["general promo"])

def cta_bottom(phone: str, areas: str, offer_text: str) -> str:
    warnings = [
        "⚠️ Lose that only key and you could be looking at hundreds in recovery & replacement costs",
        "⚠️ Only got one key? Losing it can turn into an expensive problem fast",
        "⚠️ One working key is a risk — a spare now can save a lot of hassle later",
    ]
    service_bits = [
        "✅ Spare keys cut & programmed\n✅ Lost keys replaced\n✅ Remote keys & fobs supplied\n✅ Fast turnaround – no waiting around",
        "✅ Spare keys supplied & coded\n✅ Lost key solutions available\n✅ Remote keys & fobs programmed\n✅ Quick turnaround with no dealership delays",
        "✅ Spare key cutting & programming\n✅ Replacement keys for lost keys\n✅ Remote fobs supplied & set up\n✅ Fast, efficient turnaround",
    ]
    closers = [
        "Don’t leave it too late — get your spare key sorted today and stay one step ahead 🔐",
        "Stay one step ahead — getting a spare key sorted now can save a lot of stress 🔐",
        "Best sorted before it becomes a bigger problem — get your spare key booked in today 🔐",
    ]
    offer_line = f"\n🔥 {offer_text}\n" if offer_text.strip() else "\n"
    return (
        f"{random.choice(warnings)}\n"
        f"{random.choice(service_bits)}\n"
        f"{random.choice(closers)}\n"
        f"{offer_line}"
        "📍 Visit us: Unit 6, Macon Way Business Park, Macon Way, Crewe, CW1 6DG\n"
        f"📞 Call / WhatsApp: {phone}\n"
        f"📍 Areas covered: {areas}\n"
        "💬 Message us now for a quote or to book in!"
    )

def build_post(vehicle: str, location: str, service_type: str, phone: str, areas: str, offer_text: str) -> str:
    title_options = [
        f"🔑 {vehicle} {service_type.title()} Job Completed 🔑",
        f"🚗 {vehicle} – {service_type.title()} Sorted ✅",
        f"🔧 {vehicle} in for {service_type.title()} in {location}",
    ]
    post = [
        random.choice(title_options),
        "",
        varied_intro(vehicle, location, service_type),
        "",
        f"📍 {location}",
        "",
        service_block(service_type, vehicle),
        "",
        cta_bottom(phone, areas, offer_text),
        "",
        smart_hashtags(vehicle, location, service_type),
    ]
    return "\n".join(post)

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML, result=None)

@app.route("/generate", methods=["POST"])
def generate():
    photo = request.files.get("photo")
    if not photo:
        return render_template_string(HTML, result={"vehicle":"Vehicle","confidence":"low","clues":"No photo uploaded","post":"Please upload a photo."})

    location = (request.form.get("location") or "Crewe").strip()
    service_type = (request.form.get("service_type") or "spare key").strip().lower()
    offer_text = (request.form.get("offer_text") or "").strip()
    phone = (request.form.get("phone") or "07842 524607").strip()
    areas = (request.form.get("areas") or "Crewe, Cheshire, Stoke-on-Trent, Nantwich, Winsford, Middlewich, Northwich, Sandbach").strip()
    manual_vehicle = (request.form.get("vehicle_override") or "").strip()

    image_data_url = image_to_data_url(photo)
    detection = consensus_detect(image_data_url)

    vehicle = manual_vehicle or detection.get("vehicle") or "Vehicle"
    post = build_post(vehicle, location, service_type, phone, areas, offer_text)

    result = {
        "vehicle": vehicle,
        "confidence": detection.get("confidence", "low"),
        "clues": detection.get("clues", "AI detection unavailable"),
        "post": post,
    }
    return render_template_string(HTML, result=result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
