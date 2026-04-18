/**
 * A/B Testing & Experimentation Dashboard
 * Handles experiment design, allocation, tracking, and statistical analysis
 * TIER 12 - A/B Testing Platform
 */

export const ExperimentsManager = {

    activeExperiments: {},
    userAllocations: {},

    async createExperiment(experimentConfig) {
        try {
            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';
            
            const response = await fetch(`${apiUrl}/experiments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}`
                },
                body: JSON.stringify({
                    name: experimentConfig.name,
                    hypothesis: experimentConfig.hypothesis,
                    control_group: experimentConfig.controlGroup,
                    variant_group: experimentConfig.variantGroup,
                    allocation_ratio: experimentConfig.allocationRatio || 0.5,
                    duration_days: experimentConfig.durationDays || 14,
                    success_metric: experimentConfig.successMetric,
                    min_sample_size: experimentConfig.minSampleSize || 100,
                    description: experimentConfig.description
                })
            });

            if (!response.ok) throw new Error('Failed to create experiment');

            const experiment = await response.json();
            this.activeExperiments[experiment.id] = experiment;
            
            console.log(`✅ Experiment created: ${experiment.name}`);
            return experiment;

        } catch (error) {
            console.error('Experiment creation failed:', error);
            throw error;
        }
    },

    showExperimentsUI() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7); z-index: 2500;
            display: flex; align-items: center; justify-content: center;
            overflow-y: auto;
        `;

        modal.innerHTML = `
            <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 16px; 
                        padding: 24px; max-width: 800px; width: 95%; margin: 20px 0;">
                
                <h2 style="font-family: var(--font-hud); font-size: 1.2rem; letter-spacing: 2px; 
                           color: #10b981; margin-bottom: 20px;">
                    🧪 A/B EXPERIMENTS MANAGER
                </h2>

                <!-- Active Experiments -->
                <div style="margin-bottom: 20px;">
                    <h3 style="font-size: 0.9rem; color: var(--cyan); margin-bottom: 12px;">ACTIVE EXPERIMENTS</h3>
                    <div id="experiments-list" style="display: grid; gap: 12px; max-height: 300px; overflow-y: auto;">
                        ${this.renderExperimentsList()}
                    </div>
                </div>

                <!-- Create New Experiment -->
                <div style="background: rgba(0,0,0,0.3); padding: 16px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 16px;">
                    <h3 style="font-size: 0.9rem; color: #10b981; margin-bottom: 12px;">CREATE NEW EXPERIMENT</h3>
                    
                    <div style="display: grid; gap: 12px;">
                        <input id="exp-name" type="text" placeholder="Experiment Name" 
                               style="background: rgba(0,0,0,0.2); border: 1px solid var(--border); 
                                       padding: 8px; border-radius: 6px; color: var(--text); font-size: 0.85rem;">
                        
                        <textarea id="exp-hypothesis" placeholder="Hypothesis (e.g., AI feedback improves form score by 15%)" 
                                  style="background: rgba(0,0,0,0.2); border: 1px solid var(--border); 
                                          padding: 8px; border-radius: 6px; color: var(--text); font-size: 0.85rem; height: 60px;">
                        </textarea>

                        <select id="exp-metric" style="background: rgba(0,0,0,0.2); border: 1px solid var(--border); 
                                                       padding: 8px; border-radius: 6px; color: var(--text); font-size: 0.85rem;">
                            <option value="">Select Success Metric</option>
                            <option value="form_score">Form Score Improvement</option>
                            <option value="rep_count">Rep Count</option>
                            <option value="injury_risk_reduction">Injury Risk Reduction</option>
                            <option value="user_engagement">User Engagement</option>
                            <option value="retention_rate">Retention Rate</option>
                        </select>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <input id="exp-duration" type="number" placeholder="Duration (days)" value="14"
                                   style="background: rgba(0,0,0,0.2); border: 1px solid var(--border); 
                                           padding: 8px; border-radius: 6px; color: var(--text); font-size: 0.85rem;">
                            <input id="exp-sample" type="number" placeholder="Min Sample Size" value="100"
                                   style="background: rgba(0,0,0,0.2); border: 1px solid var(--border); 
                                           padding: 8px; border-radius: 6px; color: var(--text); font-size: 0.85rem;">
                        </div>

                        <button onclick="window.ExperimentsManager.handleCreateExperiment()" 
                                style="padding: 10px; background: rgba(16,185,129,0.2); 
                                        border: 1px solid #10b981; border-radius: 6px; 
                                        color: #10b981; cursor: pointer; font-weight: 600;">
                            ✓ CREATE EXPERIMENT
                        </button>
                    </div>
                </div>

                <button onclick="this.parentElement.parentElement.remove()" 
                        style="width: 100%; padding: 10px; background: rgba(255,255,255,0.05); 
                                border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; 
                                color: var(--text2); cursor: pointer;">
                    CLOSE
                </button>
            </div>
        `;

        document.body.appendChild(modal);
    },

    renderExperimentsList() {
        return Object.values(this.activeExperiments).map(exp => `
            <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border-left: 3px solid #10b981;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                    <div>
                        <div style="font-weight: 600; color: #10b981; margin-bottom: 4px;">${exp.name}</div>
                        <div style="font-size: 0.75rem; color: var(--text2);">${exp.hypothesis}</div>
                    </div>
                    <span style="font-size: 0.7rem; background: rgba(16,185,129,0.2); padding: 4px 8px; 
                                 border-radius: 4px; color: #10b981;">RUNNING</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; font-size: 0.75rem;">
                    <div>
                        <span style="color: var(--text2);">Sample Size:</span>
                        <span style="color: var(--cyan);">${exp.sample_size || 0}/${exp.min_sample_size}</span>
                    </div>
                    <div>
                        <span style="color: var(--text2);">Control:</span>
                        <span style="color: var(--cyan);">${((exp.allocation_ratio) * 100).toFixed(0)}%</span>
                    </div>
                    <div>
                        <span style="color: var(--text2);">Variant:</span>
                        <span style="color: var(--cyan);">${((1 - exp.allocation_ratio) * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <button onclick="window.ExperimentsManager.showExperimentResults('${exp.id}')" 
                        style="width: 100%; margin-top: 8px; padding: 6px; 
                                background: rgba(99,102,241,0.1); border: 1px solid #6366f1; 
                                border-radius: 4px; color: #6366f1; cursor: pointer; font-size: 0.75rem;">
                    VIEW RESULTS
                </button>
            </div>
        `).join('');
    },

    async handleCreateExperiment() {
        const name = document.getElementById('exp-name').value;
        const hypothesis = document.getElementById('exp-hypothesis').value;
        const metric = document.getElementById('exp-metric').value;
        const duration = parseInt(document.getElementById('exp-duration').value);
        const sampleSize = parseInt(document.getElementById('exp-sample').value);

        if (!name || !hypothesis || !metric) {
            alert('❌ Please fill in all fields');
            return;
        }

        try {
            await this.createExperiment({
                name,
                hypothesis,
                successMetric: metric,
                durationDays: duration,
                minSampleSize: sampleSize,
                controlGroup: 'control',
                variantGroup: 'variant'
            });

            alert('✅ Experiment created successfully!');
            this.showExperimentsUI();
        } catch (error) {
            alert('❌ Failed to create experiment');
        }
    },

    async showExperimentResults(experimentId) {
        try {
            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';
            
            const response = await fetch(`${apiUrl}/experiments/${experimentId}/results`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}` }
            });

            if (!response.ok) throw new Error('Failed to fetch results');

            const results = await response.json();

            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.7); z-index: 2600;
                display: flex; align-items: center; justify-content: center;
            `;

            modal.innerHTML = `
                <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 16px; 
                            padding: 24px; max-width: 700px; width: 95%;">
                    
                    <h2 style="font-family: var(--font-hud); font-size: 1.1rem; color: #6366f1; margin-bottom: 16px;">
                        📊 EXPERIMENT RESULTS
                    </h2>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 0.75rem; color: var(--text2); margin-bottom: 4px;">CONTROL GROUP</div>
                            <div style="font-size: 1.3rem; color: var(--cyan); font-weight: 600;">
                                ${results.control_mean?.toFixed(2) || 'N/A'}
                            </div>
                            <div style="font-size: 0.7rem; color: var(--text2); margin-top: 4px;">
                                n=${results.control_n}
                            </div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 0.75rem; color: var(--text2); margin-bottom: 4px;">VARIANT GROUP</div>
                            <div style="font-size: 1.3rem; color: #10b981; font-weight: 600;">
                                ${results.variant_mean?.toFixed(2) || 'N/A'}
                            </div>
                            <div style="font-size: 0.7rem; color: var(--text2); margin-top: 4px;">
                                n=${results.variant_n}
                            </div>
                        </div>
                    </div>

                    <div style="background: rgba(0,255,204,0.05); padding: 12px; border-radius: 8px; 
                                border: 1px solid rgba(0,255,204,0.2); margin-bottom: 16px;">
                        <div style="font-size: 0.75rem; color: var(--text2); margin-bottom: 4px;">STATISTICAL SIGNIFICANCE</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; font-size: 0.8rem;">
                            <div>
                                <span style="color: var(--text2);">P-value:</span>
                                <span style="color: var(--cyan); font-weight: 600;">${results.p_value?.toFixed(4) || 'N/A'}</span>
                            </div>
                            <div>
                                <span style="color: var(--text2);">CI 95%:</span>
                                <span style="color: var(--cyan); font-weight: 600;">[${results.ci_lower?.toFixed(2) || 'N/A'}, ${results.ci_upper?.toFixed(2) || 'N/A'}]</span>
                            </div>
                            <div>
                                <span style="color: var(--text2);">Effect Size:</span>
                                <span style="color: var(--cyan); font-weight: 600;">${results.effect_size?.toFixed(2) || 'N/A'}</span>
                            </div>
                        </div>
                    </div>

                    <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                        <div style="font-size: 0.75rem; color: var(--text2); margin-bottom: 8px;">CONCLUSION</div>
                        <div style="font-size: 0.85rem; color: #10b981; line-height: 1.5;">
                            ${results.is_significant ? 
                              `✅ Results are statistically significant (p < 0.05). Variant shows ${Math.abs(results.improvement).toFixed(1)}% improvement.` :
                              `⚠️ Results are not yet statistically significant. Continue running the experiment.`}
                        </div>
                    </div>

                    <button onclick="this.parentElement.parentElement.remove()" 
                            style="width: 100%; padding: 10px; background: rgba(255,255,255,0.05); 
                                    border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; 
                                    color: var(--text2); cursor: pointer;">
                        CLOSE
                    </button>
                </div>
            `;

            document.body.appendChild(modal);

        } catch (error) {
            console.error('Failed to show results:', error);
            alert('❌ Failed to fetch experiment results');
        }
    }
};

window.ExperimentsManager = ExperimentsManager;

export default ExperimentsManager;
