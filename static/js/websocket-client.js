/**
 * WebSocket Real-Time Client
 * Handles live streaming updates for pose detection, form feedback, and alerts
 * TIER 11 - Real-Time Communication System
 */

class BiomechWebSocketClient {
    constructor(url = null) {
        this.url = url || this.getWebSocketURL();
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.messageQueue = [];
        this.subscriptions = {};
        this.listeners = {};
    }

    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const backend = window.BIOMECH_CONFIG?.BACKEND_URL || 'localhost:8000';
        const host = backend.replace(/^https?:\/\//, '').replace(/^http:\/\//, '');
        return `${protocol}//${host}/ws`;
    }

    connect(userId, sessionId = null) {
        return new Promise((resolve, reject) => {
            try {
                console.log("🔌 WebSocket: Connecting to", this.url);
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log("✅ WebSocket Connected");
                    this.reconnectAttempts = 0;
                    
                    // Send connection message
                    this.send({
                        type: 'connect',
                        user_id: userId,
                        session_id: sessionId,
                        timestamp: new Date().toISOString()
                    });

                    // Flush queued messages
                    this.messageQueue.forEach(msg => this.send(msg));
                    this.messageQueue = [];

                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (e) {
                        console.error("❌ WebSocket message parse error:", e);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error("❌ WebSocket error:", error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log("⏸️ WebSocket Disconnected");
                    this.attemptReconnect(userId, sessionId);
                };

            } catch (e) {
                console.error("❌ WebSocket connection failed:", e);
                reject(e);
            }
        });
    }

    attemptReconnect(userId, sessionId) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            setTimeout(() => {
                this.connect(userId, sessionId).catch(() => {});
            }, this.reconnectDelay);
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            this.messageQueue.push(message);
        }
    }

    subscribe(channel, callback) {
        this.subscriptions[channel] = callback;
        this.send({
            type: 'subscribe',
            channel: channel,
            timestamp: new Date().toISOString()
        });
    }

    unsubscribe(channel) {
        delete this.subscriptions[channel];
        this.send({
            type: 'unsubscribe',
            channel: channel,
            timestamp: new Date().toISOString()
        });
    }

    on(event, callback) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(callback);
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(cb => cb(data));
        }
    }

    handleMessage(message) {
        const { type, channel, data } = message;

        // Emit generic event
        this.emit('message', message);

        // Route to channel subscriber
        if (channel && this.subscriptions[channel]) {
            this.subscriptions[channel](data);
        }

        // Emit typed events
        switch (type) {
            case 'realtime_update':
                this.emit('realtime_analysis', data);
                break;
            case 'form_feedback':
                this.emit('form_feedback', data);
                break;
            case 'alert':
                this.emit('alert', data);
                break;
            case 'rep_update':
                this.emit('rep_count', data);
                break;
            case 'risk_alert':
                this.emit('risk_alert', data);
                break;
            case 'performance_update':
                this.emit('performance_update', data);
                break;
            case 'group_sync':
                this.emit('group_update', data);
                break;
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Global export
window.BiomechWebSocketClient = BiomechWebSocketClient;

export { BiomechWebSocketClient };
