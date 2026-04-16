from flask import Flask, request, render_template_string
import os
import random
import re

app = Flask(__name__)

AKS_ADDRESS = "Unit 6, Macon Way Business Park, Macon Way, Crewe, CW1 6DG"
AKS_PHONE = "07842 524607"
AKS_AREAS = [
    "Crewe", "Cheshire", "Stoke-on-Trent", "Nantwich",
    "Winsford", "Middlewich", "Northwich", "Sandbach"
]

SERVICE_OPTIONS = [
    "Spare key cut & programmed",
    "Lost key replacement",
    "Remote key / fob supplied",
    "Diagnostics / coding",
    "Emergency lockout",
    "General promo",
]

VEHICLE_TYPE_OPTIONS = ["Car", "Van"]

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
      --panel:#0f1425;
      --panel2:#0a0e1a;
      --line:#28314f;
      --text:#f4f5f8;
      --muted:#b8c0d3;
      --red:#ef4444;
      --red2:#dc2626;
      --silver:#d7dae4;
      --pill:#121a31;
    }
    *{box-sizing:border-box}
    body{
      margin:0;padding:24px 14px 48px;
      background:linear-gradient(180deg,#2a0303 0%, #080b14 18%, #07090f 100%);
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    }
    .wrap{max-width:780px;margin:0 auto}
    .card{
      background:linear-gradient(180deg,#101626 0%, #090d18 100%);
      border:1px solid var(--line);
      border-radius:30px;
      padding:24px;
      box-shadow:0 10px 34px rgba(0,0,0,.38);
      margin-bottom:18px;
    }
    .hero{
      display:flex;align-items:center;gap:16px;
    }
    .logo{
      width:64px;height:64px;border-radius:18px;
      background:linear-gradient(180deg,#151515 0%, #000 100%);
      border:1px solid #39415d;
      display:flex;align-items:center;justify-content:center;
      font-weight:900;font-size:20px;letter-spacing:.5px;
      color:white;box-shadow:0 0 18px rgba(239,68,68,.18);
      flex:0 0 auto;
    }
    .logo .aks{color:var(--red)}
    .hero-title{font-size:28px;line-height:1.02;font-weight:900;margin:0 0 8px}
    .hero-sub{font-size:16px;line-height:1.52;color:var(--muted);margin:0}
    .brand{color:var(--red)}
    label{display:block;font-size:15px;margin:14px 0 8px;color:#e5e8f2}
    input[type="text"], textarea, select{
      width:100%;padding:16px 18px;border-radius:18px;
      border:1px solid #39415d;background:#0d1222;color:white;
      font-size:16px;outline:none;
    }
    textarea{min-height:100px;resize:vertical}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
    .btn{
      width:100%;border:none;border-radius:24px;padding:18px 20px;
      font-size:18px;font-weight:900;cursor:pointer;
      margin-top:18px;
      background:linear-gradient(180deg,#ff6868 0%, var(--red2) 100%);
      color:white;
      box-shadow:0 10px 24px rgba(220,38,38,.25);
    }
    .result{
      white-space:pre-wrap;line-height:1.72;font-size:18px;
      background:linear-gradient(180deg,#0f1425 0%, #090d18 100%);
      border-radius:26px;border:1px solid var(--line);padding:22px;
    }
    .copy-btn{
      display:inline-block;margin-top:16px;padding:15px 18px;border-radius:18px;
      background:#f3f4f8;color:#111;font-weight:900;border:none;cursor:pointer;
      width:100%;
    }
    .footer-tip{margin-top:12px;color:#b9bfd1;font-size:14px;text-align:center}
    @media (max-width: 640px){
      .grid{grid-template-columns:1fr}
      .hero-title{font-size:24px}
    }
  </style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <div class="hero">
      <div class="logo"><span class="aks">AKS</span></div>
      <div>
        <div class="hero-title"><span class="brand">AKS</span> Marketing<br>Post Builder</div>
        <p class="hero-sub">Manual vehicle entry only. Generate more engaging AKS-style Facebook posts with cleaner structure, better spacing, and local SEO hashtags.</p>
      </div>
    </div>
  </div>

  <div class="card">
    <form method="post">
      <label>Vehicle details</label>
      <input type="text" name="vehicle" value="{{ vehicle }}" placeholder="e.g. 2013 Vauxhall Vivaro">

      <div class="grid">
        <div>
          <label>Vehicle type</label>
          <select name="vehicle_type">
            {% for opt in vehicle_type_options %}
              <option value="{{ opt }}" {% if opt == vehicle_type %}selected{% endif %}>{{ opt }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>Location</label>
          <input type="text" name="location" value="{{ location }}" placeholder="e.g. Crewe">
        </div>
      </div>

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

      <button class="btn" type="submit">Generate Facebook Post</button>
    </form>
  </div>

  {% if post %}
  <div class="card">
    <h2 style="font-size:22px;margin:0 0 14px;">Facebook Post</h2>
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

TITLE_TEMPLATES = {
    "Car": [
        "🔑 {vehicle} sorted by AKS Auto Key Services in {location}",
        "🚗 Another {vehicle} completed in {location}",
        "✅ {vehicle} back on the road in {location}",
        "🔧 Fresh key work completed on this {vehicle} in {location}",
        "✨ {vehicle} job completed for a customer in {location}",
        "📍 Another AKS job wrapped up on this {vehicle} in {location}",
    ],
    "Van": [
        "🔑 {vehicle} van key work completed in {location}",
        "🚐 Another {vehicle} sorted by AKS Auto Key Services in {location}",
        "✅ {vehicle} van back in action in {location}",
        "🛠️ Key work completed on this {vehicle} van in {location}",
        "📍 Another van job wrapped up on this {vehicle} in {location}",
        "🚐 {vehicle} sorted and ready to go again in {location}",
    ],
}

INTRO_TEMPLATES = [
    "Another customer sorted by AKS Auto Key Services after we supplied and programmed the right key solution quickly and professionally.",
    "We recently completed another job for a customer and got everything sorted quickly, professionally and without the dealership hassle.",
    "Another smooth job completed by AKS Auto Key Services, getting everything supplied, programmed and tested properly.",
    "A customer came to us needing a reliable key solution and we got it sorted quickly, efficiently and ready to go.",
]

SERVICE_LINES = {
    "Spare key cut & programmed": [
        "✅ Spare key cutting & programming\n✅ Remote / transponder setup\n✅ Fully tested and working perfectly",
        "✅ Spare key supplied and programmed\n✅ Key functions checked and confirmed\n✅ Ready to use straight away",
    ],
    "Lost key replacement": [
        "✅ Lost key solution provided\n✅ Replacement key supplied and programmed\n✅ Everything checked before handover",
        "✅ New key supplied for a lost key situation\n✅ Programmed to the vehicle correctly\n✅ Final testing completed",
    ],
    "Remote key / fob supplied": [
        "✅ Remote key / fob supplied\n✅ Programmed to the vehicle\n✅ Button functions tested and working",
        "✅ Replacement remote supplied\n✅ Key and remote functions set up\n✅ Fully tested before completion",
    ],
    "Diagnostics / coding": [
        "✅ Diagnostic work carried out\n✅ Coding / programming completed\n✅ Final checks done and working properly",
        "✅ Fault finding and coding completed\n✅ Correct setup sorted\n✅ Everything checked before finish",
    ],
    "Emergency lockout": [
        "✅ Fast response assistance\n✅ Access regained quickly\n✅ Customer back moving without the wait",
        "✅ Lockout assistance completed\n✅ Entry gained and issue resolved\n✅ Quick turnaround from AKS",
    ],
    "General promo": [
        "✅ Key cutting & programming carried out\n✅ Remote / transponder setup\n✅ Fully tested and working perfectly",
        "✅ Vehicle key work completed\n✅ Key functions checked and confirmed\n✅ Everything ready to go",
    ],
}

WARNINGS = [
    "⚠️ Lose that only key and you could be looking at hundreds in recovery & replacement costs",
    "⚠️ Only got one key left? It can get expensive very quickly if that one goes missing",
    "⚠️ One working key might feel enough — until it disappears and the replacement costs stack up",
    "⚠️ Leaving it until you lose your last key can turn a simple job into a much more expensive one",
]

SERVICE_BLOCKS = [
    "✅ Spare keys cut & programmed\n\n✅ Lost keys replaced\n\n✅ Remote keys & fobs supplied\n\n✅ Fast turnaround – no waiting around",
    "🔑 Spare key cutting & programming\n\n🔑 Lost key solutions\n\n🔑 Remote keys & fobs supplied\n\n🔑 Fast turnaround without the waiting around",
    "✔️ Spare keys supplied & coded\n\n✔️ Lost keys replaced\n\n✔️ Remote keys & fobs available\n\n✔️ Quick turnaround and hassle-free service",
]

CLOSERS = [
    "Don’t leave it too late — get your spare key sorted today and stay one step ahead 🔐",
    "Stay one step ahead — getting a spare key sorted now can save a lot of hassle later 🔐",
    "Avoid the stress later on and get your spare key sorted before it becomes a bigger problem 🔐",
    "A spare key now can save a lot of time, hassle and money later — get it sorted before you need it 🔐",
]

def clean_vehicle(text: str) -> str:
    text = (text or "").strip()
    return re.sub(r"\s+", " ", text) if text else "Vehicle"

def vehicle_emoji(vehicle_type: str) -> str:
    return "🚐" if vehicle_type == "Van" else "🚗"

def title_tail(service_type: str) -> str:
    tails = {
        "Spare key cut & programmed": [
            "Spare Key Sorted",
            "Spare Key Completed",
            "Spare Key Cut & Programmed",
            "Spare Key Job Finished",
        ],
        "Lost key replacement": [
            "Lost Key Solution Completed",
            "Replacement Key Sorted",
            "Lost Key Job Completed",
            "New Key Sorted",
        ],
        "Remote key / fob supplied": [
            "Remote Key / Fob Sorted",
            "Remote Key Supplied",
            "Fob Programming Completed",
            "Remote Key Job Completed",
        ],
        "Diagnostics / coding": [
            "Diagnostics / Coding Completed",
            "Coding Work Completed",
            "Programming Job Sorted",
            "Diagnostic Work Finished",
        ],
        "Emergency lockout": [
            "Lockout Assistance Completed",
            "Vehicle Access Regained",
            "Emergency Callout Completed",
            "Lockout Job Sorted",
        ],
        "General promo": [
            "Vehicle Key Work Completed",
            "Key Service Completed",
            "Job Completed",
            "Vehicle Key Job Sorted",
        ],
    }
    return random.choice(tails.get(service_type, tails["General promo"]))

def generate_hashtags(vehicle: str, location: str, service_type: str, vehicle_type: str) -> str:
    clean_loc = "#" + re.sub(r"[^A-Za-z0-9]", "", location) if location else "#Crewe"
    vehicle_words = [w for w in re.split(r"[\s/,-]+", vehicle) if w]
    vehicle_tags = []
    for w in vehicle_words[:4]:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", w)
        if cleaned and len(cleaned) > 1:
            vehicle_tags.append("#" + cleaned)

    type_tags = ["#VanLocksmith", "#VanKeyReplacement"] if vehicle_type == "Van" else ["#AutoLocksmith", "#CarKeyReplacement"]

    service_map = {
        "Spare key cut & programmed": ["#SpareCarKey", "#KeyProgramming"],
        "Lost key replacement": ["#LostCarKeys", "#ReplacementKey"],
        "Remote key / fob supplied": ["#RemoteKey", "#KeyFob"],
        "Diagnostics / coding": ["#Diagnostics", "#Coding"],
        "Emergency lockout": ["#LockedOut", "#EmergencyLocksmith"],
        "General promo": ["#VehicleKeys", "#MobileLocksmith"],
    }

    tags = [
        "#AKSAutoKeyServices", "#Crewe", "#Cheshire", clean_loc,
        "#AKS", "#CarKeys", "#KeyCutting"
    ] + type_tags + service_map.get(service_type, []) + vehicle_tags

    seen = set()
    final_tags = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            final_tags.append(t)
    return " ".join(final_tags[:14])

def generate_post(vehicle: str, location: str, vehicle_type: str, service_type: str, offer: str, notes: str) -> str:
    vehicle = clean_vehicle(vehicle)
    location = (location or "Crewe").strip() or "Crewe"

    title = random.choice(TITLE_TEMPLATES[vehicle_type]).format(vehicle=vehicle, location=location)
    intro = random.choice(INTRO_TEMPLATES)
    services = random.choice(SERVICE_LINES.get(service_type, SERVICE_LINES["General promo"]))
    warning = random.choice(WARNINGS)
    bottom_services = random.choice(SERVICE_BLOCKS)
    closer = random.choice(CLOSERS)
    tags = generate_hashtags(vehicle, location, service_type, vehicle_type)
    vemoji = vehicle_emoji(vehicle_type)
    tail = title_tail(service_type)

    offer_line = f"\n\n🔥 {offer.strip()}" if offer and offer.strip() else ""
    notes_line = f"\n\n💬 {notes.strip()}" if notes and notes.strip() else ""
    areas = ", ".join(AKS_AREAS)

    return (
        f"{title}\n\n"
        f"{intro}\n\n"
        f"📍 {location}\n\n"
        f"We carried out:\n\n"
        f"{services}\n\n"
        f"{warning}\n\n"
        f"{bottom_services}\n\n"
        f"{closer}\n\n"
        f"📍 Visit us: {AKS_ADDRESS}\n\n"
        f"📞 Call / WhatsApp: {AKS_PHONE}\n\n"
        f"💬 Message us now for a quote or to book in!\n\n"
        f"📍 Areas covered: {areas}"
        f"{offer_line}"
        f"{notes_line}\n\n"
        f"{vemoji} {vehicle} — {tail}\n\n"
        f"{tags}"
    )

@app.route("/", methods=["GET", "POST"])
def index():
    vehicle = ""
    location = "Crewe"
    vehicle_type = "Car"
    service_type = "Spare key cut & programmed"
    offer = ""
    notes = ""
    post = ""

    if request.method == "POST":
        vehicle = request.form.get("vehicle", "").strip()
        location = request.form.get("location", "Crewe").strip() or "Crewe"
        vehicle_type = request.form.get("vehicle_type", "Car")
        service_type = request.form.get("service_type", "Spare key cut & programmed")
        offer = request.form.get("offer", "").strip()
        notes = request.form.get("notes", "").strip()
        post = generate_post(vehicle, location, vehicle_type, service_type, offer, notes)

    return render_template_string(
        HTML,
        vehicle=vehicle,
        location=location,
        vehicle_type=vehicle_type,
        service_type=service_type,
        offer=offer,
        notes=notes,
        post=post,
        service_options=SERVICE_OPTIONS,
        vehicle_type_options=VEHICLE_TYPE_OPTIONS,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
