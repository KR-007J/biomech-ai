/**
 * Report Generation & Download Component
 * Handles session reports, PDF export, HTML download, and session comparison
 * TIER 4 - Analytics & Reporting System
 */

export const ReportGenerator = {
    
    async generateAndDownloadReport(sessionId, format = 'html', userId = null) {
        try {
            const alertBanner = document.getElementById('alert-banner');
            const alertText = document.getElementById('alert-text');
            
            alertBanner.className = 'alert-banner warning';
            alertText.innerHTML = `<span class="loader-spinner"></span> GENERATING ${format.toUpperCase()} REPORT...`;

            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';
            
            if (format === 'html') {
                // Fetch HTML report directly
                const response = await fetch(`${apiUrl}/reports/html/${sessionId}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}` }
                });

                if (!response.ok) throw new Error('Failed to generate report');

                const html = await response.text();
                
                // Create and download HTML file
                const element = document.createElement("a");
                element.setAttribute("href", "data:text/html;charset=utf-8," + encodeURIComponent(html));
                element.setAttribute("download", `biomech-report-${sessionId}.html`);
                element.style.display = "none";
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);

            } else if (format === 'pdf') {
                // Use backend PDF generation
                const response = await fetch(`${apiUrl}/reports/generate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}`
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        format: 'pdf',
                        user_id: userId
                    })
                });

                if (!response.ok) throw new Error('Failed to generate PDF');

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const element = document.createElement("a");
                element.setAttribute("href", url);
                element.setAttribute("download", `biomech-report-${sessionId}.pdf`);
                element.style.display = "none";
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
                window.URL.revokeObjectURL(url);

            } else if (format === 'json') {
                // Export as JSON
                const response = await fetch(`${apiUrl}/session/results/${sessionId}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}` }
                });

                if (!response.ok) throw new Error('Failed to fetch session data');

                const data = await response.json();
                const element = document.createElement("a");
                element.setAttribute("href", "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2)));
                element.setAttribute("download", `biomech-session-${sessionId}.json`);
                element.style.display = "none";
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
            }

            alertBanner.className = 'alert-banner success';
            alertText.innerText = `✅ REPORT DOWNLOADED (${format.toUpperCase()})`;

            setTimeout(() => {
                alertBanner.classList.add('hidden');
            }, 3000);

        } catch (error) {
            console.error('Report generation failed:', error);
            alertBanner.className = 'alert-banner error';
            alertText.innerText = '❌ REPORT GENERATION FAILED';
        }
    },

    showReportUI() {
        const modal = document.getElementById('report-modal');
        if (!modal) {
            const newModal = document.createElement('div');
            newModal.id = 'report-modal';
            newModal.className = 'modal';
            newModal.style.cssText = `
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.7); z-index: 2000;
                display: flex; align-items: center; justify-content: center;
            `;
            newModal.innerHTML = `
                <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 16px; 
                            padding: 24px; max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto;">
                    <h2 style="font-family: var(--font-hud); font-size: 1.2rem; margin-bottom: 20px; color: var(--cyan);">
                        📊 GENERATE REPORT
                    </h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px;">
                        <button onclick="window.ReportGenerator.handleReportDownload('html')" 
                                style="padding: 12px; background: rgba(0,255,204,0.1); border: 1px solid var(--cyan); 
                                        border-radius: 8px; color: var(--cyan); cursor: pointer; font-weight: 600;">
                            📄 HTML Report
                        </button>
                        <button onclick="window.ReportGenerator.handleReportDownload('pdf')" 
                                style="padding: 12px; background: rgba(239,68,68,0.1); border: 1px solid #ef4444; 
                                        border-radius: 8px; color: #ef4444; cursor: pointer; font-weight: 600;">
                            📕 PDF Report
                        </button>
                        <button onclick="window.ReportGenerator.handleReportDownload('json')" 
                                style="padding: 12px; background: rgba(167,139,250,0.1); border: 1px solid var(--purple2); 
                                        border-radius: 8px; color: var(--purple2); cursor: pointer; font-weight: 600;">
                            🔹 JSON Data
                        </button>
                        <button onclick="document.getElementById('report-modal').style.display='none'" 
                                style="padding: 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); 
                                        border-radius: 8px; color: var(--text2); cursor: pointer;">
                            Cancel
                        </button>
                    </div>

                    <div style="background: rgba(0,255,204,0.05); padding: 12px; border-radius: 8px; 
                                border-left: 3px solid var(--cyan); font-size: 0.85rem; color: var(--text2); line-height: 1.5;">
                        <strong>📌 Tip:</strong> Reports include form analysis, risk assessment, trends, and recommendations.
                    </div>
                </div>
            `;
            document.body.appendChild(newModal);
        }
        modal.style.display = 'flex';
    },

    handleReportDownload(format) {
        const currentSession = window.state?.currentSessionId || window.db?.sessions?.[0]?.id;
        if (!currentSession) {
            alert('No active session found');
            return;
        }
        this.generateAndDownloadReport(currentSession, format, window.db?.googleUser?.sub);
        document.getElementById('report-modal').style.display = 'none';
    },

    async compareSessions(sessionId1, sessionId2) {
        try {
            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';
            
            const [res1, res2] = await Promise.all([
                fetch(`${apiUrl}/session/results/${sessionId1}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}` }
                }),
                fetch(`${apiUrl}/session/results/${sessionId2}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}` }
                })
            ]);

            if (!res1.ok || !res2.ok) throw new Error('Failed to fetch session data');

            const data1 = await res1.json();
            const data2 = await res2.json();

            return this.generateComparisonHTML(data1, data2);
        } catch (error) {
            console.error('Session comparison failed:', error);
            return null;
        }
    },

    generateComparisonHTML(session1, session2) {
        const comparison = {
            session1_id: session1.session_id,
            session2_id: session2.session_id,
            metrics: {
                form_score_improvement: session2.average_form_score - session1.average_form_score,
                rep_count_improvement: session2.total_reps - session1.total_reps,
                risk_level_change: session1.risk_level !== session2.risk_level ? `${session1.risk_level} → ${session2.risk_level}` : 'No change',
                duration_change: session2.session_duration - session1.session_duration
            }
        };

        return comparison;
    }
};

window.ReportGenerator = ReportGenerator;

export default ReportGenerator;
