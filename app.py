import base64
import json
import os
import random
import re
from typing import Optional

from flask import Flask, request, render_template_string
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

AKS_ADDRESS = "Unit 6, Macon Way Business Park, Macon Way, Crewe, CW1 6DG"
AKS_PHONE = "07842 524607"
AKS_AREAS = [
    "Crewe", "Cheshire", "Stoke-on-Trent", "Nantwich",
    "Winsford", "Middlewich", "Northwich", "Sandbach"
]

HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>AKS Marketing Post Builder</title>
  <style>
    :root{
      --bg:#07090f;
      --panel:#0e1220;
      --panel-2:#12182a;
      --line:#2a3150;
      --text:#f3f4f8;
      --muted:#b9bfd1;
      --red:#ef4444;
      --red2:#dc2626;
      --green:#22c55e;
      --pill:#151b31;
    }
    *{box-sizing:border-box}
    body{
      margin:0;padding:24px 14px 40px;
      background:linear-gradient(180deg,#210303 0%, #07090f 18%, #07090f 100%);
      color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    }
    .wrap{max-width:760px;margin:0 auto}
    .card{
      background:linear-gradient(180deg,#101522 0%, #080b14 100%);
      border:1px solid var(--line);
      border-radius:28px;
      padding:22px;
      box-shadow:0 10px 30px rgba(0,0,0,.35);
      margin-bottom:18px;
    }
    h1,h2,h3,p{margin:0}
    .hero-title{font-size:28px;line-height:1.05;font-weight:800;margin-bottom:8px}
    .hero-sub{font-size:16px;line-height:1.5;color:var(--muted)}
    .brand{color:var(--red)}
    label{display:block;font-size:15px;margin:14px 0 8px;color:#dfe3ee}
    input[type="text"], textarea, select{
      width:100%;padding:16px 18px;border-radius:18px;
      border:1px solid #39415d;background:#0d1222;color:white;
      font-size:16px;outline:none;
    }
    textarea{min-height:96px;resize:vertical}
    input[type="file"]{
      width:100%;padding:16px 12px;border-radius:18px;
      border:1px solid #39415d;background:#0d1222;color:white;
      font-size:16px;
    }
    .btn{
      width:100%;border:none;border-radius:24px;padding:18px 20px;
      font-size:18px;font-weight:800;cursor:pointer;
      margin-top:16px;
    }
    .btn-primary{
      background:linear-gradient(180deg,#ff6464 0%, var(--red2) 100%);
      color:white;
      box-shadow:0 10px 24px rgba(220,38,38,.25);
    }
    .btn-secondary{
      background:#10162b;color:white;border:1px solid #36405e;
    }
    .pill{
      display:inline-block;padding:14px 18px;border-radius:999px;
      border:1px solid #5b4a38;background:#14172a;
      font-size:16px;margin:8px 8px 0 0;
    }
    .muted{color:var(--muted)}
    .result{
      white-space:pre-wrap;line-height:1.52;font-size:18px;
      background:linear-gradient(180deg,#0f1425 0%, #080b14 100%);
      border-radius:24px;border:1px solid var(--line);padding:20px;
    }
    .small{font-size:14px}
    .row{display:grid;grid-template-columns:1fr;gap:14px}
    .meta{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
    .meta .pill{margin:0;border-color:#34405e;background:#10162b}
    .ok{color:#9ee6b2}
    .warn{color:#ffd18e}
    .copy-btn{
      display:inline-block;margin-top:16px;padding:14px 18px;border-radius:18px;
      background:#f0f1f5;color:#111;font-weight:800;border:none;cursor:pointer;
    }
    .footer-tip{margin-top:14px;color:#b9bfd1;font-size:14px;text-align:center}
  </style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <div class="hero-title"><span class="brand">AKS</span> Marketing Post Builder</div>
    <div class="hero-sub">Upload a photo, optionally detect the vehicle with AI, then generate a Facebook post in your AKS style with local SEO hashtags.</div>
  </div>

  <div class="card">
    <form method="post" enctype="multipart/form-data">
      <label>Upload photo</label>
      <input type="file" name="photo" accept="image/*">

      <label>Vehicle (manual override)</label>
      <input type="text" name="vehicle" value="{{ vehicle }}" placeholder="e.g. 2013 Vauxhall Adam">

      <label>Location</label>
      <input type="text" name="location" value="{{ location }}" placeholder="e.g. Crewe">

      <label>Service type</label>
      <select name="service_type">
        {% for opt in service_options %}
          <option value="{{ opt }}" {% if opt == service_type %}selected{% endif %}>{{ opt }}</option>
        {% endfor %}
      </select>

      <label>Offer or promo text (optional)</label>
      <input type="text" name="offer" value="{{ offer }}" placeholder="e.g. Same-day service available">

      <label>Extra job notes (optional)</label>
      <textarea name="notes" placeholder="Any useful details you want worked into the post...">{{ notes }}</textarea>

      <button class="btn btn-secondary" name="action" value="detect">Detect vehicle from photo</button>
      <button class="btn btn-primary" name="action" value="generate">Generate Facebook Post</button>
    </form>

    {% if detection %}
      <div class="meta" style="margin-top:18px;">
        <span class="pill">🧠 Confidence: {{ detection.confidence }}</span>
        {% if detection.vehicle %}
          <span class="pill">🚗 Vehicle: {{ detection.vehicle }}</span>
        {% endif %}
        {% if detection.service_hint %}
          <span class="pill">🔧 Service hint: {{ detection.service_hint }}</span>
        {% endif %}
      </div>
      {% if detection.clues %}
        <div class="result small" style="margin-top:12px;">👀 Clues: {{ detection.clues }}</div>
      {% endif %}
    {% endif %}

    {% if status_message %}
      <div class="result small" style="margin-top:12px;">{{ status_message }}</div>
    {% endif %}
  </div>

  {% if post %}
  <div class="card">
    <h2 style="font-size:22px;margin-bottom:14px;">Facebook Post</h2>
    <div id="postText" class="result">{{ post }}</div>
    <button class="copy-btn" onclick="copyPost()">Copy post</button>
    <div class="footer-tip">Open in Safari, then tap Share → Add to Home Screen.</div>
  </div>
  {% endif %}
</div>

<script>
function copyPost() {
  const text = document.getElementById("postText").innerText;
  navigator.clipboard.writeText(text).then(() => {
    alert("Post copied");
  }).catch(() => {
    alert("Could not copy automatically.");
  });
}
</script>
</body>
</html>
"""

SERVICE_OPTIONS = [
    "Auto detect / general",
    "Spare key cut & programmed",
    "Lost key replacement",
    "Remote key / fob supplied",
    "Diagnostics / coding",
    "Emergency lockout",
    "Van key service",
]

INTRO_TEMPLATES = [
    "🔑 {vehicle} sorted by AKS Auto Key Services in {location} 🔑",
    "🚗 Another {vehicle} completed in {location} by AKS Auto Key Services",
    "✅ Job done on this {vehicle} in {location}",
    "🔧 Another customer sorted with this {vehicle} in {location}",
]

MIDDLE_TEMPLATES = [
    "Another happy customer sorted by AKS Auto Key Services after we supplied and programmed a key solution for this {vehicle} in {location}. 👌",
    "This {vehicle} came in to us in {location} and we got everything sorted quickly, professionally and without the dealership hassle.",
    "We recently carried out work on this {vehicle} in {location}, getting the customer back on the road with everything fully tested and working properly.",
]

BOTTOM_WARNINGS = [
    "⚠️ Lose that only key and you could be looking at hundreds in recovery & replacement costs",
    "⚠️ Only got one key left? It can get expensive very quickly if that one goes missing",
    "⚠️ One working key might seem enough — until you lose it and the costs start stacking up",
]

BOTTOM_SERVICES = [
    "✅ Spare keys cut & programmed\n✅ Lost keys replaced\n✅ Remote keys & fobs supplied\n✅ Fast turnaround – no waiting around",
    "🔑 Spare key cutting & programming\n🔑 Lost key solutions\n🔑 Remote keys & fobs supplied\n🔑 Fast turnaround without the waiting around",
    "✔️ Spare keys supplied & coded\n✔️ Lost keys replaced\n✔️ Remote keys & fobs available\n✔️ Quick turnaround and hassle-free service",
]

BOTTOM_CLOSERS = [
    "Don’t leave it too late — get your spare key sorted today and stay one step ahead 🔐",
    "Stay one step ahead — getting a spare key sorted now can save a lot of hassle later 🔐",
    "Avoid the stress and get your spare key sorted before it becomes a bigger problem 🔐",
]

def to_data_url(file_storage) -> Optional[str]:
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None
    raw = file_storage.read()
    file_storage.stream.seek(0)
    if not raw:
        return None
    mime = file_storage.mimetype or "image/jpeg"
    b64 = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def simple_text_vehicle_guess(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "Vehicle"
    brands = [
        "Vauxhall", "Ford", "BMW", "Audi", "Mercedes", "Volkswagen", "VW",
        "Peugeot", "Citroen", "Renault", "Nissan", "Toyota", "Kia",
        "Hyundai", "Land Rover", "Mini", "Skoda", "Seat", "Fiat"
    ]
    models = [
        "Adam", "Corsa", "Astra", "Focus", "Fiesta", "Golf", "Polo",
        "Vivaro", "Berlingo", "Partner", "Doblo", "Sprinter", "Sportage",
        "Ranger", "Discovery", "A Class", "A-Class", "Transit", "Transporter"
    ]

    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    year = year_match.group(1) if year_match else ""

    brand = next((b for b in brands if b.lower() in text.lower()), "")
    model = next((m for m in models if m.lower() in text.lower()), "")

    parts = [p for p in [year, brand, model] if p]
    return " ".join(parts) if parts else text

def detect_vehicle_ai(photo) -> dict:
    fallback = {
        "vehicle": "",
        "confidence": "low",
        "clues": "AI detection unavailable",
        "service_hint": "",
    }

    if not client:
        return fallback

    data_url = to_data_url(photo)
    if not data_url:
        return fallback

    prompt = (
        "Look at this vehicle-related image and identify the vehicle as safely as possible. "
        "Return strict JSON only with keys: "
        'vehicle, make, model, year, confidence, clues, service_hint. '
        "Use confidence values high, medium, or low. "
        "If uncertain, prefer a broader answer like make-only instead of guessing a specific model. "
        "service_hint should be one of: spare key, lost key, diagnostics, coding, van key, lockout, unknown. "
        "clues should be a short plain-English sentence."
    )

    try:
        response = client.responses.create(
            model="gpt-5.4",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }],
        )
        text = (response.output_text or "").strip()
        data = json.loads(text)

        vehicle = (data.get("vehicle") or "").strip()
        make = (data.get("make") or "").strip()
        model = (data.get("model") or "").strip()
        year = str(data.get("year") or "").strip()
        confidence = (data.get("confidence") or "low").strip().lower()
        clues = (data.get("clues") or "AI detection complete.").strip()
        service_hint = (data.get("service_hint") or "unknown").strip().lower()

        if confidence not in {"high", "medium", "low"}:
            confidence = "low"

        # Safer fallback assembly
        if not vehicle:
            parts = [p for p in [year, make, model] if p]
            vehicle = " ".join(parts).strip()

        if confidence == "low" and make:
            vehicle = f"{year + ' ' if year else ''}{make}".strip()

        if not vehicle:
            vehicle = ""

        return {
            "vehicle": vehicle,
            "confidence": confidence,
            "clues": clues,
            "service_hint": service_hint,
        }
    except Exception:
        return fallback

def generate_hashtags(vehicle: str, location: str, service_type: str) -> str:
    clean_loc = "#" + re.sub(r"[^A-Za-z0-9]", "", location) if location else "#Crewe"
    vehicle_words = [w for w in re.split(r"[\s/,-]+", vehicle) if w]
    vehicle_tags = []
    for w in vehicle_words[:3]:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", w)
        if cleaned and len(cleaned) > 1:
            vehicle_tags.append("#" + cleaned)

    service_map = {
        "Spare key cut & programmed": ["#SpareCarKey", "#KeyProgramming"],
        "Lost key replacement": ["#LostCarKeys", "#CarKeyReplacement"],
        "Remote key / fob supplied": ["#RemoteKey", "#KeyFob"],
        "Diagnostics / coding": ["#Diagnostics", "#Coding"],
        "Emergency lockout": ["#LockedOut", "#EmergencyLocksmith"],
        "Van key service": ["#VanKey", "#VanLocksmith"],
        "Auto detect / general": ["#AutoLocksmith", "#VehicleKeys"],
    }

    tags = [
        "#AKSAutoKeyServices", "#AutoLocksmith", "#CarKeyReplacement",
        "#KeyProgramming", "#SpareCarKey", "#VehicleKeys",
        "#Crewe", "#Cheshire", clean_loc
    ]
    tags.extend(service_map.get(service_type, service_map["Auto detect / general"]))
    tags.extend(vehicle_tags)

    # de-dupe while preserving order
    seen = set()
    final_tags = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            final_tags.append(t)
    return " ".join(final_tags[:14])

def varied_service_lines(service_type: str) -> str:
    options = {
        "Spare key cut & programmed": [
            "✅ Spare key cutting & programming\n✅ Remote / transponder setup\n✅ Fully tested and working perfectly",
            "✅ Spare key supplied and programmed\n✅ Key functions checked\n✅ Ready to use straight away",
        ],
        "Lost key replacement": [
            "✅ Lost key solution provided\n✅ Replacement key supplied & programmed\n✅ Everything tested before handover",
            "✅ New key supplied for a lost key situation\n✅ Programmed and matched to the vehicle\n✅ Checked and working correctly",
        ],
        "Remote key / fob supplied": [
            "✅ Remote key / fob supplied\n✅ Programmed to the vehicle\n✅ Fully tested and working properly",
            "✅ Replacement remote supplied\n✅ Key and button functions programmed\n✅ Everything checked before completion",
        ],
        "Diagnostics / coding": [
            "✅ Diagnostic work carried out\n✅ Coding / programming completed\n✅ Vehicle checked and working correctly",
            "✅ Fault finding and coding completed\n✅ Module / key setup sorted\n✅ Final checks carried out",
        ],
        "Emergency lockout": [
            "✅ Fast response lockout assistance\n✅ Vehicle access regained\n✅ Customer back on the road quickly",
            "✅ Lockout assistance completed\n✅ Entry gained without the dealership hassle\n✅ Quick turnaround",
        ],
        "Van key service": [
            "✅ Van key supplied / programmed\n✅ Remote / transponder setup\n✅ Fully tested and ready to go",
            "✅ Spare / replacement van key sorted\n✅ Key functions checked\n✅ Quick turnaround",
        ],
        "Auto detect / general": [
            "✅ Key cutting & programming carried out\n✅ Remote / transponder setup\n✅ Fully tested and working perfectly",
            "✅ Vehicle key work completed\n✅ Key functions checked\n✅ Everything tested before completion",
        ],
    }
    return random.choice(options.get(service_type, options["Auto detect / general"]))

def generate_post(vehicle: str, location: str, service_type: str, offer: str, notes: str) -> str:
    vehicle = vehicle.strip() if vehicle else "Vehicle"
    location = location.strip() if location else "Crewe"

    intro = random.choice(INTRO_TEMPLATES).format(vehicle=vehicle, location=location)
    middle = random.choice(MIDDLE_TEMPLATES).format(vehicle=vehicle, location=location)
    services = varied_service_lines(service_type)
    warning = random.choice(BOTTOM_WARNINGS)
    bottom_services = random.choice(BOTTOM_SERVICES)
    closer = random.choice(BOTTOM_CLOSERS)
    hashtags = generate_hashtags(vehicle, location, service_type)

    offer_line = f"\n🔥 {offer.strip()}" if offer and offer.strip() else ""
    notes_line = ""
    if notes and notes.strip():
        trimmed = notes.strip()
        notes_line = f"\n\n💬 Extra detail: {trimmed}"

    areas = ", ".join(AKS_AREAS)

    title_tail = {
        "Spare key cut & programmed": "Spare Key Job Completed",
        "Lost key replacement": "Lost Key Solution Completed",
        "Remote key / fob supplied": "Remote Key / Fob Supplied",
        "Diagnostics / coding": "Diagnostics / Coding Completed",
        "Emergency lockout": "Lockout Assistance Completed",
        "Van key service": "Van Key Job Completed",
        "Auto detect / general": "Vehicle Key Job Completed",
    }.get(service_type, "Vehicle Key Job Completed")

    post = (
        f"{intro}\n\n"
        f"{middle}\n\n"
        f"📍 {location}\n\n"
        f"We carried out:\n"
        f"{services}\n\n"
        f"🚗 {vehicle}\n"
        f"🔧 {title_tail}\n\n"
        f"{warning}\n"
        f"{bottom_services}\n"
        f"{closer}\n"
        f"📍 Visit us: {AKS_ADDRESS}\n"
        f"📞 Call / WhatsApp: {AKS_PHONE}\n"
        f"💬 Message us now for a quote or to book in!\n"
        f"📍 Areas covered: {areas}"
        f"{offer_line}"
        f"{notes_line}\n\n"
        f"{hashtags}"
    )
    return post

@app.route("/", methods=["GET", "POST"])
def index():
    vehicle = ""
    location = "Crewe"
    service_type = "Auto detect / general"
    offer = ""
    notes = ""
    post = ""
    detection = None
    status_message = ""

    if request.method == "POST":
        action = request.form.get("action", "generate")
        manual_vehicle = (request.form.get("vehicle") or "").strip()
        location = (request.form.get("location") or "Crewe").strip()
        service_type = request.form.get("service_type") or "Auto detect / general"
        offer = (request.form.get("offer") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        photo = request.files.get("photo")

        detection = detect_vehicle_ai(photo) if photo and getattr(photo, "filename", "") else None

        # Decide vehicle
        if manual_vehicle:
            vehicle = manual_vehicle
        elif detection and detection.get("vehicle"):
            vehicle = detection["vehicle"]
        else:
            vehicle = simple_text_vehicle_guess(notes)

        if action == "detect":
            status_message = "Vehicle detection updated. You can still edit the vehicle field manually before generating the post."
            if detection and detection.get("service_hint") and service_type == "Auto detect / general":
                hint = detection["service_hint"]
                mapping = {
                    "spare key": "Spare key cut & programmed",
                    "lost key": "Lost key replacement",
                    "diagnostics": "Diagnostics / coding",
                    "coding": "Diagnostics / coding",
                    "van key": "Van key service",
                    "lockout": "Emergency lockout",
                }
                service_type = mapping.get(hint, service_type)
        else:
            post = generate_post(vehicle=vehicle, location=location, service_type=service_type, offer=offer, notes=notes)

    return render_template_string(
        HTML,
        vehicle=vehicle,
        location=location,
        service_type=service_type,
        offer=offer,
        notes=notes,
        post=post,
        detection=detection,
        status_message=status_message,
        service_options=SERVICE_OPTIONS,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
