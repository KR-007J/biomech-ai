/**
 * SkeletonOverlay Component
 * Renders the MediaPipe skeleton on a canvas
 */
export const SkeletonOverlay = (ctx, landmarks, options = {}) => {
    if (!landmarks || !ctx) return;

    const { 
        color = '#00ffcc', 
        lineWidth = 3, 
        pointRadius = 4 
    } = options;

    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.fillStyle = color;

    // Define connections (based on MediaPipe Pose)
    const connections = [
        [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], // Upper body
        [11, 23], [12, 24], [23, 24],                   // Torso
        [23, 25], [25, 27], [24, 26], [26, 28]         // Legs
    ];

    // Draw lines
    connections.forEach(([i, j]) => {
        const p1 = landmarks[i];
        const p2 = landmarks[j];
        if (p1.visibility > 0.5 && p2.visibility > 0.5) {
            ctx.beginPath();
            ctx.moveTo(p1.x * ctx.canvas.width, p1.y * ctx.canvas.height);
            ctx.lineTo(p2.x * ctx.canvas.width, p2.y * ctx.canvas.height);
            ctx.stroke();
        }
    });

    // Draw points
    landmarks.forEach((landmark) => {
        if (landmark.visibility > 0.5) {
            ctx.beginPath();
            ctx.arc(landmark.x * ctx.canvas.width, landmark.y * ctx.canvas.height, pointRadius, 0, 2 * Math.PI);
            ctx.fill();
        }
    });

    ctx.restore();
};
