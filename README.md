# AKS Marketing Post Builder for iPhone

This is the upgraded AKS-branded iPhone web app.

## New features
- AKS logo and black/red/silver branding
- Local SEO target city field
- **Use my location** button for iPhone browsers
- Click-to-call button
- Booking link button
- Multiple post styles: promo, educational, emergency, trust
- Assisted Facebook sharing flow: copy + open Facebook

## Important note about Facebook posting
A simple web app can help you copy and share quickly, but it does **not** directly auto-post to Facebook accounts by itself. This version gives you the fastest compliant flow on iPhone.

## Deploy on Render
1. Create a GitHub repo and upload these files.
2. Create a new Render Web Service.
3. Connect the repo.
4. Render will detect `render.yaml`.
5. Add an environment variable named `OPENAI_API_KEY`.
6. Deploy.
7. Open the live URL on your iPhone in Safari.
8. Tap **Share > Add to Home Screen**.

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
python app.py
```

## Optional browser services used
- Browser geolocation on iPhone for the **Use my location** feature
- OpenStreetMap Nominatim reverse geocoding from the browser to detect city/area

## Notes
- Without `OPENAI_API_KEY`, the app still works in fallback mode.
- This app improves local relevance and marketing speed, but it does not guarantee search rankings.
