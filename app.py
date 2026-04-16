import base64
import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file, url_for
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


STATIC_DIR = Path(app.static_folder)
LOGO_FILE = STATIC_DIR / "aks-logo.jpeg"


def image_to_data_url(file_storage):
    content = file_storage.read()
    mime = file_storage.mimetype or 'image/jpeg'
    b64 = base64.b64encode(content).decode('utf-8')
    return f"data:{mime};base64,{b64}"


def safe_slug(text: str) -> str:
    return ''.join(ch for ch in (text or '').title() if ch.isalnum())


def build_keywords(area, city):
    geo = city or area or "near me"
    return [
        f"auto key replacement {geo}",
        f"car key replacement {geo}",
        f"mobile auto locksmith {geo}",
        f"key fob programming {geo}",
        f"lost car key service {geo}",
        f"spare car keys {geo}",
        f"transponder key cutting {geo}",
        f"ignition key repair {geo}",
        f"emergency auto locksmith {geo}",
        f"same day car key service {geo}",
    ]


def fallback_copy(service_area, business_name, phone, tone, post_style, seo_city, booking_link, offer_text, note=None):
    area = service_area or "your area"
    city = seo_city or service_area or "your area"
    biz = business_name or "AKS Auto Key Services"
    phone_line = f" Call {phone}." if phone else ""
    book_line = f" Book now: {booking_link}" if booking_link else ""
    offer_line = f" Offer: {offer_text}." if offer_text else ""

    openers = {
        "friendly": "Need a spare car key or quick help getting back on the road?",
        "urgent": "Locked out or lost your car key and need fast mobile help?",
        "professional": "Reliable mobile auto key support when you need it most.",
    }
    styles = {
        "promo": "We provide fast mobile car key replacement, key fob programming, transponder key cutting, spare car keys, and lost car key solutions",
        "educational": "If your remote stops working, your transponder fails, or you've lost your only key, we can diagnose and replace the right solution on site",
        "emergency": "For lockouts, lost keys, damaged remotes, and urgent roadside situations, our mobile service comes to you",
        "trust": "Drivers trust us for responsive mobile service, clear communication, and practical solutions for replacement keys and fob programming",
    }
    opener = openers.get(tone, openers["friendly"])
    body = styles.get(post_style, styles["promo"])

    post = (
        f"{opener} {biz} offers mobile auto locksmith support across {area}. {body} in {city}. "
        f"""We help with car key replacement, spare keys, ignition key issues, and same-day callouts when possible.{offer_line}{phone_line}"""

"
        f"Message us now for a quote or fast assistance.{book_line}"
    )

    hashtags = [
        "#AKSAutoKeyServices", "#AutoKeyServices", "#CarKeyReplacement", "#KeyFobProgramming",
        "#MobileAutoLocksmith", "#LostCarKey", "#SpareCarKey", "#EmergencyLocksmith",
        f"#{safe_slug(city)}" if city else "#MobileLocksmith", "#AutoLocksmith"
    ]

    cta = f"Call {phone} now for mobile auto key help." if phone else "Message now for a fast quote."
    if booking_link:
        cta += f" Book online: {booking_link}"

    return {
        "facebook_post": post,
        "seo_keywords": build_keywords(area, city),
        "hashtags": hashtags,
        "alt_text": "Promotional image for AKS Auto Key Services mobile car key replacement and key fob programming.",
        "cta": cta,
        "share_text": f"{post}

{cta}",
        "note": note or "Generated in fallback mode because no OpenAI API connection was available.",
    }


def generate_copy(image_data_url, service_area, business_name, phone, tone, post_style, seo_city, booking_link, offer_text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return fallback_copy(service_area, business_name, phone, tone, post_style, seo_city, booking_link, offer_text)

    prompt = f"""
You are writing Facebook marketing copy for a mobile auto locksmith / auto key business.
Use the uploaded photo as context.

Business name: {business_name or 'AKS Auto Key Services'}
Primary service area: {service_area or 'Not provided'}
Local SEO target city: {seo_city or 'Not provided'}
Phone: {phone or 'Not provided'}
Booking link: {booking_link or 'Not provided'}
Tone: {tone}
Post style: {post_style}
Offer or promotion: {offer_text or 'Not provided'}

Return valid JSON only with these keys:
facebook_post: 90-140 words, persuasive and natural for Facebook.
seo_keywords: array of exactly 10 local SEO keyword phrases.
hashtags: array of exactly 10 relevant hashtags.
alt_text: one short descriptive alt text for the image.
cta: one concise call-to-action line.
share_text: one combined share-ready text block including the post and CTA.

Rules:
- Focus on mobile auto locksmith services, car key replacement, spare keys, key fob programming, transponder keys, ignition key help, lockout help, and lost car keys.
- If a local SEO target city is provided, include strong local intent naturally without keyword stuffing.
- Mention the phone only if provided.
- Mention the booking link only if provided.
- Use the selected tone and post style.
- Do not promise rankings or make exaggerated guarantees.
- Avoid spammy repetition.
""".strip()

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
            temperature=0.8,
        )
        text = response.choices[0].message.content or "{}"
        return json.loads(text)
    except Exception as exc:
        return fallback_copy(
            service_area,
            business_name,
            phone,
            tone,
            post_style,
            seo_city,
            booking_link,
            offer_text,
            note=f"OpenAI fallback mode was used because the live AI request failed: {str(exc)[:160]}",
        )


@app.route('/')
def home():
    return render_template('index.html', logo_src=url_for('brand_logo'))


@app.route('/brand-logo')
def brand_logo():
    if LOGO_FILE.exists():
        return send_file(LOGO_FILE, mimetype='image/jpeg', max_age=3600)
    return ('', 404)


@app.route('/generate', methods=['POST'])
def generate():
    image = request.files.get('image')
    if not image:
        return jsonify({"error": "Please upload a photo."}), 400

    service_area = request.form.get('service_area', '').strip()
    business_name = request.form.get('business_name', '').strip()
    phone = request.form.get('phone', '').strip()
    tone = request.form.get('tone', 'friendly').strip()
    post_style = request.form.get('post_style', 'promo').strip()
    seo_city = request.form.get('seo_city', '').strip()
    booking_link = request.form.get('booking_link', '').strip()
    offer_text = request.form.get('offer_text', '').strip()

    image_data_url = image_to_data_url(image)
    result = generate_copy(
        image_data_url=image_data_url,
        service_area=service_area,
        business_name=business_name,
        phone=phone,
        tone=tone,
        post_style=post_style,
        seo_city=seo_city,
        booking_link=booking_link,
        offer_text=offer_text,
    )
    return jsonify(result)


@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')


@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
