/**
 * RiskMeter Component
 * Displays a visual gauge for injury risk
 */
export const RiskMeter = (containerId, riskInfo) => {
    const container = document.getElementById(containerId);
    const { risk_level, risk_score, explanation } = riskInfo;
    
    let color = '#10b981'; // LOW
    if (risk_level === 'MEDIUM') color = '#f59e0b';
    if (risk_level === 'HIGH') color = '#ef4444';

    container.innerHTML = `
        <div class="risk-meter-wrap" style="text-align: center; padding: 10px; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; background: rgba(0,0,0,0.2);">
            <div class="risk-header" style="font-family: 'Michroma', sans-serif; font-size: 0.7rem; color: ${color}; letter-spacing: 2px; margin-bottom: 8px;">
                RISK LEVEL: ${risk_level}
            </div>
            <div class="risk-bar" style="height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; margin-bottom: 12px;">
                <div class="risk-fill" style="height: 100%; width: ${risk_score}%; background: ${color}; transition: width 1s ease;"></div>
            </div>
            <p class="risk-explanation" style="font-size: 0.7rem; color: #94a3b8; line-height: 1.4;">
                ${explanation}
            </p>
        </div>
    `;
};
