/**
 * LumenAGI Dashboard v4.1 — Realtime Updates
 * Actualiza TODOS los elementos del DOM con datos del WebSocket
 */

class DashboardController {
    constructor() {
        this.ws = null;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.history = { gpu: [], agents: [] };
        this.maxHistory = 50;
        this.charts = {};
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.initCharts();
        this.startPeriodicChecks();
        // Initial load
        this.fetchInitialData();
    }

    async fetchInitialData() {
        try {
            const res = await fetch('/api/v1/metrics');
            const data = await res.json();
            this.updateDashboard(data);
        } catch (e) {
            console.log('[INIT] API fallback failed, waiting for WS...');
        }
    }

    connectWebSocket() {
        const wsUrl = 'ws://127.0.0.1:8766/ws';
        
        console.log('[WS] Attempting connection to:', wsUrl);
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('[WS] ✅ Connected successfully');
                this.updateConnectionStatus(true);
                this.reconnectDelay = 1000;
            };
            
            this.ws.onmessage = (event) => {
                console.log('[WS] 📨 Message received:', event.data.substring(0, 200));
                try {
                    const data = JSON.parse(event.data);
                    console.log('[WS] Parsed data keys:', Object.keys(data));
                    this.updateDashboard(data);
                    this.handleHistory(data);
                } catch (e) {
                    console.error('[WS] ❌ Parse error:', e);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('[WS] ❌ Disconnected. Code:', event.code, 'Reason:', event.reason);
                this.updateConnectionStatus(false);
                this.scheduleReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('[WS] ❌ Error:', error);
                this.updateConnectionStatus(false, 'Connection Error');
            };
            
        } catch (e) {
            console.error('[WS] ❌ Failed to connect:', e);
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        console.log(`[WS] Reconnecting in ${this.reconnectDelay}ms...`);
        setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
    }

    updateConnectionStatus(connected, message = null) {
        const dot = document.getElementById('conn-dot') || document.getElementById('connection-dot');
        const text = document.getElementById('conn-text') || document.getElementById('connection-text');
        
        if (dot && text) {
            if (connected) {
                dot.classList.remove('disconnected');
                dot.style.background = '#00ff88';
                text.textContent = 'Connected (0.5s live)';
                text.style.color = '#00ff88';
            } else {
                dot.classList.add('disconnected');
                dot.style.background = '#ff4444';
                text.textContent = message || 'Disconnected — retrying...';
                text.style.color = '#ff4444';
            }
        }
    }

    // ============================================================
    // ACTUALIZACIÓN PRINCIPAL — Aquí actualiza TODOS los elementos
    // ============================================================
    updateDashboard(data) {
        console.log('[DASHBOARD] Update received:', new Date().toLocaleTimeString());

        // 1. GPU METRICS
        if (data.gpu) {
            const g = data.gpu;
            
            // GPU Name
            const gpuDev = document.getElementById('gpu-dev') || document.getElementById('gpu-name');
            if (gpuDev) gpuDev.textContent = g.device || 'RTX 3090';
            
            // Utilization
            const gpuUtil = document.getElementById('gpu-util');
            if (gpuUtil) {
                gpuUtil.textContent = g.utilization + '%';
                gpuUtil.className = 'metric-value ' + (g.utilization > 80 ? 'danger' : g.utilization > 50 ? 'warning' : 'success');
            }
            
            // Temperature  
            const gpuTemp = document.getElementById('gpu-temp');
            if (gpuTemp) {
                gpuTemp.textContent = g.temperature + '°C';
                gpuTemp.className = 'metric-value ' + (g.temperature > 80 ? 'danger' : g.temperature > 70 ? 'warning' : '');
            }
            
            // Power
            const gpuPower = document.getElementById('gpu-power');
            if (gpuPower) gpuPower.textContent = (g.power_draw || 0).toFixed(1) + 'W';
            
            // Clocks
            const gpuClockG = document.getElementById('gpu-clock-g');
            if (gpuClockG) gpuClockG.textContent = (g.clock_graphics || 0) + ' MHz';
            
            const gpuClockM = document.getElementById('gpu-clock-m');  
            if (gpuClockM) gpuClockM.textContent = (g.clock_memory || 0) + ' MHz';
            
            // VRAM Bar
            const vramBar = document.getElementById('vram-bar');
            const vramLabel = document.getElementById('vram-label') || document.getElementById('vram-text');
            if (vramBar && vramLabel && g.total_mb) {
                const usedGB = (g.used_mb / 1024).toFixed(1);
                const totalGB = (g.total_mb / 1024).toFixed(0);
                const pct = (g.used_mb / g.total_mb) * 100;
                
                vramBar.style.width = pct + '%';
                vramBar.className = 'memory-fill ' + (pct > 85 ? 'critical' : pct > 70 ? 'caution' : '');
                vramLabel.textContent = `${usedGB} / ${totalGB} GB`;
            }
            
            // GPU Processes
            if (g.processes && g.processes.length > 0) {
                const gpuProcs = document.getElementById('gpu-procs') || document.getElementById('gpu-processes');
                if (gpuProcs) {
                    gpuProcs.innerHTML = g.processes.map(p => `
                        <div class="proc-item">
                            <div class="proc-name">
                                <span>${p.name}</span>
                                <span class="proc-pid">${p.pid}</span>
                            </div>
                            <span style="color: var(--accent-secondary)">${(p.memory_mb/1024).toFixed(1)} GB</span>
                        </div>
                    `).join('');
                }
            }
        }

        // 2. OLLAMA MODELS
        const models = data.ollama_models || data.ollama;
        if (models && models.length > 0) {
            const ollamaList = document.getElementById('ollama-list') || document.getElementById('ollama-models');
            if (ollamaList) {
                ollamaList.innerHTML = models.map(m => `
                    <div class="proc-item">
                        <span class="proc-name">🧠 ${m}</span>
                        <span style="color: var(--accent-secondary); font-size: 0.75rem;">Active</span>
                    </div>
                `).join('');
            }
        }

        // 3. AGENT TRACES
        if (data.agents && data.agents.length > 0) {
            const tracesList = document.getElementById('traces-list');
            if (tracesList) {
                tracesList.innerHTML = data.agents.map(a => `
                    <div class="trace-row">
                        <div class="trace-badge ${a.agent_id === 'main' ? 'main' : 'worker'}">
                            ${a.agent_id === 'main' ? '🧠' : '⚡'}
                        </div>
                        <div class="trace-task">${a.task || a.agent_id}</div>
                        <div class="trace-meta">${a.latency_ms || 0}ms</div>
                        <div class="trace-meta">$${(a.cost_usd || 0).toFixed(3)}</div>
                        <div class="trace-tag ${a.status}">${a.status}</div>
                    </div>
                `).join('');
            }
            
            // Update costs
            let kimiCost = 0, qwenCost = 0, apiCost = 0;
            data.agents.forEach(a => {
                const model = (a.model || '').toLowerCase();
                if (model.includes('kimi')) kimiCost += a.cost_usd || 0;
                else if (model.includes('qwen')) qwenCost += a.cost_usd || 0;
                else apiCost += a.cost_usd || 0;
            });
            
            const costKimi = document.getElementById('cost-kimi');
            const costQwen = document.getElementById('cost-qwen');
            const costApi = document.getElementById('cost-api');
            
            if (costKimi) costKimi.textContent = '$' + kimiCost.toFixed(4);
            if (costQwen) costQwen.textContent = '$' + qwenCost.toFixed(4);
            if (costApi) costApi.textContent = '$' + apiCost.toFixed(4);
            
            // Update avg latency
            const avgLat = data.agents.reduce((a, b) => a + (b.latency_ms || 0), 0) / data.agents.length;
            const avgLatEl = document.getElementById('avg-lat');
            if (avgLatEl) avgLatEl.textContent = avgLat.toFixed(0) + 'ms';
            
            // Update agent count
            const agentCount = document.getElementById('agent-count');
            if (agentCount) agentCount.textContent = data.agents.length;
            
            // Highlight active agent in topology
            if (data.agents[0]) {
                const lastAgent = data.agents[0].agent_id;
                document.querySelectorAll('.agent-node').forEach(node => {
                    node.classList.remove('active');
                    const statusDot = node.querySelector('.agent-status');
                    if (statusDot) statusDot.classList.remove('active');
                });
                
                const prefix = lastAgent.split('-')[0];
                const activeNode = document.getElementById('node-' + prefix);
                if (activeNode) {
                    activeNode.classList.add('active');
                    const statusDot = activeNode.querySelector('.agent-status');
                    if (statusDot) statusDot.classList.add('active');
                }
            }
        }

        // 4. SWARM STATUS
        if (data.swarm) {
            const agentCount = document.getElementById('agent-count') || document.getElementById('active-agents');
            if (agentCount && data.swarm.workers) {
                agentCount.textContent = 1 + data.swarm.workers.length;
            }
        }
    }

    // ============================================================
    // CHARTS HISTORY
    // ============================================================
    handleHistory(data) {
        if (data.gpu) {
            this.history.gpu.push({
                timestamp: Date.now(),
                utilization: data.gpu.utilization,
                temperature: data.gpu.temperature,
                vram_used: data.gpu.used_mb
            });
            if (this.history.gpu.length > this.maxHistory) this.history.gpu.shift();
            this.updateCharts();
        }
    }

    initCharts() {
        // GPU Chart
        const gpuCtx = document.getElementById('gpu-chart');
        if (gpuCtx && typeof Chart !== 'undefined') {
            this.charts.gpu = new Chart(gpuCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'GPU %',
                        data: [],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { min: 0, max: 100, grid: { color: '#2a2a3a' }, ticks: { color: '#888' } },
                        x: { display: false }
                    }
                }
            });
        }

        // Agent Chart
        const agentCtx = document.getElementById('agent-chart');
        if (agentCtx && typeof Chart !== 'undefined') {
            this.charts.agent = new Chart(agentCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Active',
                        data: [],
                        backgroundColor: '#ff6b35'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { min: 0, max: 5, grid: { color: '#2a2a3a' } },
                        x: { display: false }
                    }
                }
            });
        }
    }

    updateCharts() {
        if (this.charts.gpu && this.history.gpu.length > 0) {
            this.charts.gpu.data.labels = this.history.gpu.map((_, i) => i);
            this.charts.gpu.data.datasets[0].data = this.history.gpu.map(g => g.utilization);
            this.charts.gpu.update('none');
        }
    }

    startPeriodicChecks() {
        // API fallback cada 30s
        setInterval(() => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                fetch('/api/v1/metrics')
                    .then(r => r.json())
                    .then(data => this.updateDashboard(data))
                    .catch(e => console.error('[API] Fallback failed:', e));
            }
        }, 30000);
    }
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    window.Dashboard = new DashboardController();
    console.log('[DASHBOARD] v4.1 initialized');
});
