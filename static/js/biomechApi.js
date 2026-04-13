/**
 * Biomech AI - Backend Integration Service
 * Communicates with the FastAPI Python backend
 */

const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8000' 
    : 'https://your-cloud-backend-url.com'; // Placeholder for Phase 10

const BiomechApi = {
    /**
     * Uploads a video for processing
     * @param {File} file 
     * @returns {Promise<Object>} Job ID and initial status
     */
    async uploadVideo(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/upload-video`, {
                method: 'POST',
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error('API Upload Error:', error);
            throw error;
        }
    },

    /**
     * Polls for results for a given job ID
     * @param {string} jobId 
     * @returns {Promise<Object>} Analysis results
     */
    async getResults(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/results/${jobId}`);
            return await response.json();
        } catch (error) {
            console.error('API Results Error:', error);
            throw error;
        }
    },

    /**
     * Helper to poll until completion
     */
    async pollForResults(jobId, onProgress) {
        let completed = false;
        let results = null;

        while (!completed) {
            results = await this.getResults(jobId);
            if (results.status === 'completed' || results.status === 'error') {
                completed = true;
            } else {
                if (onProgress && results.progress) {
                    onProgress(results.progress);
                }
                // Wait 2 seconds before polling again
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        return results;
    }
};

// Export to window for global access (vanilla compatibility)
window.BiomechApi = BiomechApi;
