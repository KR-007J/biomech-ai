# ⚡ BioMech AI — Real-Time Biomechanical Trainer

**Client-side** AI fitness coach powered by **MediaPipe Pose** + **Gemini 2.5 Flash**. 
Works in any browser. Deployable on Render, GitHub Pages, Netlify — **no server-side webcam processing needed**.

---

## 🌟 Features

| Feature | Details |
|---------|---------|
| 🦴 **Skeleton Tracking** | MediaPipe Pose — 33 body landmarks at 30fps |
| 📐 **Cosine Rule Engine** | Real-time joint angle calculation via Law of Cosines |
| 🎯 **7 Exercises** | Squat, Push-Up, Lunge, Plank, Bicep Curl, Shoulder Press, Deadlift |
| 🔢 **Rep Counter** | Auto-counting with state detection (up/down) |
| 📊 **Form Score** | Weighted multi-checkpoint scoring with letter grade |
| 🎨 **4 Skeleton Styles** | Neon Teal, Fire Orange, Matrix Green, Holographic Purple |
| 🤖 **Gemini 2.5 Flash** | Real-time AI biomechanical coaching analysis |
| 📸 **Screenshot** | Capture annotated pose snapshot |
| 🔊 **Voice Feedback** | Optional Web Speech API rep count |
| 💾 **Settings Saved** | API key and preferences persisted in localStorage |
| 🌐 **100% Client-side** | No backend processing — works fully in browser |

---

## 🚀 Quick Start (Local)

### Option A — Open Directly (Simplest)

> MediaPipe CDN scripts require a web server (not `file://`). Use one of these:

```bash
# Python (no install needed)
python -m http.server 5000
# Then open: http://localhost:5000
```

```bash
# Node.js
npx serve . -p 5000
```

```bash
# VS Code — install "Live Server" extension, click "Go Live"
```

### Option B — Flask Server

```bash
# Install
pip install flask gunicorn

# Run
python server.py

# Open: http://localhost:5000
```

---

## 🤖 Gemini AI Setup

1. Go to **https://aistudio.google.com**
2. Click **"Get API Key"** → Create free key
3. In the app, click **⚙ Settings** → paste your key
4. Key is stored in browser localStorage — never sent to any server

---

## 📁 Project Structure

```
biomech-ai/
├── index.html              ← Main app (single-page)
├── server.py               ← Flask static file server
├── requirements.txt        ← Flask + gunicorn only
├── Procfile                ← Render start command
├── render.yaml             ← Render deployment config
├── .gitignore
├── README.md
└── static/
    ├── css/
    │   └── style.css       ← Full cyberpunk UI design
    └── js/
        └── biomech.js      ← Core engine (MediaPipe + math + AI)
```

---

## 🌐 Deploy to Render

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "BioMech AI v2.0"
   git remote add origin https://github.com/YOUR_USERNAME/biomech-ai.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to [render.com](https://render.com) → **New Web Service**
   - Connect your GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn server:app`
   - Click **Deploy**

3. **Access:** Your app will be live at `https://biomech-ai-trainer.onrender.com`

> ⚡ Camera works on Render because processing happens **in the browser**, not the server!

---

## 🎮 How to Use

1. **Start Session** — click ▶ START SESSION, allow camera
2. **Select Exercise** — choose from 7 exercises in left panel
3. **Perform Exercise** — stand 2–3m from camera
4. **Read Feedback** — real-time corrections on screen
5. **AI Coach** — click 🤖 AI COACH after adding Gemini API key
6. **Screenshot** — capture your form with 📸

---

## 📐 Mathematical Engine

### Law of Cosines
For three body landmarks A (proximal joint), B (vertex joint), C (distal joint):

```
cos(B) = (AB² + BC² - AC²) / (2 · AB · BC)
∴ B = arccos((AB² + BC² - AC²) / (2 · AB · BC))
```

### Example — Knee Angle Calculation
```
A = Hip    landmark [x₁, y₁]
B = Knee   landmark [x₂, y₂]  ← Angle measured here
C = Ankle  landmark [x₃, y₃]

AB = √((x₂-x₁)² + (y₂-y₁)²)   ← Thigh length
BC = √((x₃-x₂)² + (y₃-y₂)²)   ← Shin length  
AC = √((x₃-x₁)² + (y₃-y₁)²)   ← Hypotenuse

Knee_angle = arccos((AB²+BC²-AC²)/(2·AB·BC)) → degrees
```

### Exercise Targets

| Exercise | Joint | Ideal | Tolerance |
|----------|-------|-------|-----------|
| Squat | Knee | 90° | ±18° |
| Push-Up | Elbow | 90° | ±18° |
| Lunge | Both Knees | 90° | ±18° |
| Plank | Body Line | 180° | ±10° |
| Bicep Curl | Elbow | 40° | ±20° |
| Shoulder Press | Elbow | 180° | ±10° |
| Deadlift | Hip | 180° | ±20° |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Pose Detection** | MediaPipe Pose (JS) — 33 landmarks, GPU-accelerated |
| **Angle Math** | Vanilla JS — Law of Cosines implementation |
| **AI Coaching** | Google Gemini 2.5 Flash API (direct from browser) |
| **Rendering** | HTML5 Canvas with neon glow effects |
| **UI** | Pure CSS — cyberpunk HUD design |
| **Fonts** | Michroma + Exo 2 + Share Tech Mono |
| **Server** | Flask (serves HTML/CSS/JS only) |
| **Hosting** | Render.com (free tier) |

---

## 🎨 Skeleton Styles

Change in Settings ⚙:
- **Neon Teal** — `#00ffcc` cyan holographic
- **Fire Orange** — `#ff6b35` thermal imaging
- **Matrix Green** — `#00ff41` classic terminal
- **Holographic Purple** — `#a78bfa` sci-fi

---

## 📝 License

MIT License — free to use, modify, distribute.

---

*Built with ❤️ | BioMech AI v2.0 | Client-side Biomechanical Analysis*
