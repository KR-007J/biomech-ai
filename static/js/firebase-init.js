// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-analytics.js";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCJTKs_ride3thAE_r4lMZrA7dh0ruxnck",
  authDomain: "abyssal-mobile.firebaseapp.com",
  projectId: "abyssal-mobile",
  storageBucket: "abyssal-mobile.firebasestorage.app",
  messagingSenderId: "136266338296",
  appId: "1:136266338296:web:53d8c91d086c87becf900d"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
window.firebaseApp = app;
window.firebaseAnalytics = analytics;
