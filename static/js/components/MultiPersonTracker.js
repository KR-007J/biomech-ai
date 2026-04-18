/**
 * Multi-Person Tracking Component
 * Handles simultaneous tracking of multiple users, person re-identification, and group analysis
 * TIER 8 - Multi-User Synchronization System
 */

export const MultiPersonTracker = {
    
    trackedPeople: {},
    selectedPersonId: null,
    groupMode: false,

    async initializeTracking(maxPeople = 10) {
        this.createTrackingUI(maxPeople);
        console.log(`✅ Multi-person tracking initialized (max: ${maxPeople})`);
    },

    createTrackingUI(maxPeople) {
        const container = document.getElementById('multi-person-container');
        if (!container) {
            const newContainer = document.createElement('div');
            newContainer.id = 'multi-person-container';
            newContainer.style.cssText = `
                position: fixed; bottom: 20px; right: 20px; z-index: 100;
                background: rgba(8,12,26,0.95); border: 1px solid var(--border);
                border-radius: 12px; padding: 16px; width: 280px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            `;
            document.body.appendChild(newContainer);
        }

        const container2 = document.getElementById('multi-person-container');
        container2.innerHTML = `
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <label style="font-family: var(--font-hud); font-size: 0.75rem; letter-spacing: 1px; 
                                  color: var(--cyan);">👥 TRACKED PEOPLE (${Object.keys(this.trackedPeople).length}/${maxPeople})</label>
                    <button onclick="window.MultiPersonTracker.toggleGroupMode()" 
                            style="background: ${this.groupMode ? 'var(--cyan)' : 'rgba(0,255,204,0.2)'}; 
                                    color: ${this.groupMode ? '#000' : 'var(--cyan)'}; border: none; 
                                    padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; 
                                    cursor: pointer; font-weight: 600; transition: all 0.2s;">
                        ${this.groupMode ? '🔗 GROUP ON' : '🔓 GROUP OFF'}
                    </button>
                </div>

                <div id="person-list" style="display: grid; grid-template-columns: 1fr; gap: 8px; max-height: 200px; 
                                            overflow-y: auto; margin-bottom: 12px;">
                </div>
            </div>

            <div style="border-top: 1px solid var(--border); padding-top: 12px;">
                <button onclick="window.MultiPersonTracker.startGroupTracking()" 
                        style="width: 100%; padding: 8px; background: rgba(0,255,204,0.2); 
                                border: 1px solid var(--cyan); border-radius: 6px; 
                                color: var(--cyan); cursor: pointer; font-weight: 600; font-size: 0.8rem; margin-bottom: 8px;">
                    ▶️ START GROUP SYNC
                </button>
                <button onclick="window.MultiPersonTracker.showLeaderboard()" 
                        style="width: 100%; padding: 8px; background: rgba(167,139,250,0.2); 
                                border: 1px solid var(--purple2); border-radius: 6px; 
                                color: var(--purple2); cursor: pointer; font-weight: 600; font-size: 0.8rem;">
                    🏆 LEADERBOARD
                </button>
            </div>
        `;
    },

    addTrackedPerson(personId, name, confidence = 0.85) {
        this.trackedPeople[personId] = {
            id: personId,
            name: name,
            confidence: confidence,
            position: null,
            formScore: 0,
            repCount: 0,
            joinedAt: new Date(),
            riskLevel: 'LOW'
        };
        this.updatePersonList();
        console.log(`✅ Person added: ${name} (${personId})`);
    },

    updatePersonList() {
        const personList = document.getElementById('person-list');
        if (!personList) return;

        personList.innerHTML = Object.entries(this.trackedPeople).map(([id, person]) => `
            <div onclick="window.MultiPersonTracker.selectPerson('${id}')" 
                 style="background: ${this.selectedPersonId === id ? 'rgba(0,255,204,0.2)' : 'rgba(0,0,0,0.3)'}; 
                         padding: 8px; border-radius: 6px; border: 1px solid ${this.selectedPersonId === id ? 'var(--cyan)' : 'transparent'}; 
                         cursor: pointer; transition: all 0.2s; user-select: none;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-weight: 600; color: var(--cyan); font-size: 0.8rem;">${person.name}</span>
                    <span style="font-size: 0.65rem; color: var(--text2); font-family: var(--font-mono);">
                        ${(person.confidence * 100).toFixed(0)}%
                    </span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.7rem;">
                    <div>Form: <span style="color: var(--cyan);">${person.formScore}%</span></div>
                    <div>Reps: <span style="color: var(--cyan);">${person.repCount}</span></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 0.65rem;">
                    <span>Risk: <span style="color: ${person.riskLevel === 'HIGH' ? '#ef4444' : person.riskLevel === 'MEDIUM' ? '#f59e0b' : '#10b981'};">${person.riskLevel}</span></span>
                    <span style="color: var(--text2);">${this.getTimeSinceJoined(person.joinedAt)}</span>
                </div>
            </div>
        `).join('');
    },

    selectPerson(personId) {
        this.selectedPersonId = personId;
        this.updatePersonList();
        console.log(`👤 Selected: ${this.trackedPeople[personId].name}`);
    },

    async updatePersonMetrics(personId, metrics) {
        if (this.trackedPeople[personId]) {
            this.trackedPeople[personId] = {
                ...this.trackedPeople[personId],
                ...metrics
            };
            this.updatePersonList();
        }
    },

    async startGroupTracking() {
        try {
            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';
            
            const response = await fetch(`${apiUrl}/group-analysis/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}`
                },
                body: JSON.stringify({
                    people: Object.values(this.trackedPeople),
                    group_id: window.state?.currentSessionId,
                    sync_type: 'realtime'
                })
            });

            if (!response.ok) throw new Error('Group sync failed');

            const result = await response.json();
            this.groupMode = true;
            this.updatePersonList();
            
            console.log('✅ Group tracking started');
            alert('✅ Group Synchronization Started!\nAll people are now tracked together.');

        } catch (error) {
            console.error('Group tracking error:', error);
            alert('❌ Group tracking failed. Check console.');
        }
    },

    async trackMultiplePeople(frameData) {
        try {
            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';
            
            const response = await fetch(`${apiUrl}/multi-person/track`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('biomech_jwt')}`
                },
                body: JSON.stringify({
                    frame: frameData,
                    max_people: 10,
                    min_confidence: 0.7
                })
            });

            if (!response.ok) throw new Error('Multi-person tracking failed');

            const result = await response.json();
            
            // Update tracked people
            result.detections.forEach(detection => {
                this.addTrackedPerson(
                    detection.person_id,
                    `Person ${Object.keys(this.trackedPeople).length + 1}`,
                    detection.confidence
                );
            });

            return result;

        } catch (error) {
            console.error('Multi-person tracking error:', error);
        }
    },

    showLeaderboard() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7); z-index: 3000;
            display: flex; align-items: center; justify-content: center;
        `;

        const sortedPeople = Object.values(this.trackedPeople)
            .sort((a, b) => b.formScore - a.formScore);

        modal.innerHTML = `
            <div style="background: var(--bg3); border: 1px solid var(--border); border-radius: 16px; 
                        padding: 24px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
                <h2 style="font-family: var(--font-hud); font-size: 1.2rem; margin-bottom: 20px; color: #f59e0b;">
                    🏆 GROUP LEADERBOARD
                </h2>
                
                <div style="display: grid; gap: 12px;">
                    ${sortedPeople.map((person, idx) => `
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; 
                                    border-left: 4px solid ${idx === 0 ? '#f59e0b' : idx === 1 ? '#c0c0c0' : idx === 2 ? '#cd7f32' : 'var(--cyan)'};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 1.2rem; margin-right: 8px;">
                                    ${idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${idx + 1}`}
                                </span>
                                <div style="flex: 1;">
                                    <div style="font-weight: 600; color: var(--cyan);">${person.name}</div>
                                    <div style="font-size: 0.8rem; color: var(--text2);">
                                        Form Score: ${person.formScore}% | Reps: ${person.repCount}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <button onclick="this.parentElement.parentElement.remove()" 
                        style="width: 100%; margin-top: 16px; padding: 10px; 
                                background: rgba(0,255,204,0.2); border: 1px solid var(--cyan); 
                                border-radius: 6px; color: var(--cyan); cursor: pointer; font-weight: 600;">
                    CLOSE
                </button>
            </div>
        `;

        document.body.appendChild(modal);
    },

    toggleGroupMode() {
        this.groupMode = !this.groupMode;
        this.updatePersonList();
    },

    getTimeSinceJoined(joinedAt) {
        const seconds = Math.floor((new Date() - joinedAt) / 1000);
        if (seconds < 60) return `${seconds}s`;
        return `${Math.floor(seconds / 60)}m`;
    },

    removePerson(personId) {
        delete this.trackedPeople[personId];
        if (this.selectedPersonId === personId) {
            this.selectedPersonId = null;
        }
        this.updatePersonList();
    },

    clearAll() {
        this.trackedPeople = {};
        this.selectedPersonId = null;
        this.groupMode = false;
        this.updatePersonList();
    }
};

window.MultiPersonTracker = MultiPersonTracker;

export default MultiPersonTracker;
