# ⚡ BioMech AI — Real-Time Biomechanical Trainer

**Client-side** AI fitness coach powered by **MediaPipe Pose** + **Gemini AI**.
Works in any browser. Fully hosted on **Firebase** — **no server-side webcam processing needed**.

---

## 🌟 Features

| Feature | Details |
|---------|---------|
| 🦴 **Skeleton Tracking** | MediaPipe Pose — 33 body landmarks at 30fps |
| 📐 **Cosine Rule Engine** | Real-time joint angle calculation |
| 🎯 **7 Exercises** | Squat, Push-Up, Lunge, Plank, Bicep Curl, Shoulder Press, Deadlift |
| 🔢 **Rep Counter** | Auto-counting with state detection |
| 🔍 **Digital Zoom** | manual +/- and pinch-to-zoom support |
| 📊 **AI Audit Report** | **[NEW]** Generate full performance audit reports using Gemini AI |
| 🤖 **Hardcoded AI** | Seamless experience — Gemini key integrated for project demo |
| 📸 **Screenshot** | Capture annotated pose snapshot |
| 🔊 **Voice Feedback** | Hands-free commands and optional rep counting |
| 💾 **Cloud Sync** | Session history synced via Supabase |

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

## 🤖 Gemini AI Integration

The system is now pre-configured for **BioMech AI 3.2.0**.
- **Internal Key Management:** Gemini API key is hardcoded into the build for the personal project demo.
- **Form Analysis:** Real-time form assessment with anatomical reasoning.
- **Performance Audit:** Click the `GENERATE REPORT` button in the AI modal for a deep-dive analysis of your entire session history.

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

## 📏 Mathematical Engine — Law of Cosines

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

*Built with ❤️ | BioMech AI v3.2.0 | Science-Based Training*
