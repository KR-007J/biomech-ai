/**
 * Biomech AI - Enhanced Backend Integration Logic
 * Handles structured AI output, metrics, and visualization
 */

import { AngleChart } from './components/AngleChart.js';
import { RiskMeter } from './components/RiskMeter.js';
import { TimelineChart } from './components/TimelineChart.js';

window.handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const alertBanner = document.getElementById('alert-banner');
    const alertText = document.getElementById('alert-text');
    alertBanner.className = 'alert-banner warning';
    alertText.innerHTML = `<span class="loader-spinner"></span> INITIALIZING SECURE AI CHANNEL...`;

    try {
        // Since we are on Supabase free tier, we process the metadata 
        // and current session metrics rather than uploading GBs of video.
        
        // Mocking the 'metrics' gathering - in a real session, 
        // this would be the aggregated state.sessions data.
        const sessionData = window.state?.sessionLogs || [];
        const currentExercise = window.state?.exercise || "General Workout";
        
        // For demonstration, we'll use the latest real-time frame or average
        const metrics = {
            angles: window.state?.currentAngles || {},
            deviations: window.state?.currentDeviations || {},
            ideal_ranges: {
                knee: { min: 85, max: 100 },
                elbow: { min: 45, max: 160 },
                hip: { min: 70, max: 180 }
            },
            pose_confidence: 0.95
        };

        alertText.innerHTML = `<span class="loader-spinner"></span> COMMUNICATING WITH GEMINI AI COACH...`;
        
        const finalResults = await window.BiomechApi.analyzeMetrics(
            metrics, 
            currentExercise, 
            window.db?.googleUser?.sub
        );

        if (finalResults.status === 'completed') {
            displayBackendResults(finalResults);
            alertBanner.className = 'alert-banner success';
            alertText.innerText = 'SUPABASE AI ANALYSIS COMPLETE';
        } else {
            throw new Error(finalResults.error || 'Analysis failed');
        }
    } catch (error) {
        console.error('Supabase Processing Error:', error);
        alertBanner.className = 'alert-banner error';
        alertText.innerText = 'AI OFFLINE: CHECK SUPABASE SECRETS';
    }
};


function displayBackendResults(results) {
    const aiModal = document.getElementById('ai-modal');
    aiModal.style.display = 'flex';

    const responseArea = document.getElementById('ai-response-area');
    
    // Inject enhanced UI components
    responseArea.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 20px; font-family: 'Inter', sans-serif;">
            
            <!-- Performance Metrics Header -->
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                <div class="metric-card">
                    <label>PROCESSING TIME</label>
                    <value>${results.performance_metrics.total_processing_time}</value>
                </div>
                <div class="metric-card">
                    <label>AVG LATENCY</label>
                    <value>${results.performance_metrics.avg_latency_per_frame}</value>
                </div>
                <div class="metric-card">
                    <label>SYS ACCURACY</label>
                    <value>${results.performance_metrics.estimated_accuracy}</value>
                </div>
            </div>

            <div id="backend-risk-meter"></div>
            
            <!-- Biomechanical Radar -->
            <div style="background: rgba(0,255,204,0.03); padding: 15px; border-radius: 10px; border: 1px solid rgba(0,255,204,0.1);">
                <div class="section-tag" style="color: #00ffcc;">JOINT KINEMATICS RADAR</div>
                <div style="height: 220px;">
                    <canvas id="backend-angle-chart"></canvas>
                </div>
            </div>

            <!-- Time Series Timeline -->
            <div style="background: rgba(167, 139, 250, 0.03); padding: 15px; border-radius: 10px; border: 1px solid rgba(167, 139, 250, 0.1);">
                <div class="section-tag" style="color: #a78bfa;">MOVEMENT PROGRESSION (TIMELINE)</div>
                <div style="height: 150px;">
                    <canvas id="backend-timeline-chart"></canvas>
                </div>
            </div>

            <!-- Gemini AI Structured Coaching -->
            <div style="background: rgba(255,255,255,0.02); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); position: relative; overflow: hidden;">
                <div class="section-tag" style="color: #6366f1;">GEMINI AI COACHING ENGINE</div>
                <div style="margin-top: 15px;">
                    <div style="font-weight: 700; color: #ff3366; font-size: 0.9rem; margin-bottom: 5px;">ISSUE:</div>
                    <div style="color: #e2e8f0; font-size: 0.85rem; margin-bottom: 12px;">${results.coach_feedback.issue}</div>
                    
                    <div style="font-weight: 700; color: #00ffcc; font-size: 0.9rem; margin-bottom: 5px;">ANALYSIS:</div>
                    <div style="color: #e2e8f0; font-size: 0.85rem; margin-bottom: 12px;">${results.coach_feedback.reason}</div>
                    
                    <div style="font-weight: 700; color: #6366f1; font-size: 0.9rem; margin-bottom: 5px;">CORRECTIVE ACTION:</div>
                    <div style="color: #e2e8f0; font-size: 0.85rem; padding: 10px; background: rgba(99,102,241,0.1); border-left: 3px solid #6366f1; border-radius: 4px;">
                        ${results.coach_feedback.fix}
                    </div>
                </div>
            </div>
        </div>
    `;

    // Initialize Components
    setTimeout(() => {
        RiskMeter('backend-risk-meter', results.summary.risk);
        AngleChart('backend-angle-chart', results.summary.angles);
        TimelineChart('backend-timeline-chart', results.time_series);
    }, 100);
}

// Add CSS for metric cards if not already in index.css
const style = document.createElement('style');
style.innerHTML = `
    .metric-card {
        background: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .metric-card label {
        display: block;
        font-size: 10px;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 4px;
        letter-spacing: 0.5px;
    }
    .metric-card value {
        display: block;
        font-size: 13px;
        color: #fff;
        font-weight: 700;
        font-family: 'Michroma', sans-serif;
    }
    .section-tag {
        font-family: 'Michroma', sans-serif;
        font-size: 0.65rem;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .loader-spinner {
        display: inline-block;
        width: 12px;
        height: 12px;
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
        margin-right: 8px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
`;
document.head.appendChild(style);
