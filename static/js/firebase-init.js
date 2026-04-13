// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-analytics.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: window.BIOMECH_CONFIG?.FIREBASE_API_KEY || "",
  authDomain: "ai-biomech.firebaseapp.com",
  projectId: "ai-biomech",
  storageBucket: "ai-biomech.firebasestorage.app",
  messagingSenderId: "185590626393",
  appId: "1:185590626393:web:8e8a19206b962cbf175948",
  measurementId: "G-G8Z8PW62HL"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
window.firebaseApp = app;
window.firebaseAnalytics = analytics;
