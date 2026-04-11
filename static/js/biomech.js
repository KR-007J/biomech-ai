/* ══════════════════════════════════════════════════════════════════
   BioMech AI v3.1 — Full Feature Engine
   © 2026 Krish Joshi & Omrajsinh Sisodiya · All Rights Reserved

   v3.1 Changes:
   - Camera adjustment controls (flip, zoom, brightness guidance)
   - Maximized camera display area for mobile & laptop
   - Camera expand/fullscreen toggle
   - Camera selection (front/back)
   - Pinch-to-zoom on mobile camera
   - Resizable camera panel on desktop
══════════════════════════════════════════════════════════════════ */
'use strict';

// Global database reference (var so it's accessible as window.db)
var db = null;

// ── GLOBAL EXPORTS (IMMEDIATE) ───────────────────────────────────
console.log("BioMech AI: Binding Core Handlers...");
window.continueAsGuest = function() {
  console.log("Guest Login Initiated");
  try {
    // Ensure db is initialized immediately
    if (typeof getDB === 'function') {
      db = getDB();
    } else {
      db = db || { googleUser: null, sessions: [], totalReps: 0, streak: 0 };
    }
    
    db.googleUser = { guest: true, name: 'Guest Athlete', sub: 'guest_' + Date.now() };
    if (typeof saveStorage === 'function') saveStorage(db);
    if (typeof dismissLoginScreen === 'function') {
      dismissLoginScreen();
    } else {
      // Emergency DOM bypass
      var ls = document.getElementById('login-screen');
      if (ls) { ls.classList.add('hidden'); ls.style.display = 'none'; }
      if (typeof launchSplash === 'function') launchSplash();
    }
  } catch(e) { console.error("Guest login failed:", e); }
};
window.startSession = startSession;
window.stopSession = stopSession;
window.signOut = signOut;
window.triggerGoogleSignIn = triggerGoogleSignIn;

// ── SUPABASE INITIALIZATION ──────────────────────────────────────
const SUPABASE_URL = 'https://ezpduovdfwccncobomlw.supabase.co';
const SUPABASE_KEY = 'sb_publishable_-YdDaDb10urzMbB46Upg9w_QWyowVZy';
const supabaseClient = window.supabase ? window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY) : null;

// Configuration settings for AI and UI

// ── CONFIG ─────────────────────────────────────────────────────────
const CONFIG = {
  minDetectionConf:0.7, minTrackingConf:0.7, modelComplexity:1,
  skeletonStyle:'neon', showAngles:true, showSkeleton:true,
  voiceFeedback:false, audioCues:true,
  cameraZoom:1.0, cameraMirror:true, cameraExpanded:false,
  cameraFacing:'user', // 'user' = front, 'environment' = back
};

// ── EXERCISE DATABASE ──────────────────────────────────────────────
const EXERCISES = {
  squat:{name:'Squat',instruction:'Stand feet shoulder-width apart. Bend knees to 90°. Keep torso upright.',tips:['Face camera at full body distance','Point toes slightly outward','Keep chest up, core tight'],repJoint:'left_knee',repDownThreshold:110,repUpThreshold:160,muscles:{torso:0.3,leftLeg:0.9,rightLeg:0.9,glutes:0.8}},
  pushup:{name:'Push-Up',instruction:'Keep body in straight line. Lower until elbows reach 90°. Full range.',tips:['Hands wider than shoulders','Squeeze glutes and core','Look at floor 30cm ahead'],repJoint:'left_elbow',repDownThreshold:110,repUpThreshold:155,muscles:{torso:0.6,leftArm:0.9,rightArm:0.9}},
  lunge:{name:'Lunge',instruction:'Step forward. Both knees at 90°. Front knee over ankle.',tips:['Keep torso tall','Front knee tracks second toe','Push through front heel'],repJoint:'right_knee',repDownThreshold:110,repUpThreshold:160,muscles:{leftLeg:0.85,rightLeg:0.85,glutes:0.6,torso:0.2}},
  plank:{name:'Plank',instruction:'Straight line head to heels. Engage core. Hold position.',tips:['Press floor away','Neutral spine','Breathe steadily'],repJoint:null,repDownThreshold:0,repUpThreshold:0,muscles:{torso:0.95,leftArm:0.4,rightArm:0.4,leftLeg:0.3,rightLeg:0.3}},
  bicep_curl:{name:'Bicep Curl',instruction:'Elbows close to torso. Full range. Controlled descent.',tips:["Don't swing body",'Supinate wrist on the way up','Squeeze at the top'],repJoint:'left_elbow',repDownThreshold:130,repUpThreshold:50,muscles:{leftArm:0.95,rightArm:0.95,torso:0.1}},
  shoulder_press:{name:'Shoulder Press',instruction:'Press overhead to full extension. Elbows 90° at start.',tips:['Core tight','Full lockout at top','Control descent'],repJoint:'left_elbow',repDownThreshold:100,repUpThreshold:155,muscles:{leftArm:0.8,rightArm:0.8,torso:0.5}},
  deadlift:{name:'Deadlift',instruction:'Hip hinge. Bar close to body. Neutral spine throughout.',tips:['Brace core before lifting','Drive hips forward','Bar over mid-foot'],repJoint:'left_hip',repDownThreshold:70,repUpThreshold:155,muscles:{torso:0.8,leftLeg:0.7,rightLeg:0.7,glutes:0.9}},
};

// ── LANDMARK INDICES ───────────────────────────────────────────────
const LM={NOSE:0,LEFT_SHOULDER:11,RIGHT_SHOULDER:12,LEFT_ELBOW:13,RIGHT_ELBOW:14,LEFT_WRIST:15,RIGHT_WRIST:16,LEFT_HIP:23,RIGHT_HIP:24,LEFT_KNEE:25,RIGHT_KNEE:26,LEFT_ANKLE:27,RIGHT_ANKLE:28,LEFT_HEEL:29,RIGHT_HEEL:30};

// ── WORKOUT PROGRAMS ───────────────────────────────────────────────
const PROGRAMS = [
  {id:'beginner',name:'Beginner Strength',weeks:4,desc:'Foundation movement patterns',exercises:['squat','pushup','lunge'],color:'#00ffcc'},
  {id:'mobility',name:'Mobility & Form',weeks:3,desc:'Perfect your technique',exercises:['plank','lunge','deadlift'],color:'#a78bfa'},
  {id:'upper',name:'Upper Body Power',weeks:4,desc:'Arms, shoulders & chest',exercises:['pushup','bicep_curl','shoulder_press'],color:'#f59e0b'},
  {id:'full',name:'Full Body Blast',weeks:6,desc:'Complete workout program',exercises:['squat','pushup','deadlift','bicep_curl'],color:'#ec4899'},
];

// ── ACHIEVEMENTS ───────────────────────────────────────────────────
const ACHIEVEMENTS_DEF = [
  {id:'first_rep',   icon:'🎯', name:'First Rep',        desc:'Complete your first rep',   check:s=>s.totalReps>=1},
  {id:'ten_reps',    icon:'💪', name:'10 Rep Club',       desc:'Complete 10 reps',          check:s=>s.totalReps>=10},
  {id:'century',     icon:'💯', name:'Century',           desc:'Complete 100 total reps',   check:s=>s.totalReps>=100},
  {id:'perfect_form',icon:'⭐', name:'Perfect Form',      desc:'Score 100% on a session',   check:s=>s.bestScore>=100},
  {id:'streak3',     icon:'🔥', name:'3-Day Warrior',     desc:'Work out 3 days in a row',  check:s=>s.streak>=3},
  {id:'streak7',     icon:'🏆', name:'7-Day Legend',      desc:'Work out 7 days in a row',  check:s=>s.streak>=7},
  {id:'speed_demon', icon:'⚡', name:'Speed Demon',       desc:'Complete 10 reps in 30s',   check:s=>s.fastestSet<=30},
  {id:'all7',        icon:'🌟', name:'All-Rounder',       desc:'Try all 7 exercises',       check:s=>s.exercisesTried>=7},
  {id:'ai_coach',    icon:'🤖', name:'AI Student',        desc:'Use AI Coach 5 times',      check:s=>s.aiCoachUses>=5},
  {id:'week_warrior',icon:'📅', name:'Week Warrior',      desc:'Complete 10 sessions',      check:s=>s.totalSessions>=10},
  {id:'recorded',    icon:'🎬', name:'On Camera',         desc:'Record a session',          check:s=>s.hasRecorded},
  {id:'shared',      icon:'🔗', name:'Social Athlete',    desc:'Share a workout card',      check:s=>s.hasShared},
];

// ── STATE ──────────────────────────────────────────────────────────
let state = {
  exercise:'squat', sessionActive:false, repCount:0, repState:'up',
  formScore:100, bestScore:100, totalReps:0, corrections:0,
  startTime:null, lastAngles:{}, lastFeedback:[], frameCount:0,
  lastFpsTime:Date.now(), fps:0, pose:null, camera:null,
  videoEl:null, canvasEl:null, ctx:null, 
  geminiKey:'AIzaSyAE7FGde0OUDMhrp421-u4XtBPyzRxq_CI', // Hardcoded personal key for college project
  scoreBreakdown:{depth:100,alignment:100,balance:100},
  scoreHistory:[], repTimestamps:[], sessionStartReps:0,
  // Camera state
  cameraZoom:1.0, cameraMirror:true, cameraStream:null,
  availableCameras:[], activeCameraId:null,
};

// ── PERSISTENT DATA (localStorage) ────────────────────────────────
function loadStorage() {
  try { return JSON.parse(localStorage.getItem('biomech_v3')||'{}'); }
  catch(e) { return {}; }
}
function saveStorage(data) {
  try { localStorage.setItem('biomech_v3', JSON.stringify(data)); } catch(e){}
}
function getDB() {
  const defaults = {
    sessions:[], totalReps:0, streak:0, lastDate:'', exercisesTried:[],
    aiCoachUses:0, fastestSet:9999, hasRecorded:false, hasShared:false,
    totalSessions:0, unlockedAchievements:[],
    activeProgram:null, programProgress:{},
    googleUser:null,
    profiles: [], activeProfile: null // Added for compatibility with any legacy filters
  };
  const saved = loadStorage();
  return {...defaults,...saved};
}

if (!db) db = getDB();




// ── SKELETON STYLES ────────────────────────────────────────────────
const SKELETON_STYLES = {
  neon:  {joint:'#00ffcc',bone:'#00ffcc'},
  fire:  {joint:'#ff6b35',bone:'#ff6b35'},
  matrix:{joint:'#00ff41',bone:'#00ff41'},
  purple:{joint:'#a78bfa',bone:'#a78bfa'},
};

// ══════════════════════════════════════════════════════════════════
//  CAMERA ADJUSTMENT SYSTEM (NEW v3.1)
// ══════════════════════════════════════════════════════════════════

/**
 * Enumerate available cameras and populate the camera selector
 */
async function loadAvailableCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    state.availableCameras = devices.filter(d => d.kind === 'videoinput');
    const sel = document.getElementById('camera-select');
    if (sel) {
      sel.innerHTML = state.availableCameras.map((cam, i) => {
        const label = cam.label || `Camera ${i + 1}`;
        const isFront = label.toLowerCase().includes('front') || label.toLowerCase().includes('user') || i === 0;
        return `<option value="${cam.deviceId}">${isFront ? '📸 ' : '🎥 '}${label.length > 22 ? label.substring(0, 22) + '…' : label}</option>`;
      }).join('');
      if (state.activeCameraId) {
        sel.value = state.activeCameraId;
      }
    }
  } catch(e) {
    console.warn('Could not enumerate cameras:', e);
  }
}

/**
 * Switch to a different camera device
 */
async function switchCamera(deviceId) {
  if (!state.sessionActive) {
    showToast('Start session first to switch camera', 'info');
    return;
  }
  state.activeCameraId = deviceId;
  // Restart session with new camera
  await stopSession();
  await sleep(300);
  await startSession(deviceId);
}

/**
 * Toggle camera mirror/flip
 */
function toggleMirror() {
  state.cameraMirror = !state.cameraMirror;
  CONFIG.cameraMirror = state.cameraMirror;
  const btn = document.getElementById('btn-mirror');
  if (btn) {
    btn.classList.toggle('cam-ctrl-active', state.cameraMirror);
    btn.title = state.cameraMirror ? 'Mirror: ON' : 'Mirror: OFF';
  }
  showToast(state.cameraMirror ? '🪞 Mirror ON' : '🪞 Mirror OFF');
}

/**
 * Adjust camera zoom (CSS transform on canvas/video)
 */
function adjustZoom(delta) {
  state.cameraZoom = Math.max(0.7, Math.min(2.5, state.cameraZoom + delta));
  applyZoom();
  document.getElementById('zoom-level').textContent = Math.round(state.cameraZoom * 100) + '%';
}

function applyZoom() {
  const canvas = document.getElementById('output-canvas');
  const video = document.getElementById('webcam');
  const z = state.cameraZoom;
  if (canvas) {
    canvas.style.transform = `scale(${z})`;
    canvas.style.transformOrigin = 'center center';
  }
  if (video) {
    video.style.transform = `scale(${z})`;
    video.style.transformOrigin = 'center center';
  }
}

function resetZoom() {
  state.cameraZoom = 1.0;
  applyZoom();
  document.getElementById('zoom-level').textContent = '100%';
  showToast('Zoom reset');
}

/**
 * Toggle camera expand mode — takes over more screen space
 */
function toggleCameraExpand() {
  CONFIG.cameraExpanded = !CONFIG.cameraExpanded;
  const frame = document.querySelector('.cam-frame');
  const bodyGrid = document.querySelector('.body-grid');
  const centerPanel = document.querySelector('.center-panel');
  const expandBtn = document.getElementById('btn-expand');

  if (CONFIG.cameraExpanded) {
    // Expand camera to fill more space
    if (bodyGrid) bodyGrid.classList.add('camera-expanded-mode');
    if (expandBtn) { expandBtn.textContent = '⊡'; expandBtn.title = 'Collapse Camera'; }
    showToast('📷 Camera Expanded');
  } else {
    if (bodyGrid) bodyGrid.classList.remove('camera-expanded-mode');
    if (expandBtn) { expandBtn.textContent = '⊞'; expandBtn.title = 'Expand Camera'; }
    showToast('Camera Normal View');
  }
}

/**
 * Toggle fullscreen on camera frame
 */
function toggleFullscreen() {
  const frame = document.querySelector('.cam-frame');
  if (!frame) return;
  if (!document.fullscreenElement) {
    frame.requestFullscreen().catch(err => showToast('Fullscreen not available', 'error'));
    showToast('▶ Fullscreen — Press Esc to exit');
  } else {
    document.exitFullscreen();
  }
}

/**
 * Setup pinch-to-zoom on mobile
 */
function setupPinchZoom() {
  const frame = document.querySelector('.cam-frame');
  if (!frame) return;
  let initialDist = 0;
  let initialZoom = 1.0;

  frame.addEventListener('touchstart', (e) => {
    if (e.touches.length === 2) {
      initialDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      initialZoom = state.cameraZoom;
    }
  }, { passive: true });

  frame.addEventListener('touchmove', (e) => {
    if (e.touches.length === 2) {
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      const scale = dist / initialDist;
      state.cameraZoom = Math.max(0.7, Math.min(2.5, initialZoom * scale));
      applyZoom();
      const zl = document.getElementById('zoom-level');
      if (zl) zl.textContent = Math.round(state.cameraZoom * 100) + '%';
    }
  }, { passive: true });
}

/**
 * Show the camera setup guide popup
 */
function showCameraGuide() {
  const guide = document.getElementById('cam-guide-popup');
  if (guide) {
    guide.classList.toggle('show');
  }
}

// ── GOOGLE SIGN-IN ─────────────────────────────────────────────────
function handleGoogleLoginCallback(response) {
  try {
    const payload = parseJwt(response.credential);
    db.googleUser = {
      name:    payload.name    || 'Athlete',
      email:   payload.email   || '',
      picture: payload.picture || '',
      sub:     payload.sub     || '',
      given:   payload.given_name || (payload.name ? payload.name.split(' ')[0] : 'Athlete'),
    };
    saveStorage(db);
    syncProfile(); // Sync to Supabase cloud
    dismissLoginScreen();
  } catch(e) {
    console.error('Google login error:', e);
    showLoginError('Sign-in failed. Please try again.');
  }
}
window.handleGoogleLoginCallback = handleGoogleLoginCallback;

/**
 * Cloud Synchronization logic
 */
async function syncProfile() {
  if (!supabaseClient || !db.googleUser) return;
  const { error } = await supabaseClient
    .from('profiles')
    .upsert({
      id: db.googleUser.sub,
      name: db.googleUser.name,
      email: db.googleUser.email,
      picture: db.googleUser.picture,
      stats: {
        totalReps: db.totalReps,
        streak: db.streak,
        totalSessions: db.totalSessions,
        unlockedAchievements: db.unlockedAchievements
      },
      updated_at: new Date()
    });
  if (error) console.error('Cloud Sync (Profile) Error:', error);
}

async function syncSession(sessionData) {
  if (!supabaseClient || !db.googleUser) return;
  const { error } = await supabaseClient
    .from('sessions')
    .insert({
      user_id: db.googleUser.sub,
      exercise: sessionData.exercise,
      reps: sessionData.reps,
      score: sessionData.score,
      duration: sessionData.duration,
      date: new Date()
    });
  if (error) console.error('Cloud Sync (Session) Error:', error);
}

function parseJwt(token) {
  const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
  const json = decodeURIComponent(
    atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
  );
  return JSON.parse(json);
}

function triggerGoogleSignIn() {
  if (window.google && google.accounts && google.accounts.id) {
    google.accounts.id.prompt();
  } else {
    showLoginError('Google Sign-In not loaded. Check your internet connection.');
  }
}

// Legacy functions removed - now handled by global window bindings at top of script

function signOut() {
  console.log("BioMech AI: Sign Out initiated...");
  try {
    if (window.google && google.accounts && db?.googleUser?.email) {
      google.accounts.id.revoke(db.googleUser.email, () => {
        console.log('Google Auth Revoked');
      });
    }
  } catch(e) { console.error("SignOut Revoke failed:", e); }
  
  // Clear all persistent data
  db = null;
  localStorage.removeItem('biomech_v3');
  sessionStorage.clear();
  
  console.log("Session cleared. Reloading...");
  setTimeout(() => {
    window.location.href = window.location.origin + window.location.pathname + '?v=' + Date.now();
  }, 100);
}

function dismissLoginScreen() {
  const ls = document.getElementById('login-screen');
  ls.classList.add('hidden');
  setTimeout(() => { ls.style.display = 'none'; launchSplash(); }, 750);
}

function showLoginError(msg) {
  let el = document.getElementById('login-error');
  if (!el) {
    el = document.createElement('div');
    el.id = 'login-error';
    el.style.cssText = 'font-size:0.7rem;color:#ef4444;font-family:var(--font-mono);text-align:center;padding:0.3rem;';
    document.querySelector('.login-card').appendChild(el);
  }
  el.textContent = msg;
}

function updateUserPill() {
  const pill = document.getElementById('user-pill');
  const nameEl = document.getElementById('hdr-username');
  const avatarImg = document.getElementById('user-avatar-img');
  const avatarFallback = document.getElementById('user-avatar-fallback');
  if (db.googleUser) {
    pill.style.display = 'flex';
    nameEl.textContent = db.googleUser.given || db.googleUser.name;
    if (db.googleUser.picture) {
      avatarImg.src = db.googleUser.picture;
      avatarImg.style.display = 'block';
      avatarFallback.style.display = 'none';
    }
  } else {
    pill.style.display = 'flex';
    nameEl.textContent = 'Guest';
    avatarFallback.textContent = '👤';
  }
}

// ── GEMINI KEY ─────────────────────────────────────────────────────
async function loadGeminiKey() {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) throw new Error('no endpoint');
    const data = await res.json();
    if (data.geminiKey) { state.geminiKey = data.geminiKey; }
  } catch(e) {}
}

// ── AUDIO ENGINE ───────────────────────────────────────────────────
let audioCtx = null;
function getAudioCtx() {
  if (!audioCtx) audioCtx = new (window.AudioContext||window.webkitAudioContext)();
  return audioCtx;
}
function playBeep(freq=440, dur=0.08, vol=0.3, type='sine') {
  if (!CONFIG.audioCues) return;
  try {
    const ctx = getAudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = freq; osc.type = type;
    gain.gain.setValueAtTime(vol, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
    osc.start(); osc.stop(ctx.currentTime + dur);
  } catch(e){}
}
function playRepSound()    { playBeep(880,  0.06, 0.25, 'triangle'); }
function playErrorSound()  { playBeep(220,  0.15, 0.2,  'sawtooth'); }
function playSuccessSound(){ playBeep(1047, 0.1,  0.2,  'sine'); setTimeout(()=>playBeep(1319,0.15,0.2,'sine'),100); }

// Legacy Metronome System Removed as per decluttering request

// ── RECORDING ──────────────────────────────────────────────────────
let mediaRecorder=null, recordedChunks=[], isRecording=false;

function toggleRecording() { if (isRecording) stopRecording(); else startRecording(); }
function startRecording() {
  const canvas = document.getElementById('output-canvas');
  if (!canvas || !state.sessionActive) { showToast('Start a session first!', 'error'); return; }
  try {
    const stream = canvas.captureStream(30);
    mediaRecorder = new MediaRecorder(stream, {mimeType:'video/webm;codecs=vp8'});
    recordedChunks = [];
    mediaRecorder.ondataavailable = e => { if (e.data.size>0) recordedChunks.push(e.data); };
    mediaRecorder.onstop = saveRecording;
    mediaRecorder.start(100);
    isRecording = true;
    document.getElementById('btn-record').classList.add('rec-active');
    document.getElementById('btn-record').querySelector('.ctrl-icon').textContent='⏹';
    document.getElementById('rec-indicator').style.display='flex';
    db.hasRecorded=true; saveStorage(db); checkAchievements();
    showToast('Recording started 🎬'); addLog('Recording started','good');
  } catch(e) { showToast('Recording not supported on this browser','error'); }
}
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state!=='inactive') mediaRecorder.stop();
  isRecording=false;
  document.getElementById('btn-record').classList.remove('rec-active');
  document.getElementById('btn-record').querySelector('.ctrl-icon').textContent='⏺';
  document.getElementById('rec-indicator').style.display='none';
  addLog('Recording saved','good');
}
function saveRecording() {
  const blob = new Blob(recordedChunks, {type:'video/webm'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href=url; a.download=`biomech-session-${Date.now()}.webm`; a.click();
  URL.revokeObjectURL(url);
  showToast('Video downloaded! 🎬');
}

// ── VOICE COMMANDS ──────────────────────────────────────────────────
let voiceRecognition=null, voiceActive=false;
const EXERCISE_KEYS = Object.keys(EXERCISES);

function toggleVoiceCommands() { if (voiceActive) stopVoiceCommands(); else startVoiceCommands(); }
function startVoiceCommands() {
  const SR = window.SpeechRecognition||window.webkitSpeechRecognition;
  if (!SR) { showToast('Voice commands not supported','error'); return; }
  voiceRecognition = new SR();
  voiceRecognition.continuous=true; voiceRecognition.interimResults=false; voiceRecognition.lang='en-US';
  voiceRecognition.onresult = e => handleVoiceCommand(e.results[e.results.length-1][0].transcript.toLowerCase().trim());
  voiceRecognition.onerror = ()=>{};
  voiceRecognition.onend = ()=>{ if(voiceActive) voiceRecognition.start(); };
  voiceRecognition.start(); voiceActive=true;
  document.getElementById('btn-voice').classList.add('voice-active');
  document.getElementById('voice-status').style.display='flex';
  showToast('🎙 Voice commands active!');
}
function stopVoiceCommands() {
  if (voiceRecognition) { voiceRecognition.stop(); voiceRecognition=null; }
  voiceActive=false;
  document.getElementById('btn-voice').classList.remove('voice-active');
  document.getElementById('voice-status').style.display='none';
  showToast('Voice commands off');
}
function handleVoiceCommand(cmd) {
  showToast(`🎙 "${cmd}"`, 'info');
  if (cmd.includes('start'))        { if (!state.sessionActive) startSession(); }
  else if (cmd.includes('stop')||cmd.includes('pause')) { if (state.sessionActive) stopSession(); }
  else if (cmd.includes('reset'))    resetSession();
  else if (cmd.includes('record'))   toggleRecording();
  else if (cmd.includes('screenshot')||cmd.includes('capture')) takeScreenshot();
  else if (cmd.includes('ai')||cmd.includes('coach')||cmd.includes('analyze')) openAICoach();
  else if (cmd.includes('expand')||cmd.includes('big camera')) toggleCameraExpand();
  else if (cmd.includes('fullscreen')||cmd.includes('full screen')) toggleFullscreen();
  else if (cmd.includes('flip')||cmd.includes('mirror')) toggleMirror();
  else if (cmd.includes('zoom in'))  adjustZoom(0.2);
  else if (cmd.includes('zoom out')) adjustZoom(-0.2);
  else if (cmd.includes('next')) {
    const idx=EXERCISE_KEYS.indexOf(state.exercise);
    selectExercise(EXERCISE_KEYS[(idx+1)%EXERCISE_KEYS.length]);
  } else {
    EXERCISE_KEYS.forEach(k=>{ if(cmd.includes(EXERCISES[k].name.toLowerCase())) selectExercise(k); });
  }
}

// ── MOBILE TAB NAV ─────────────────────────────────────────────────
let currentTab='camera';
function showTab(tab) {
  currentTab=tab;
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
  const tabEl=document.getElementById(`tab-${tab}`);
  if(tabEl) tabEl.classList.add('active');
  document.querySelectorAll('.mobile-panel').forEach(p=>p.classList.remove('active'));
  const cp=document.querySelector('.center-panel');
  if (tab==='exercises') { document.getElementById('mobile-exercises').classList.add('active'); if(cp) cp.style.display='none'; }
  else if (tab==='stats') { document.getElementById('mobile-stats').classList.add('active'); if(cp) cp.style.display='none'; }
  else if (tab==='progress') { document.getElementById('mobile-progress').classList.add('active'); if(cp) cp.style.display='none'; renderHistoryChart('history-chart-m'); }
  else { if(cp) cp.style.display=''; }
}

// ── ANGLE CALC ─────────────────────────────────────────────────────
function calculateAngle(A,B,C) {
  const AB=Math.hypot(B[0]-A[0],B[1]-A[1]), BC=Math.hypot(C[0]-B[0],C[1]-B[1]), AC=Math.hypot(C[0]-A[0],C[1]-A[1]);
  if(AB===0||BC===0) return 0;
  return Math.round(Math.acos(Math.max(-1,Math.min(1,(AB*AB+BC*BC-AC*AC)/(2*AB*BC))))*(180/Math.PI));
}
function lmXY(lms,idx){return[lms[idx].x,lms[idx].y];}
function lmPX(lms,idx,w,h){return[lms[idx].x*w,lms[idx].y*h];}

// ── ANALYZERS ──────────────────────────────────────────────────────
function analyzeSquat(lms,w,h){
  const angles={},feedback=[];let depthScore=100,alignScore=100,balScore=100;
  try{
    const LH=lmXY(lms,LM.LEFT_HIP),LK=lmXY(lms,LM.LEFT_KNEE),LA=lmXY(lms,LM.LEFT_ANKLE);
    const RH=lmXY(lms,LM.RIGHT_HIP),RK=lmXY(lms,LM.RIGHT_KNEE),RA=lmXY(lms,LM.RIGHT_ANKLE);
    const LS=lmXY(lms,LM.LEFT_SHOULDER);
    const lK=calculateAngle(LH,LK,LA),rK=calculateAngle(RH,RK,RA),lH=calculateAngle(LS,LH,LK);
    const avg=(lK+rK)/2,diff=Math.abs(lK-rK);
    angles.left_knee=lK;angles.right_knee=rK;angles.left_hip=lH;
    if(avg>155){feedback.push({msg:'⬇ Go Deeper — Bend Knees to 90°',severity:'warning'});depthScore=Math.max(0,100-(avg-90)*1.5);}
    else if(avg>=72&&avg<=108){feedback.push({msg:'🎯 Perfect Squat Depth!',severity:'success'});}
    else if(avg<60){feedback.push({msg:'⬆ Too Deep — Rise Slightly',severity:'warning'});depthScore=70;}
    else{depthScore=85;}
    if(lH<45){feedback.push({msg:'❌ Keep Torso Upright',severity:'error'});alignScore=40;}
    else if(lH<65){feedback.push({msg:'⚠ Less Forward Lean',severity:'warning'});alignScore=70;}
    if(diff>20){feedback.push({msg:'⚖ Balance Both Sides',severity:'warning'});balScore=Math.max(0,100-diff*2);}
  }catch(e){feedback.push({msg:'📷 Show Full Body',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:0,balance:0}};}
  return{angles,feedback,score:Math.round(depthScore*0.4+alignScore*0.35+balScore*0.25),breakdown:{depth:depthScore,alignment:alignScore,balance:balScore}};
}
function analyzePushup(lms,w,h){
  const angles={},feedback=[];let eS=100,aS=100;
  try{
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LE=lmXY(lms,LM.LEFT_ELBOW),LW=lmXY(lms,LM.LEFT_WRIST);
    const RS=lmXY(lms,LM.RIGHT_SHOULDER),RE=lmXY(lms,LM.RIGHT_ELBOW),RW=lmXY(lms,LM.RIGHT_WRIST);
    const LH=lmXY(lms,LM.LEFT_HIP),LA=lmXY(lms,LM.LEFT_ANKLE);
    const lE=calculateAngle(LS,LE,LW),rE=calculateAngle(RS,RE,RW),body=calculateAngle(LS,LH,LA),avg=(lE+rE)/2;
    angles.left_elbow=lE;angles.right_elbow=rE;angles.body_alignment=body;
    if(avg>155){feedback.push({msg:'⬇ Lower Chest Further!',severity:'warning'});eS=Math.max(0,100-(avg-90)*1.2);}
    else if(avg>=72&&avg<=108){feedback.push({msg:'💪 Perfect Push-Up Depth!',severity:'success'});}
    if(body<152){feedback.push({msg:'❌ Raise Hips',severity:'error'});aS=30;}
    else if(body>198){feedback.push({msg:'❌ Lower Hips',severity:'error'});aS=30;}
    else if(Math.abs(body-180)<12){feedback.push({msg:'✓ Great Body Alignment',severity:'success'});}
  }catch(e){feedback.push({msg:'📷 Adjust Camera for Side View',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:0,balance:100}};}
  return{angles,feedback,score:Math.round(eS*0.5+aS*0.5),breakdown:{depth:eS,alignment:aS,balance:100}};
}
function analyzeLunge(lms,w,h){return analyzeSquat(lms,w,h);}
function analyzePlank(lms,w,h){
  const angles={},feedback=[];let bS=100,hS=100;
  try{
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LH=lmXY(lms,LM.LEFT_HIP),LA=lmXY(lms,LM.LEFT_ANKLE);
    const bl=calculateAngle(LS,LH,LA);angles.body_alignment=bl;
    const dev=Math.abs(bl-180);
    if(dev>15){feedback.push({msg:bl<165?'❌ Hips Too High':'❌ Hips Sagging — Engage Core',severity:'error'});bS=Math.max(0,100-dev*4);}
    else if(dev<6){feedback.push({msg:'⚡ Perfect Plank!',severity:'success'});}
    else{feedback.push({msg:'⚠ Adjust Hip Height',severity:'warning'});bS=75;}
  }catch(e){feedback.push({msg:'📷 Show Side Profile',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(bS*0.7+hS*0.3),breakdown:{depth:bS,alignment:hS,balance:100}};
}
function analyzeBicepCurl(lms,w,h){
  const angles={},feedback=[];let cS=100;
  try{
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LE=lmXY(lms,LM.LEFT_ELBOW),LW=lmXY(lms,LM.LEFT_WRIST);
    const RS=lmXY(lms,LM.RIGHT_SHOULDER),RE=lmXY(lms,LM.RIGHT_ELBOW),RW=lmXY(lms,LM.RIGHT_WRIST);
    const lE=calculateAngle(LS,LE,LW),rE=calculateAngle(RS,RE,RW),avg=(lE+rE)/2;
    angles.left_elbow=lE;angles.right_elbow=rE;
    if(avg<35){feedback.push({msg:'🔥 Full Curl — Excellent!',severity:'success'});}
    else if(avg<70){feedback.push({msg:'✓ Good Curl Range',severity:'success'});cS=85;}
    else if(avg>150){feedback.push({msg:'↑ Start Curling',severity:'info'});cS=60;}
    else{feedback.push({msg:'⬆ Curl Higher!',severity:'warning'});cS=65;}
  }catch(e){feedback.push({msg:'📷 Face Camera',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(cS*0.7+30),breakdown:{depth:cS,alignment:100,balance:100}};
}
function analyzeShoulderPress(lms,w,h){
  const angles={},feedback=[];let score=100;
  try{
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LE=lmXY(lms,LM.LEFT_ELBOW),LW=lmXY(lms,LM.LEFT_WRIST);
    const RS=lmXY(lms,LM.RIGHT_SHOULDER),RE=lmXY(lms,LM.RIGHT_ELBOW),RW=lmXY(lms,LM.RIGHT_WRIST);
    const avg=(calculateAngle(LS,LE,LW)+calculateAngle(RS,RE,RW))/2;
    angles.left_elbow=Math.round(avg);
    if(avg>160){feedback.push({msg:'🏆 Full Lockout!',severity:'success'});}
    else if(avg<100){feedback.push({msg:'↑ Press to Full Extension',severity:'warning'});score=Math.max(0,100-(160-avg)*1.2);}
    else{feedback.push({msg:'↑ Press Higher',severity:'info'});score=75;}
  }catch(e){return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(score),breakdown:{depth:score,alignment:100,balance:100}};
}
function analyzeDeadlift(lms,w,h){
  const angles={},feedback=[];let score=100;
  try{
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LH=lmXY(lms,LM.LEFT_HIP),LK=lmXY(lms,LM.LEFT_KNEE);
    const h2=calculateAngle(LS,LH,LK);angles.left_hip=h2;
    if(h2>155){feedback.push({msg:'💎 Full Extension!',severity:'success'});}
    else if(h2<50){feedback.push({msg:'⬆ Drive Hips Forward!',severity:'warning'});score=Math.max(0,100-(155-h2));}
  }catch(e){return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(score),breakdown:{depth:score,alignment:100,balance:100}};
}
const ANALYZERS={squat:analyzeSquat,pushup:analyzePushup,lunge:analyzeLunge,plank:analyzePlank,bicep_curl:analyzeBicepCurl,shoulder_press:analyzeShoulderPress,deadlift:analyzeDeadlift};

// ── SKELETON DRAWING ───────────────────────────────────────────────
const POSE_CONNECTIONS=[[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],[23,25],[25,27],[24,26],[26,28],[27,29],[28,30]];
const ANGLE_JOINTS={left_knee:[23,25,27],right_knee:[24,26,28],left_elbow:[11,13,15],right_elbow:[12,14,16],left_hip:[11,23,25],body_alignment:[11,23,27]};

function drawSkeleton(ctx,lms,w,h,feedback){
  if(!CONFIG.showSkeleton) return;
  const style=SKELETON_STYLES[CONFIG.skeletonStyle]||SKELETON_STYLES.neon;
  const hasError=feedback.some(f=>f.severity==='error'), hasSuccess=feedback.some(f=>f.severity==='success');
  let color=style.joint;
  if(hasError) color='#ef4444';
  else if(hasSuccess) color='#10b981';
  ctx.save();ctx.globalAlpha=0.45;
  POSE_CONNECTIONS.forEach(([a,b])=>{
    if(a>=lms.length||b>=lms.length) return;
    const pa=lmPX(lms,a,w,h),pb=lmPX(lms,b,w,h);
    ctx.beginPath();ctx.moveTo(pa[0],pa[1]);ctx.lineTo(pb[0],pb[1]);
    ctx.strokeStyle=color;ctx.lineWidth=12;ctx.lineCap='round';ctx.filter='blur(8px)';ctx.stroke();
  });
  ctx.restore();ctx.save();ctx.filter='none';
  POSE_CONNECTIONS.forEach(([a,b])=>{
    if(a>=lms.length||b>=lms.length) return;
    const pa=lmPX(lms,a,w,h),pb=lmPX(lms,b,w,h);
    ctx.beginPath();ctx.moveTo(pa[0],pa[1]);ctx.lineTo(pb[0],pb[1]);
    ctx.strokeStyle=color;ctx.lineWidth=3;ctx.lineCap='round';ctx.shadowColor=color;ctx.shadowBlur=10;ctx.stroke();
  });
  for(let idx=11;idx<=32;idx++){
    if(idx>=lms.length) continue;
    const p=lmPX(lms,idx,w,h);
    ctx.beginPath();ctx.arc(p[0],p[1],5,0,Math.PI*2);ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=15;ctx.fill();
    ctx.beginPath();ctx.arc(p[0],p[1],2,0,Math.PI*2);ctx.fillStyle='#fff';ctx.shadowBlur=0;ctx.fill();
  }
  ctx.restore();
  if(CONFIG.showAngles){
    ctx.save();
    Object.entries(state.lastAngles).forEach(([name,angle])=>{
      if(!ANGLE_JOINTS[name]) return;
      const ji=ANGLE_JOINTS[name][1];if(ji>=lms.length) return;
      const p=lmPX(lms,ji,w,h);
      ctx.fillStyle='rgba(4,6,15,0.82)';ctx.beginPath();ctx.roundRect(p[0]-28,p[1]-16,56,28,6);ctx.fill();
      ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.shadowColor=color;ctx.shadowBlur=8;ctx.stroke();
      ctx.fillStyle=color;ctx.shadowBlur=0;ctx.font='bold 13px "Share Tech Mono"';ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(`${angle}°`,p[0],p[1]);
    });
    ctx.restore();
  }
}

// ── REP COUNTING ───────────────────────────────────────────────────
function countRep(angles,exercise){
  const ex=EXERCISES[exercise];
  if(!ex.repJoint) return;
  const angle=angles[ex.repJoint];if(angle===undefined) return;
  if(exercise==='bicep_curl'){
    if(angle<ex.repUpThreshold&&state.repState==='up'){state.repState='down';updateRepStateUI('down');}
    if(angle>ex.repDownThreshold&&state.repState==='down'){state.repState='up';updateRepStateUI('up');triggerRep();}
  }else{
    if(angle<ex.repDownThreshold&&state.repState==='up'){state.repState='down';updateRepStateUI('down');}
    if(angle>ex.repUpThreshold&&state.repState==='down'){state.repState='up';updateRepStateUI('up');triggerRep();}
  }
}
function triggerRep(){
  state.repCount++;state.totalReps++;
  state.repTimestamps.push(Date.now());
  if(state.repTimestamps.length>=10){
    const t=state.repTimestamps;
    const setTime=(t[t.length-1]-t[t.length-10])/1000;
    if(setTime<db.fastestSet){db.fastestSet=setTime;saveStorage(db);}
  }
  const el=document.getElementById('rep-number');
  if(el){el.textContent=state.repCount;el.classList.add('pop');setTimeout(()=>el.classList.remove('pop'),250);}
  const elm=document.getElementById('rep-number-m');
  if(elm){elm.textContent=state.repCount;elm.classList.add('pop');setTimeout(()=>elm.classList.remove('pop'),250);}
  document.getElementById('hdr-reps').textContent=state.repCount;
  setEl('stat-total-reps',state.totalReps);setEl('stat-reps-m',state.totalReps);
  playRepSound();
  if(CONFIG.voiceFeedback) speak(`${state.repCount}`);
  addLog(`Rep ${state.repCount}`,state.formScore>70?'good':'bad');
  showToast(`Rep ${state.repCount} ✓`);
  db.totalReps=state.totalReps;
  checkAchievements();
}
function updateRepStateUI(s){
  document.getElementById('chip-down')?.classList.toggle('active',s==='down');
  document.getElementById('chip-up')?.classList.toggle('active',s==='up');
  document.getElementById('chip-down-m')?.classList.toggle('active',s==='down');
  document.getElementById('chip-up-m')?.classList.toggle('active',s==='up');
}

// ── POSE RESULTS ───────────────────────────────────────────────────
function onResults(results){
  const canvas=state.canvasEl,ctx=state.ctx,video=state.videoEl;
  if(!canvas||!ctx) return;
  const w=canvas.width=video.videoWidth||canvas.offsetWidth;
  const h=canvas.height=video.videoHeight||canvas.offsetHeight;
  ctx.clearRect(0,0,w,h);
  ctx.save();
  // Apply mirror based on CONFIG
  if (state.cameraMirror) { ctx.scale(-1,1); ctx.translate(-w,0); }
  ctx.drawImage(video,0,0,w,h);
  if(results.poseLandmarks&&state.sessionActive){
    const lms=results.poseLandmarks;
    const analysis=(ANALYZERS[state.exercise]||analyzeSquat)(lms,w,h);
    state.lastAngles=analysis.angles;state.lastFeedback=analysis.feedback;
    state.formScore=analysis.score;state.scoreBreakdown=analysis.breakdown;
    if(analysis.score>state.bestScore){state.bestScore=analysis.score;}
    if(state.frameCount%30===0){state.scoreHistory.push(analysis.score);if(state.scoreHistory.length>20) state.scoreHistory.shift();}
    countRep(analysis.angles,state.exercise);
    drawSkeleton(ctx,lms,w,h,analysis.feedback);
    ctx.restore();
    updateFeedbackUI(analysis.feedback);updateAnglesStrip(analysis.angles);
    updateFormScore(analysis.score,analysis.breakdown);updateAlertBanner(analysis.feedback);
    updatePulse(analysis.feedback);
    if(analysis.feedback.some(f=>f.severity==='error')&&state.frameCount%60===0) playErrorSound();
    if(analysis.feedback.some(f=>f.severity==='success')&&state.frameCount%90===0) playSuccessSound();
  }else{
    ctx.restore();
    if(state.sessionActive) updateAlertBanner([{msg:'No Pose Detected — Step Back',severity:'info'}]);
  }
  state.frameCount++;
  const now=Date.now();
  if(now-state.lastFpsTime>=1000){state.fps=state.frameCount;state.frameCount=0;state.lastFpsTime=now;document.getElementById('hdr-fps').textContent=state.fps;}
}

// ── UI UPDATES ─────────────────────────────────────────────────────
function updateFeedbackUI(feedback){
  const icons={success:'✅',warning:'⚠️',error:'❌',info:'💡'};
  const html=feedback.length?feedback.slice(0,4).map(fb=>`<div class="fb-item ${fb.severity}"><div class="fb-icon">${icons[fb.severity]||'•'}</div><div class="fb-text">${fb.msg}</div></div>`).join(''):'<div class="fb-item info"><div class="fb-icon">💡</div><div class="fb-text">Analyzing pose...</div></div>';
  setHTML('feedback-list',html);setHTML('feedback-list-m',html);
  if(feedback.some(f=>f.severity==='error')){state.corrections++;setEl('stat-alerts',state.corrections);setEl('stat-alerts-m',state.corrections);}
}
function updateAnglesStrip(angles){
  const entries=Object.entries(angles).slice(0,4);
  entries.forEach(([name,val],i)=>{
    const chip=document.getElementById(`ac-${i}`);if(!chip) return;
    chip.querySelector('.ac-name').textContent=name.replace(/_/g,' ');
    chip.querySelector('.ac-val').textContent=`${val}°`;
    chip.className='angle-chip';
    if(val>=75&&val<=105) chip.classList.add('good');
    else if(val>=55&&val<=135) chip.classList.add('warn');
    else chip.classList.add('bad');
  });
  for(let i=entries.length;i<4;i++){const c=document.getElementById(`ac-${i}`);if(c){c.querySelector('.ac-name').textContent='—';c.querySelector('.ac-val').textContent='—°';c.className='angle-chip';}}
}
function updateFormScore(score,breakdown){
  const circ=364.4,offset=circ-(score/100)*circ;
  setEl('score-pct',score);setEl('score-pct-m',score);
  const pg=document.getElementById('score-prog');if(pg) pg.style.strokeDashoffset=offset;
  const pgm=document.getElementById('score-prog-m');if(pgm) pgm.style.strokeDashoffset=offset;
  let grade='A+';if(score<50)grade='F';else if(score<60)grade='D';else if(score<70)grade='C';else if(score<80)grade='B';else if(score<90)grade='A';
  setEl('score-grade',grade);setEl('score-grade-m',grade);
  const hdr=document.getElementById('hdr-score');
  if(hdr){hdr.textContent=score+'%';hdr.style.color=score>75?'#00ffcc':score>50?'#f59e0b':'#ef4444';}
  setEl('quality-pct',score+'%');
  const qb=document.getElementById('quality-bar');if(qb) qb.style.width=score+'%';
  setEl('stat-best',state.bestScore+'%');setEl('stat-best-m',state.bestScore+'%');
  const d=breakdown||{depth:score,alignment:score,balance:score};
  const sb=document.getElementById('sb-depth');if(sb) sb.style.width=Math.round(d.depth)+'%';
  const sa=document.getElementById('sb-align');if(sa) sa.style.width=Math.round(d.alignment)+'%';
  const sba=document.getElementById('sb-balance');if(sba) sba.style.width=Math.round(d.balance)+'%';
}
function updateAlertBanner(feedback){
  const banner=document.getElementById('alert-banner'),text=document.getElementById('alert-text'),icon=document.getElementById('alert-icon');
  if(!feedback.length||!banner) return;
  const top=feedback[0];const icons={success:'✅',warning:'⚠️',error:'🚨',info:'⚡'};
  text.textContent=top.msg;icon.textContent=icons[top.severity]||'⚡';banner.className='alert-banner '+top.severity;
}
function updatePulse(feedback){
  const dot=document.getElementById('pulse-dot'),label=document.getElementById('pulse-label');
  const hasError=feedback.some(f=>f.severity==='error'),hasSuccess=feedback.some(f=>f.severity==='success');
  if(hasError){dot.className='pulse-dot error';label.textContent='FIX FORM';label.style.color='#ef4444';}
  else if(hasSuccess){dot.className='pulse-dot active';label.textContent='PERFECT FORM';label.style.color='#10b981';}
  else{dot.className='pulse-dot active';label.textContent='TRACKING';label.style.color='#00ffcc';}
}

// ── MUSCLE HEATMAP ─────────────────────────────────────────────────
function updateHeatmap(exerciseKey){
  const ex=EXERCISES[exerciseKey];if(!ex||!ex.muscles) return;
  const m=ex.muscles;
  const map={torso:'hm-torso',leftArm:'hm-left-arm',rightArm:'hm-right-arm',leftLeg:'hm-left-leg',rightLeg:'hm-right-leg',glutes:'hm-glutes'};
  const mapM={torso:'hm-torso-m',leftArm:'hm-left-arm-m',rightArm:'hm-right-arm-m',leftLeg:'hm-left-leg-m',rightLeg:'hm-right-leg-m',glutes:'hm-glutes-m'};
  Object.keys(map).forEach(k=>{
    const val=m[k]||0;
    const color=val>0.7?`rgba(239,68,68,${val})`:(val>0.3?`rgba(245,158,11,${val})`:`rgba(255,255,255,0.05)`);
    const el=document.getElementById(map[k]);if(el) el.setAttribute('fill',color);
    const elm=document.getElementById(mapM[k]);if(elm) elm.setAttribute('fill',color);
  });
  const label=document.getElementById('heatmap-label');
  if(label){const active=Object.entries(m).filter(([,v])=>v>0.5).map(([k])=>k.replace(/([A-Z])/g,' $1').trim()).join(', ');label.textContent=active||'Low intensity';}
}

// ── SESSION HISTORY ────────────────────────────────────────────────
function saveSession(){
  const elapsed=state.startTime?Math.floor((Date.now()-state.startTime)/1000):0;
  const session={id:Date.now(),exercise:state.exercise,exerciseName:EXERCISES[state.exercise]?.name||state.exercise,score:state.bestScore,reps:state.repCount,duration:elapsed,date:new Date().toLocaleDateString(),time:new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'})};
  db.sessions.unshift(session);if(db.sessions.length>50) db.sessions.pop();
  db.totalSessions++;db.totalReps=Math.max(db.totalReps,state.totalReps);
  const today=new Date().toDateString();
  if(db.lastDate!==today){
    const yesterday=new Date(Date.now()-86400000).toDateString();
    db.streak=db.lastDate===yesterday?db.streak+1:1;
    db.lastDate=today;
  }
  if(!db.exercisesTried.includes(state.exercise)){db.exercisesTried.push(state.exercise);}
  saveStorage(db);
  syncSession(session); // Sync session to Supabase
  syncProfile(); // Update profile stats in cloud
  updateStreakUI(); checkAchievements();
}
function renderHistoryList(targetId){
  const el=document.getElementById(targetId);if(!el) return;
  if(!db.sessions.length){el.innerHTML='<div class="log-empty">No sessions yet</div>';return;}
  const icons={squat:'🏋️',pushup:'💪',lunge:'🦵',plank:'⚡',bicep_curl:'🔥',shoulder_press:'🏆',deadlift:'💎'};
  el.innerHTML=db.sessions.slice(0,15).map(s=>{
    let grade='A+';if(s.score<50)grade='F';else if(s.score<60)grade='D';else if(s.score<70)grade='C';else if(s.score<80)grade='B';else if(s.score<90)grade='A';
    const m=Math.floor(s.duration/60),sec=s.duration%60;
    return`<div class="history-item"><div class="hist-icon">${icons[s.exercise]||'🏋️'}</div><div class="hist-info"><div class="hist-exercise">${s.exerciseName}</div><div class="hist-meta">${s.date} · ${s.time} · ${s.reps} reps · ${m}:${String(sec).padStart(2,'0')}</div></div><div style="text-align:right"><div class="hist-score">${s.score}%</div><div class="hist-grade">${grade}</div></div></div>`;
  }).join('');
}
function renderHistoryChart(canvasId){
  const canvas=document.getElementById(canvasId);if(!canvas) return;
  const scores=db.sessions.slice(0,10).reverse().map(s=>s.score);
  const labels=db.sessions.slice(0,10).reverse().map(s=>s.exerciseName.substring(0,3).toUpperCase());
  if(window[canvasId+'_chart']) window[canvasId+'_chart'].destroy();
  window[canvasId+'_chart']=new Chart(canvas,{
    type:'line',
    data:{labels,datasets:[{label:'Form Score',data:scores,borderColor:'#00ffcc',backgroundColor:'rgba(0,255,204,0.1)',borderWidth:2,pointBackgroundColor:'#00ffcc',pointRadius:4,tension:0.4,fill:true}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#94a3b8',font:{size:10}},grid:{color:'rgba(255,255,255,0.05)'}},y:{min:0,max:100,ticks:{color:'#94a3b8',font:{size:10}},grid:{color:'rgba(255,255,255,0.05)'}}}}
  });
}
function openHistory(){ renderHistoryList('history-list'); renderHistoryChart('history-chart'); document.getElementById('history-modal').style.display='flex'; }
function closeHistory(){ document.getElementById('history-modal').style.display='none'; }
function clearHistory(){ if(confirm('Clear all session history?')){ db.sessions=[]; saveStorage(db); renderHistoryList('history-list'); showToast('History cleared'); } }

// ── ACHIEVEMENTS ───────────────────────────────────────────────────
function checkAchievements(){
  const stats={totalReps:db.totalReps,bestScore:state.bestScore,streak:db.streak,fastestSet:db.fastestSet,exercisesTried:db.exercisesTried.length,aiCoachUses:db.aiCoachUses,hasRecorded:db.hasRecorded,hasShared:db.hasShared,totalSessions:db.totalSessions};
  ACHIEVEMENTS_DEF.forEach(ach=>{
    if(!db.unlockedAchievements.includes(ach.id)&&ach.check(stats)){
      db.unlockedAchievements.push(ach.id);saveStorage(db);showAchievementPopup(ach);
    }
  });
  renderAchievements();
}
function showAchievementPopup(ach){
  const popup=document.getElementById('ach-popup');
  document.getElementById('ach-pop-icon').textContent=ach.icon;
  document.getElementById('ach-pop-name').textContent=ach.name;
  popup.classList.add('show');playSuccessSound();
  setTimeout(()=>popup.classList.remove('show'),3500);
}
function renderAchievements(){
  ['achievements-grid','achievements-grid-m'].forEach(id=>{
    const el=document.getElementById(id);if(!el) return;
    el.innerHTML=ACHIEVEMENTS_DEF.map(a=>{
      const unlocked=db.unlockedAchievements.includes(a.id);
      return`<div class="ach-item${unlocked?' unlocked':''}" title="${a.desc}"><div class="ach-icon">${a.icon}</div><div class="ach-name">${a.name}</div><div class="ach-shine"></div></div>`;
    }).join('');
  });
}

// ── WORKOUT PROGRAMS ───────────────────────────────────────────────
function renderPrograms(){
  ['program-list','program-list-m'].forEach(id=>{
    const el=document.getElementById(id);if(!el) return;
    el.innerHTML=PROGRAMS.map(p=>{
      const prog=db.programProgress[p.id]||0;
      const pct=Math.round((prog/(p.weeks*7))*100);
      const isActive=db.activeProgram===p.id;
      return`<div class="prog-card${isActive?' active-prog':''}" onclick="selectProgram('${p.id}')"><div class="prog-header"><span class="prog-name" style="color:${p.color}">${p.name}</span><span class="prog-week">${p.weeks}wk</span></div><div class="prog-desc">${p.desc}</div><div class="prog-progress"><div class="prog-progress-fill" style="width:${pct}%;background:${p.color}"></div></div></div>`;
    }).join('');
  });
}
function selectProgram(id){
  db.activeProgram=db.activeProgram===id?null:id;
  saveStorage(db);renderPrograms();
  if(db.activeProgram){
    const p=PROGRAMS.find(x=>x.id===id);
    showToast(`Program: ${p.name} ✓`);
    if(p.exercises[0]) selectExercise(p.exercises[0]);
  }
}

// Profile switching replaced by unified Cloud Sync (Google-based)
function updateStreakUI(){ setEl('streak-desktop',db.streak+'🔥'); }


// ── SHARE CARD ─────────────────────────────────────────────────────
function openShareCard(){
  const elapsed=state.startTime?Math.floor((Date.now()-state.startTime)/1000):0;
  const m=Math.floor(elapsed/60),s=elapsed%60;
  setEl('share-score',state.bestScore+'%');
  setEl('share-reps',state.repCount);
  setEl('share-time',`${m}:${String(s).padStart(2,'0')}`);
  setEl('share-date',new Date().toLocaleDateString('en-US',{weekday:'long',month:'short',day:'numeric'}));
  setEl('share-exercise-badge',EXERCISES[state.exercise]?.name||'Workout');
  document.getElementById('share-modal').style.display='flex';
  db.hasShared=true;saveStorage(db);checkAchievements();
}
function closeShareCard(){ document.getElementById('share-modal').style.display='none'; }

function downloadShareCard(){
  const canvas=document.createElement('canvas');
  canvas.width=600;canvas.height=320;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='#04060f';ctx.fillRect(0,0,600,320);
  ctx.strokeStyle='rgba(0,255,204,0.04)';ctx.lineWidth=1;
  for(let x=0;x<600;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,320);ctx.stroke();}
  for(let y=0;y<320;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(600,y);ctx.stroke();}
  ctx.strokeStyle='rgba(0,255,204,0.3)';ctx.lineWidth=2;ctx.strokeRect(1,1,598,318);
  ctx.fillStyle='#00ffcc';ctx.font='bold 28px monospace';ctx.textAlign='center';ctx.fillText('⚡ BIOMECH AI',300,60);
  const stats=[['FORM SCORE',state.bestScore+'%'],[EXERCISES[state.exercise]?.name||'EXERCISE',state.repCount+' REPS'],['DURATION',`${Math.floor((state.startTime?(Date.now()-state.startTime)/1000:0)/60)}m`]];
  stats.forEach(([label,val],i)=>{
    const x=100+i*200;
    ctx.fillStyle='#00ffcc';ctx.font='bold 40px monospace';ctx.textAlign='center';ctx.fillText(val,x,160);
    ctx.fillStyle='#94a3b8';ctx.font='12px monospace';ctx.fillText(label,x,185);
  });
  ctx.fillStyle='rgba(0,255,204,0.15)';ctx.beginPath();ctx.roundRect(180,205,240,36,18);ctx.fill();
  ctx.fillStyle='#00ffcc';ctx.font='13px monospace';ctx.textAlign='center';ctx.fillText('ai-biomech.web.app',300,228);
  ctx.fillStyle='rgba(0,255,204,0.35)';ctx.font='10px monospace';ctx.textAlign='center';ctx.fillText('© 2026 Krish Joshi · All Rights Reserved',300,295);
  const link=document.createElement('a');
  link.download=`biomech-share-${Date.now()}.png`;
  link.href=canvas.toDataURL('image/png');link.click();
  showToast('Share card downloaded! 🔗');
}

// ── TIMER ──────────────────────────────────────────────────────────
let timerInterval=null;
function startTimer(){
  state.startTime=Date.now();
  timerInterval=setInterval(()=>{
    const e=Math.floor((Date.now()-state.startTime)/1000);
    const t=`${Math.floor(e/60)}:${String(e%60).padStart(2,'0')}`;
    setEl('hud-timer',t);setEl('stat-time',t);setEl('stat-time-m',t);
  },1000);
}
function stopTimer(){ if(timerInterval){clearInterval(timerInterval);timerInterval=null;} }

// ── SESSION CONTROL ────────────────────────────────────────────────
async function startSession(preferredDeviceId) {
  try {
    const video=document.getElementById('webcam'),canvas=document.getElementById('output-canvas');
    state.videoEl=video;state.canvasEl=canvas;state.ctx=canvas.getContext('2d');

    // Build video constraints — use selected camera or facing mode
    const videoConstraints = {
      width:{ideal:1280},height:{ideal:720},
      frameRate:{ideal:30}
    };
    if (preferredDeviceId) {
      videoConstraints.deviceId = {exact: preferredDeviceId};
    } else if (state.activeCameraId) {
      videoConstraints.deviceId = {exact: state.activeCameraId};
    } else {
      videoConstraints.facingMode = CONFIG.cameraFacing;
    }

    const stream=await navigator.mediaDevices.getUserMedia({video:videoConstraints,audio:false});
    state.cameraStream=stream;

    // After getting stream, enumerate cameras so we have labels
    await loadAvailableCameras();

    video.srcObject=stream;video.style.display='block';
    await new Promise(res=>{video.onloadedmetadata=res;});
    const pose=new Pose({locateFile:f=>`https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}`});
    pose.setOptions({modelComplexity:CONFIG.modelComplexity,smoothLandmarks:true,enableSegmentation:false,minDetectionConfidence:CONFIG.minDetectionConf,minTrackingConfidence:CONFIG.minTrackingConf});
    pose.onResults(onResults);
    const camera=new Camera(video,{onFrame:async()=>{await pose.send({image:video});},width:1280,height:720});
    await camera.start();
    state.pose=pose;state.camera=camera;state.sessionActive=true;
    state.scoreHistory=[];state.repTimestamps=[];state.sessionStartReps=state.totalReps;
    document.getElementById('cam-overlay').style.display='none';
    document.getElementById('live-hud').style.display='flex';
    document.getElementById('btn-start').disabled=true;
    document.getElementById('btn-stop').disabled=false;

    // Apply zoom if set
    applyZoom();

    // Enable camera control buttons
    document.querySelectorAll('.cam-ctrl-btn').forEach(b => b.disabled = false);

    setHTML('log-list','');
    startTimer();addLog('Session started','good');
    showToast('Session Started! 🚀');playSuccessSound();
    if(db.activeProgram){db.programProgress[db.activeProgram]=(db.programProgress[db.activeProgram]||0)+1;saveStorage(db);renderPrograms();}
  }catch(err){
    showToast('Camera error: '+err.message,'error');
    updateAlertBanner([{msg:'Camera access denied — check permissions',severity:'error'}]);
  }
}

function stopSession(){
  state.sessionActive=false;
  if(isRecording) stopRecording();
  if(state.camera){state.camera.stop();state.camera=null;}
  if(state.pose){state.pose.close();state.pose=null;}
  const video=document.getElementById('webcam');
  if(video.srcObject){video.srcObject.getTracks().forEach(t=>t.stop());video.srcObject=null;}
  video.style.display='none';
  if(state.ctx&&state.canvasEl) state.ctx.clearRect(0,0,state.canvasEl.width,state.canvasEl.height);
  document.getElementById('cam-overlay').style.display='flex';
  document.getElementById('live-hud').style.display='none';
  document.getElementById('btn-start').disabled=false;
  document.getElementById('btn-stop').disabled=true;

  // Disable camera controls
  document.querySelectorAll('.cam-ctrl-btn:not(#btn-expand):not(#btn-fullscreen)').forEach(b => b.disabled = true);

  const pd=document.getElementById('pulse-dot');if(pd) pd.className='pulse-dot';
  const pl=document.getElementById('pulse-label');if(pl){pl.textContent='READY';pl.style.color='';}
  stopTimer();saveSession();addLog('Session saved','good');
  if(state.repCount>0) showToast(`Session saved! ${state.repCount} reps · ${state.bestScore}% best`);
}
function resetSession(){
  state.repCount=0;state.repState='up';state.bestScore=100;state.corrections=0;state.formScore=100;
  ['rep-number','rep-number-m'].forEach(id=>setEl(id,'0'));
  document.getElementById('hdr-reps').textContent='0';
  ['stat-total-reps','stat-reps-m','stat-alerts','stat-alerts-m'].forEach(id=>setEl(id,'0'));
  ['stat-best','stat-best-m'].forEach(id=>setEl(id,'100%'));
  updateRepStateUI('up');updateFormScore(100,{depth:100,alignment:100,balance:100});
  showToast('Session Reset ↺');addLog('Reset','good');
}

// ── EXERCISE SELECT ────────────────────────────────────────────────
function selectExercise(key){
  if(!EXERCISES[key]) return;
  state.exercise=key;state.repCount=0;state.repState='up';
  document.querySelectorAll('.ex-card').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll(`[data-ex="${key}"]`).forEach(b=>b.classList.add('active'));
  const ex=EXERCISES[key];
  ['inst-text','inst-text-m'].forEach(id=>setEl(id,ex.instruction));
  const tipsHTML=ex.tips.map(t=>`<div class="inst-tip">${t}</div>`).join('');
  ['inst-tips','inst-tips-m'].forEach(id=>setHTML(id,tipsHTML));
  setEl('hud-exercise',ex.name.toUpperCase());
  ['rep-number','rep-number-m'].forEach(id=>setEl(id,'0'));
  document.getElementById('hdr-reps').textContent='0';
  updateRepStateUI('up');updateHeatmap(key);
  addLog(`Exercise: ${ex.name}`,'good');
  if(!db.exercisesTried.includes(key)){db.exercisesTried.push(key);saveStorage(db);}
}

// ── SCREENSHOT ─────────────────────────────────────────────────────
function takeScreenshot(){
  const canvas=document.getElementById('output-canvas');if(!canvas) return;
  const link=document.createElement('a');link.download=`biomech-${Date.now()}.png`;link.href=canvas.toDataURL('image/png');link.click();
  showToast('Screenshot saved! 📸');
}

// ── AI COACH ───────────────────────────────────────────────────────
function openAICoach(){
  const m=document.getElementById('ai-modal');
  if(!m) return;
  m.style.display='flex';
  const ex = EXERCISES[state.exercise]||{name:state.exercise};
  setHTML('ai-ex-chip', `Exercise: ${ex.name}`);
  setHTML('ai-score-chip', `Score: ${state.formScore}%`);
  setHTML('ai-rep-chip', `Reps: ${state.repCount}`);
}
function closeAICoach(){ document.getElementById('ai-modal').style.display='none'; }


async function runGeminiAnalysis(){
  db.aiCoachUses++;saveStorage(db);checkAchievements();
  const area=document.getElementById('ai-response-area'),btn=document.getElementById('ai-analyze-btn');
  btn.disabled=true;
  setHTML('ai-response-area',`<div class="ai-loading-wrap" style="text-align:center;padding:40px;"><div class="ai-spinner" style="border:3px solid rgba(255,255,255,0.1);border-top:3px solid var(--cyan);border-radius:50%;width:30px;height:30px;animation:spin 1s linear infinite;margin:0 auto 10px;"></div><div class="ai-loading-text" style="color:var(--cyan);font-family:'Michroma',sans-serif;font-size:0.7rem;">GEMINI ANALYZING...</div></div>`);
  
  const ex=EXERCISES[state.exercise]||{};
  const prompt=`You are an elite AI biomechanical coach.
Exercise: ${ex.name||state.exercise} | Score: ${state.formScore}/100 | Reps: ${state.repCount}
Joint Angles: ${Object.entries(state.lastAngles).map(([k,v])=>`${k.replace(/_/g,' ')}: ${v}°`).join(', ')||'No data yet'}
Live Feedback: ${state.lastFeedback.map(f=>f.msg).join(', ')||'None'}
Session History: ${db.sessions.length} sessions, ${db.totalReps} total reps, ${db.streak} day streak

Respond concisely:
**FORM ASSESSMENT** (2 sentences, cite specific angles)
**TOP 3 CORRECTIONS** (biomechanical reasoning)
**MUSCLE ACTIVATION TIP** (one cue)
**PROGRESSIVE OVERLOAD** (one suggestion based on history)
**MOTIVATIONAL PUSH** (one energetic sentence)

Max 280 words. Use anatomical terms.`;

  try{
    // Using direct Google Gemini API with the hardcoded key
    const url = `https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=${state.geminiKey}`;
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }]
      })
    });

    if(!resp.ok){
      const e=await resp.json();
      throw new Error(e?.error?.message||e?.error||`HTTP ${resp.status}`);
    }
    const data=await resp.json();
    const text=data?.candidates?.[0]?.content?.parts?.[0]?.text||'No response.';
    
    // Update live toast summary
    const toastText = document.getElementById('ai-toast-text');
    const toastWrap = document.getElementById('cam-ai-toast');
    if(toastText && toastWrap) {
      toastText.textContent = text.split('\n')[0].replace(/\*\*/g, ''); 
      toastWrap.style.display = 'flex';
      setTimeout(() => { toastWrap.style.display = 'none'; }, 8000);
    }

    const formatted=text.replace(/\*\*(.*?)\*\*/g,'<strong style="color:#a78bfa;font-family:\'Michroma\',monospace;font-size:11px;letter-spacing:2px;">$1</strong>').replace(/\n/g,'<br>');
    setHTML('ai-response-area',`<div class="ai-text" style="animation:fadeIn 0.5s ease-out;">${formatted}</div>`);
    addLog('AI Analysis complete','good');playSuccessSound();
  }catch(err){
    setHTML('ai-response-area',`<div class="ai-text" style="color:#f87171;padding:20px;text-align:center;">❌ ${err.message}<br><small style="opacity:0.6;font-size:0.6rem;">Double check the hardcoded Gemini API key is active.</small></div>`);
    showToast('AI Error: ' + err.message, 'error');
  }
  finally{btn.disabled=false;}
}

async function generatePerformanceReport() {
  const btn = document.getElementById('ai-report-btn');
  btn.disabled = true;
  setHTML('ai-response-area', `<div class="ai-loading-wrap" style="text-align:center;padding:40px;"><div class="ai-spinner" style="border:3px solid rgba(255,255,255,0.1);border-top:3px solid var(--purple);border-radius:50%;width:30px;height:30px;animation:spin 1s linear infinite;margin:0 auto 10px;"></div><div class="ai-loading-text" style="color:var(--purple);font-family:'Michroma',sans-serif;font-size:0.7rem;">GENERATING PERFORMANCE AUDIT...</div></div>`);

  const summaryData = {
    totalReps: db.totalReps,
    totalSessions: db.sessions.length,
    streak: db.streak,
    topExercise: Object.entries(db.programProgress).sort((a,b)=>b[1]-a[1])[0]?.[0] || 'None',
    recentScores: db.sessions.slice(-5).map(s=>s.score),
    unlockedAchievements: db.unlockedAchievements.length
  };

  const prompt = `Generate a high-level Athletic Performance Report for the user.
Data: ${JSON.stringify(summaryData)}
User Identity: ${db.googleUser ? db.googleUser.name : 'Guest'}

Structure:
**ATHLETIC AUDIT SUMMARY** (Professional analysis of their effort)
**KEY STRENGTHS** (Based on streaks/reps)
**AREAS FOR IMPROVEMENT** (Constructive)
**NEXT 7-DAY GOAL** (Specific, challenging)
**COACH'S VERDICT** (One powerful concluding sentence)

Keep it elite, motivational, and technical.`;

  try {
    const url = `https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=${state.geminiKey}`;
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
    });
    
    const data = await resp.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || 'Unable to generate report.';
    const formatted = text.replace(/\*\*(.*?)\*\*/g,'<strong style="color:var(--purple);font-family:\'Michroma\',monospace;font-size:11px;">$1</strong>').replace(/\n/g,'<br>');
    
    setHTML('ai-response-area', `<div class="ai-report-wrap" style="color:#e2e8f0;padding:5px;">${formatted}</div>`);
    showToast('Performance Report Generated! 📈');
  } catch(err) {
    setHTML('ai-response-area', `<div style="color:#f87171;text-align:center;padding:20px;">Failed to generate report: ${err.message}</div>`);
  } finally {
    btn.disabled = false;
  }
}

// ── SETTINGS ───────────────────────────────────────────────────────
function toggleSettings(){ 
  const m=document.getElementById('settings-modal');
  const isOpening = m.style.display==='none';
  m.style.display=isOpening?'flex':'none'; 
  
  if (isOpening) {
    // Populate current values
    document.getElementById('skeleton-style').value = CONFIG.skeletonStyle;
    document.getElementById('show-angles').checked = CONFIG.showAngles;
    document.getElementById('show-skeleton').checked = CONFIG.showSkeleton;
    document.getElementById('voice-feedback').checked = CONFIG.voiceFeedback;
    document.getElementById('audio-cues').checked = CONFIG.audioCues;
    document.getElementById('conf-slider').value = Math.round(CONFIG.minDetectionConf * 100);
    document.getElementById('conf-val').textContent = Math.round(CONFIG.minDetectionConf * 100) + '%';
    
    // Load Gemini key if available
    const keyInput = document.getElementById('gemini-key');
    if (keyInput) keyInput.value = state.geminiKey || '';
  }
}
function closeSettings(){ document.getElementById('settings-modal').style.display='none'; }
function toggleHelp(){ const m=document.getElementById('help-modal');m.style.display=m.style.display==='none'?'flex':'none'; }
function saveSettings(){
  CONFIG.skeletonStyle=document.getElementById('skeleton-style').value;
  CONFIG.showAngles=document.getElementById('show-angles').checked;
  CONFIG.showSkeleton=document.getElementById('show-skeleton').checked;
  CONFIG.voiceFeedback=document.getElementById('voice-feedback').checked;
  CONFIG.audioCues=document.getElementById('audio-cues').checked;
  const conf=parseInt(document.getElementById('conf-slider').value);
  CONFIG.minDetectionConf=conf/100;CONFIG.minTrackingConf=conf/100;
  
  saveStorage(db);
  closeSettings();
  showToast('Settings Saved ✓');
}

// ── VOICE SPEECH OUTPUT ────────────────────────────────────────────
function speak(text){ if(!window.speechSynthesis) return; const u=new SpeechSynthesisUtterance(text);u.rate=1.1;u.pitch=1;u.volume=0.8;window.speechSynthesis.speak(u); }

// ── ACTIVITY LOG ───────────────────────────────────────────────────
function addLog(msg,type='good'){
  const log=document.getElementById('log-list');if(!log) return;
  const empty=log.querySelector('.log-empty');if(empty) log.innerHTML='';
  const time=new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  const item=document.createElement('div');item.className=`log-item ${type}`;
  item.innerHTML=`<span>${msg}</span><span class="log-time">${time}</span>`;
  log.prepend(item);if(log.children.length>15) log.removeChild(log.lastChild);
}

// ── TOAST ──────────────────────────────────────────────────────────
let toastTimer=null;
function showToast(msg,type='success'){
  const t=document.getElementById('toast');
  t.textContent=msg;
  t.style.background=type==='error'?'rgba(239,68,68,0.9)':type==='info'?'rgba(124,58,237,0.9)':'rgba(16,185,129,0.9)';
  t.classList.add('show');if(toastTimer) clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.classList.remove('show'),2500);
}

// ── BACKGROUND ─────────────────────────────────────────────────────


// ── HELPERS ────────────────────────────────────────────────────────
function setEl(id,val){ const e=document.getElementById(id);if(e) e.textContent=val; }
function setHTML(id,html){ const e=document.getElementById(id);if(e) e.innerHTML=html; }
function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

// ── SETTINGS SLIDER INIT ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  const sl=document.getElementById('conf-slider'),vl=document.getElementById('conf-val');
  if(sl&&vl) sl.addEventListener('input',()=>{vl.textContent=sl.value+'%';});

  // Camera select change handler
  const camSel = document.getElementById('camera-select');
  if (camSel) {
    camSel.addEventListener('change', (e) => {
      state.activeCameraId = e.target.value;
      if (state.sessionActive) switchCamera(e.target.value);
    });
  }

  // Close camera guide on outside click
  document.addEventListener('click', (e) => {
    const guide = document.getElementById('cam-guide-popup');
    if (guide && guide.classList.contains('show')) {
      if (!guide.contains(e.target) && !e.target.closest('#btn-cam-guide')) {
        guide.classList.remove('show');
      }
    }
  });

  // Setup pinch-to-zoom for mobile
  setupPinchZoom();
});

// ── FULLSCREEN CHANGE HANDLER ──────────────────────────────────────
document.addEventListener('fullscreenchange', () => {
  const btn = document.getElementById('btn-fullscreen');
  if (btn) {
    btn.textContent = document.fullscreenElement ? '⛶' : '⛶';
    btn.title = document.fullscreenElement ? 'Exit Fullscreen' : 'Fullscreen';
  }
  // When entering fullscreen, hide the browser chrome overlap
  const frame = document.querySelector('.cam-frame');
  if (document.fullscreenElement && frame) {
    frame.style.borderRadius = '0';
  } else if (frame) {
    frame.style.borderRadius = '';
  }
});

// ── DYNAMIC BACKGROUND ─────────────────────────────────────────────
function initBackground() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;
  
  const particles = [];
  const numParticles = Math.floor((width * height) / 15000);
  
  for(let i = 0; i < numParticles; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 2 + 0.5,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      color: Math.random() < 0.5 ? 'rgba(0, 255, 204, 0.4)' : 'rgba(124, 58, 237, 0.4)'
    });
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    
    // Subtle Cyberpunk Grid
    ctx.strokeStyle = 'rgba(0, 255, 204, 0.02)';
    ctx.lineWidth = 1;
    const gridSize = 60;
    const offsetX = (Date.now() / 60) % gridSize;
    const offsetY = (Date.now() / 60) % gridSize;
    
    ctx.beginPath();
    for (let x = -gridSize; x < width + gridSize; x += gridSize) {
      ctx.moveTo(x + offsetX, 0);
      ctx.lineTo(x + offsetX, height);
    }
    for (let y = -gridSize; y < height + gridSize; y += gridSize) {
      ctx.moveTo(0, y + offsetY);
      ctx.lineTo(width, y + offsetY);
    }
    ctx.stroke();

    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();
    });

    particles.forEach((p1, i) => {
      for(let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
        if (dist < 130) {
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          let op = (1 - dist / 130) * 0.35;
          ctx.strokeStyle = p1.color.replace('0.4', op.toFixed(2));
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    });

    requestAnimationFrame(draw);
  }

  draw();

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    // Optionally update numParticles if resize is significant
  });
}

// ══════════════════════════════════════════════════════════════════
//  APP INIT SEQUENCE
// ══════════════════════════════════════════════════════════════════

async function launchSplash(){
  const splash=document.getElementById('splash');
  const fill=document.getElementById('loading-fill');
  const loadTxt=document.getElementById('loading-text');
  const ssTf=document.getElementById('ss-tf');
  const ssMp=document.getElementById('ss-mp');
  const ssCam=document.getElementById('ss-cam');

  splash.style.display='flex';

  loadTxt.textContent='Loading libraries...';fill.style.width='15%';await sleep(400);ssTf.textContent='✓';
  loadTxt.textContent='Loading Gemini key...';fill.style.width='35%';
  await loadGeminiKey();await sleep(300);
  loadTxt.textContent='Initializing Pose Model...';fill.style.width='55%';await sleep(500);ssMp.textContent='✓';
  loadTxt.textContent='Loading your data...';fill.style.width='70%';
  db=getDB();renderAchievements();renderPrograms();updateStreakUI();
  updateHeatmap('squat');await sleep(300);
  loadTxt.textContent='Checking Camera...';fill.style.width='85%';
  try{
    const d=await navigator.mediaDevices.enumerateDevices();
    const cams = d.filter(x=>x.kind==='videoinput');
    ssCam.textContent=cams.length+'✓';
    state.availableCameras = cams;
  }catch(e){ssCam.textContent='?';}
  await sleep(400);
  loadTxt.textContent='Welcome, '+(db.googleUser?.given||'Athlete')+'!';fill.style.width='100%';await sleep(600);

  splash.classList.add('hidden');
  setTimeout(()=>{ splash.style.display='none'; },800);

  document.getElementById('app').classList.remove('hidden');
  updateUserPill();

  // Populate camera selector after app loads
  await loadAvailableCameras();
}

async function initApp(){
  console.log("BioMech AI Initializing App...");
  initBackground();
  if(db && db.googleUser && db.googleUser.sub){
    document.getElementById('login-screen').classList.add('hidden');
    setTimeout(()=>{ document.getElementById('login-screen').style.display='none'; },0);
    await launchSplash();
    return;
  }
  setTimeout(()=>{
    if(!document.querySelector('.g_id_signin iframe')){
      const fb=document.getElementById('google-fallback-btn');
      if(fb) fb.style.display='flex';
    }
  }, 3000);
}

// Kick everything off
initApp();