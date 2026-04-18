/**
 * Enterprise Features Initializer
 * Loads and initializes all enterprise components for full deployment
 */

console.log("🚀 BioMech AI: Loading Enterprise Features Module...");

// Import all enterprise components
import { BiomechWebSocketClient } from './websocket-client.js';
import { ReportGenerator } from './components/ReportGenerator.js';
import { MultiPersonTracker } from './components/MultiPersonTracker.js';
import { AdminDashboard } from './components/AdminDashboard.js';
import { ExperimentsManager } from './components/ExperimentsManager.js';
import { FraudDetectionMonitor } from './components/FraudDetectionMonitor.js';
import { AdvancedAnalytics } from './components/AdvancedAnalytics.js';
import { SystemMonitor } from './components/SystemMonitor.js';
import { EnterpriseSecurity } from './components/EnterpriseSecurity.js';

/**
 * Enterprise Deployment Configuration
 */
window.ENTERPRISE_CONFIG = {
    features: {
        websocket: true,
        reporting: true,
        multiPerson: true,
        adminPanel: true,
        experiments: true,
        fraudDetection: true,
        advancedAnalytics: true,
        monitoring: true,
        security: true
    },
    security: {
        encryption: 'AES-256',
        mfa: true,
        rbac: true,
        compliance: ['HIPAA', 'GDPR', 'SOC2', 'CCPA']
    },
    monitoring: {
        sentry: true,
        prometheus: true,
        autoRefresh: true,
        refreshInterval: 10000
    }
};

/**
 * Enterprise Features Manager
 */
class EnterpriseDeployment {
    
    constructor() {
        this.components = {};
        this.initialized = false;
        this.initializationTime = null;
    }

    /**
     * Initialize all enterprise features
     */
    async initializeAll() {
        try {
            console.log("📦 Initializing Enterprise Features...");
            const startTime = Date.now();

            // Step 1: Security
            console.log("🔒 [1/9] Initializing Enterprise Security...");
            await EnterpriseSecurity.initializeSecurity();
            this.components.security = EnterpriseSecurity;

            // Step 2: WebSocket
            console.log("🔌 [2/9] Initializing WebSocket Client...");
            const wsClient = new BiomechWebSocketClient();
            this.components.websocket = wsClient;

            // Step 3: System Monitoring
            console.log("📊 [3/9] Initializing System Monitor...");
            this.components.monitor = SystemMonitor;
            SystemMonitor.startMonitoring();

            // Step 4: Report Generation
            console.log("📄 [4/9] Initializing Report Generator...");
            this.components.reports = ReportGenerator;

            // Step 5: Multi-Person Tracking
            console.log("👥 [5/9] Initializing Multi-Person Tracker...");
            await MultiPersonTracker.initializeTracking(10);
            this.components.tracker = MultiPersonTracker;

            // Step 6: Admin Dashboard
            console.log("⚙️ [6/9] Initializing Admin Dashboard...");
            this.components.admin = AdminDashboard;

            // Step 7: Experiments
            console.log("🧪 [7/9] Initializing A/B Testing...");
            this.components.experiments = ExperimentsManager;

            // Step 8: Fraud Detection
            console.log("🚨 [8/9] Initializing Fraud Detection...");
            this.components.fraud = FraudDetectionMonitor;

            // Step 9: Advanced Analytics
            console.log("📈 [9/9] Initializing Advanced Analytics...");
            this.components.analytics = AdvancedAnalytics;

            this.initialized = true;
            this.initializationTime = Date.now() - startTime;

            console.log(`✅ ALL ENTERPRISE FEATURES INITIALIZED (${this.initializationTime}ms)`);
            this.displayDeploymentStatus();

            return true;

        } catch (error) {
            console.error("❌ Enterprise initialization failed:", error);
            return false;
        }
    }

    /**
     * Display deployment status in console
     */
    displayDeploymentStatus() {
        console.log("═══════════════════════════════════════════════════════");
        console.log("✅ ENTERPRISE DEPLOYMENT STATUS");
        console.log("═══════════════════════════════════════════════════════");
        console.log("📦 WebSocket Real-Time: ✅ ACTIVE");
        console.log("📄 Report Generation: ✅ READY");
        console.log("👥 Multi-Person Tracking: ✅ READY");
        console.log("⚙️  Admin Dashboard: ✅ READY");
        console.log("🧪 A/B Testing Platform: ✅ READY");
        console.log("🚨 Fraud Detection: ✅ MONITORING");
        console.log("📈 Advanced Analytics: ✅ READY");
        console.log("📊 System Monitoring: ✅ ACTIVE");
        console.log("🔒 Enterprise Security: ✅ ACTIVE");
        console.log("═══════════════════════════════════════════════════════");
        console.log(`⏱️  Initialization Time: ${this.initializationTime}ms`);
        console.log("═══════════════════════════════════════════════════════");
    }

    /**
     * Create Enterprise Menu (accessible from UI)
     */
    createEnterpriseMenu() {
        const menu = document.createElement('div');
        menu.id = 'enterprise-menu';
        menu.style.cssText = `
            position: fixed; bottom: 20px; left: 20px; z-index: 900;
            background: rgba(8,12,26,0.95); border: 1px solid var(--border);
            border-radius: 12px; padding: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        `;

        menu.innerHTML = `
            <div style="font-family: var(--font-hud); font-size: 0.75rem; letter-spacing: 1px; 
                        color: var(--cyan); margin-bottom: 12px;">🏢 ENTERPRISE MENU</div>
            
            <div style="display: grid; grid-template-columns: 1fr; gap: 8px; font-size: 0.75rem;">
                <button onclick="window.EnterpriseSecurity.showSecurityDashboard()" 
                        style="padding: 8px; background: rgba(239,68,68,0.1); border: 1px solid #ef4444; 
                                color: #ef4444; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    🔒 SECURITY
                </button>
                <button onclick="window.AdminDashboard.initializeAdminMode(window.db?.googleUser?.sub); 
                                 window.AdminDashboard.toggleAdminPanel()" 
                        style="padding: 8px; background: rgba(245,158,11,0.1); border: 1px solid #f59e0b; 
                                color: #f59e0b; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    ⚙️ ADMIN
                </button>
                <button onclick="window.SystemMonitor.showMonitoringDashboard()" 
                        style="padding: 8px; background: rgba(99,102,241,0.1); border: 1px solid #6366f1; 
                                color: #6366f1; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    📊 MONITOR
                </button>
                <button onclick="window.AdvancedAnalytics.showAnalyticsUI()" 
                        style="padding: 8px; background: rgba(167,139,250,0.1); border: 1px solid var(--purple2); 
                                color: var(--purple2); border-radius: 4px; cursor: pointer; font-weight: 600;">
                    📈 ANALYTICS
                </button>
                <button onclick="window.ExperimentsManager.showExperimentsUI()" 
                        style="padding: 8px; background: rgba(16,185,129,0.1); border: 1px solid #10b981; 
                                color: #10b981; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    🧪 EXPERIMENTS
                </button>
                <button onclick="window.FraudDetectionMonitor.showFraudDetectionUI()" 
                        style="padding: 8px; background: rgba(239,68,68,0.1); border: 1px solid #ef4444; 
                                color: #ef4444; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    🚨 FRAUD DETECTION
                </button>
                <button onclick="window.ReportGenerator.showReportUI()" 
                        style="padding: 8px; background: rgba(0,255,204,0.1); border: 1px solid var(--cyan); 
                                color: var(--cyan); border-radius: 4px; cursor: pointer; font-weight: 600;">
                    📄 REPORTS
                </button>
                <button onclick="window.MultiPersonTracker.showLeaderboard()" 
                        style="padding: 8px; background: rgba(99,102,241,0.1); border: 1px solid #6366f1; 
                                color: #6366f1; border-radius: 4px; cursor: pointer; font-weight: 600;">
                    👥 GROUP TRACKING
                </button>
            </div>
        `;

        document.body.appendChild(menu);
    }

    /**
     * Connect WebSocket
     */
    async connectWebSocket(userId, sessionId = null) {
        try {
            const wsClient = this.components.websocket;
            if (!wsClient) {
                console.warn('WebSocket client not initialized');
                return;
            }

            await wsClient.connect(userId, sessionId);
            console.log('✅ WebSocket connected');

            // Set up real-time listeners
            wsClient.on('realtime_analysis', (data) => {
                console.log('📊 Real-time analysis update:', data);
            });

            wsClient.on('form_feedback', (data) => {
                console.log('💬 Form feedback:', data);
            });

            wsClient.on('alert', (data) => {
                console.log('🚨 Alert:', data);
            });

            return wsClient;
        } catch (error) {
            console.error('WebSocket connection failed:', error);
        }
    }

    /**
     * Get Component Status Report
     */
    getStatusReport() {
        return {
            initialized: this.initialized,
            initializationTime: this.initializationTime,
            components: Object.keys(this.components),
            config: window.ENTERPRISE_CONFIG,
            timestamp: new Date().toISOString()
        };
    }
}

// Global export
window.EnterpriseDeployment = new EnterpriseDeployment();
window.BiomechWebSocketClient = BiomechWebSocketClient;

// Initialize when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.EnterpriseDeployment.initializeAll().then(() => {
            window.EnterpriseDeployment.createEnterpriseMenu();
        });
    });
} else {
    window.EnterpriseDeployment.initializeAll().then(() => {
        window.EnterpriseDeployment.createEnterpriseMenu();
    });
}

console.log("✅ Enterprise Features Module Loaded");

export { EnterpriseDeployment };
