/* ══════════════════════════════════════════════════════════════════
   BioMech AI — Core Engine
   Client-side: MediaPipe Pose + Cosine Rule + Gemini 2.5 Flash
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
    primaryAngles: ['left_knee', 'right_knee', 'left_hip', 'right_hip'],
    repJoint: 'left_knee',
    repDownThreshold: 110,
    repUpThreshold:   160,
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
    primaryAngles: ['left_elbow', 'right_elbow', 'body_alignment'],
    repJoint: 'left_elbow',
    repDownThreshold: 110,
    repUpThreshold:   155,
    checkpoints: {
      elbow:     { ideal: 90,  tolerance: 18, label: 'Elbow Bend',  weight: 50 },
      alignment: { ideal: 180, tolerance: 12, label: 'Body Line',   weight: 50 },
    }
  },
  lunge: {
    name: 'Lunge',
    instruction: 'Step forward. Both knees at 90°. Front knee directly over ankle.',
    tips: ['Keep torso tall', 'Front knee tracks over second toe', 'Push back through front heel'],
    primaryAngles: ['left_knee', 'right_knee', 'left_hip'],
    repJoint: 'right_knee',
    repDownThreshold: 110,
    repUpThreshold:   160,
    checkpoints: {
      front_knee: { ideal: 90,  tolerance: 18, label: 'Front Knee', weight: 45 },
      back_knee:  { ideal: 90,  tolerance: 18, label: 'Back Knee',  weight: 35 },
      torso:      { ideal: 90,  tolerance: 25, label: 'Torso Upright', weight: 20 },
    }
  },
  plank: {
    name: 'Plank',
    instruction: 'Straight line from head to heels. Engage core throughout. Hold position.',
    tips: ['Press floor away', 'Neutral spine — no sagging', 'Breathe steadily'],
    primaryAngles: ['body_alignment', 'hip_alignment'],
    repJoint: null,
    repDownThreshold: 0,
    repUpThreshold:   0,
    checkpoints: {
      body: { ideal: 180, tolerance: 10, label: 'Body Straight', weight: 60 },
      hip:  { ideal: 180, tolerance: 10, label: 'Hip Level',     weight: 40 },
    }
  },
  bicep_curl: {
    name: 'Bicep Curl',
    instruction: 'Elbows close to torso. Full range: straight arm to full curl. Controlled descent.',
    tips: ['Don\'t swing body', 'Supinate wrist on the way up', 'Squeeze at the top'],
    primaryAngles: ['left_elbow', 'right_elbow'],
    repJoint: 'left_elbow',
    repDownThreshold: 130,
    repUpThreshold:   50,
    checkpoints: {
      curl_depth: { ideal: 40, tolerance: 20, label: 'Curl Depth',    weight: 60 },
      stability:  { ideal: 0,  tolerance: 10, label: 'Body Stable',   weight: 40 },
    }
  },
  shoulder_press: {
    name: 'Shoulder Press',
    instruction: 'Press overhead to full extension. Elbows at 90° at start position.',
    tips: ['Core tight, slight forward lean', 'Full lockout at top', 'Control the descent'],
    primaryAngles: ['left_elbow', 'right_elbow', 'left_shoulder'],
    repJoint: 'left_elbow',
    repDownThreshold: 100,
    repUpThreshold:   155,
    checkpoints: {
      elbow:    { ideal: 90,  tolerance: 20, label: 'Start Position', weight: 50 },
      lockout:  { ideal: 175, tolerance: 10, label: 'Lockout',        weight: 50 },
    }
  },
  deadlift: {
    name: 'Deadlift',
    instruction: 'Hip hinge movement. Bar close to body. Neutral spine throughout.',
    tips: ['Brace core before lifting', 'Drive hips forward', 'Keep bar over mid-foot'],
    primaryAngles: ['left_hip', 'right_hip', 'back_angle'],
    repJoint: 'left_hip',
    repDownThreshold: 70,
    repUpThreshold:   155,
    checkpoints: {
      hip_hinge:  { ideal: 45, tolerance: 20, label: 'Hip Hinge',     weight: 45 },
      back_neutral: { ideal: 180, tolerance: 20, label: 'Back Neutral', weight: 55 },
    }
  }
};

// ── Pose Landmark Indices (MediaPipe) ──────────────────────────────
const LM = {
  NOSE: 0, LEFT_EYE: 1, RIGHT_EYE: 2,
  LEFT_SHOULDER: 11, RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13,    RIGHT_ELBOW: 14,
  LEFT_WRIST: 15,    RIGHT_WRIST: 16,
  LEFT_HIP: 23,      RIGHT_HIP: 24,
  LEFT_KNEE: 25,     RIGHT_KNEE: 26,
  LEFT_ANKLE: 27,    RIGHT_ANKLE: 28,
  LEFT_HEEL: 29,     RIGHT_HEEL: 30,
  LEFT_FOOT: 31,     RIGHT_FOOT: 32,
};

// ── State ──────────────────────────────────────────────────────────
let state = {
  exercise:     'squat',
  sessionActive: false,
  repCount:     0,
  repState:     'up',     // 'up' | 'down'
  formScore:    100,
  bestScore:    100,
  totalReps:    0,
  corrections:  0,
  startTime:    null,
  lastAngles:   {},
  lastFeedback: [],
  frameCount:   0,
  lastFpsTime:  Date.now(),
  fps:          0,
  pose:         null,
  camera:       null,
  videoEl:      null,
  canvasEl:     null,
  ctx:          null,
  geminiKey:    '',
  scoreBreakdown: { depth: 100, alignment: 100, balance: 100 },
};

// ── Skeleton Color Schemes ─────────────────────────────────────────
const SKELETON_STYLES = {
  neon:    { joint: '#00ffcc', bone: '#00ffcc', glow: 'rgba(0,255,204,', angle: '#00ffcc' },
  fire:    { joint: '#ff6b35', bone: '#ff6b35', glow: 'rgba(255,107,53,', angle: '#ff6b35' },
  matrix:  { joint: '#00ff41', bone: '#00ff41', glow: 'rgba(0,255,65,',  angle: '#00ff41' },
  purple:  { joint: '#a78bfa', bone: '#a78bfa', glow: 'rgba(167,139,250,', angle: '#a78bfa' },
};

// ── Cosine Rule Angle Calculation ──────────────────────────────────
/**
 * Calculate angle at vertex B using the Law of Cosines:
 * cos(B) = (AB² + BC² - AC²) / (2 · AB · BC)
 * @param {Array} A - [x, y] point A
 * @param {Array} B - [x, y] vertex point (angle measured here)
 * @param {Array} C - [x, y] point C
 * @returns {number} Angle in degrees
 */
function calculateAngle(A, B, C) {
  const AB = Math.hypot(B[0]-A[0], B[1]-A[1]);
  const BC = Math.hypot(C[0]-B[0], C[1]-B[1]);
  const AC = Math.hypot(C[0]-A[0], C[1]-A[1]);
  if (AB === 0 || BC === 0) return 0;
  const cosB = Math.max(-1, Math.min(1, (AB*AB + BC*BC - AC*AC) / (2*AB*BC)));
  return Math.round(Math.acos(cosB) * (180 / Math.PI));
}

// ── Get Landmark XY ────────────────────────────────────────────────
function lmXY(landmarks, idx) {
  const lm = landmarks[idx];
  return [lm.x, lm.y];
}
function lmPX(landmarks, idx, w, h) {
  const lm = landmarks[idx];
  return [lm.x * w, lm.y * h];
}

// ── Biomechanics Analyzers ─────────────────────────────────────────
function analyzeSquat(lms, w, h) {
  const angles = {};
  const feedback = [];
  let score = 100;
  let depthScore = 100, alignScore = 100, balScore = 100;

  try {
    const LH = lmXY(lms, LM.LEFT_HIP),   LK = lmXY(lms, LM.LEFT_KNEE),   LA = lmXY(lms, LM.LEFT_ANKLE);
    const RH = lmXY(lms, LM.RIGHT_HIP),  RK = lmXY(lms, LM.RIGHT_KNEE),  RA = lmXY(lms, LM.RIGHT_ANKLE);
    const LS = lmXY(lms, LM.LEFT_SHOULDER);

    const lKnee = calculateAngle(LH, LK, LA);
    const rKnee = calculateAngle(RH, RK, RA);
    const lHip  = calculateAngle(LS, LH, LK);
    const avgKnee = (lKnee + rKnee) / 2;
    const kneeDiff = Math.abs(lKnee - rKnee);

    angles.left_knee  = lKnee;
    angles.right_knee = rKnee;
    angles.left_hip   = lHip;

    // Depth check
    if (avgKnee > 155) {
      feedback.push({ msg: '⬇ Go Deeper — Bend Knees to 90°', severity: 'warning' });
      depthScore = Math.max(0, 100 - (avgKnee - 90) * 1.5);
    } else if (avgKnee >= 72 && avgKnee <= 108) {
      feedback.push({ msg: '🎯 Perfect Squat Depth!', severity: 'success' });
    } else if (avgKnee < 60) {
      feedback.push({ msg: '⬆ Too Deep — Rise Slightly', severity: 'warning' });
      depthScore = 70;
    } else {
      depthScore = 85;
    }

    // Torso check
    if (lHip < 45) {
      feedback.push({ msg: '❌ Keep Torso Upright — Don\'t Lean Forward', severity: 'error' });
      alignScore = 40;
    } else if (lHip < 65) {
      feedback.push({ msg: '⚠ Less Forward Lean', severity: 'warning' });
      alignScore = 70;
    }

    // Balance check
    if (kneeDiff > 20) {
      feedback.push({ msg: '⚖ Balance Both Sides — Knee Asymmetry Detected', severity: 'warning' });
      balScore = Math.max(0, 100 - kneeDiff * 2);
    }

    score = (depthScore * 0.4 + alignScore * 0.35 + balScore * 0.25);
  } catch(e) {
    feedback.push({ msg: '📷 Show Full Body in Frame', severity: 'info' });
    score = 0;
  }

  return { angles, feedback, score: Math.round(score),
    breakdown: { depth: depthScore, alignment: alignScore, balance: balScore } };
}

function analyzePushup(lms, w, h) {
  const angles = {};
  const feedback = [];
  let score = 100;
  let elbowScore = 100, alignScore = 100;

  try {
    const LS = lmXY(lms, LM.LEFT_SHOULDER), LE = lmXY(lms, LM.LEFT_ELBOW), LW = lmXY(lms, LM.LEFT_WRIST);
    const RS = lmXY(lms, LM.RIGHT_SHOULDER), RE = lmXY(lms, LM.RIGHT_ELBOW), RW = lmXY(lms, LM.RIGHT_WRIST);
    const LH = lmXY(lms, LM.LEFT_HIP), LA = lmXY(lms, LM.LEFT_ANKLE);

    const lElbow  = calculateAngle(LS, LE, LW);
    const rElbow  = calculateAngle(RS, RE, RW);
    const bodyAngle = calculateAngle(LS, LH, LA);
    const avgElbow = (lElbow + rElbow) / 2;

    angles.left_elbow  = lElbow;
    angles.right_elbow = rElbow;
    angles.body_alignment = bodyAngle;

    if (avgElbow > 155) {
      feedback.push({ msg: '⬇ Lower Your Chest Further!', severity: 'warning' });
      elbowScore = Math.max(0, 100 - (avgElbow - 90) * 1.2);
    } else if (avgElbow >= 72 && avgElbow <= 108) {
      feedback.push({ msg: '💪 Perfect Push-Up Depth!', severity: 'success' });
    }

    if (bodyAngle < 152) {
      feedback.push({ msg: '❌ Raise Hips — Keep Body Straight', severity: 'error' });
      alignScore = 30;
    } else if (bodyAngle > 198) {
      feedback.push({ msg: '❌ Lower Hips — Stop Sagging', severity: 'error' });
      alignScore = 30;
    } else if (Math.abs(bodyAngle - 180) < 12) {
      feedback.push({ msg: '✓ Great Body Alignment', severity: 'success' });
    }

    score = (elbowScore * 0.5 + alignScore * 0.5);
  } catch(e) {
    feedback.push({ msg: '📷 Adjust Camera for Side View', severity: 'info' });
    score = 0;
  }

  return { angles, feedback, score: Math.round(score),
    breakdown: { depth: elbowScore, alignment: alignScore, balance: 100 } };
}

function analyzeLunge(lms, w, h) {
  return analyzeSquat(lms, w, h); // Similar joint mechanics
}

function analyzePlank(lms, w, h) {
  const angles = {};
  const feedback = [];
  let score = 100;
  let bodyScore = 100, hipScore = 100;

  try {
    const LS = lmXY(lms, LM.LEFT_SHOULDER);
    const LH = lmXY(lms, LM.LEFT_HIP);
    const LA = lmXY(lms, LM.LEFT_ANKLE);
    const LE = lmXY(lms, LM.LEFT_ELBOW);

    const bodyLine = calculateAngle(LS, LH, LA);
    const upperBody = calculateAngle(LE, LS, LH);

    angles.body_alignment = bodyLine;
    angles.hip_alignment  = upperBody;

    const bodyDev = Math.abs(bodyLine - 180);
    if (bodyDev > 15) {
      if (bodyLine < 165) {
        feedback.push({ msg: '❌ Hips Too High — Lower Down', severity: 'error' });
      } else {
        feedback.push({ msg: '❌ Hips Sagging — Engage Core', severity: 'error' });
      }
      bodyScore = Math.max(0, 100 - bodyDev * 4);
    } else if (bodyDev < 6) {
      feedback.push({ msg: '⚡ Perfect Plank Position!', severity: 'success' });
    } else {
      feedback.push({ msg: '⚠ Adjust Hip Height', severity: 'warning' });
      bodyScore = 75;
    }

    score = bodyScore * 0.7 + hipScore * 0.3;
  } catch(e) {
    feedback.push({ msg: '📷 Show Side Profile', severity: 'info' });
    score = 0;
  }

  return { angles, feedback, score: Math.round(score),
    breakdown: { depth: bodyScore, alignment: hipScore, balance: 100 } };
}

function analyzeBicepCurl(lms, w, h) {
  const angles = {};
  const feedback = [];
  let score = 100;
  let curlScore = 100, stabScore = 100;

  try {
    const LS = lmXY(lms, LM.LEFT_SHOULDER), LE = lmXY(lms, LM.LEFT_ELBOW), LW = lmXY(lms, LM.LEFT_WRIST);
    const RS = lmXY(lms, LM.RIGHT_SHOULDER), RE = lmXY(lms, LM.RIGHT_ELBOW), RW = lmXY(lms, LM.RIGHT_WRIST);
    const LH = lmXY(lms, LM.LEFT_HIP);

    const lElbow = calculateAngle(LS, LE, LW);
    const rElbow = calculateAngle(RS, RE, RW);
    const torso  = calculateAngle(LS, LH, [LH[0], LH[1]+1]);
    const avgElbow = (lElbow + rElbow) / 2;

    angles.left_elbow  = lElbow;
    angles.right_elbow = rElbow;

    if (avgElbow < 35) {
      feedback.push({ msg: '🔥 Full Curl — Excellent Contraction!', severity: 'success' });
    } else if (avgElbow < 70) {
      feedback.push({ msg: '✓ Good Curl Range', severity: 'success' });
      curlScore = 85;
    } else if (avgElbow > 150) {
      feedback.push({ msg: '↑ Start Curling Upward', severity: 'info' });
      curlScore = 60;
    } else {
      feedback.push({ msg: '⬆ Curl Higher — Full Range of Motion!', severity: 'warning' });
      curlScore = 65;
    }

    score = (curlScore * 0.65 + stabScore * 0.35);
  } catch(e) {
    feedback.push({ msg: '📷 Face Camera — Arms Visible', severity: 'info' });
    score = 0;
  }

  return { angles, feedback, score: Math.round(score),
    breakdown: { depth: curlScore, alignment: stabScore, balance: 100 } };
}

function analyzeShoulderPress(lms, w, h) {
  const angles = {};
  const feedback = [];
  let score = 100;

  try {
    const LS = lmXY(lms, LM.LEFT_SHOULDER), LE = lmXY(lms, LM.LEFT_ELBOW), LW = lmXY(lms, LM.LEFT_WRIST);
    const RS = lmXY(lms, LM.RIGHT_SHOULDER), RE = lmXY(lms, LM.RIGHT_ELBOW), RW = lmXY(lms, LM.RIGHT_WRIST);

    const lElbow = calculateAngle(LS, LE, LW);
    const rElbow = calculateAngle(RS, RE, RW);
    const avgElbow = (lElbow + rElbow) / 2;

    angles.left_elbow  = lElbow;
    angles.right_elbow = rElbow;

    if (avgElbow > 160) {
      feedback.push({ msg: '🏆 Full Lockout — Perfect!', severity: 'success' });
    } else if (avgElbow < 100) {
      feedback.push({ msg: '↑ Press to Full Extension', severity: 'warning' });
      score = Math.max(0, 100 - (160 - avgElbow) * 1.2);
    } else {
      feedback.push({ msg: '↑ Press Higher for Full Extension', severity: 'info' });
      score = 75;
    }
  } catch(e) {
    feedback.push({ msg: '📷 Show Upper Body', severity: 'info' });
    score = 0;
  }

  return { angles, feedback, score: Math.round(score),
    breakdown: { depth: score, alignment: 100, balance: 100 } };
}

function analyzeDeadlift(lms, w, h) {
  const angles = {};
  const feedback = [];
  let score = 100;

  try {
    const LS = lmXY(lms, LM.LEFT_SHOULDER), LH = lmXY(lms, LM.LEFT_HIP), LK = lmXY(lms, LM.LEFT_KNEE);

    const hipAngle  = calculateAngle(LS, LH, LK);
    const backAngle = calculateAngle(LS, LH, [LH[0], LH[1]+0.1]);

    angles.left_hip   = hipAngle;
    angles.back_angle = Math.round(backAngle);

    if (hipAngle > 155) {
      feedback.push({ msg: '💎 Full Hip Extension — Excellent!', severity: 'success' });
    } else if (hipAngle < 50) {
      feedback.push({ msg: '⬆ Drive Hips Forward!', severity: 'warning' });
      score = Math.max(0, 100 - (155 - hipAngle));
    }
  } catch(e) {
    feedback.push({ msg: '📷 Show Full Side Profile', severity: 'info' });
    score = 0;
  }

  return { angles, feedback, score: Math.round(score),
    breakdown: { depth: score, alignment: 100, balance: 100 } };
}

const ANALYZERS = {
  squat:          analyzeSquat,
  pushup:         analyzePushup,
  lunge:          analyzeLunge,
  plank:          analyzePlank,
  bicep_curl:     analyzeBicepCurl,
  shoulder_press: analyzeShoulderPress,
  deadlift:       analyzeDeadlift,
};

// ── Canvas Drawing ─────────────────────────────────────────────────
const POSE_CONNECTIONS = [
  [LM.LEFT_SHOULDER,  LM.RIGHT_SHOULDER],
  [LM.LEFT_SHOULDER,  LM.LEFT_ELBOW],
  [LM.LEFT_ELBOW,     LM.LEFT_WRIST],
  [LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW],
  [LM.RIGHT_ELBOW,    LM.RIGHT_WRIST],
  [LM.LEFT_SHOULDER,  LM.LEFT_HIP],
  [LM.RIGHT_SHOULDER, LM.RIGHT_HIP],
  [LM.LEFT_HIP,       LM.RIGHT_HIP],
  [LM.LEFT_HIP,       LM.LEFT_KNEE],
  [LM.LEFT_KNEE,      LM.LEFT_ANKLE],
  [LM.RIGHT_HIP,      LM.RIGHT_KNEE],
  [LM.RIGHT_KNEE,     LM.RIGHT_ANKLE],
  [LM.LEFT_ANKLE,     LM.LEFT_HEEL],
  [LM.RIGHT_ANKLE,    LM.RIGHT_HEEL],
];

const ANGLE_JOINTS = {
  left_knee:       [LM.LEFT_HIP,      LM.LEFT_KNEE,      LM.LEFT_ANKLE],
  right_knee:      [LM.RIGHT_HIP,     LM.RIGHT_KNEE,     LM.RIGHT_ANKLE],
  left_elbow:      [LM.LEFT_SHOULDER, LM.LEFT_ELBOW,     LM.LEFT_WRIST],
  right_elbow:     [LM.RIGHT_SHOULDER,LM.RIGHT_ELBOW,    LM.RIGHT_WRIST],
  left_hip:        [LM.LEFT_SHOULDER, LM.LEFT_HIP,       LM.LEFT_KNEE],
  right_hip:       [LM.RIGHT_SHOULDER,LM.RIGHT_HIP,      LM.RIGHT_KNEE],
  body_alignment:  [LM.LEFT_SHOULDER, LM.LEFT_HIP,       LM.LEFT_ANKLE],
};

function drawSkeleton(ctx, landmarks, w, h, feedback) {
  if (!CONFIG.showSkeleton) return;

  const style = SKELETON_STYLES[CONFIG.skeletonStyle] || SKELETON_STYLES.neon;
  const hasError   = feedback.some(f => f.severity === 'error');
  const hasSuccess = feedback.some(f => f.severity === 'success');

  let color = style.joint;
  if (hasError)   color = '#ef4444';
  else if (hasSuccess) color = '#10b981';

  const glowAlpha = 0.35;

  // Draw glow layer (thick, dim)
  ctx.save();
  ctx.globalAlpha = 0.45;
  POSE_CONNECTIONS.forEach(([a, b]) => {
    const pa = lmPX(landmarks, a, w, h);
    const pb = lmPX(landmarks, b, w, h);
    ctx.beginPath();
    ctx.moveTo(pa[0], pa[1]);
    ctx.lineTo(pb[0], pb[1]);
    ctx.strokeStyle = color;
    ctx.lineWidth = 12;
    ctx.lineCap = 'round';
    ctx.filter = `blur(8px)`;
    ctx.stroke();
  });
  ctx.restore();

  // Draw neon layer (sharp, bright)
  ctx.save();
  ctx.filter = 'none';
  POSE_CONNECTIONS.forEach(([a, b]) => {
    const pa = lmPX(landmarks, a, w, h);
    const pb = lmPX(landmarks, b, w, h);
    ctx.beginPath();
    ctx.moveTo(pa[0], pa[1]);
    ctx.lineTo(pb[0], pb[1]);
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.shadowColor = color;
    ctx.shadowBlur = 10;
    ctx.stroke();
  });

  // Draw joint dots
  Object.values(LM).forEach(idx => {
    if (idx > 10) { // Skip face landmarks
      const p = lmPX(landmarks, idx, w, h);
      ctx.beginPath();
      ctx.arc(p[0], p[1], 5, 0, Math.PI*2);
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 15;
      ctx.fill();

      // Inner white dot
      ctx.beginPath();
      ctx.arc(p[0], p[1], 2, 0, Math.PI*2);
      ctx.fillStyle = '#fff';
      ctx.shadowBlur = 0;
      ctx.fill();
    }
  });
  ctx.restore();

  // Draw angle labels
  if (CONFIG.showAngles) {
    ctx.save();
    Object.entries(state.lastAngles).forEach(([name, angle]) => {
      if (!ANGLE_JOINTS[name]) return;
      const jointIdx = ANGLE_JOINTS[name][1];
      const p = lmPX(landmarks, jointIdx, w, h);
      const px = p[0], py = p[1];

      // Background bubble
      ctx.fillStyle = 'rgba(4,6,15,0.82)';
      ctx.beginPath();
      ctx.roundRect(px - 28, py - 16, 56, 28, 6);
      ctx.fill();

      // Border
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.shadowColor = color;
      ctx.shadowBlur = 8;
      ctx.stroke();

      // Text
      ctx.fillStyle = color;
      ctx.shadowBlur = 0;
      ctx.font = 'bold 13px "Share Tech Mono"';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${angle}°`, px, py);
    });
    ctx.restore();
  }
}

// ── Rep Counting ────────────────────────────────────────────────────
function countRep(angles, exercise) {
  const ex = EXERCISES[exercise];
  if (!ex.repJoint) return; // Plank — time-based

  const angle = angles[ex.repJoint];
  if (angle === undefined) return;

  if (exercise === 'bicep_curl') {
    // Reverse logic for curls
    if (angle < ex.repUpThreshold && state.repState === 'up') {
      state.repState = 'down';
      updateRepStateUI('down');
    }
    if (angle > ex.repDownThreshold && state.repState === 'down') {
      state.repState = 'up';
      updateRepStateUI('up');
      triggerRep();
    }
  } else {
    if (angle < ex.repDownThreshold && state.repState === 'up') {
      state.repState = 'down';
      updateRepStateUI('down');
    }
    if (angle > ex.repUpThreshold && state.repState === 'down') {
      state.repState = 'up';
      updateRepStateUI('up');
      triggerRep();
    }
  }
}

function triggerRep() {
  state.repCount++;
  state.totalReps++;

  // Animate rep counter
  const el = document.getElementById('rep-number');
  el.textContent = state.repCount;
  el.classList.add('pop');
  setTimeout(() => el.classList.remove('pop'), 250);

  // Update header
  document.getElementById('hdr-reps').textContent = state.repCount;
  document.getElementById('hdr-reps').textContent = state.repCount;

  // Voice feedback
  if (CONFIG.voiceFeedback) {
    speak(`${state.repCount}`);
  }

  addLog(`Rep ${state.repCount}`, state.formScore > 70 ? 'good' : 'bad');
  showToast(`Rep ${state.repCount} ✓`);
}

function updateRepStateUI(s) {
  const chipDown = document.getElementById('chip-down');
  const chipUp   = document.getElementById('chip-up');
  chipDown.classList.toggle('active', s === 'down');
  chipUp.classList.toggle('active',   s === 'up');
}

// ── Pose Results Handler ────────────────────────────────────────────
function onResults(results) {
  const canvas = state.canvasEl;
  const ctx    = state.ctx;
  const video  = state.videoEl;

  if (!canvas || !ctx) return;

  const w = canvas.width  = video.videoWidth  || canvas.offsetWidth;
  const h = canvas.height = video.videoHeight || canvas.offsetHeight;

  ctx.clearRect(0, 0, w, h);

  // Mirror canvas to match flipped video
  ctx.save();
  ctx.scale(-1, 1);
  ctx.translate(-w, 0);

  // Draw video frame
  ctx.drawImage(video, 0, 0, w, h);

  if (results.poseLandmarks && state.sessionActive) {
    const lms = results.poseLandmarks;
    const analyzer = ANALYZERS[state.exercise] || analyzeSquat;
    const analysis = analyzer(lms, w, h);

    state.lastAngles   = analysis.angles;
    state.lastFeedback = analysis.feedback;
    state.formScore    = analysis.score;
    state.scoreBreakdown = analysis.breakdown;

    if (analysis.score > state.bestScore) state.bestScore = analysis.score;

    // Count reps
    countRep(analysis.angles, state.exercise);

    // Draw skeleton
    drawSkeleton(ctx, lms, w, h, analysis.feedback);

    ctx.restore();

    // Update UI
    updateFeedbackUI(analysis.feedback, analysis.score);
    updateAnglesStrip(analysis.angles);
    updateFormScore(analysis.score, analysis.breakdown);
    updateAlertBanner(analysis.feedback);
    updatePulse(analysis.feedback);
    updateHUDQuality(analysis.score);
  } else {
    ctx.restore();
    if (state.sessionActive) {
      updateAlertBanner([{ msg: 'No Pose Detected — Step Back', severity: 'info' }]);
    }
  }

  // FPS
  state.frameCount++;
  const now = Date.now();
  if (now - state.lastFpsTime >= 1000) {
    state.fps = state.frameCount;
    state.frameCount = 0;
    state.lastFpsTime = now;
    document.getElementById('hdr-fps').textContent = state.fps;
  }
}

// ── UI Update Functions ─────────────────────────────────────────────
function updateFeedbackUI(feedback, score) {
  const list = document.getElementById('feedback-list');
  if (!feedback.length) {
    list.innerHTML = '<div class="fb-item info"><div class="fb-icon">💡</div><div class="fb-text">Analyzing pose...</div></div>';
    return;
  }
  const icons = { success:'✅', warning:'⚠️', error:'❌', info:'💡' };
  list.innerHTML = feedback.slice(0, 4).map(fb =>
    `<div class="fb-item ${fb.severity}">
      <div class="fb-icon">${icons[fb.severity] || '•'}</div>
      <div class="fb-text">${fb.msg}</div>
    </div>`
  ).join('');

  // Count corrections
  if (feedback.some(f => f.severity === 'error')) {
    state.corrections++;
    document.getElementById('stat-alerts').textContent = state.corrections;
  }
}

function updateAnglesStrip(angles) {
  const entries = Object.entries(angles).slice(0, 4);
  entries.forEach(([name, val], i) => {
    const chip = document.getElementById(`ac-${i}`);
    if (!chip) return;
    chip.querySelector('.ac-name').textContent = name.replace(/_/g, ' ');
    chip.querySelector('.ac-val').textContent  = `${val}°`;
    // Color by deviation from exercise target
    chip.className = 'angle-chip';
    const ex = EXERCISES[state.exercise];
    if (val >= 75 && val <= 105) chip.classList.add('good');
    else if (val >= 55 && val <= 135) chip.classList.add('warn');
    else chip.classList.add('bad');
  });
  // Clear unused chips
  for (let i = entries.length; i < 4; i++) {
    const chip = document.getElementById(`ac-${i}`);
    if (chip) {
      chip.querySelector('.ac-name').textContent = '—';
      chip.querySelector('.ac-val').textContent  = '—°';
      chip.className = 'angle-chip';
    }
  }
}

function updateFormScore(score, breakdown) {
  const circ  = 364.4;
  const offset = circ - (score / 100) * circ;

  document.getElementById('score-pct').textContent = score;
  document.getElementById('hdr-score').textContent  = score + '%';
  document.getElementById('quality-pct').textContent = score + '%';
  document.getElementById('stat-best').textContent   = state.bestScore + '%';

  const prog = document.getElementById('score-prog');
  prog.style.strokeDashoffset = offset;

  // Grade
  let grade = 'A+';
  if (score < 50) grade = 'F';
  else if (score < 60) grade = 'D';
  else if (score < 70) grade = 'C';
  else if (score < 80) grade = 'B';
  else if (score < 90) grade = 'A';
  document.getElementById('score-grade').textContent = grade;

  // Breakdown bars
  const d = breakdown || { depth: score, alignment: score, balance: score };
  const bars = document.querySelectorAll('.sb-fill');
  if (bars[0]) bars[0].style.width = Math.round(d.depth)     + '%';
  if (bars[1]) bars[1].style.width = Math.round(d.alignment) + '%';
  if (bars[2]) bars[2].style.width = Math.round(d.balance)   + '%';

  // Quality bar in HUD
  const qbar = document.getElementById('quality-bar');
  if (qbar) qbar.style.width = score + '%';

  // Update header chip color
  const hdrScore = document.getElementById('hdr-score');
  hdrScore.style.color = score > 75 ? '#00ffcc' : score > 50 ? '#f59e0b' : '#ef4444';
}

function updateAlertBanner(feedback) {
  const banner = document.getElementById('alert-banner');
  const text   = document.getElementById('alert-text');
  const icon   = document.getElementById('alert-icon');

  if (!feedback.length) return;
  const top = feedback[0];
  const icons = { success:'✅', warning:'⚠️', error:'🚨', info:'⚡' };

  text.textContent = top.msg;
  icon.textContent = icons[top.severity] || '⚡';
  banner.className = 'alert-banner ' + top.severity;
}

function updatePulse(feedback) {
  const dot   = document.querySelector('.pulse-dot');
  const label = document.getElementById('pulse-label');
  const hasError   = feedback.some(f => f.severity === 'error');
  const hasSuccess = feedback.some(f => f.severity === 'success');

  if (hasError) {
    dot.className = 'pulse-dot error';
    label.textContent = 'FIX FORM';
    label.style.color = '#ef4444';
  } else if (hasSuccess) {
    dot.className = 'pulse-dot active';
    label.textContent = 'PERFECT FORM';
    label.style.color = '#10b981';
  } else {
    dot.className = 'pulse-dot active';
    label.textContent = 'TRACKING';
    label.style.color = '#00ffcc';
  }
}

function updateHUDQuality(score) {
  const qbar = document.getElementById('quality-bar');
  if (qbar) qbar.style.width = score + '%';
}

// ── Timer ──────────────────────────────────────────────────────────
let timerInterval = null;
function startTimer() {
  state.startTime = Date.now();
  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
    const m = Math.floor(elapsed / 60);
    const s = elapsed % 60;
    const timeStr = `${m}:${s.toString().padStart(2,'0')}`;
    document.getElementById('hud-timer').textContent  = timeStr;
    document.getElementById('stat-time').textContent  = timeStr;
  }, 1000);
}
function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
}

// ── Session Control ─────────────────────────────────────────────────
async function startSession() {
  try {
    const video  = document.getElementById('webcam');
    const canvas = document.getElementById('output-canvas');
    state.videoEl  = video;
    state.canvasEl = canvas;
    state.ctx      = canvas.getContext('2d');

    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user', frameRate: { ideal: 30 } },
      audio: false
    });
    video.srcObject = stream;
    video.style.display = 'block';

    await new Promise(res => { video.onloadedmetadata = res; });

    // Init MediaPipe Pose
    const pose = new Pose({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    });
    pose.setOptions({
      modelComplexity:      CONFIG.modelComplexity,
      smoothLandmarks:      true,
      enableSegmentation:   false,
      smoothSegmentation:   false,
      minDetectionConfidence: CONFIG.minDetectionConf,
      minTrackingConfidence:  CONFIG.minTrackingConf,
    });
    pose.onResults(onResults);

    const camera = new Camera(video, {
      onFrame: async () => { await pose.send({ image: video }); },
      width: 1280, height: 720
    });
    await camera.start();

    state.pose   = pose;
    state.camera = camera;
    state.sessionActive = true;

    // Update UI
    document.getElementById('cam-overlay').style.display = 'none';
    document.getElementById('live-hud').style.display    = 'flex';
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-stop').disabled  = false;
    document.getElementById('log-list').innerHTML = '';

    startTimer();
    addLog('Session started', 'good');
    showToast('Session Started! 🚀');

  } catch(err) {
    console.error('Camera error:', err);
    showToast('Camera error: ' + err.message, 'error');
    updateAlertBanner([{ msg: 'Camera access denied — check permissions', severity: 'error' }]);
  }
}

function stopSession() {
  state.sessionActive = false;

  if (state.camera) { state.camera.stop(); state.camera = null; }
  if (state.pose)   { state.pose.close();  state.pose   = null; }

  const video = document.getElementById('webcam');
  if (video.srcObject) {
    video.srcObject.getTracks().forEach(t => t.stop());
    video.srcObject = null;
  }
  video.style.display = 'none';

  const ctx = state.ctx;
  if (ctx && state.canvasEl) ctx.clearRect(0, 0, state.canvasEl.width, state.canvasEl.height);

  document.getElementById('cam-overlay').style.display = 'flex';
  document.getElementById('live-hud').style.display    = 'none';
  document.getElementById('btn-start').disabled = false;
  document.getElementById('btn-stop').disabled  = true;
  document.querySelector('.pulse-dot').className = 'pulse-dot';
  document.getElementById('pulse-label').textContent = 'READY';
  document.getElementById('pulse-label').style.color = '';

  stopTimer();
  addLog('Session stopped', 'good');
}

function resetSession() {
  state.repCount  = 0;
  state.repState  = 'up';
  state.bestScore = 100;
  state.corrections = 0;
  state.formScore = 100;
  document.getElementById('rep-number').textContent = '0';
  document.getElementById('hdr-reps').textContent   = '0';
  document.getElementById('stat-total-reps').textContent = '0';
  document.getElementById('stat-alerts').textContent = '0';
  document.getElementById('stat-best').textContent   = '100%';
  updateRepStateUI('up');
  updateFormScore(100, { depth:100, alignment:100, balance:100 });
  showToast('Session Reset ↺');
  addLog('Reset session', 'good');
}

// ── Exercise Selection ──────────────────────────────────────────────
function selectExercise(key) {
  if (!EXERCISES[key]) return;
  state.exercise  = key;
  state.repCount  = 0;
  state.repState  = 'up';

  document.querySelectorAll('.ex-card').forEach(b => b.classList.remove('active'));
  document.querySelector(`[data-ex="${key}"]`).classList.add('active');

  const ex = EXERCISES[key];
  document.getElementById('inst-text').textContent = ex.instruction;
  document.getElementById('hud-exercise').textContent = ex.name.toUpperCase();
  document.getElementById('rep-number').textContent = '0';
  document.getElementById('hdr-reps').textContent   = '0';
  updateRepStateUI('up');

  // Update tips
  const tips = document.getElementById('inst-tips');
  tips.innerHTML = ex.tips.map(t => `<div class="inst-tip">${t}</div>`).join('');

  addLog(`Exercise: ${ex.name}`, 'good');
}

// ── Screenshot ─────────────────────────────────────────────────────
function takeScreenshot() {
  const canvas = document.getElementById('output-canvas');
  if (!canvas) return;
  const link = document.createElement('a');
  link.download = `biomech-${Date.now()}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
  showToast('Screenshot saved! 📸');
}

// ── Gemini AI Coach ─────────────────────────────────────────────────
function openAICoach() {
  const key = state.geminiKey || localStorage.getItem('geminiKey') || '';
  const modal = document.getElementById('ai-modal');
  const noKey = document.getElementById('ai-no-key');

  document.getElementById('ai-ex-chip').textContent    = `Exercise: ${EXERCISES[state.exercise]?.name || '—'}`;
  document.getElementById('ai-score-chip').textContent = `Score: ${state.formScore}%`;
  document.getElementById('ai-rep-chip').textContent   = `Reps: ${state.repCount}`;

  noKey.style.display = key ? 'none' : 'block';
  modal.style.display = 'flex';
}

function closeAICoach() {
  document.getElementById('ai-modal').style.display = 'none';
}

async function runGeminiAnalysis() {
  const key = state.geminiKey || localStorage.getItem('geminiKey') || '';
  if (!key) {
    document.getElementById('ai-no-key').style.display = 'block';
    return;
  }

  const area    = document.getElementById('ai-response-area');
  const btn     = document.getElementById('ai-analyze-btn');
  btn.disabled = true;

  area.innerHTML = `
    <div class="ai-loading-wrap">
      <div class="ai-spinner"></div>
      <div class="ai-loading-text">GEMINI 2.5 FLASH ANALYZING...</div>
    </div>`;

  const ex = EXERCISES[state.exercise] || {};
  const prompt = `You are an elite AI biomechanical coach and physiotherapist with expertise in sports science.

Analyze this real-time exercise data:
- Exercise: ${ex.name || state.exercise}
- Form Score: ${state.formScore}/100
- Reps Completed: ${state.repCount}
- Joint Angles (degrees):
${Object.entries(state.lastAngles).map(([k,v]) => `  • ${k.replace(/_/g,' ')}: ${v}°`).join('\n')}
- Live Feedback Flags: ${state.lastFeedback.map(f => f.msg).join(', ') || 'None'}
- Exercise Targets: ${JSON.stringify(ex.checkpoints || {})}

Provide a structured, high-energy biomechanical coaching response:

**FORM ASSESSMENT** (2 sentences using specific angle values)
**TOP 3 CORRECTIONS** (with biomechanical reasoning for each)
**MUSCLE ACTIVATION TIP** (one specific technique cue)
**MOTIVATIONAL PUSH** (one sentence, energetic)

Be technically precise, use anatomical terms, cite specific angles. Max 250 words.`;

  try {
    const resp = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${key}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.7, maxOutputTokens: 512 }
        })
      }
    );

    if (!resp.ok) {
      const errData = await resp.json();
      throw new Error(errData?.error?.message || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || 'No response received.';

    // Format markdown-style response
    const formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#a78bfa;font-family:\'Michroma\',monospace;font-size:11px;letter-spacing:2px;">$1</strong>')
      .replace(/\n/g, '<br>');

    area.innerHTML = `<div class="ai-text">${formatted}</div>`;
    addLog('AI Analysis complete', 'good');

  } catch(err) {
    area.innerHTML = `<div class="ai-text" style="color:#f87171;">
      ❌ Gemini Error: ${err.message}<br><br>
      Check your API key in Settings ⚙<br>
      <a href="https://aistudio.google.com" target="_blank" style="color:#a78bfa;">Get free key →</a>
    </div>`;
  } finally {
    btn.disabled = false;
  }
}

// ── Settings ────────────────────────────────────────────────────────
function toggleSettings() {
  const modal = document.getElementById('settings-modal');
  const key   = localStorage.getItem('geminiKey') || '';
  document.getElementById('gemini-key-input').value = key;
  modal.style.display = modal.style.display === 'none' ? 'flex' : 'none';
}

function closeSettings() {
  document.getElementById('settings-modal').style.display = 'none';
}

function saveSettings() {
  const key  = document.getElementById('gemini-key-input').value.trim();
  if (key) { localStorage.setItem('geminiKey', key); state.geminiKey = key; }

  CONFIG.skeletonStyle  = document.getElementById('skeleton-style').value;
  CONFIG.showAngles     = document.getElementById('show-angles').checked;
  CONFIG.showSkeleton   = document.getElementById('show-skeleton').checked;
  CONFIG.voiceFeedback  = document.getElementById('voice-feedback').checked;
  const conf = parseInt(document.getElementById('conf-slider').value);
  CONFIG.minDetectionConf = conf / 100;
  CONFIG.minTrackingConf  = conf / 100;

  closeSettings();
  showToast('Settings Saved ✓');
}

// ── Voice Feedback ──────────────────────────────────────────────────
function speak(text) {
  if (!window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.1; u.pitch = 1; u.volume = 0.8;
  window.speechSynthesis.speak(u);
}

// ── Activity Log ────────────────────────────────────────────────────
function addLog(msg, type = 'good') {
  const log = document.getElementById('log-list');
  const empty = log.querySelector('.log-empty');
  if (empty) log.innerHTML = '';

  const time = new Date().toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  const item = document.createElement('div');
  item.className = `log-item ${type}`;
  item.innerHTML = `<span>${msg}</span><span class="log-time">${time}</span>`;
  log.prepend(item);
  if (log.children.length > 15) log.removeChild(log.lastChild);
}

// ── Toast ────────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.style.background = type === 'error' ? 'rgba(239,68,68,0.9)' : 'rgba(16,185,129,0.9)';
  toast.classList.add('show');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
}

// ── Background Canvas ───────────────────────────────────────────────
function initBackground() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w = canvas.width  = window.innerWidth;
  let h = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    w = canvas.width  = window.innerWidth;
    h = canvas.height = window.innerHeight;
  });

  const nodes = Array.from({length: 60}, () => ({
    x: Math.random() * w, y: Math.random() * h,
    vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3,
    r: Math.random()*1.5+0.5,
  }));

  function draw() {
    ctx.clearRect(0,0,w,h);

    // Grid
    ctx.strokeStyle = 'rgba(0,255,204,0.03)';
    ctx.lineWidth = 1;
    for (let x=0; x<w; x+=60) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,h); ctx.stroke(); }
    for (let y=0; y<h; y+=60) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(w,y); ctx.stroke(); }

    // Nodes
    nodes.forEach(n => {
      n.x += n.vx; n.y += n.vy;
      if (n.x<0||n.x>w) n.vx*=-1;
      if (n.y<0||n.y>h) n.vy*=-1;

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(0,255,204,0.4)';
      ctx.fill();
    });

    // Connections
    ctx.strokeStyle = 'rgba(0,255,204,0.06)';
    ctx.lineWidth = 1;
    for (let i=0; i<nodes.length; i++) {
      for (let j=i+1; j<nodes.length; j++) {
        const d = Math.hypot(nodes[i].x-nodes[j].x, nodes[i].y-nodes[j].y);
        if (d < 120) {
          ctx.globalAlpha = (1 - d/120) * 0.3;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }
  draw();
}

// ── Confidence Slider UI ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const slider = document.getElementById('conf-slider');
  const valEl  = document.getElementById('conf-val');
  if (slider && valEl) {
    slider.addEventListener('input', () => { valEl.textContent = slider.value + '%'; });
  }
});

// ── Splash / Model Loading ──────────────────────────────────────────
async function initApp() {
  initBackground();

  const fill    = document.getElementById('loading-fill');
  const loadTxt = document.getElementById('loading-text');
  const ssTf    = document.getElementById('ss-tf');
  const ssMp    = document.getElementById('ss-mp');
  const ssCam   = document.getElementById('ss-cam');

  // Step 1 — Load TF
  loadTxt.textContent = 'Loading MediaPipe libraries...';
  fill.style.width = '20%';
  await sleep(600);
  ssTf.textContent = '✓';

  // Step 2 — Pose model
  loadTxt.textContent = 'Initializing Pose Detection Model...';
  fill.style.width = '55%';
  await sleep(900);
  ssMp.textContent = '✓';

  // Step 3 — Camera check
  loadTxt.textContent = 'Checking Camera Permissions...';
  fill.style.width = '80%';
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cams = devices.filter(d => d.kind === 'videoinput');
    ssCam.textContent = cams.length > 0 ? `${cams.length}✓` : '?';
  } catch(e) {
    ssCam.textContent = '?';
  }
  await sleep(500);

  // Step 4 — Done
  loadTxt.textContent = 'System Ready. Launching...';
  fill.style.width = '100%';
  await sleep(600);

  // Load saved settings
  state.geminiKey = localStorage.getItem('geminiKey') || '';

  // Transition to app
  document.getElementById('splash').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Boot ────────────────────────────────────────────────────────────
initApp();
