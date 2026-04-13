/**
 * Biomech AI - Backend Integration Logic
 * Handles video uploads and result visualization
 */

import { AngleChart } from './components/AngleChart.js';
import { RiskMeter } from './components/RiskMeter.js';

window.handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Show processing state in UI
    const alertBanner = document.getElementById('alert-banner');
    const alertText = document.getElementById('alert-text');
    alertBanner.className = 'alert-banner warning';
    alertText.innerText = 'Uploading video for AI analysis...';

    try {
        const uploadResult = await window.BiomechApi.uploadVideo(file);
        const jobId = uploadResult.job_id;

        alertText.innerText = 'AI is processing biomechanics (0%)...';

        // Poll for results
        const finalResults = await window.BiomechApi.pollForResults(jobId, (progress) => {
            alertText.innerText = `AI is processing biomechanics (${progress}%)...`;
        });

        if (finalResults.status === 'completed') {
            displayBackendResults(finalResults);
            alertBanner.className = 'alert-banner success';
            alertText.innerText = 'AI Analysis Complete!';
        } else {
            throw new Error(finalResults.message || 'Analysis failed');
        }
    } catch (error) {
        console.error('Processing Error:', error);
        alertBanner.className = 'alert-banner error';
        alertText.innerText = 'Error: ' + error.message;
    }
};

function displayBackendResults(results) {
    // Open AI Coach Modal to show results
    const aiModal = document.getElementById('ai-modal');
    aiModal.style.display = 'flex';

    const responseArea = document.getElementById('ai-response-area');
    responseArea.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 20px;">
            <div id="backend-risk-meter"></div>
            
            <div style="background: rgba(0,255,204,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(0,255,204,0.2);">
                <div style="font-family: 'Michroma', sans-serif; font-size: 0.7rem; color: #00ffcc; margin-bottom: 10px;">
                    BIOMECHANICAL SIGNATURE
                </div>
                <div style="height: 200px;">
                    <canvas id="backend-angle-chart"></canvas>
                </div>
            </div>

            <div style="background: rgba(124,58,237,0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(124,58,237,0.3);">
                <div style="font-family: 'Michroma', sans-serif; font-size: 0.7rem; color: #a78bfa; margin-bottom: 10px;">
                    GEMINI AI COACHING
                </div>
                <div style="font-size: 0.85rem; color: #e2e8f0; line-height: 1.6;">
                    ${results.feedback}
                </div>
            </div>
        </div>
    `;

    // Initialize Components
    setTimeout(() => {
        RiskMeter('backend-risk-meter', results.risk);
        AngleChart('backend-angle-chart', results.angles);
    }, 100);
}
