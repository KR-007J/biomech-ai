const API_BASE_URL = window.BIOMECH_CONFIG?.BACKEND_URL || 'http://127.0.0.1:8000';

const BiomechApi = {
    /**
     * Analyzes biomechanical metrics using our hardened Python backend.
     * Securely proxies Gemini and Supabase operations.
     */
    async analyzeMetrics(metrics, exerciseType, userId = null) {
        try {
            const response = await fetch(`${API_BASE_URL}/generate-feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    metrics, 
                    exercise_type: exerciseType,
                    user_id: userId
                })
            });
            
            if (!response.ok) throw new Error('Backend Analysis Failed');
            
            return await response.json();
        } catch (error) {
            console.error('Core API Error:', error);
            throw error;
        }
    },

    /**
     * Status tracking for live feedback
     */
    async pollForResults(jobId, onProgress) {
        return { status: 'processed_via_hardened_backend' };
    }
};

window.BiomechApi = BiomechApi;

