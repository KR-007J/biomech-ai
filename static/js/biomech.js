/* ══════════════════════════════════════════════════════════════════
   BioMech AI — Core Engine v2.1
   MediaPipe Pose + Cosine Rule + Gemini 2.5 Flash
   Responsive: Desktop 3-col | Mobile tab-navigation
   API key auto-loaded from server — no user input needed
══════════════════════════════════════════════════════════════════ */

'use strict';

// ── Configuration ──────────────────────────────────────────────────
const CONFIG = {
  minDetectionConf: 0.7,
  minTrackingConf:  0.7,
  modelComplexity:  1,
  skeletonStyle:    'neon',
  showAngles:       true,
  showSkeleton:     true,
  voiceFeedback:    false,
};

// ── Exercise Database ──────────────────────────────────────────────
const EXERCISES = {
  squat: {
    name: 'Squat',
    instruction: 'Stand with feet shoulder-width apart. Bend knees to 90°. Keep torso upright throughout.',
    tips: ['Face camera at full body distance', 'Point toes slightly outward', 'Keep chest up, core tight'],
    repJoint: 'left_knee', repDownThreshold: 110, repUpThreshold: 160,
    checkpoints: {
      knee:    { ideal: 90,  tolerance: 18, label: 'Knee Depth',   weight: 40 },
      hip:     { ideal: 90,  tolerance: 25, label: 'Hip Hinge',    weight: 30 },
      balance: { ideal: 0,   tolerance: 15, label: 'Knee Balance', weight: 30 },
    }
  },
  pushup: {
    name: 'Push-Up',
    instruction: 'Keep body in straight line. Lower until elbows reach 90°. Full range of motion.',
    tips: ['Hands slightly wider than shoulders', 'Squeeze glutes and core', 'Look at floor 30cm ahead'],
    repJoint: 'left_elbow', repDownThreshold: 110, repUpThreshold: 155,
    checkpoints: {
      elbow:     { ideal: 90,  tolerance: 18, label: 'Elbow Bend', weight: 50 },
      alignment: { ideal: 180, tolerance: 12, label: 'Body Line',  weight: 50 },
    }
  },
  lunge: {
    name: 'Lunge',
    instruction: 'Step forward. Both knees at 90°. Front knee directly over ankle.',
    tips: ['Keep torso tall', 'Front knee tracks over second toe', 'Push back through front heel'],
    repJoint: 'right_knee', repDownThreshold: 110, repUpThreshold: 160,
    checkpoints: {
      front_knee: { ideal: 90, tolerance: 18, label: 'Front Knee',     weight: 45 },
      back_knee:  { ideal: 90, tolerance: 18, label: 'Back Knee',      weight: 35 },
      torso:      { ideal: 90, tolerance: 25, label: 'Torso Upright',  weight: 20 },
    }
  },
  plank: {
    name: 'Plank',
    instruction: 'Straight line from head to heels. Engage core throughout. Hold position.',
    tips: ['Press floor away', 'Neutral spine — no sagging', 'Breathe steadily'],
    repJoint: null, repDownThreshold: 0, repUpThreshold: 0,
    checkpoints: {
      body: { ideal: 180, tolerance: 10, label: 'Body Straight', weight: 60 },
      hip:  { ideal: 180, tolerance: 10, label: 'Hip Level',     weight: 40 },
    }
  },
  bicep_curl: {
    name: 'Bicep Curl',
    instruction: 'Elbows close to torso. Full range: straight arm to full curl. Controlled descent.',
    tips: ["Don't swing body", 'Supinate wrist on the way up', 'Squeeze at the top'],
    repJoint: 'left_elbow', repDownThreshold: 130, repUpThreshold: 50,
    checkpoints: {
      curl_depth: { ideal: 40, tolerance: 20, label: 'Curl Depth',  weight: 60 },
      stability:  { ideal: 0,  tolerance: 10, label: 'Body Stable', weight: 40 },
    }
  },
  shoulder_press: {
    name: 'Shoulder Press',
    instruction: 'Press overhead to full extension. Elbows at 90° at start position.',
    tips: ['Core tight, slight forward lean', 'Full lockout at top', 'Control the descent'],
    repJoint: 'left_elbow', repDownThreshold: 100, repUpThreshold: 155,
    checkpoints: {
      elbow:   { ideal: 90,  tolerance: 20, label: 'Start Position', weight: 50 },
      lockout: { ideal: 175, tolerance: 10, label: 'Lockout',        weight: 50 },
    }
  },
  deadlift: {
    name: 'Deadlift',
    instruction: 'Hip hinge movement. Bar close to body. Neutral spine throughout.',
    tips: ['Brace core before lifting', 'Drive hips forward', 'Keep bar over mid-foot'],
    repJoint: 'left_hip', repDownThreshold: 70, repUpThreshold: 155,
    checkpoints: {
      hip_hinge:    { ideal: 45,  tolerance: 20, label: 'Hip Hinge',    weight: 45 },
      back_neutral: { ideal: 180, tolerance: 20, label: 'Back Neutral', weight: 55 },
    }
  }
};

// ── MediaPipe Landmark Indices ─────────────────────────────────────
const LM = {
  NOSE:0,LEFT_EYE:1,RIGHT_EYE:2,
  LEFT_SHOULDER:11,RIGHT_SHOULDER:12,
  LEFT_ELBOW:13,RIGHT_ELBOW:14,
  LEFT_WRIST:15,RIGHT_WRIST:16,
  LEFT_HIP:23,RIGHT_HIP:24,
  LEFT_KNEE:25,RIGHT_KNEE:26,
  LEFT_ANKLE:27,RIGHT_ANKLE:28,
  LEFT_HEEL:29,RIGHT_HEEL:30,
  LEFT_FOOT:31,RIGHT_FOOT:32,
};

// ── State ──────────────────────────────────────────────────────────
let state = {
  exercise:      'squat',
  sessionActive: false,
  repCount:      0,
  repState:      'up',
  formScore:     100,
  bestScore:     100,
  totalReps:     0,
  corrections:   0,
  startTime:     null,
  lastAngles:    {},
  lastFeedback:  [],
  frameCount:    0,
  lastFpsTime:   Date.now(),
  fps:           0,
  pose:          null,
  camera:        null,
  videoEl:       null,
  canvasEl:      null,
  ctx:           null,
  geminiKey:     '',   // auto-loaded from /api/config, never from user input
  scoreBreakdown: { depth:100, alignment:100, balance:100 },
};

// ── Skeleton Styles ────────────────────────────────────────────────
const SKELETON_STYLES = {
  neon:   { joint:'#00ffcc', bone:'#00ffcc', angle:'#00ffcc' },
  fire:   { joint:'#ff6b35', bone:'#ff6b35', angle:'#ff6b35' },
  matrix: { joint:'#00ff41', bone:'#00ff41', angle:'#00ff41' },
  purple: { joint:'#a78bfa', bone:'#a78bfa', angle:'#a78bfa' },
};

// ── Mobile Tab Navigation ──────────────────────────────────────────
let currentTab = 'camera';

function showTab(tab) {
  currentTab = tab;

  // Update nav tabs
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  const tabEl = document.getElementById(`tab-${tab}`);
  if (tabEl) tabEl.classList.add('active');

  // Show/hide mobile panels
  document.querySelectorAll('.mobile-panel').forEach(p => p.classList.remove('active'));

  if (tab === 'exercises') {
    document.getElementById('mobile-exercises').classList.add('active');
    // Hide center panel on mobile
    document.querySelector('.center-panel').style.display = 'none';
  } else if (tab === 'stats') {
    document.getElementById('mobile-stats').classList.add('active');
    document.querySelector('.center-panel').style.display = 'none';
  } else {
    // camera tab
    document.querySelector('.center-panel').style.display = '';
  }
}

// ── Auto-load Gemini Key from Backend ─────────────────────────────
async function loadGeminiKey() {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) throw new Error('endpoint unavailable');
    const data = await res.json();
    if (data.geminiKey) {
      state.geminiKey = data.geminiKey;
      console.log('✅ Gemini API key loaded from server');
    } else {
      console.warn('⚠️ GEMINI_API_KEY not set in Render environment variables');
    }
  } catch(err) {
    console.warn('⚠️ Could not fetch /api/config:', err.message);
  }
}

// ── Cosine Rule Angle Calculator ───────────────────────────────────
function calculateAngle(A, B, C) {
  const AB = Math.hypot(B[0]-A[0], B[1]-A[1]);
  const BC = Math.hypot(C[0]-B[0], C[1]-B[1]);
  const AC = Math.hypot(C[0]-A[0], C[1]-A[1]);
  if (AB===0 || BC===0) return 0;
  const cosB = Math.max(-1, Math.min(1, (AB*AB + BC*BC - AC*AC) / (2*AB*BC)));
  return Math.round(Math.acos(cosB) * (180/Math.PI));
}

function lmXY(lms, idx) { return [lms[idx].x, lms[idx].y]; }
function lmPX(lms, idx, w, h) { return [lms[idx].x*w, lms[idx].y*h]; }

// ── Exercise Analyzers ─────────────────────────────────────────────
function analyzeSquat(lms, w, h) {
  const angles = {}, feedback = [];
  let depthScore=100, alignScore=100, balScore=100;
  try {
    const LH=lmXY(lms,LM.LEFT_HIP), LK=lmXY(lms,LM.LEFT_KNEE), LA=lmXY(lms,LM.LEFT_ANKLE);
    const RH=lmXY(lms,LM.RIGHT_HIP), RK=lmXY(lms,LM.RIGHT_KNEE), RA=lmXY(lms,LM.RIGHT_ANKLE);
    const LS=lmXY(lms,LM.LEFT_SHOULDER);
    const lKnee=calculateAngle(LH,LK,LA), rKnee=calculateAngle(RH,RK,RA), lHip=calculateAngle(LS,LH,LK);
    const avgKnee=(lKnee+rKnee)/2, kneeDiff=Math.abs(lKnee-rKnee);
    angles.left_knee=lKnee; angles.right_knee=rKnee; angles.left_hip=lHip;
    if(avgKnee>155){feedback.push({msg:'⬇ Go Deeper — Bend Knees to 90°',severity:'warning'});depthScore=Math.max(0,100-(avgKnee-90)*1.5);}
    else if(avgKnee>=72&&avgKnee<=108){feedback.push({msg:'🎯 Perfect Squat Depth!',severity:'success'});}
    else if(avgKnee<60){feedback.push({msg:'⬆ Too Deep — Rise Slightly',severity:'warning'});depthScore=70;}
    else{depthScore=85;}
    if(lHip<45){feedback.push({msg:"❌ Keep Torso Upright — Don't Lean Forward",severity:'error'});alignScore=40;}
    else if(lHip<65){feedback.push({msg:'⚠ Less Forward Lean',severity:'warning'});alignScore=70;}
    if(kneeDiff>20){feedback.push({msg:'⚖ Balance Both Sides — Knee Asymmetry',severity:'warning'});balScore=Math.max(0,100-kneeDiff*2);}
  } catch(e){feedback.push({msg:'📷 Show Full Body in Frame',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:0,balance:0}};}
  return{angles,feedback,score:Math.round(depthScore*0.4+alignScore*0.35+balScore*0.25),breakdown:{depth:depthScore,alignment:alignScore,balance:balScore}};
}

function analyzePushup(lms, w, h) {
  const angles={}, feedback=[];
  let elbowScore=100, alignScore=100;
  try {
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LE=lmXY(lms,LM.LEFT_ELBOW),LW=lmXY(lms,LM.LEFT_WRIST);
    const RS=lmXY(lms,LM.RIGHT_SHOULDER),RE=lmXY(lms,LM.RIGHT_ELBOW),RW=lmXY(lms,LM.RIGHT_WRIST);
    const LH=lmXY(lms,LM.LEFT_HIP),LA=lmXY(lms,LM.LEFT_ANKLE);
    const lE=calculateAngle(LS,LE,LW),rE=calculateAngle(RS,RE,RW),bodyAngle=calculateAngle(LS,LH,LA);
    const avg=(lE+rE)/2;
    angles.left_elbow=lE; angles.right_elbow=rE; angles.body_alignment=bodyAngle;
    if(avg>155){feedback.push({msg:'⬇ Lower Your Chest Further!',severity:'warning'});elbowScore=Math.max(0,100-(avg-90)*1.2);}
    else if(avg>=72&&avg<=108){feedback.push({msg:'💪 Perfect Push-Up Depth!',severity:'success'});}
    if(bodyAngle<152){feedback.push({msg:'❌ Raise Hips — Keep Body Straight',severity:'error'});alignScore=30;}
    else if(bodyAngle>198){feedback.push({msg:'❌ Lower Hips — Stop Sagging',severity:'error'});alignScore=30;}
    else if(Math.abs(bodyAngle-180)<12){feedback.push({msg:'✓ Great Body Alignment',severity:'success'});}
  } catch(e){feedback.push({msg:'📷 Adjust Camera for Side View',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:0,balance:100}};}
  return{angles,feedback,score:Math.round(elbowScore*0.5+alignScore*0.5),breakdown:{depth:elbowScore,alignment:alignScore,balance:100}};
}

function analyzeLunge(lms,w,h){ return analyzeSquat(lms,w,h); }

function analyzePlank(lms, w, h) {
  const angles={}, feedback=[];
  let bodyScore=100, hipScore=100;
  try {
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LH=lmXY(lms,LM.LEFT_HIP),LA=lmXY(lms,LM.LEFT_ANKLE);
    const LE=lmXY(lms,LM.LEFT_ELBOW);
    const bodyLine=calculateAngle(LS,LH,LA), upperBody=calculateAngle(LE,LS,LH);
    angles.body_alignment=bodyLine; angles.hip_alignment=upperBody;
    const dev=Math.abs(bodyLine-180);
    if(dev>15){
      feedback.push({msg:bodyLine<165?'❌ Hips Too High — Lower Down':'❌ Hips Sagging — Engage Core',severity:'error'});
      bodyScore=Math.max(0,100-dev*4);
    }else if(dev<6){feedback.push({msg:'⚡ Perfect Plank Position!',severity:'success'});}
    else{feedback.push({msg:'⚠ Adjust Hip Height',severity:'warning'});bodyScore=75;}
  } catch(e){feedback.push({msg:'📷 Show Side Profile',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(bodyScore*0.7+hipScore*0.3),breakdown:{depth:bodyScore,alignment:hipScore,balance:100}};
}

function analyzeBicepCurl(lms, w, h) {
  const angles={}, feedback=[];
  let curlScore=100, stabScore=100;
  try {
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LE=lmXY(lms,LM.LEFT_ELBOW),LW=lmXY(lms,LM.LEFT_WRIST);
    const RS=lmXY(lms,LM.RIGHT_SHOULDER),RE=lmXY(lms,LM.RIGHT_ELBOW),RW=lmXY(lms,LM.RIGHT_WRIST);
    const lE=calculateAngle(LS,LE,LW),rE=calculateAngle(RS,RE,RW),avg=(lE+rE)/2;
    angles.left_elbow=lE; angles.right_elbow=rE;
    if(avg<35){feedback.push({msg:'🔥 Full Curl — Excellent Contraction!',severity:'success'});}
    else if(avg<70){feedback.push({msg:'✓ Good Curl Range',severity:'success'});curlScore=85;}
    else if(avg>150){feedback.push({msg:'↑ Start Curling Upward',severity:'info'});curlScore=60;}
    else{feedback.push({msg:'⬆ Curl Higher — Full Range of Motion!',severity:'warning'});curlScore=65;}
  } catch(e){feedback.push({msg:'📷 Face Camera — Arms Visible',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(curlScore*0.65+stabScore*0.35),breakdown:{depth:curlScore,alignment:stabScore,balance:100}};
}

function analyzeShoulderPress(lms, w, h) {
  const angles={}, feedback=[];
  let score=100;
  try {
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LE=lmXY(lms,LM.LEFT_ELBOW),LW=lmXY(lms,LM.LEFT_WRIST);
    const RS=lmXY(lms,LM.RIGHT_SHOULDER),RE=lmXY(lms,LM.RIGHT_ELBOW),RW=lmXY(lms,LM.RIGHT_WRIST);
    const lE=calculateAngle(LS,LE,LW),rE=calculateAngle(RS,RE,RW),avg=(lE+rE)/2;
    angles.left_elbow=lE; angles.right_elbow=rE;
    if(avg>160){feedback.push({msg:'🏆 Full Lockout — Perfect!',severity:'success'});}
    else if(avg<100){feedback.push({msg:'↑ Press to Full Extension',severity:'warning'});score=Math.max(0,100-(160-avg)*1.2);}
    else{feedback.push({msg:'↑ Press Higher for Full Extension',severity:'info'});score=75;}
  } catch(e){feedback.push({msg:'📷 Show Upper Body',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(score),breakdown:{depth:score,alignment:100,balance:100}};
}

function analyzeDeadlift(lms, w, h) {
  const angles={}, feedback=[];
  let score=100;
  try {
    const LS=lmXY(lms,LM.LEFT_SHOULDER),LH=lmXY(lms,LM.LEFT_HIP),LK=lmXY(lms,LM.LEFT_KNEE);
    const hipAngle=calculateAngle(LS,LH,LK);
    angles.left_hip=hipAngle;
    if(hipAngle>155){feedback.push({msg:'💎 Full Hip Extension — Excellent!',severity:'success'});}
    else if(hipAngle<50){feedback.push({msg:'⬆ Drive Hips Forward!',severity:'warning'});score=Math.max(0,100-(155-hipAngle));}
  } catch(e){feedback.push({msg:'📷 Show Full Side Profile',severity:'info'});return{angles,feedback,score:0,breakdown:{depth:0,alignment:100,balance:100}};}
  return{angles,feedback,score:Math.round(score),breakdown:{depth:score,alignment:100,balance:100}};
}

const ANALYZERS = {
  squat:analyzeSquat, pushup:analyzePushup, lunge:analyzeLunge,
  plank:analyzePlank, bicep_curl:analyzeBicepCurl,
  shoulder_press:analyzeShoulderPress, deadlift:analyzeDeadlift
};

// ── Skeleton Drawing ───────────────────────────────────────────────
const POSE_CONNECTIONS = [
  [LM.LEFT_SHOULDER,LM.RIGHT_SHOULDER],[LM.LEFT_SHOULDER,LM.LEFT_ELBOW],
  [LM.LEFT_ELBOW,LM.LEFT_WRIST],[LM.RIGHT_SHOULDER,LM.RIGHT_ELBOW],
  [LM.RIGHT_ELBOW,LM.RIGHT_WRIST],[LM.LEFT_SHOULDER,LM.LEFT_HIP],
  [LM.RIGHT_SHOULDER,LM.RIGHT_HIP],[LM.LEFT_HIP,LM.RIGHT_HIP],
  [LM.LEFT_HIP,LM.LEFT_KNEE],[LM.LEFT_KNEE,LM.LEFT_ANKLE],
  [LM.RIGHT_HIP,LM.RIGHT_KNEE],[LM.RIGHT_KNEE,LM.RIGHT_ANKLE],
  [LM.LEFT_ANKLE,LM.LEFT_HEEL],[LM.RIGHT_ANKLE,LM.RIGHT_HEEL],
];
const ANGLE_JOINTS = {
  left_knee:[LM.LEFT_HIP,LM.LEFT_KNEE,LM.LEFT_ANKLE],
  right_knee:[LM.RIGHT_HIP,LM.RIGHT_KNEE,LM.RIGHT_ANKLE],
  left_elbow:[LM.LEFT_SHOULDER,LM.LEFT_ELBOW,LM.LEFT_WRIST],
  right_elbow:[LM.RIGHT_SHOULDER,LM.RIGHT_ELBOW,LM.RIGHT_WRIST],
  left_hip:[LM.LEFT_SHOULDER,LM.LEFT_HIP,LM.LEFT_KNEE],
  right_hip:[LM.RIGHT_SHOULDER,LM.RIGHT_HIP,LM.RIGHT_KNEE],
  body_alignment:[LM.LEFT_SHOULDER,LM.LEFT_HIP,LM.LEFT_ANKLE],
};

function drawSkeleton(ctx, lms, w, h, feedback) {
  if (!CONFIG.showSkeleton) return;
  const style = SKELETON_STYLES[CONFIG.skeletonStyle] || SKELETON_STYLES.neon;
  const hasError=feedback.some(f=>f.severity==='error');
  const hasSuccess=feedback.some(f=>f.severity==='success');
  let color = style.joint;
  if(hasError) color='#ef4444';
  else if(hasSuccess) color='#10b981';

  // Glow layer
  ctx.save();
  ctx.globalAlpha=0.45;
  POSE_CONNECTIONS.forEach(([a,b])=>{
    const pa=lmPX(lms,a,w,h),pb=lmPX(lms,b,w,h);
    ctx.beginPath();ctx.moveTo(pa[0],pa[1]);ctx.lineTo(pb[0],pb[1]);
    ctx.strokeStyle=color;ctx.lineWidth=12;ctx.lineCap='round';
    ctx.filter='blur(8px)';ctx.stroke();
  });
  ctx.restore();

  // Sharp layer
  ctx.save();ctx.filter='none';
  POSE_CONNECTIONS.forEach(([a,b])=>{
    const pa=lmPX(lms,a,w,h),pb=lmPX(lms,b,w,h);
    ctx.beginPath();ctx.moveTo(pa[0],pa[1]);ctx.lineTo(pb[0],pb[1]);
    ctx.strokeStyle=color;ctx.lineWidth=3;ctx.lineCap='round';
    ctx.shadowColor=color;ctx.shadowBlur=10;ctx.stroke();
  });
  // Joint dots
  Object.values(LM).forEach(idx=>{
    if(idx>10){
      const p=lmPX(lms,idx,w,h);
      ctx.beginPath();ctx.arc(p[0],p[1],5,0,Math.PI*2);
      ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=15;ctx.fill();
      ctx.beginPath();ctx.arc(p[0],p[1],2,0,Math.PI*2);
      ctx.fillStyle='#fff';ctx.shadowBlur=0;ctx.fill();
    }
  });
  ctx.restore();

  // Angle labels
  if (CONFIG.showAngles) {
    ctx.save();
    Object.entries(state.lastAngles).forEach(([name,angle])=>{
      if(!ANGLE_JOINTS[name]) return;
      const jIdx=ANGLE_JOINTS[name][1];
      const p=lmPX(lms,jIdx,w,h);
      ctx.fillStyle='rgba(4,6,15,0.82)';
      ctx.beginPath();ctx.roundRect(p[0]-28,p[1]-16,56,28,6);ctx.fill();
      ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.shadowColor=color;ctx.shadowBlur=8;ctx.stroke();
      ctx.fillStyle=color;ctx.shadowBlur=0;
      ctx.font='bold 13px "Share Tech Mono"';ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(`${angle}°`,p[0],p[1]);
    });
    ctx.restore();
  }
}

// ── Rep Counting ───────────────────────────────────────────────────
function countRep(angles, exercise) {
  const ex=EXERCISES[exercise];
  if(!ex.repJoint) return;
  const angle=angles[ex.repJoint];
  if(angle===undefined) return;
  if(exercise==='bicep_curl'){
    if(angle<ex.repUpThreshold&&state.repState==='up'){state.repState='down';updateRepStateUI('down');}
    if(angle>ex.repDownThreshold&&state.repState==='down'){state.repState='up';updateRepStateUI('up');triggerRep();}
  } else {
    if(angle<ex.repDownThreshold&&state.repState==='up'){state.repState='down';updateRepStateUI('down');}
    if(angle>ex.repUpThreshold&&state.repState==='down'){state.repState='up';updateRepStateUI('up');triggerRep();}
  }
}

function triggerRep() {
  state.repCount++; state.totalReps++;
  // Desktop
  const el=document.getElementById('rep-number');
  if(el){el.textContent=state.repCount;el.classList.add('pop');setTimeout(()=>el.classList.remove('pop'),250);}
  // Mobile mirror
  const elm=document.getElementById('rep-number-m');
  if(elm){elm.textContent=state.repCount;elm.classList.add('pop');setTimeout(()=>elm.classList.remove('pop'),250);}
  document.getElementById('hdr-reps').textContent=state.repCount;
  const statReps=document.getElementById('stat-total-reps');
  if(statReps) statReps.textContent=state.totalReps;
  const statRepsM=document.getElementById('stat-reps-m');
  if(statRepsM) statRepsM.textContent=state.totalReps;
  if(CONFIG.voiceFeedback) speak(`${state.repCount}`);
  addLog(`Rep ${state.repCount}`,state.formScore>70?'good':'bad');
  showToast(`Rep ${state.repCount} ✓`);
}

function updateRepStateUI(s) {
  // Desktop
  document.getElementById('chip-down')?.classList.toggle('active',s==='down');
  document.getElementById('chip-up')?.classList.toggle('active',s==='up');
  // Mobile
  document.getElementById('chip-down-m')?.classList.toggle('active',s==='down');
  document.getElementById('chip-up-m')?.classList.toggle('active',s==='up');
}

// ── Pose Results Handler ───────────────────────────────────────────
function onResults(results) {
  const canvas=state.canvasEl, ctx=state.ctx, video=state.videoEl;
  if(!canvas||!ctx) return;
  const w=canvas.width=video.videoWidth||canvas.offsetWidth;
  const h=canvas.height=video.videoHeight||canvas.offsetHeight;
  ctx.clearRect(0,0,w,h);
  ctx.save();ctx.scale(-1,1);ctx.translate(-w,0);
  ctx.drawImage(video,0,0,w,h);

  if(results.poseLandmarks&&state.sessionActive){
    const lms=results.poseLandmarks;
    const analysis=(ANALYZERS[state.exercise]||analyzeSquat)(lms,w,h);
    state.lastAngles=analysis.angles;
    state.lastFeedback=analysis.feedback;
    state.formScore=analysis.score;
    state.scoreBreakdown=analysis.breakdown;
    if(analysis.score>state.bestScore) state.bestScore=analysis.score;
    countRep(analysis.angles,state.exercise);
    drawSkeleton(ctx,lms,w,h,analysis.feedback);
    ctx.restore();
    updateFeedbackUI(analysis.feedback,analysis.score);
    updateAnglesStrip(analysis.angles);
    updateFormScore(analysis.score,analysis.breakdown);
    updateAlertBanner(analysis.feedback);
    updatePulse(analysis.feedback);
  } else {
    ctx.restore();
    if(state.sessionActive) updateAlertBanner([{msg:'No Pose Detected — Step Back',severity:'info'}]);
  }
  state.frameCount++;
  const now=Date.now();
  if(now-state.lastFpsTime>=1000){
    state.fps=state.frameCount;state.frameCount=0;state.lastFpsTime=now;
    document.getElementById('hdr-fps').textContent=state.fps;
  }
}

// ── UI Updates ─────────────────────────────────────────────────────
function updateFeedbackUI(feedback, score) {
  const icons={success:'✅',warning:'⚠️',error:'❌',info:'💡'};
  const html = feedback.length
    ? feedback.slice(0,4).map(fb=>`<div class="fb-item ${fb.severity}"><div class="fb-icon">${icons[fb.severity]||'•'}</div><div class="fb-text">${fb.msg}</div></div>`).join('')
    : '<div class="fb-item info"><div class="fb-icon">💡</div><div class="fb-text">Analyzing pose...</div></div>';
  // Desktop
  const fl=document.getElementById('feedback-list');
  if(fl) fl.innerHTML=html;
  // Mobile
  const flm=document.getElementById('feedback-list-m');
  if(flm) flm.innerHTML=html;
  if(feedback.some(f=>f.severity==='error')){
    state.corrections++;
    const sa=document.getElementById('stat-alerts');
    if(sa) sa.textContent=state.corrections;
    const sam=document.getElementById('stat-alerts-m');
    if(sam) sam.textContent=state.corrections;
  }
}

function updateAnglesStrip(angles) {
  const entries=Object.entries(angles).slice(0,4);
  entries.forEach(([name,val],i)=>{
    const chip=document.getElementById(`ac-${i}`);
    if(!chip) return;
    chip.querySelector('.ac-name').textContent=name.replace(/_/g,' ');
    chip.querySelector('.ac-val').textContent=`${val}°`;
    chip.className='angle-chip';
    if(val>=75&&val<=105) chip.classList.add('good');
    else if(val>=55&&val<=135) chip.classList.add('warn');
    else chip.classList.add('bad');
  });
  for(let i=entries.length;i<4;i++){
    const chip=document.getElementById(`ac-${i}`);
    if(chip){chip.querySelector('.ac-name').textContent='—';chip.querySelector('.ac-val').textContent='—°';chip.className='angle-chip';}
  }
}

function updateFormScore(score, breakdown) {
  const circ=364.4, offset=circ-(score/100)*circ;
  // Desktop
  const sp=document.getElementById('score-pct');       if(sp) sp.textContent=score;
  const prog=document.getElementById('score-prog');    if(prog) prog.style.strokeDashoffset=offset;
  const sg=document.getElementById('score-grade');
  // Mobile
  const spm=document.getElementById('score-pct-m');    if(spm) spm.textContent=score;
  const progm=document.getElementById('score-prog-m'); if(progm) progm.style.strokeDashoffset=offset;
  const sgm=document.getElementById('score-grade-m');

  let grade='A+';
  if(score<50) grade='F';
  else if(score<60) grade='D';
  else if(score<70) grade='C';
  else if(score<80) grade='B';
  else if(score<90) grade='A';
  if(sg) sg.textContent=grade;
  if(sgm) sgm.textContent=grade;

  // Header
  const hdr=document.getElementById('hdr-score');
  if(hdr){hdr.textContent=score+'%';hdr.style.color=score>75?'#00ffcc':score>50?'#f59e0b':'#ef4444';}

  // HUD
  const qpct=document.getElementById('quality-pct');   if(qpct) qpct.textContent=score+'%';
  const qbar=document.getElementById('quality-bar');   if(qbar) qbar.style.width=score+'%';

  // Best score
  const best=document.getElementById('stat-best');     if(best) best.textContent=state.bestScore+'%';
  const bestm=document.getElementById('stat-best-m');  if(bestm) bestm.textContent=state.bestScore+'%';

  // Breakdown bars (desktop)
  const d=breakdown||{depth:score,alignment:score,balance:score};
  const bars=document.querySelectorAll('.sb-fill');
  if(bars[0]) bars[0].style.width=Math.round(d.depth)+'%';
  if(bars[1]) bars[1].style.width=Math.round(d.alignment)+'%';
  if(bars[2]) bars[2].style.width=Math.round(d.balance)+'%';
}

function updateAlertBanner(feedback) {
  const banner=document.getElementById('alert-banner');
  const text=document.getElementById('alert-text');
  const icon=document.getElementById('alert-icon');
  if(!feedback.length||!banner) return;
  const top=feedback[0];
  const icons={success:'✅',warning:'⚠️',error:'🚨',info:'⚡'};
  text.textContent=top.msg;
  icon.textContent=icons[top.severity]||'⚡';
  banner.className='alert-banner '+top.severity;
}

function updatePulse(feedback) {
  const dot=document.getElementById('pulse-dot');
  const label=document.getElementById('pulse-label');
  const hasError=feedback.some(f=>f.severity==='error');
  const hasSuccess=feedback.some(f=>f.severity==='success');
  if(hasError){dot.className='pulse-dot error';label.textContent='FIX FORM';label.style.color='#ef4444';}
  else if(hasSuccess){dot.className='pulse-dot active';label.textContent='PERFECT FORM';label.style.color='#10b981';}
  else{dot.className='pulse-dot active';label.textContent='TRACKING';label.style.color='#00ffcc';}
}

// ── Timer ──────────────────────────────────────────────────────────
let timerInterval=null;
function startTimer(){
  state.startTime=Date.now();
  timerInterval=setInterval(()=>{
    const e=Math.floor((Date.now()-state.startTime)/1000);
    const m=Math.floor(e/60),s=e%60;
    const t=`${m}:${s.toString().padStart(2,'0')}`;
    const ht=document.getElementById('hud-timer');    if(ht) ht.textContent=t;
    const st=document.getElementById('stat-time');    if(st) st.textContent=t;
    const stm=document.getElementById('stat-time-m'); if(stm) stm.textContent=t;
  },1000);
}
function stopTimer(){if(timerInterval){clearInterval(timerInterval);timerInterval=null;}}

// ── Session Control ────────────────────────────────────────────────
async function startSession() {
  try {
    const video=document.getElementById('webcam');
    const canvas=document.getElementById('output-canvas');
    state.videoEl=video; state.canvasEl=canvas; state.ctx=canvas.getContext('2d');
    const stream=await navigator.mediaDevices.getUserMedia({
      video:{width:{ideal:1280},height:{ideal:720},facingMode:'user',frameRate:{ideal:30}},
      audio:false
    });
    video.srcObject=stream; video.style.display='block';
    await new Promise(res=>{video.onloadedmetadata=res;});
    const pose=new Pose({locateFile:(f)=>`https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}`});
    pose.setOptions({
      modelComplexity:CONFIG.modelComplexity,smoothLandmarks:true,
      enableSegmentation:false,smoothSegmentation:false,
      minDetectionConfidence:CONFIG.minDetectionConf,minTrackingConfidence:CONFIG.minTrackingConf,
    });
    pose.onResults(onResults);
    const camera=new Camera(video,{onFrame:async()=>{await pose.send({image:video});},width:1280,height:720});
    await camera.start();
    state.pose=pose; state.camera=camera; state.sessionActive=true;
    document.getElementById('cam-overlay').style.display='none';
    document.getElementById('live-hud').style.display='flex';
    document.getElementById('btn-start').disabled=true;
    document.getElementById('btn-stop').disabled=false;
    const ll=document.getElementById('log-list'); if(ll) ll.innerHTML='';
    startTimer();
    addLog('Session started','good');
    showToast('Session Started! 🚀');
  } catch(err) {
    console.error('Camera error:',err);
    showToast('Camera error: '+err.message,'error');
    updateAlertBanner([{msg:'Camera access denied — check permissions',severity:'error'}]);
  }
}

function stopSession() {
  state.sessionActive=false;
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
  const pd=document.getElementById('pulse-dot');
  if(pd) pd.className='pulse-dot';
  const pl=document.getElementById('pulse-label');
  if(pl){pl.textContent='READY';pl.style.color='';}
  stopTimer();
  addLog('Session stopped','good');
}

function resetSession() {
  state.repCount=0;state.repState='up';state.bestScore=100;state.corrections=0;state.formScore=100;
  ['rep-number','rep-number-m'].forEach(id=>{const e=document.getElementById(id);if(e) e.textContent='0';});
  document.getElementById('hdr-reps').textContent='0';
  ['stat-total-reps','stat-reps-m','stat-alerts','stat-alerts-m'].forEach(id=>{const e=document.getElementById(id);if(e) e.textContent='0';});
  ['stat-best','stat-best-m'].forEach(id=>{const e=document.getElementById(id);if(e) e.textContent='100%';});
  updateRepStateUI('up');
  updateFormScore(100,{depth:100,alignment:100,balance:100});
  showToast('Session Reset ↺');
  addLog('Reset session','good');
}

// ── Exercise Selection ─────────────────────────────────────────────
function selectExercise(key) {
  if(!EXERCISES[key]) return;
  state.exercise=key; state.repCount=0; state.repState='up';
  // Update all ex-card buttons (desktop + mobile)
  document.querySelectorAll('.ex-card').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll(`[data-ex="${key}"]`).forEach(b=>b.classList.add('active'));
  const ex=EXERCISES[key];
  // Instruction text (desktop + mobile)
  ['inst-text','inst-text-m'].forEach(id=>{const e=document.getElementById(id);if(e) e.textContent=ex.instruction;});
  // Tips (desktop + mobile)
  const tipsHTML=ex.tips.map(t=>`<div class="inst-tip">${t}</div>`).join('');
  ['inst-tips','inst-tips-m'].forEach(id=>{const e=document.getElementById(id);if(e) e.innerHTML=tipsHTML;});
  document.getElementById('hud-exercise').textContent=ex.name.toUpperCase();
  ['rep-number','rep-number-m'].forEach(id=>{const e=document.getElementById(id);if(e) e.textContent='0';});
  document.getElementById('hdr-reps').textContent='0';
  updateRepStateUI('up');
  addLog(`Exercise: ${ex.name}`,'good');
}

// ── Screenshot ─────────────────────────────────────────────────────
function takeScreenshot() {
  const canvas=document.getElementById('output-canvas');
  if(!canvas) return;
  const link=document.createElement('a');
  link.download=`biomech-${Date.now()}.png`;
  link.href=canvas.toDataURL('image/png');
  link.click();
  showToast('Screenshot saved! 📸');
}

// ── AI Coach ───────────────────────────────────────────────────────
function openAICoach() {
  document.getElementById('ai-ex-chip').textContent=`Exercise: ${EXERCISES[state.exercise]?.name||'—'}`;
  document.getElementById('ai-score-chip').textContent=`Score: ${state.formScore}%`;
  document.getElementById('ai-rep-chip').textContent=`Reps: ${state.repCount}`;
  document.getElementById('ai-modal').style.display='flex';
}
function closeAICoach(){document.getElementById('ai-modal').style.display='none';}

async function runGeminiAnalysis() {
  const key=state.geminiKey;
  if(!key){
    document.getElementById('ai-response-area').innerHTML=`
      <div class="ai-text" style="color:#f87171;">
        ⚠️ AI Coach unavailable — Gemini API key not configured on server.<br><br>
        <small>Add <strong>GEMINI_API_KEY</strong> to Render environment variables.</small>
      </div>`;
    return;
  }
  const area=document.getElementById('ai-response-area');
  const btn=document.getElementById('ai-analyze-btn');
  btn.disabled=true;
  area.innerHTML=`<div class="ai-loading-wrap"><div class="ai-spinner"></div><div class="ai-loading-text">GEMINI 2.5 FLASH ANALYZING...</div></div>`;
  const ex=EXERCISES[state.exercise]||{};
  const prompt=`You are an elite AI biomechanical coach and physiotherapist.
Exercise: ${ex.name||state.exercise}
Form Score: ${state.formScore}/100
Reps: ${state.repCount}
Joint Angles: ${Object.entries(state.lastAngles).map(([k,v])=>`${k.replace(/_/g,' ')}: ${v}°`).join(', ')}
Live Feedback: ${state.lastFeedback.map(f=>f.msg).join(', ')||'None'}

Respond with:
**FORM ASSESSMENT** (2 sentences, cite specific angles)
**TOP 3 CORRECTIONS** (with biomechanical reasoning)
**MUSCLE ACTIVATION TIP** (one specific cue)
**MOTIVATIONAL PUSH** (one energetic sentence)

Max 250 words. Use anatomical terms.`;
  try {
    const resp=await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${key}`,
      {method:'POST',headers:{'Content-Type':'application/json'},
       body:JSON.stringify({contents:[{parts:[{text:prompt}]}],generationConfig:{temperature:0.7,maxOutputTokens:512}})}
    );
    if(!resp.ok){const e=await resp.json();throw new Error(e?.error?.message||`HTTP ${resp.status}`);}
    const data=await resp.json();
    const text=data?.candidates?.[0]?.content?.parts?.[0]?.text||'No response received.';
    const formatted=text
      .replace(/\*\*(.*?)\*\*/g,'<strong style="color:#a78bfa;font-family:\'Michroma\',monospace;font-size:11px;letter-spacing:2px;">$1</strong>')
      .replace(/\n/g,'<br>');
    area.innerHTML=`<div class="ai-text">${formatted}</div>`;
    addLog('AI Analysis complete','good');
  } catch(err){
    area.innerHTML=`<div class="ai-text" style="color:#f87171;">❌ Gemini Error: ${err.message}</div>`;
  } finally{btn.disabled=false;}
}

// ── Settings ───────────────────────────────────────────────────────
function toggleSettings(){
  const m=document.getElementById('settings-modal');
  m.style.display=m.style.display==='none'?'flex':'none';
}
function closeSettings(){document.getElementById('settings-modal').style.display='none';}
function saveSettings(){
  CONFIG.skeletonStyle=document.getElementById('skeleton-style').value;
  CONFIG.showAngles=document.getElementById('show-angles').checked;
  CONFIG.showSkeleton=document.getElementById('show-skeleton').checked;
  CONFIG.voiceFeedback=document.getElementById('voice-feedback').checked;
  const conf=parseInt(document.getElementById('conf-slider').value);
  CONFIG.minDetectionConf=conf/100; CONFIG.minTrackingConf=conf/100;
  closeSettings();
  showToast('Settings Saved ✓');
}

// ── Voice ──────────────────────────────────────────────────────────
function speak(text){
  if(!window.speechSynthesis) return;
  const u=new SpeechSynthesisUtterance(text);
  u.rate=1.1;u.pitch=1;u.volume=0.8;
  window.speechSynthesis.speak(u);
}

// ── Activity Log ───────────────────────────────────────────────────
function addLog(msg,type='good'){
  const log=document.getElementById('log-list');
  if(!log) return;
  const empty=log.querySelector('.log-empty');
  if(empty) log.innerHTML='';
  const time=new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  const item=document.createElement('div');
  item.className=`log-item ${type}`;
  item.innerHTML=`<span>${msg}</span><span class="log-time">${time}</span>`;
  log.prepend(item);
  if(log.children.length>15) log.removeChild(log.lastChild);
}

// ── Toast ──────────────────────────────────────────────────────────
let toastTimer=null;
function showToast(msg,type='success'){
  const t=document.getElementById('toast');
  t.textContent=msg;
  t.style.background=type==='error'?'rgba(239,68,68,0.9)':'rgba(16,185,129,0.9)';
  t.classList.add('show');
  if(toastTimer) clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.classList.remove('show'),2500);
}

// ── Background Canvas ──────────────────────────────────────────────
function initBackground(){
  const canvas=document.getElementById('bg-canvas');
  if(!canvas) return;
  const ctx=canvas.getContext('2d');
  let w=canvas.width=window.innerWidth, h=canvas.height=window.innerHeight;
  window.addEventListener('resize',()=>{w=canvas.width=window.innerWidth;h=canvas.height=window.innerHeight;});
  const nodes=Array.from({length:60},()=>({
    x:Math.random()*w,y:Math.random()*h,
    vx:(Math.random()-0.5)*0.3,vy:(Math.random()-0.5)*0.3,
    r:Math.random()*1.5+0.5
  }));
  function draw(){
    ctx.clearRect(0,0,w,h);
    ctx.strokeStyle='rgba(0,255,204,0.03)';ctx.lineWidth=1;
    for(let x=0;x<w;x+=60){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
    for(let y=0;y<h;y+=60){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
    nodes.forEach(n=>{
      n.x+=n.vx;n.y+=n.vy;
      if(n.x<0||n.x>w)n.vx*=-1;if(n.y<0||n.y>h)n.vy*=-1;
      ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);ctx.fillStyle='rgba(0,255,204,0.4)';ctx.fill();
    });
    ctx.strokeStyle='rgba(0,255,204,0.06)';ctx.lineWidth=1;
    for(let i=0;i<nodes.length;i++){
      for(let j=i+1;j<nodes.length;j++){
        const d=Math.hypot(nodes[i].x-nodes[j].x,nodes[i].y-nodes[j].y);
        if(d<120){ctx.globalAlpha=(1-d/120)*0.3;ctx.beginPath();ctx.moveTo(nodes[i].x,nodes[i].y);ctx.lineTo(nodes[j].x,nodes[j].y);ctx.stroke();}
      }
    }
    ctx.globalAlpha=1;
    requestAnimationFrame(draw);
  }
  draw();
}

// ── Confidence slider ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  const sl=document.getElementById('conf-slider'),vl=document.getElementById('conf-val');
  if(sl&&vl) sl.addEventListener('input',()=>{vl.textContent=sl.value+'%';});
});

// ── Splash / Init ──────────────────────────────────────────────────
async function initApp(){
  initBackground();
  const fill=document.getElementById('loading-fill');
  const loadTxt=document.getElementById('loading-text');
  const ssTf=document.getElementById('ss-tf');
  const ssMp=document.getElementById('ss-mp');
  const ssCam=document.getElementById('ss-cam');

  loadTxt.textContent='Loading MediaPipe libraries...';
  fill.style.width='20%';
  await sleep(600);
  ssTf.textContent='✓';

  loadTxt.textContent='Initializing Pose Model...';
  fill.style.width='45%';
  await loadGeminiKey();   // ← silent, auto-fetches from /api/config
  await sleep(500);
  ssMp.textContent='✓';

  loadTxt.textContent='Checking Camera...';
  fill.style.width='80%';
  try{
    const devices=await navigator.mediaDevices.enumerateDevices();
    const cams=devices.filter(d=>d.kind==='videoinput');
    ssCam.textContent=cams.length>0?`${cams.length}✓`:'?';
  }catch(e){ssCam.textContent='?';}
  await sleep(500);

  loadTxt.textContent='System Ready. Launching...';
  fill.style.width='100%';
  await sleep(600);

  document.getElementById('splash').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
}

function sleep(ms){return new Promise(r=>setTimeout(r,ms));}

// ── Boot ───────────────────────────────────────────────────────────
initApp();