# ⚡ BioMech AI — Real-Time Biomechanical Trainer

**Client-side** AI fitness coach powered by **MediaPipe Pose** + **Gemini AI**.
Works in any browser. Fully hosted on **Firebase** — **no server-side webcam processing needed**.

---

## 🌟 Features

| Feature | Details |
|---------|---------|
| 🦴 **Skeleton Tracking** | MediaPipe Pose — 33 body landmarks at 30fps |
| 📐 **Cosine Rule Engine** | Real-time joint angle calculation via Law of Cosines |
| 🎯 **7 Exercises** | Squat, Push-Up, Lunge, Plank, Bicep Curl, Shoulder Press, Deadlift |
| 🔢 **Rep Counter** | Auto-counting with state detection (up/down) |
| 🔍 **Digital Zoom** | Manual +/- zoom and pinch-to-zoom support for better tracking |
| 📊 **Form Score** | Weighted multi-checkpoint scoring with letter grade |
| 🎨 **4 Skeleton Styles** | Neon Teal, Fire Orange, Matrix Green, Holographic Purple |
| 🤖 **Gemini AI** | Real-time AI biomechanical coaching analysis |
| 📸 **Screenshot** | Capture annotated pose snapshot |
| 🔊 **Voice Feedback** | Hands-free commands and optional rep counting |
| 💾 **Cloud Sync** | Profile and session history synced via Supabase |

---

## 🚀 Quick Start (Local)

### Option A — Simple Server

> MediaPipe CDN scripts require a web server. Use one of these:

```bash
# Python (no install needed)
python -m http.server 5000
# Then open: http://localhost:5000
```

```bash
# Node.js
npx serve . -p 5000
```

---

## 🤖 Gemini AI Setup

1. Go to **https://aistudio.google.com**
2. Click **"Get API Key"** → Create free key
3. In the app, click **⚙ Settings** → paste your key
4. Key is stored locally in your browser's `localStorage` and is never sent to any server except Google's AI endpoint.

---

## 🌐 Deployment (Firebase)

The project is optimized for **Firebase Hosting**.

1. **Initialize Firebase:**
   ```bash
   firebase init hosting
   ```
2. **Deploy:**
   ```bash
   firebase deploy --only hosting
   ```

**Live URL:** [https://ai-biomech.web.app](https://ai-biomech.web.app)

---

## 📐 Mathematical Engine — Law of Cosines

For three body landmarks A, B, C:
`B = arccos((AB² + BC² - AC²) / (2 · AB · BC))`

This allows the engine to calculate precise joint angles regardless of body size or camera distance.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Pose Detection** | MediaPipe Pose (JS) |
| **Logic/Math** | Vanilla JavaScript (ES6+) |
| **AI Insights** | Google Gemini AI |
| **Persistence** | Supabase (Database) + LocalStorage |
| **Auth** | Google Identity Services (GSI) |
| **UI** | HTML5 + Modern CSS (Glassmorphism) |
| **Hosting** | Firebase Hosting |

---

## 👥 Developers

- **Krish Joshi** — Lead Developer & Architect
- **Omrajsinh Sisodiya** — Core Developer

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ | BioMech AI v3.1 | Science-Based Training*
