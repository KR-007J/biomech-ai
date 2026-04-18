/**
 * Fraud Detection & Behavioral Analysis Dashboard
 * Monitors suspicious activities, anomalies, and user behavior patterns
 * TIER 12 - Fraud Detection System
 */

export const FraudDetectionMonitor = {

    suspiciousActivities: [],
    behavioralProfiles: {},
    riskThresholds: {
        impossible_rep_speed: 0.8,
        unnatural_angles: 0.7,
        too_perfect_form: 0.6,
        pattern_mismatch: 0.75
    },

    async analyzeBehavior(userId, sessionMetrics) {
        try {
            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';
            
            const response = await fetch(`${apiUrl}/fraud-detection/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}`
                },
                body: JSON.stringify({
                    user_id: userId,
                    metrics: sessionMetrics,
                    historical_data: this.behavioralProfiles[userId] || {}
                })
            });

            if (!response.ok) throw new Error('Fraud analysis failed');

            const analysis = await response.json();
            
            if (analysis.is_suspicious) {
                this.handleSuspiciousActivity(userId, analysis);
            }

            return analysis;

        } catch (error) {
            console.error('Behavior analysis error:', error);
        }
    },

    handleSuspiciousActivity(userId, analysis) {
        const activity = {
            userId,
            timestamp: new Date(),
            riskScore: analysis.risk_score,
            reasons: analysis.reasons,
            severity: analysis.severity
        };

        this.suspiciousActivities.push(activity);
        this.notifyAdmin(activity);

        if (analysis.severity === 'CRITICAL') {
            this.flagAccount(userId);
        }
    },

    notifyAdmin(activity) {
        const alert = document.createElement('div');
        alert.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 5000;
            background: ${activity.severity === 'CRITICAL' ? '#ef4444' : activity.severity === 'HIGH' ? '#f59e0b' : '#6366f1'};
            color: white; padding: 16px; border-radius: 8px;
            max-width: 300px; font-size: 0.85rem; line-height: 1.4;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        `;

        alert.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 8px;">
                🚨 ${activity.severity} ALERT: SUSPICIOUS ACTIVITY
            </div>
            <div style="margin-bottom: 8px;">
                User: ${activity.userId.substring(0, 12)}...
            </div>
            <div style="margin-bottom: 8px; font-size: 0.8rem; opacity: 0.9;">
                ${activity.reasons.join(' • ')}
            </div>
            <div style="font-size: 0.75rem; opacity: 0.8;">
                Risk Score: ${(activity.riskScore * 100).toFixed(0)}%
            </div>
        `;

        document.body.appendChild(alert);

        setTimeout(() => {
            alert.remove();
        }, 8000);
    },

    flagAccount(userId) {
        console.warn(`🚨 CRITICAL: Account flagged for review: ${userId}`);
        // This would typically trigger an admin review workflow
    },

    showFraudDetectionUI() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7); z-index: 2700;
            display: flex; align-items: center; justify-content: center;
            overflow-y: auto;
        `;

        modal.innerHTML = `
            <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 16px; 
                        padding: 24px; max-width: 900px; width: 95%; margin: 20px 0;">
                
                <h2 style="font-family: var(--font-hud); font-size: 1.2rem; letter-spacing: 2px; 
                           color: #ef4444; margin-bottom: 20px;">
                    🚨 FRAUD DETECTION MONITOR
                </h2>

                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
                    <div style="background: rgba(239,68,68,0.1); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 600; color: #ef4444;">
                            ${this.suspiciousActivities.length}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text2);">ALERTS</div>
                    </div>
                    <div style="background: rgba(245,158,11,0.1); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 600; color: #f59e0b;">
                            ${this.suspiciousActivities.filter(a => a.severity === 'HIGH').length}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text2);">HIGH RISK</div>
                    </div>
                    <div style="background: rgba(239,68,68,0.1); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 600; color: #ef4444;">
                            ${this.suspiciousActivities.filter(a => a.severity === 'CRITICAL').length}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text2);">CRITICAL</div>
                    </div>
                    <div style="background: rgba(99,102,241,0.1); padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 600; color: #6366f1;">
                            ${Object.keys(this.behavioralProfiles).length}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text2);">PROFILED USERS</div>
                    </div>
                </div>

                <!-- Recent Suspicious Activities -->
                <div style="background: rgba(0,0,0,0.3); padding: 16px; border-radius: 12px; border: 1px solid var(--border);">
                    <h3 style="font-size: 0.95rem; color: #ef4444; margin-bottom: 12px;">RECENT SUSPICIOUS ACTIVITIES</h3>
                    <div style="display: grid; gap: 8px; max-height: 300px; overflow-y: auto;">
                        ${this.suspiciousActivities.length === 0 ? 
                          '<div style="text-align: center; color: var(--text2); padding: 20px;">✅ No suspicious activities detected</div>' :
                          this.suspiciousActivities.slice(-10).reverse().map(activity => `
                            <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; 
                                        border-left: 3px solid ${activity.severity === 'CRITICAL' ? '#ef4444' : activity.severity === 'HIGH' ? '#f59e0b' : '#6366f1'};">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                    <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--cyan);">
                                        ${activity.userId.substring(0, 12)}...
                                    </span>
                                    <span style="font-size: 0.7rem; background: ${activity.severity === 'CRITICAL' ? '#ef444433' : activity.severity === 'HIGH' ? '#f59e0b33' : '#6366f133'}; 
                                                 color: ${activity.severity === 'CRITICAL' ? '#ef4444' : activity.severity === 'HIGH' ? '#f59e0b' : '#6366f1'};
                                                 padding: 2px 6px; border-radius: 3px;">
                                        ${activity.severity}
                                    </span>
                                </div>
                                <div style="font-size: 0.75rem; color: var(--text2); margin-bottom: 6px;">
                                    ${activity.reasons.join(', ')}
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 0.7rem;">
                                    <span>Risk: ${(activity.riskScore * 100).toFixed(0)}%</span>
                                    <span style="color: var(--text2);">${this.getTimeAgo(activity.timestamp)}</span>
                                </div>
                            </div>
                          `).join('')
                        }
                    </div>
                </div>

                <div style="margin-top: 16px; padding: 12px; background: rgba(0,255,204,0.05); 
                            border-radius: 8px; border-left: 3px solid var(--cyan); font-size: 0.8rem; 
                            color: var(--text2); line-height: 1.5;">
                    <strong>Detection Methods:</strong><br>
                    • Impossible rep speeds & unnatural angles<br>
                    • Form consistency anomalies<br>
                    • Behavioral pattern deviations<br>
                    • Account activity time patterns
                </div>

                <button onclick="this.parentElement.parentElement.remove()" 
                        style="width: 100%; margin-top: 16px; padding: 10px; 
                                background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); 
                                border-radius: 6px; color: var(--text2); cursor: pointer;">
                    CLOSE
                </button>
            </div>
        `;

        document.body.appendChild(modal);
    },

    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        return `${Math.floor(seconds / 3600)}h ago`;
    }
};

window.FraudDetectionMonitor = FraudDetectionMonitor;

export default FraudDetectionMonitor;
