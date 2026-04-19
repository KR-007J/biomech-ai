/**
 * BIOMECH AI - CORE API ENGINE
 * v4.2.4 - Ultimate Resilience Edition
 */

window.BiomechApi = {
    async analyzeMetrics(data, exerciseType = "General", userId = null) {
        console.log(`%c🚀 API_ENGINE: Analyzing ${exerciseType}...`, "color:#00ffcc; font-weight:bold;");
        
        try {
            const apiUrl = window.BIOMECH_CONFIG?.BACKEND_URL || "http://localhost:8000";
            
            // 1. Attempt Backend Proxy
            try {
                const response = await fetch(`${apiUrl}/generate-feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ metrics: data, exercise_type: exerciseType, user_id: userId || 'anon' }),
                    signal: AbortSignal.timeout?.(4000)
                });
                
                if (response.ok) {
                    console.log("✅ Backend analysis successful.");
                    return await response.json();
                }
            } catch (e) {
                console.warn("⚠️ Backend Proxy unreachable. Activating direct failover...");
            }

            // 2. Direct Failover
            return await this.fallbackDirectAnalysis(data, exerciseType);
        } catch (error) {
            console.error("❌ API_ENGINE ERROR:", error);
            return this.getErrorFeedback("Critical engine failure.");
        }
    },

    async fallbackDirectAnalysis(data, exercise) {
        const key = window.BIOMECH_CONFIG?.GEMINI_KEY?.trim();
        if (!key || key.length < 10) return this.getErrorFeedback("Invalid API Key in secrets.js");

        // The 404 issue is often caused by incorrect model IDs for certain API versions.
        // We will try the most stable paths first.
        const variations = [
            { v: "v1", m: "gemini-1.5-flash" },
            { v: "v1beta", m: "gemini-1.5-flash" },
            { v: "v1", m: "gemini-pro" },
            { v: "v1", m: "gemini-1.5-pro" }
        ];

        const prompt = `Elite Biomechanics Coach: Analyze ${exercise} metrics: ${JSON.stringify(data)}. 
                        Provide concise JSON feedback with keys: issue, reason, fix.`;

        let lastError = "Target unreachable.";

        for (const target of variations) {
            try {
                const url = `https://generativelanguage.googleapis.com/${target.v}/models/${target.m}:generateContent?key=${key}`;
                console.log(`📡 Probing ${target.m} (${target.v})...`);

                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
                });

                if (response.ok) {
                    const json = await response.json();
                    const text = json.candidates?.[0]?.content?.parts?.[0]?.text || "{}";
                    const cleanedMatch = text.match(/\{[\s\S]*\}/);
                    if (cleanedMatch) {
                        console.log(`%c✅ SUCCESS: ${target.m} responded.`, "color:#10b981; font-weight:bold;");
                        return JSON.parse(cleanedMatch[0]);
                    }
                } else {
                    const errorDetails = await response.json().catch(() => ({}));
                    lastError = `${response.status} ${response.statusText}${errorDetails.error?.message ? ': ' + errorDetails.error.message : ''}`;
                    console.warn(`❌ FAIL: ${target.m} (${target.v}) -> ${lastError}`);
                    
                    if (response.status === 403 || response.status === 429) {
                        return this.getErrorFeedback(`Status ${response.status}: ${errorDetails.error?.message || 'Access Denied'}`);
                    }
                }
            } catch (err) {
                lastError = err.message;
                console.error(`Network attempt failed for ${target.m}:`, err.message);
            }
        }

        return this.getErrorFeedback(`Pipeline Blocked: ${lastError}`);
    },

    getErrorFeedback(reason) {
        return {
            status: "error",
            coach_feedback: {
                issue: "AI Service Connection Error",
                reason: reason,
                fix: "1. Refresh the page (Ctrl+F5). 2. Ensure your internet is active. 3. Check that your API key in secrets.js is active and authorized for Gemini 1.5 models."
            }
        };
    },

    async generateReport() {
        const textArea = document.getElementById('ai-response-area');
        const content = textArea ? textArea.innerText : "No data.";
        const blob = new Blob([`BIOMECH AI PERFORMANCE DATA\n\n${content}`], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `BioMech-Audit-${Date.now()}.txt`;
        a.click();
    }
};
