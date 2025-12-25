// WOLF Memory Control Dashboard
// Virtual LCD Interface with Real-time API Integration

class WolfDashboard {
    constructor() {
        this.config = {
            wolfBackend: 'http://localhost:4500',
            openMemory: 'http://localhost:8765',
            qdrant: 'http://localhost:6333',
            neo4j: 'http://localhost:7474',
            lmStudio: 'https://ai-studio.complexsimplicityai.com/v1',
            updateInterval: 2000, // 2 seconds
            gpuUpdateInterval: 1000, // 1 second for GPU
        };
        
        this.apiKey = 'wolf-permanent-api-key-2024-never-expires';
        this.startTime = Date.now();
        this.gpuHistory = [];
        this.maxGpuHistory = 8;
        
        this.init();
    }
    
    init() {
        console.log('🐺 WOLF Dashboard initializing...');
        
        // Hide boot screen after 3 seconds
        setTimeout(() => {
            const bootScreen = document.getElementById('bootScreen');
            if (bootScreen) {
                bootScreen.classList.add('hidden');
            }
        }, 3500);
        
        this.addLog('System initialized', 'success');
        this.startUpdateCycles();
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);
    }
    
    // ============ UPDATE CYCLES ============
    
    startUpdateCycles() {
        // Initial updates
        this.updateMemoryStats();
        this.updateAgentStatus();
        this.updatePipelineStatus();
        this.updateLMStudioStatus();
        this.updateGPUMetrics();

        // Periodic updates
        setInterval(() => this.updateMemoryStats(), this.config.updateInterval);
        setInterval(() => this.updateAgentStatus(), this.config.updateInterval);
        setInterval(() => this.updatePipelineStatus(), this.config.updateInterval * 2);
        setInterval(() => this.updateLMStudioStatus(), this.config.updateInterval * 3);
        setInterval(() => this.updateGPUMetrics(), this.config.gpuUpdateInterval);
    }

    // ============ PIPELINE STATUS ============

    async updatePipelineStatus() {
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/pipeline/status`);

            if (response.ok) {
                const data = await response.json();

                // Update MariaDB status
                const mariaStatus = data.components?.mariadb?.status || 'offline';
                this.setIndicatorStatus('mariadb-status', mariaStatus === 'online' ? 'online' : 'offline');

                // Update Qdrant status
                const qdrantStatus = data.components?.qdrant?.status || 'offline';
                this.setIndicatorStatus('qdrant-status', qdrantStatus === 'online' ? 'online' : 'offline');

                // Update Neo4j status
                const neo4jStatus = data.components?.neo4j?.status || 'offline';
                this.setIndicatorStatus('neo4j-status', neo4jStatus === 'online' ? 'online' : 'offline');

                // Update sync progress
                if (data.sync_percentage !== undefined) {
                    this.updateProgress(data.sync_percentage);
                }

                // Update sync status text
                const syncStatus = document.getElementById('sync-status');
                if (syncStatus) {
                    syncStatus.textContent = data.sync_status?.toUpperCase() || 'UNKNOWN';
                }

            } else {
                this.setIndicatorStatus('mariadb-status', 'offline');
            }

        } catch (error) {
            console.error('Pipeline status error:', error);
            this.setIndicatorStatus('mariadb-status', 'offline');
        }
    }
    
    // ============ MEMORY STATISTICS ============
    
    async updateMemoryStats() {
        try {
            // MariaDB Stats (Source of Truth)
            const mariaResponse = await fetch(`${this.config.wolfBackend}/api/mariadb/stats`);
            
            if (mariaResponse.ok) {
                const mariaData = await mariaResponse.json();
                this.updateElement('total-memories', this.formatNumber(mariaData.total || 0));
                this.updateElement('total-apps', mariaData.apps?.length || 0);
                this.updateTimestamp('memory-timestamp');
                this.setIndicatorStatus('openmemory-status', 'online');
            } else {
                this.setIndicatorStatus('openmemory-status', 'offline');
            }
            
            // Qdrant Vector Count (will show 0 until synced from MariaDB)
            await this.updateQdrantStats();
            
            // Neo4j Relationship Count
            await this.updateNeo4jStats();
            
        } catch (error) {
            console.error('Memory stats error:', error);
            this.setIndicatorStatus('openmemory-status', 'offline');
        }
    }
    
    async updateQdrantStats() {
        try {
            const response = await fetch(`${this.config.qdrant}/collections`);
            if (response.ok) {
                const data = await response.json();
                let totalVectors = 0;
                
                if (data.result && data.result.collections) {
                    for (const collection of data.result.collections) {
                        const collResponse = await fetch(`${this.config.qdrant}/collections/${collection.name}`);
                        if (collResponse.ok) {
                            const collData = await collResponse.json();
                            totalVectors += collData.result?.points_count || 0;
                        }
                    }
                }
                
                this.updateElement('total-vectors', this.formatNumber(totalVectors));
                this.setIndicatorStatus('qdrant-status', totalVectors > 0 ? 'online' : 'warning');
                
                // Update sync progress
                const memoryCount = parseInt(document.getElementById('total-memories').textContent.replace(/,/g, '')) || 0;
                const progress = memoryCount > 0 ? (totalVectors / memoryCount) * 100 : 0;
                this.updateProgress(progress);
                
            } else {
                this.setIndicatorStatus('qdrant-status', 'offline');
            }
        } catch (error) {
            console.error('Qdrant stats error:', error);
            this.setIndicatorStatus('qdrant-status', 'offline');
            this.updateElement('total-vectors', '0');
        }
    }
    
    async updateNeo4jStats() {
        try {
            // Neo4j relationship count via Cypher query
            // This would require authentication - placeholder for now
            this.updateElement('total-relations', '0');
            this.setIndicatorStatus('neo4j-status', 'warning');
        } catch (error) {
            console.error('Neo4j stats error:', error);
            this.setIndicatorStatus('neo4j-status', 'offline');
        }
    }
    
    // ============ GPU METRICS ============
    
    async updateGPUMetrics() {
        try {
            // Get real GPU metrics from sysfs via backend
            const response = await fetch(`${this.config.wolfBackend}/api/wolf/gpu-stats`);
            
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    this.updateGPUDisplay(result.data);
                } else {
                    console.warn('GPU metrics unavailable:', result.error);
                    this.displayGPUUnavailable();
                }
            } else {
                console.error('GPU endpoint error:', response.status);
                this.displayGPUUnavailable();
            }
            
            this.updateTimestamp('gpu-timestamp');
        } catch (error) {
            console.error('GPU metrics error:', error);
            this.displayGPUUnavailable();
        }
    }
    
    displayGPUUnavailable() {
        // Show N/A instead of fake data when GPU monitoring unavailable
        this.updateElement('gpu-load', 'N/A');
        this.updateElement('gpu-temp', 'N/A');
        this.updateElement('vram-usage', 'N/A');
        this.updateElement('power-draw', 'N/A');
    }
    
    updateGPUDisplay(data) {
        // Display real GPU metrics from sysfs/LACT
        this.updateElement('gpu-load', `${data.load}%`);
        
        const temp = data.temperature;
        const tempEl = document.getElementById('gpu-temp');
        this.updateElement('gpu-temp', `${temp}°C`);
        if (temp > 80) {
            tempEl.classList.add('hot');
        } else {
            tempEl.classList.remove('hot');
        }
        
        this.updateElement('vram-usage', `${data.vram_used}/${data.vram_total} MB`);
        this.updateElement('power-draw', `${data.power_draw}W`);
        
        // Update bar graph
        this.gpuHistory.push(data.load);
        if (this.gpuHistory.length > this.maxGpuHistory) {
            this.gpuHistory.shift();
        }
        
        const bars = document.querySelectorAll('#gpu-graph .bar');
        bars.forEach((bar, index) => {
            const value = this.gpuHistory[index] || 0;
            bar.style.height = `${value}%`;
        });
    }
    
    // ============ AGENT STATUS ============
    
    async updateAgentStatus() {
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/wolf/status`);

            if (response.ok) {
                const data = await response.json();
                this.setIndicatorStatus('backend-status', 'online');

                // Update agent states
                this.setAgentState('embedder', data.agents?.embedder || 'offline');
                this.setAgentState('categorization', data.agents?.categorization || 'offline');

                // Update queue size
                this.updateElement('queue-size', data.queue_size || 0);

            } else {
                this.setIndicatorStatus('backend-status', 'offline');
                this.setAgentState('embedder', 'offline');
                this.setAgentState('categorization', 'offline');
            }

            // Check LM Studio models status separately
            await this.updateLMStudioAgents();

            this.updateTimestamp('agent-timestamp');

        } catch (error) {
            console.error('Agent status error:', error);
            this.setIndicatorStatus('backend-status', 'offline');
            this.setAllAgentsOffline();
        }
    }

    async updateLMStudioAgents() {
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/lmstudio/status`);

            if (response.ok) {
                const data = await response.json();

                if (data.ok && data.status === 'online') {
                    // Check if chat model (Amethyst) is loaded
                    if (data.chat_model) {
                        this.setAgentState('amethyst', 'running');
                    } else {
                        this.setAgentState('amethyst', 'offline');
                    }

                    // Check if embed model (Qwen3) is loaded
                    if (data.embed_model) {
                        this.setAgentState('qwen3embed', 'running');
                    } else {
                        this.setAgentState('qwen3embed', 'offline');
                    }
                } else {
                    this.setAgentState('amethyst', 'offline');
                    this.setAgentState('qwen3embed', 'offline');
                }
            } else {
                this.setAgentState('amethyst', 'offline');
                this.setAgentState('qwen3embed', 'offline');
            }
        } catch (error) {
            console.error('LM Studio agents error:', error);
            this.setAgentState('amethyst', 'offline');
            this.setAgentState('qwen3embed', 'offline');
        }
    }
    
    setAgentState(agentName, state) {
        const stateEl = document.getElementById(`${agentName}-state`);
        const ledEl = document.getElementById(`${agentName}-led`);
        
        if (stateEl && ledEl) {
            stateEl.textContent = state.toUpperCase();
            ledEl.className = 'led';
            
            if (state === 'running' || state === 'online' || state === 'active') {
                stateEl.classList.add('active');
                ledEl.classList.add('online');
            } else if (state === 'warning' || state === 'degraded') {
                ledEl.classList.add('warning');
            } else {
                stateEl.classList.remove('active');
                ledEl.classList.add('offline');
            }
        }
    }
    
    setAllAgentsOffline() {
        ['embedder', 'categorization', 'amethyst', 'qwen3embed'].forEach(agent => {
            this.setAgentState(agent, 'offline');
        });
        this.updateElement('queue-size', '0');
    }
    
    // ============ LM STUDIO STATUS ============

    async updateLMStudioStatus() {
        try {
            // Use backend proxy to avoid CORS issues
            const response = await fetch(`${this.config.wolfBackend}/api/lmstudio/status`);

            if (response.ok) {
                const data = await response.json();

                if (data.ok && data.status === 'online') {
                    this.updateElement('lm-status', 'ONLINE');
                    this.updateElement('lm-endpoint', data.endpoint || this.config.lmStudio);

                    // Update models from backend response
                    if (data.chat_model) {
                        this.updateElement('chat-model', this.formatModelName(data.chat_model));
                    }
                    if (data.embed_model) {
                        this.updateElement('embed-model', this.formatModelName(data.embed_model));
                    }
                } else {
                    this.updateElement('lm-status', 'OFFLINE');
                    this.updateElement('lm-endpoint', data.endpoint || this.config.lmStudio);
                }

            } else {
                // Fallback: try direct connection
                try {
                    const directResponse = await fetch(`${this.config.lmStudio}/models`);
                    if (directResponse.ok) {
                        const data = await directResponse.json();
                        this.updateElement('lm-status', 'ONLINE');

                        if (data.data && data.data.length > 0) {
                            const chatModel = data.data.find(m => m.id.includes('mistral') || m.id.includes('amethyst'));
                            const embedModel = data.data.find(m => m.id.includes('qwen') || m.id.includes('embedding'));

                            if (chatModel) this.updateElement('chat-model', this.formatModelName(chatModel.id));
                            if (embedModel) this.updateElement('embed-model', this.formatModelName(embedModel.id));
                        }
                    } else {
                        this.updateElement('lm-status', 'OFFLINE');
                    }
                } catch (directError) {
                    this.updateElement('lm-status', 'OFFLINE');
                }
            }

            this.updateTimestamp('lm-timestamp');

        } catch (error) {
            console.error('LM Studio status error:', error);
            this.updateElement('lm-status', 'OFFLINE');
        }
    }
    
    formatModelName(modelId) {
        // Clean up model ID for display
        return modelId.replace(/^.*\//, '').replace(/-/g, ' ').toUpperCase();
    }
    
    // ============ SYSTEM STATUS ============
    
    async updateSystemStatus() {
        try {
            // Check all services
            const checks = [
                this.checkService(this.config.wolfBackend, 'backend-status'),
                this.checkService(this.config.openMemory, 'openmemory-status'),
                this.checkService(this.config.qdrant, 'qdrant-status'),
                this.checkService(this.config.neo4j, 'neo4j-status')
            ];
            
            await Promise.all(checks);
            
            // Update system load (mock for now)
            const load = Math.round(Math.random() * 30 + 10);
            this.updateElement('system-load', `${load}%`);
            
        } catch (error) {
            console.error('System status error:', error);
        }
    }
    
    async checkService(url, elementId) {
        try {
            const response = await fetch(url, { method: 'HEAD', mode: 'no-cors' });
            // Note: no-cors won't give us status, so we just assume success if no error
            this.setIndicatorStatus(elementId, 'online');
        } catch (error) {
            this.setIndicatorStatus(elementId, 'offline');
        }
    }
    
    // ============ BUTTON FEEDBACK SYSTEM ============
    
    setButtonState(button, state) {
        // Remove all state classes
        button.classList.remove('executing', 'success', 'error');
        
        if (state === 'executing') {
            button.classList.add('executing');
        } else if (state === 'success') {
            button.classList.add('success');
            setTimeout(() => button.classList.remove('success'), 2000);
        } else if (state === 'error') {
            button.classList.add('error');
            setTimeout(() => button.classList.remove('error'), 2000);
        }
    }
    
    // ============ CONTROL ACTIONS ============
    
    async initSystem() {
        const button = event?.target?.closest('.lcd-button');
        if (button) this.setButtonState(button, 'executing');
        
        this.addLog('Initializing system...', 'warning');
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/wolf/init`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.addLog('System initialized successfully', 'success');
                if (button) this.setButtonState(button, 'success');
                setTimeout(() => this.refreshAll(), 1000);
            } else {
                this.addLog('System initialization failed', 'error');
                if (button) this.setButtonState(button, 'error');
            }
        } catch (error) {
            this.addLog(`Init error: ${error.message}`, 'error');
            if (button) this.setButtonState(button, 'error');
        }
    }

    async syncPipeline() {
        const button = event?.target?.closest('.lcd-button');
        if (button) this.setButtonState(button, 'executing');

        this.addLog('Starting pipeline sync: MariaDB → Qdrant + Neo4j...', 'warning');
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/pipeline/sync`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.addLog(`✓ Pipeline sync started (PID: ${data.pid})`, 'success');
                    if (button) this.setButtonState(button, 'success');
                    // Start checking pipeline status more frequently
                    setTimeout(() => this.updatePipelineStatus(), 2000);
                } else {
                    this.addLog(`✗ Pipeline sync failed: ${data.error || 'Unknown error'}`, 'error');
                    if (button) this.setButtonState(button, 'error');
                }
            } else {
                this.addLog(`✗ Failed to start pipeline sync (HTTP ${response.status})`, 'error');
                if (button) this.setButtonState(button, 'error');
            }
        } catch (error) {
            this.addLog(`Pipeline sync error: ${error.message}`, 'error');
            if (button) this.setButtonState(button, 'error');
        }
    }

    async startEmbedder() {
        const button = event?.target?.closest('.lcd-button');
        if (button) this.setButtonState(button, 'executing');
        
        this.addLog('Starting embedder agent...', 'warning');
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/wolf/embedder/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.addLog('✓ Embedder agent started successfully', 'success');
                    if (button) this.setButtonState(button, 'success');
                    setTimeout(() => this.updateAgentStatus(), 1000);
                } else {
                    this.addLog(`✗ Embedder failed: ${data.error || 'Unknown error'}`, 'error');
                    if (button) this.setButtonState(button, 'error');
                }
            } else {
                this.addLog(`✗ Failed to start embedder (HTTP ${response.status})`, 'error');
                if (button) this.setButtonState(button, 'error');
            }
        } catch (error) {
            this.addLog(`✗ Embedder error: ${error.message}`, 'error');
            if (button) this.setButtonState(button, 'error');
        }
    }
    
    async searchMemories() {
        const button = event?.target?.closest('.lcd-button');
        const query = prompt('Enter search query:');
        if (!query) return;

        if (button) this.setButtonState(button, 'executing');
        this.addLog(`Searching for: ${query}`, 'warning');
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/wolf/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, limit: 10 })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.addLog(`Found ${data.results?.length || 0} results`, 'success');
                if (button) this.setButtonState(button, 'success');
                console.log('Search results:', data);
            } else {
                this.addLog('Search failed', 'error');
                if (button) this.setButtonState(button, 'error');
            }
        } catch (error) {
            this.addLog(`Search error: ${error.message}`, 'error');
            if (button) this.setButtonState(button, 'error');
        }
    }
    
    async clearCache() {
        const button = event?.target?.closest('.lcd-button');
        if (!confirm('Clear memory cache? This will remove cached data but not memories.')) return;
        
        if (button) this.setButtonState(button, 'executing');
        this.addLog('Clearing cache...', 'warning');
        try {
            const response = await fetch(`${this.config.wolfBackend}/api/wolf/clear`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ all: false, category: 'cache' })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.addLog('✓ Cache cleared successfully', 'success');
                    if (button) this.setButtonState(button, 'success');
                    setTimeout(() => this.refreshAll(), 1000);
                } else {
                    this.addLog(`✗ Clear failed: ${data.error || 'Unknown error'}`, 'error');
                    if (button) this.setButtonState(button, 'error');
                }
            } else {
                this.addLog(`✗ Failed to clear cache (HTTP ${response.status})`, 'error');
                if (button) this.setButtonState(button, 'error');
            }
        } catch (error) {
            this.addLog(`✗ Clear error: ${error.message}`, 'error');
            if (button) this.setButtonState(button, 'error');
        }
    }
    
    refreshAll() {
        const button = event?.target?.closest('.lcd-button');
        if (button) this.setButtonState(button, 'executing');
        
        this.addLog('Refreshing all data...', 'warning');
        this.updateMemoryStats();
        this.updateAgentStatus();
        this.updateSystemStatus();
        this.updateLMStudioStatus();
        this.updateGPUMetrics();
        
        setTimeout(() => {
            this.addLog('Refresh complete', 'success');
            if (button) this.setButtonState(button, 'success');
        }, 500);
    }
    
    viewLogs() {
        const button = event?.target?.closest('.lcd-button');
        if (button) this.setButtonState(button, 'executing');
        
        this.addLog('Opening backend logs...', 'info');
        window.open(`${this.config.wolfBackend}/logs`, '_blank', 'width=1000,height=800');
        
        setTimeout(() => {
            if (button) this.setButtonState(button, 'success');
        }, 300);
    }
    
    // ============ UI HELPERS ============
    
    updateElement(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    }
    
    updateTimestamp(id) {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { hour12: false });
        this.updateElement(id, time);
    }
    
    updateProgress(percentage) {
        const progressBar = document.getElementById('memory-progress');
        if (progressBar) {
            progressBar.style.width = `${Math.min(100, percentage)}%`;
        }
        
        const syncStatus = document.getElementById('sync-status');
        if (syncStatus) {
            if (percentage >= 99) {
                syncStatus.textContent = 'COMPLETE';
                syncStatus.style.color = 'var(--lcd-green)';
            } else if (percentage > 0) {
                syncStatus.textContent = `SYNCING ${percentage.toFixed(1)}%`;
                syncStatus.style.color = 'var(--lcd-amber)';
            } else {
                syncStatus.textContent = 'IDLE';
                syncStatus.style.color = 'var(--text-dim)';
            }
        }
    }
    
    setIndicatorStatus(id, status) {
        const indicator = document.getElementById(id);
        if (indicator) {
            const led = indicator.querySelector('.led');
            if (led) {
                led.className = 'led';
                led.classList.add(status);
            }
        }
    }
    
    addLog(message, type = 'info') {
        const logContainer = document.getElementById('activity-log');
        if (!logContainer) return;
        
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        entry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message">${message}</span>
        `;
        
        // Add to top
        logContainer.insertBefore(entry, logContainer.firstChild);
        
        // Keep only last 20 entries
        while (logContainer.children.length > 20) {
            logContainer.removeChild(logContainer.lastChild);
        }
        
        // Update last update timestamp
        this.updateElement('last-update', time);
    }
    
    updateClock() {
        // Update uptime
        const uptime = Date.now() - this.startTime;
        const hours = Math.floor(uptime / 3600000);
        const minutes = Math.floor((uptime % 3600000) / 60000);
        const seconds = Math.floor((uptime % 60000) / 1000);
        
        this.updateElement('uptime', 
            `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
        );
    }
    
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
}

// Initialize dashboard when DOM is ready
const dashboard = new WolfDashboard();

console.log('🐺 WOLF Dashboard loaded and running');
