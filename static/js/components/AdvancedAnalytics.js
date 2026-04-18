/**
 * Advanced Analytics Dashboard
 * Cohort analysis, funnel tracking, retention metrics, and segmentation
 * TIER 12 - Advanced Analytics System
 */

export const AdvancedAnalytics = {

    cohorts: {},
    funnels: {},
    segments: {},
    retentionData: {},

    showAnalyticsUI() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7); z-index: 2800;
            display: flex; align-items: center; justify-content: center;
            overflow-y: auto;
        `;

        modal.innerHTML = `
            <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 16px; 
                        padding: 24px; max-width: 1000px; width: 95%; margin: 20px 0;">
                
                <h2 style="font-family: var(--font-hud); font-size: 1.2rem; letter-spacing: 2px; 
                           color: #a78bfa; margin-bottom: 20px;">
                    📊 ADVANCED ANALYTICS
                </h2>

                <!-- Tab Navigation -->
                <div style="display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 12px;">
                    <button onclick="window.AdvancedAnalytics.showCohortAnalysis()" 
                            style="padding: 8px 16px; background: rgba(167,139,250,0.2); border: none; 
                                    border-radius: 6px; color: var(--purple2); cursor: pointer; font-weight: 600;">
                        👥 COHORT ANALYSIS
                    </button>
                    <button onclick="window.AdvancedAnalytics.showFunnelAnalysis()" 
                            style="padding: 8px 16px; background: transparent; border: none; 
                                    border-radius: 6px; color: var(--text2); cursor: pointer;">
                        📈 FUNNEL
                    </button>
                    <button onclick="window.AdvancedAnalytics.showRetentionCurve()" 
                            style="padding: 8px 16px; background: transparent; border: none; 
                                    border-radius: 6px; color: var(--text2); cursor: pointer;">
                        📉 RETENTION
                    </button>
                    <button onclick="window.AdvancedAnalytics.showSegmentation()" 
                            style="padding: 8px 16px; background: transparent; border: none; 
                                    border-radius: 6px; color: var(--text2); cursor: pointer;">
                        🔹 SEGMENTS
                    </button>
                </div>

                <!-- Cohort Analysis -->
                <div id="cohort-view" style="display: grid; gap: 12px;">
                    <h3 style="font-size: 0.95rem; color: var(--purple2); margin-bottom: 8px;">COHORT RETENTION TABLE</h3>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; font-size: 0.8rem; color: var(--text2); text-align: center;">
                            <thead>
                                <tr style="border-bottom: 1px solid var(--border);">
                                    <th style="padding: 8px; text-align: left;">Cohort</th>
                                    <th style="padding: 8px;">Day 0</th>
                                    <th style="padding: 8px;">Day 1</th>
                                    <th style="padding: 8px;">Day 7</th>
                                    <th style="padding: 8px;">Day 14</th>
                                    <th style="padding: 8px;">Day 30</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                    <td style="padding: 8px; text-align: left; color: var(--cyan);">Apr 1-7</td>
                                    <td style="padding: 8px; background: rgba(16,185,129,0.2);">100%</td>
                                    <td style="padding: 8px;">68%</td>
                                    <td style="padding: 8px;">45%</td>
                                    <td style="padding: 8px;">32%</td>
                                    <td style="padding: 8px;">18%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                    <td style="padding: 8px; text-align: left; color: var(--cyan);">Apr 8-14</td>
                                    <td style="padding: 8px; background: rgba(16,185,129,0.2);">100%</td>
                                    <td style="padding: 8px;">72%</td>
                                    <td style="padding: 8px;">48%</td>
                                    <td style="padding: 8px;">35%</td>
                                    <td style="padding: 8px;">-</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; text-align: left; color: var(--cyan);">Apr 15-21</td>
                                    <td style="padding: 8px; background: rgba(16,185,129,0.2);">100%</td>
                                    <td style="padding: 8px;">75%</td>
                                    <td style="padding: 8px;">52%</td>
                                    <td style="padding: 8px;">-</td>
                                    <td style="padding: 8px;">-</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Funnel Analysis -->
                <div id="funnel-view" style="display: none; gap: 12px;">
                    <h3 style="font-size: 0.95rem; color: var(--purple2); margin-bottom: 12px;">USER FUNNEL</h3>
                    <div style="display: grid; gap: 8px;">
                        ${this.renderFunnelStage('Sign Up', 10000, 100)}
                        ${this.renderFunnelStage('Complete First Session', 8200, 82)}
                        ${this.renderFunnelStage('Use AI Coaching', 5904, 72)}
                        ${this.renderFunnelStage('Set Personal Goals', 3541, 60)}
                        ${this.renderFunnelStage('Subscribe (Upgrade)', 1416, 40)}
                    </div>
                </div>

                <!-- Retention Curve -->
                <div id="retention-view" style="display: none;">
                    <h3 style="font-size: 0.95rem; color: var(--purple2); margin-bottom: 12px;">RETENTION CURVE (D0-D30)</h3>
                    <div style="height: 200px; background: rgba(0,0,0,0.3); border-radius: 8px; 
                                display: flex; align-items: flex-end; gap: 4px; padding: 16px; justify-content: center;">
                        ${[100, 68, 52, 42, 35, 28, 22, 18, 15, 12, 10, 8, 6, 5, 4, 3, 2, 2, 1, 1, 1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.3, 0.2, 0.2, 0.1, 0.1]
                            .map((val, idx) => `<div style="flex: 1; background: linear-gradient(180deg, rgba(16,185,129,0.6), rgba(16,185,129,0.3)); height: ${val}%; border-radius: 2px;" title="Day ${idx}: ${val}%"></div>`)
                            .join('')}
                    </div>
                    <div style="margin-top: 12px; font-size: 0.8rem; color: var(--text2); text-align: center;">
                        Day 1 Retention: 68% | Day 7 Retention: 22% | Day 30 Retention: 0.1%
                    </div>
                </div>

                <!-- Segmentation -->
                <div id="segment-view" style="display: none; gap: 12px;">
                    <h3 style="font-size: 0.95rem; color: var(--purple2); margin-bottom: 12px;">USER SEGMENTS</h3>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border-left: 3px solid #10b981;">
                            <div style="font-weight: 600; color: #10b981; margin-bottom: 8px;">💪 Power Users</div>
                            <div style="font-size: 0.85rem; line-height: 1.4; color: var(--text2);">
                                • 45% of users<br>
                                • 20+ sessions/month<br>
                                • High AI coach usage<br>
                                • 82% retention rate
                            </div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border-left: 3px solid var(--cyan);">
                            <div style="font-weight: 600; color: var(--cyan); margin-bottom: 8px;">🏃 Casual Users</div>
                            <div style="font-size: 0.85rem; line-height: 1.4; color: var(--text2);">
                                • 35% of users<br>
                                • 3-10 sessions/month<br>
                                • Moderate AI usage<br>
                                • 48% retention rate
                            </div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border-left: 3px solid var(--purple2);">
                            <div style="font-weight: 600; color: var(--purple2); margin-bottom: 8px;">🎯 Focused Athletes</div>
                            <div style="font-size: 0.85rem; line-height: 1.4; color: var(--text2);">
                                • 15% of users<br>
                                • Form-focused sessions<br>
                                • Heavy injury prevention use<br>
                                • 75% retention rate
                            </div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border-left: 3px solid #f59e0b;">
                            <div style="font-weight: 600; color: #f59e0b; margin-bottom: 8px;">👤 One-Time Users</div>
                            <div style="font-size: 0.85rem; line-height: 1.4; color: var(--text2);">
                                • 5% of users<br>
                                • 1-2 sessions total<br>
                                • Minimal engagement<br>
                                • 5% retention rate
                            </div>
                        </div>
                    </div>
                </div>

                <button onclick="this.parentElement.parentElement.remove()" 
                        style="width: 100%; margin-top: 20px; padding: 10px; 
                                background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); 
                                border-radius: 6px; color: var(--text2); cursor: pointer;">
                    CLOSE
                </button>
            </div>
        `;

        document.body.appendChild(modal);
    },

    renderFunnelStage(stage, count, percentage) {
        return `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="flex: 1; background: rgba(16,185,129,0.1); padding: 12px; border-radius: 8px; 
                            display: flex; justify-content: space-between;">
                    <span style="font-weight: 600; color: var(--cyan);">${stage}</span>
                    <span style="color: var(--text2);">${count.toLocaleString()} users</span>
                </div>
                <div style="width: 60px; background: linear-gradient(90deg, rgba(16,185,129,0.6), rgba(16,185,129,0.3)); 
                            height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: center;
                            font-size: 0.75rem; color: white; font-weight: 600;">
                    ${percentage}%
                </div>
            </div>
        `;
    },

    showCohortAnalysis() {
        document.getElementById('cohort-view').style.display = 'grid';
        document.getElementById('funnel-view').style.display = 'none';
        document.getElementById('retention-view').style.display = 'none';
        document.getElementById('segment-view').style.display = 'none';
    },

    showFunnelAnalysis() {
        document.getElementById('cohort-view').style.display = 'none';
        document.getElementById('funnel-view').style.display = 'grid';
        document.getElementById('retention-view').style.display = 'none';
        document.getElementById('segment-view').style.display = 'none';
    },

    showRetentionCurve() {
        document.getElementById('cohort-view').style.display = 'none';
        document.getElementById('funnel-view').style.display = 'none';
        document.getElementById('retention-view').style.display = 'block';
        document.getElementById('segment-view').style.display = 'none';
    },

    showSegmentation() {
        document.getElementById('cohort-view').style.display = 'none';
        document.getElementById('funnel-view').style.display = 'none';
        document.getElementById('retention-view').style.display = 'none';
        document.getElementById('segment-view').style.display = 'grid';
    }
};

window.AdvancedAnalytics = AdvancedAnalytics;

export default AdvancedAnalytics;
