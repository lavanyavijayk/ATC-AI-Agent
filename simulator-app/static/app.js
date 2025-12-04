/**
 * AI-ATC Simulator - Frontend Application
 */

class ATCSimulator {
    constructor() {
        this.canvas = document.getElementById('mapCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.flights = [];
        this.waypoints = {};
        this.landingRules = {};
        this.airport = {};
        this.selectedFlight = null;
        this.viewRange = 35;
        this.ws = null;
        this.activeTab = 'all';
        this._mouseOverDetailPanel = false;
        
        this.stats = {
            landed: 0,
            departed: 0,
            near_misses: 0,
            failed: false,
            failure_reason: null,
            speed_multiplier: 1.0
        };
        this.nearMisses = [];
        this.history = { landed: [], departed: [] };
        this.currentSpeed = 1;
        
        // Chat settings
        this.maxChatMessages = 100;
        this.chatAutoScroll = true;
        
        this.init();
    }
    
    // =========================================================================
    // Chat Methods
    // =========================================================================
    
    addChatMessage(type, sender, text, isImportant = false) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        
        // Remove welcome message if it exists
        const welcome = container.querySelector('.chat-welcome');
        if (welcome) welcome.remove();
        
        // Create message element
        const msg = document.createElement('div');
        msg.className = `chat-message ${type}${isImportant ? ' clearance' : ''}`;
        
        const time = new Date().toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        
        msg.innerHTML = `
            <span class="msg-time">${time}</span>
            <span class="msg-sender">${sender}:</span>
            <span class="msg-text">${text}</span>
        `;
        
        container.appendChild(msg);
        
        // Limit messages
        while (container.children.length > this.maxChatMessages) {
            container.removeChild(container.firstChild);
        }
        
        // Auto-scroll
        if (this.chatAutoScroll) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    formatATCCommand(callsign, command) {
        // Format the ATC command into readable text
        const parts = [];
        
        if (command.waypoint) {
            parts.push(`proceed direct ${command.waypoint}`);
        }
        if (command.altitude) {
            const action = command.altitude > 5000 ? 'climb and maintain' : 'descend and maintain';
            parts.push(`${action} ${command.altitude.toLocaleString()} feet`);
        }
        if (command.speed) {
            parts.push(`reduce speed to ${command.speed} knots`);
        }
        if (command.heading) {
            parts.push(`turn heading ${command.heading.toString().padStart(3, '0')}`);
        }
        if (command.clear_to_land) {
            return `cleared to land runway 34`;
        }
        if (command.cleared_for_takeoff) {
            return `cleared for takeoff runway 34, fly heading 340`;
        }
        
        return parts.join(', ') || 'roger';
    }
    
    formatFlightReadback(callsign, command) {
        // Generate pilot readback
        const parts = [];
        
        if (command.waypoint) {
            parts.push(`direct ${command.waypoint}`);
        }
        if (command.altitude) {
            parts.push(`${command.altitude.toLocaleString()}`);
        }
        if (command.speed) {
            parts.push(`speed ${command.speed}`);
        }
        if (command.heading) {
            parts.push(`heading ${command.heading.toString().padStart(3, '0')}`);
        }
        if (command.clear_to_land) {
            return `cleared to land runway 34, ${callsign}`;
        }
        if (command.cleared_for_takeoff) {
            return `cleared for takeoff runway 34, ${callsign}`;
        }
        
        return parts.length > 0 ? `${parts.join(', ')}, ${callsign}` : `roger, ${callsign}`;
    }
    
    handleATCMessage(data) {
        // Handle incoming ATC communication
        const { callsign, command, source } = data;
        
        // Determine if this is an important clearance
        const isClearance = command.clear_to_land || command.cleared_for_takeoff;
        
        // Add ATC command
        const atcText = this.formatATCCommand(callsign, command);
        this.addChatMessage('atc', 'KRNT Tower', `${callsign}, ${atcText}`, isClearance);
        
        // Add flight readback after short delay
        setTimeout(() => {
            const readback = this.formatFlightReadback(callsign, command);
            this.addChatMessage('flight', callsign, readback, isClearance);
        }, 800 + Math.random() * 400);
    }
    
    addSystemMessage(text) {
        this.addChatMessage('system', 'SYSTEM', text);
    }
    
    async init() {
        this.setupCanvas();
        this.setupEventListeners();
        await this.loadStaticData();
        this.connectWebSocket();
        this.startClock();
        this.render();
    }
    
    async loadStaticData() {
        try {
            const [waypointsRes, rulesRes, airportRes] = await Promise.all([
                fetch('/api/waypoints'),
                fetch('/api/landing-rules'),
                fetch('/api/airport')
            ]);
            
            this.waypoints = await waypointsRes.json();
            this.landingRules = await rulesRes.json();
            this.airport = await airportRes.json();
            
            this.updateRulesPanel();
        } catch (err) {
            console.error('Failed to load static data:', err);
        }
    }
    
    updateRulesPanel() {
        const r = this.landingRules;
        document.getElementById('ruleAlt').textContent = `< ${r.max_altitude} ft`;
        document.getElementById('ruleSpd').textContent = `${r.min_speed}-${r.max_speed} kt`;
        document.getElementById('ruleDist').textContent = `< ${r.max_distance} nm`;
        document.getElementById('ruleWpt').textContent = r.required_waypoint;
    }
    
    setupCanvas() {
        const resize = () => {
            const container = this.canvas.parentElement;
            const rect = container.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            
            this.canvas.width = rect.width * dpr;
            this.canvas.height = rect.height * dpr;
            this.ctx.scale(dpr, dpr);
            
            this.canvasWidth = rect.width;
            this.canvasHeight = rect.height;
            this.centerX = rect.width / 2;
            this.centerY = rect.height / 2;
            this.scale = Math.min(rect.width, rect.height) / (this.viewRange * 2.2);
            
            document.getElementById('pixelValue').textContent = Math.round(this.scale);
        };
        
        resize();
        window.addEventListener('resize', resize);
    }
    
    setupEventListeners() {
        document.getElementById('zoomIn').addEventListener('click', () => {
            this.viewRange = Math.max(10, this.viewRange - 5);
            this.setupCanvas();
        });
        
        document.getElementById('zoomOut').addEventListener('click', () => {
            this.viewRange = Math.min(60, this.viewRange + 5);
            this.setupCanvas();
        });
        
        document.getElementById('spawnArrival').addEventListener('click', async () => {
            await fetch('/api/simulation/spawn/arrival', { method: 'POST' });
        });
        
        document.getElementById('spawnDeparture').addEventListener('click', async () => {
            await fetch('/api/simulation/spawn/departure', { method: 'POST' });
        });
        
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.activeTab = e.target.dataset.tab;
                this.updateFlightStrips();
            });
        });
        
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            this.selectFlightAtPosition(x, y);
        });
        
        document.getElementById('closeDetail').addEventListener('click', () => {
            this.deselectFlight();
        });
        
        document.getElementById('toggleRules').addEventListener('click', () => {
            document.getElementById('rulesPanel').classList.toggle('collapsed');
        });
        
        const detailPanel = document.getElementById('detailPanel');
        detailPanel.addEventListener('mouseenter', () => {
            this._mouseOverDetailPanel = true;
        });
        detailPanel.addEventListener('mouseleave', () => {
            this._mouseOverDetailPanel = false;
            setTimeout(() => this.updateDetailPanel(), 100);
        });
        
        document.querySelectorAll('.speed-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const speed = parseFloat(e.target.dataset.speed);
                this.setSpeed(speed);
            });
        });
        document.querySelector('.speed-btn[data-speed="1"]').classList.add('active');
        
        document.getElementById('restartBtn').addEventListener('click', () => {
            this.restart();
        });
        document.getElementById('failureRestartBtn').addEventListener('click', () => {
            this.restart();
        });
    }
    
    setSpeed(multiplier) {
        this.currentSpeed = multiplier;
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'set_speed',
                multiplier: multiplier
            }));
        }
        
        document.querySelectorAll('.speed-btn').forEach(btn => {
            btn.classList.toggle('active', parseFloat(btn.dataset.speed) === multiplier);
        });
    }
    
    restart() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'restart' }));
        }
        document.getElementById('failureOverlay').classList.remove('visible');
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.updateConnectionStatus('connected');
        };
        
        this.ws.onclose = () => {
            this.updateConnectionStatus('disconnected');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onerror = () => {
            this.updateConnectionStatus('disconnected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'update') {
                this.flights = data.flights;
                this.stats = data.stats || this.stats;
                this.nearMisses = data.near_misses || [];
                this.history = data.history || this.history;
                
                this.updateStats();
                this.updateFlightStrips();
                
                if (!this.isUserInteracting()) {
                    this.updateDetailPanel();
                } else if (this.selectedFlight) {
                    const updated = this.flights.find(f => f.callsign === this.selectedFlight.callsign);
                    if (updated) this.selectedFlight = updated;
                }
                
                if (this.stats.failed) {
                    this.showFailure();
                }
            }
            
            // Handle ATC radio communications
            if (data.type === 'atc_message') {
                this.handleATCMessage(data);
            }
            
            // Handle system messages
            if (data.type === 'system_message') {
                this.addSystemMessage(data.text);
            }
        };
    }
    
    updateStats() {
        document.getElementById('landedCount').textContent = this.stats.landed || 0;
        document.getElementById('departedCount').textContent = this.stats.departed || 0;
        document.getElementById('nearMissCount').textContent = this.stats.near_misses || 0;
    }
    
    showFailure() {
        document.getElementById('failureReason').textContent = this.stats.failure_reason || 'Unknown error';
        document.getElementById('finalLanded').textContent = this.stats.landed || 0;
        document.getElementById('finalDeparted').textContent = this.stats.departed || 0;
        document.getElementById('finalNearMisses').textContent = this.stats.near_misses || 0;
        document.getElementById('failureOverlay').classList.add('visible');
    }
    
    isUserInteracting() {
        const activeElement = document.activeElement;
        const detailPanel = document.getElementById('detailPanel');
        if (!detailPanel || !activeElement) return false;
        
        if (detailPanel.contains(activeElement)) {
            const tagName = activeElement.tagName.toLowerCase();
            if (tagName === 'input' || tagName === 'select' || tagName === 'button') {
                return true;
            }
        }
        
        if (this._mouseOverDetailPanel) {
            return true;
        }
        
        return false;
    }
    
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connectionStatus');
        indicator.className = 'status-indicator ' + status;
        indicator.querySelector('.status-text').textContent = 
            status === 'connected' ? 'Connected' : 
            status === 'disconnected' ? 'Disconnected' : 'Connecting...';
    }
    
    startClock() {
        const updateClock = () => {
            const now = new Date();
            const utc = now.toISOString().substr(11, 8) + 'Z';
            document.getElementById('clock').textContent = utc;
        };
        
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    toCanvasCoords(x, y) {
        return {
            x: this.centerX + x * this.scale,
            y: this.centerY - y * this.scale
        };
    }
    
    render() {
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        this.drawMapBackground();
        this.drawWaypoints();
        this.drawRunway();
        this.drawNearMisses();
        this.drawFlights();
        
        requestAnimationFrame(() => this.render());
    }
    
    drawMapBackground() {
        this.ctx.fillStyle = '#0f1419';
        this.ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        this.ctx.strokeStyle = '#1e2530';
        this.ctx.lineWidth = 1;
        
        const gridSpacing = 5;
        const gridRange = Math.ceil(this.viewRange / gridSpacing) * gridSpacing;
        
        for (let i = -gridRange; i <= gridRange; i += gridSpacing) {
            const vx = this.toCanvasCoords(i, 0).x;
            this.ctx.beginPath();
            this.ctx.moveTo(vx, 0);
            this.ctx.lineTo(vx, this.canvasHeight);
            this.ctx.stroke();
            
            const hy = this.toCanvasCoords(0, i).y;
            this.ctx.beginPath();
            this.ctx.moveTo(0, hy);
            this.ctx.lineTo(this.canvasWidth, hy);
            this.ctx.stroke();
        }
        
        this.ctx.fillStyle = '#4a5568';
        this.ctx.font = '10px JetBrains Mono';
        this.ctx.textAlign = 'center';
        
        for (let d = gridSpacing; d <= gridRange; d += gridSpacing) {
            if (d <= this.viewRange) {
                const pos = this.toCanvasCoords(d, 0);
                this.ctx.fillText(`${d}nm`, pos.x, this.centerY + 12);
            }
        }
    }
    
    drawWaypoints() {
        Object.entries(this.waypoints).forEach(([name, wp]) => {
            const pos = this.toCanvasCoords(wp.position.x, wp.position.y);
            
            if (Math.abs(wp.position.x) > this.viewRange * 1.1 || 
                Math.abs(wp.position.y) > this.viewRange * 1.1) {
                return;
            }
            
            let color = '#8b5cf6';
            let size = 6;
            
            if (name === 'RUNWAY') {
                return;
            } else if (name === 'FINAL') {
                color = '#ef4444';
                size = 8;
            } else if (['DOWNWIND', 'BASE'].includes(name)) {
                color = '#f59e0b';
            } else if (name === 'NORTH') {
                color = '#22c55e';  // Green for departure exit
            } else if (['ALPHA', 'BRAVO', 'CHARLIE', 'DELTA', 'ECHO', 'HOTEL'].includes(name)) {
                color = '#06b6d4';  // Cyan for AI sequencing waypoints
                size = 5;
            } else {
                color = '#3b82f6';
            }
            
            this.ctx.fillStyle = color;
            this.ctx.beginPath();
            this.ctx.moveTo(pos.x, pos.y - size);
            this.ctx.lineTo(pos.x - size * 0.866, pos.y + size * 0.5);
            this.ctx.lineTo(pos.x + size * 0.866, pos.y + size * 0.5);
            this.ctx.closePath();
            this.ctx.fill();
            
            this.ctx.fillStyle = '#e2e8f0';
            this.ctx.font = 'bold 10px JetBrains Mono';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(name, pos.x, pos.y + size + 12);
            
            if (wp.altitude_restriction && wp.altitude_restriction > 100) {
                this.ctx.fillStyle = '#94a3b8';
                this.ctx.font = '9px JetBrains Mono';
                this.ctx.fillText(`${wp.altitude_restriction}'`, pos.x, pos.y + size + 22);
            }
        });
        
        // Draw pattern legs
        this.ctx.strokeStyle = '#4a556880';
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([5, 5]);
        
        const pattern = ['DOWNWIND', 'BASE', 'FINAL', 'RUNWAY'];
        for (let i = 0; i < pattern.length - 1; i++) {
            const wp1 = this.waypoints[pattern[i]];
            const wp2 = this.waypoints[pattern[i + 1]];
            if (wp1 && wp2) {
                const p1 = this.toCanvasCoords(wp1.position.x, wp1.position.y);
                const p2 = this.toCanvasCoords(wp2.position.x, wp2.position.y);
                this.ctx.beginPath();
                this.ctx.moveTo(p1.x, p1.y);
                this.ctx.lineTo(p2.x, p2.y);
                this.ctx.stroke();
            }
        }
        
        // Draw extended centerline
        const finalWp = this.waypoints['FINAL'];
        const runwayWp = this.waypoints['RUNWAY'];
        if (finalWp && runwayWp) {
            this.ctx.strokeStyle = '#ef444450';
            this.ctx.setLineDash([8, 4]);
            
            const dx = runwayWp.position.x - finalWp.position.x;
            const dy = runwayWp.position.y - finalWp.position.y;
            const extendedX = finalWp.position.x - dx * 2;
            const extendedY = finalWp.position.y - dy * 2;
            
            const pExtended = this.toCanvasCoords(extendedX, extendedY);
            const pRunway = this.toCanvasCoords(runwayWp.position.x, runwayWp.position.y);
            
            this.ctx.beginPath();
            this.ctx.moveTo(pExtended.x, pExtended.y);
            this.ctx.lineTo(pRunway.x, pRunway.y);
            this.ctx.stroke();
        }
        
        // Draw departure route (runway to NORTH)
        const northWp = this.waypoints['NORTH'];
        if (runwayWp && northWp) {
            this.ctx.strokeStyle = '#22c55e40';
            this.ctx.setLineDash([8, 4]);
            
            const pRunway = this.toCanvasCoords(runwayWp.position.x, runwayWp.position.y);
            const pNorth = this.toCanvasCoords(northWp.position.x, northWp.position.y);
            
            this.ctx.beginPath();
            this.ctx.moveTo(pRunway.x, pRunway.y);
            this.ctx.lineTo(pNorth.x, pNorth.y);
            this.ctx.stroke();
        }
        
        this.ctx.setLineDash([]);
    }
    
    drawRunway() {
        const runwayLength = this.airport.runway_length || 1;
        const heading = this.airport.runway_heading || 340;
        
        const headingRad = (heading) * Math.PI / 180;
        
        const halfLen = runwayLength / 2;
        const dx = Math.sin(headingRad) * halfLen;
        const dy = Math.cos(headingRad) * halfLen;
        
        const start = this.toCanvasCoords(-dx, -dy);
        const end = this.toCanvasCoords(dx, dy);
        
        this.ctx.strokeStyle = '#64748b';
        this.ctx.lineWidth = 10;
        this.ctx.lineCap = 'butt';
        
        this.ctx.beginPath();
        this.ctx.moveTo(start.x, start.y);
        this.ctx.lineTo(end.x, end.y);
        this.ctx.stroke();
        
        this.ctx.strokeStyle = '#f1f5f9';
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([10, 10]);
        
        this.ctx.beginPath();
        this.ctx.moveTo(start.x, start.y);
        this.ctx.lineTo(end.x, end.y);
        this.ctx.stroke();
        
        this.ctx.setLineDash([]);
        
        this.ctx.fillStyle = '#e2e8f0';
        this.ctx.font = 'bold 12px Oxanium';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('34', end.x + 15, end.y);
        
        const center = this.toCanvasCoords(0, 0);
        this.ctx.fillStyle = '#06b6d4';
        this.ctx.beginPath();
        this.ctx.arc(center.x, center.y, 4, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    drawNearMisses() {
        this.nearMisses.forEach(nm => {
            const pos = this.toCanvasCoords(nm.position.x, nm.position.y);
            
            const time = Date.now() / 500;
            const pulseSize = 20 + Math.sin(time) * 5;
            
            this.ctx.strokeStyle = '#ef4444';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(pos.x, pos.y, pulseSize, 0, Math.PI * 2);
            this.ctx.stroke();
            
            this.ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
            this.ctx.beginPath();
            this.ctx.arc(pos.x, pos.y, pulseSize, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.ctx.fillStyle = '#ef4444';
            this.ctx.font = 'bold 10px JetBrains Mono';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('NEAR MISS', pos.x, pos.y - pulseSize - 5);
        });
    }
    
    drawFlights() {
        this.flights.forEach(flight => {
            const pos = this.toCanvasCoords(flight.position.x, flight.position.y);
            const isSelected = this.selectedFlight?.callsign === flight.callsign;
            const isArrival = flight.flight_type === 'arrival';
            
            if (Math.abs(flight.position.x) > this.viewRange * 1.2 || 
                Math.abs(flight.position.y) > this.viewRange * 1.2) {
                return;
            }
            
            if (flight.target_waypoint && this.waypoints[flight.target_waypoint]) {
                const targetWp = this.waypoints[flight.target_waypoint];
                const targetPos = this.toCanvasCoords(targetWp.position.x, targetWp.position.y);
                
                this.ctx.strokeStyle = isArrival ? '#22c55e50' : '#3b82f650';
                this.ctx.lineWidth = 1;
                this.ctx.setLineDash([3, 3]);
                this.ctx.beginPath();
                this.ctx.moveTo(pos.x, pos.y);
                this.ctx.lineTo(targetPos.x, targetPos.y);
                this.ctx.stroke();
                this.ctx.setLineDash([]);
            }
            
            this.ctx.save();
            this.ctx.translate(pos.x, pos.y);
            this.ctx.rotate((flight.heading - 90) * Math.PI / 180);
            
            const color = isSelected ? '#ffffff' : (isArrival ? '#22c55e' : '#3b82f6');
            this.ctx.fillStyle = color;
            this.ctx.strokeStyle = '#1e293b';
            this.ctx.lineWidth = 1;
            
            this.ctx.beginPath();
            this.ctx.moveTo(10, 0);
            this.ctx.lineTo(-6, -5);
            this.ctx.lineTo(-3, 0);
            this.ctx.lineTo(-6, 5);
            this.ctx.closePath();
            this.ctx.fill();
            this.ctx.stroke();
            
            this.ctx.restore();
            
            const vectorLength = Math.min(flight.speed / 15, 30);
            const headingRad = (flight.heading - 90) * Math.PI / 180;
            
            this.ctx.strokeStyle = isArrival ? '#22c55e80' : '#3b82f680';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.moveTo(pos.x, pos.y);
            this.ctx.lineTo(
                pos.x + Math.cos(headingRad) * vectorLength,
                pos.y + Math.sin(headingRad) * vectorLength
            );
            this.ctx.stroke();
            
            const blockX = pos.x + 14;
            const blockY = pos.y - 12;
            
            this.ctx.fillStyle = 'rgba(15, 20, 25, 0.9)';
            this.ctx.fillRect(blockX, blockY, 75, 28);
            this.ctx.strokeStyle = isSelected ? color : '#3b4559';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(blockX, blockY, 75, 28);
            
            this.ctx.font = 'bold 10px JetBrains Mono';
            this.ctx.fillStyle = color;
            this.ctx.textAlign = 'left';
            this.ctx.fillText(flight.callsign, blockX + 3, blockY + 11);
            
            this.ctx.font = '9px JetBrains Mono';
            this.ctx.fillStyle = '#06b6d4';
            const alt = Math.round(flight.altitude / 100).toString().padStart(3, '0');
            const spd = Math.round(flight.speed);
            this.ctx.fillText(`${alt} ${spd}kt`, blockX + 3, blockY + 22);
            
            if (isSelected) {
                this.ctx.strokeStyle = color;
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.arc(pos.x, pos.y, 16, 0, Math.PI * 2);
                this.ctx.stroke();
            }
        });
    }
    
    selectFlightAtPosition(x, y) {
        for (const flight of this.flights) {
            const pos = this.toCanvasCoords(flight.position.x, flight.position.y);
            const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
            
            if (dist < 25) {
                this.selectFlight(flight);
                return;
            }
        }
        this.deselectFlight();
    }
    
    selectFlight(flight) {
        this.selectedFlight = flight;
        document.getElementById('detailPanel').classList.add('visible');
        this.updateDetailPanel();
        this.updateFlightStrips();
    }
    
    deselectFlight() {
        this.selectedFlight = null;
        document.getElementById('detailPanel').classList.remove('visible');
        this.updateFlightStrips();
    }
    
    updateFlightStrips() {
        const container = document.getElementById('flightStrips');
        
        // History tab
        if (this.activeTab === 'history') {
            this.renderHistoryTab(container);
            return;
        }
        
        let filteredFlights = this.flights.filter(f => 
            !['landed', 'departed'].includes(f.status)
        );
        
        if (this.activeTab === 'arrivals') {
            filteredFlights = filteredFlights.filter(f => f.flight_type === 'arrival');
        } else if (this.activeTab === 'departures') {
            filteredFlights = filteredFlights.filter(f => f.flight_type === 'departure');
        }
        
        if (filteredFlights.length === 0) {
            container.innerHTML = '<div class="no-flights">No active flights. Click "Spawn Arrival" to add one.</div>';
            return;
        }
        
        container.innerHTML = '';
        
        filteredFlights.forEach(flight => {
            const strip = document.createElement('div');
            strip.className = `flight-strip ${flight.flight_type}`;
            
            if (this.selectedFlight?.callsign === flight.callsign) {
                strip.classList.add('selected');
            }
            
            const statusClass = this.getStatusClass(flight.status);
            const waypointInfo = flight.target_waypoint ? 
                `→ ${flight.target_waypoint}` : 
                `HDG ${Math.round(flight.heading)}°`;
            
            strip.innerHTML = `
                <div class="strip-header">
                    <span class="strip-callsign">${flight.callsign}</span>
                    <span class="strip-aircraft">${flight.aircraft_type}</span>
                </div>
                <div class="strip-data">
                    <div class="strip-data-item">
                        <span class="strip-data-label">ALT</span>
                        <span class="strip-data-value">${Math.round(flight.altitude).toLocaleString()}'</span>
                    </div>
                    <div class="strip-data-item">
                        <span class="strip-data-label">SPD</span>
                        <span class="strip-data-value">${Math.round(flight.speed)} kt</span>
                    </div>
                    <div class="strip-data-item">
                        <span class="strip-data-label">NAV</span>
                        <span class="strip-data-value">${waypointInfo}</span>
                    </div>
                </div>
                <span class="strip-status ${statusClass}">${this.formatStatus(flight.status)}</span>
            `;
            
            strip.addEventListener('click', () => this.selectFlight(flight));
            container.appendChild(strip);
        });
    }
    
    renderHistoryTab(container) {
        const landed = this.history.landed || [];
        const departed = this.history.departed || [];
        
        if (landed.length === 0 && departed.length === 0) {
            container.innerHTML = '<div class="no-flights">No completed flights yet.</div>';
            return;
        }
        
        let html = '';
        
        if (landed.length > 0) {
            html += '<div class="history-section-header">✈️ Landed Flights</div>';
            landed.slice().reverse().forEach(f => {
                const time = f.completed_at ? new Date(f.completed_at).toLocaleTimeString() : '';
                html += `
                    <div class="history-entry">
                        <div class="entry-header">
                            <span class="entry-callsign">${f.callsign}</span>
                            <span class="entry-time">${time}</span>
                        </div>
                        <div class="entry-route">${f.origin} → ${f.destination} (${f.aircraft_type})</div>
                    </div>
                `;
            });
        }
        
        if (departed.length > 0) {
            html += '<div class="history-section-header">🛫 Departed Flights</div>';
            departed.slice().reverse().forEach(f => {
                const time = f.completed_at ? new Date(f.completed_at).toLocaleTimeString() : '';
                html += `
                    <div class="history-entry departure">
                        <div class="entry-header">
                            <span class="entry-callsign">${f.callsign}</span>
                            <span class="entry-time">${time}</span>
                        </div>
                        <div class="entry-route">${f.origin} → ${f.destination} (${f.aircraft_type})</div>
                    </div>
                `;
            });
        }
        
        container.innerHTML = html;
    }
    
    getStatusClass(status) {
        const warningStatuses = ['on_final', 'taking_off', 'ready_for_takeoff'];
        const criticalStatuses = ['landing'];
        
        if (criticalStatuses.includes(status)) return 'critical';
        if (warningStatuses.includes(status)) return 'warning';
        return '';
    }
    
    formatStatus(status) {
        return status.replace(/_/g, ' ');
    }
    
    updateDetailPanel() {
        if (!this.selectedFlight) return;
        
        const flight = this.flights.find(f => f.callsign === this.selectedFlight.callsign);
        if (!flight) {
            this.deselectFlight();
            return;
        }
        
        this.selectedFlight = flight;
        document.getElementById('detailCallsign').textContent = flight.callsign;
        
        const content = document.getElementById('detailContent');
        const isArrival = flight.flight_type === 'arrival';
        
        const waypointOptions = Object.keys(this.waypoints)
            .map(w => `<option value="${w}" ${flight.target_waypoint === w ? 'selected' : ''}>${w}</option>`)
            .join('');
        
        const denialMessage = flight.clearance_denial_reason ? 
            `<div class="denial-message">⚠ ${flight.clearance_denial_reason}</div>` : '';
        
        content.innerHTML = `
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Altitude</div>
                    <div class="detail-value">${Math.round(flight.altitude).toLocaleString()}'</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Speed</div>
                    <div class="detail-value">${Math.round(flight.speed)} kt</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Heading</div>
                    <div class="detail-value">${Math.round(flight.heading)}°</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value">${this.formatStatus(flight.status)}</div>
                </div>
            </div>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Aircraft</div>
                    <div class="detail-value">${flight.aircraft_type}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Origin</div>
                    <div class="detail-value">${flight.origin || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Destination</div>
                    <div class="detail-value">${flight.destination || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Passed WPTs</div>
                    <div class="detail-value">${flight.passed_waypoints?.length || 0}</div>
                </div>
            </div>
            <div class="command-row">
                <div class="command-input">
                    <label>Altitude (ft)</label>
                    <input type="number" id="cmdAltitude" value="${flight.target_altitude || ''}" step="500">
                </div>
                <div class="command-input">
                    <label>Speed (kt)</label>
                    <input type="number" id="cmdSpeed" value="${flight.target_speed || ''}" step="10">
                </div>
                <div class="command-input">
                    <label>Heading (°)</label>
                    <input type="number" id="cmdHeading" placeholder="0-360" min="0" max="360" step="5">
                </div>
            </div>
            <div class="command-row">
                <div class="command-input" style="flex: 2;">
                    <label>Direct To Waypoint</label>
                    <select id="cmdWaypoint">
                        <option value="">-- Select Waypoint --</option>
                        ${waypointOptions}
                    </select>
                </div>
            </div>
            <div class="detail-actions">
                <button class="action-btn" onclick="atc.sendCommand()">Send Command</button>
                ${isArrival ? `
                    <button class="action-btn ${flight.cleared_to_land ? 'danger' : 'primary'}" onclick="atc.clearToLand()">
                        ${flight.cleared_to_land ? 'Cancel Landing' : 'Clear to Land'}
                    </button>
                ` : `
                    <button class="action-btn ${flight.cleared_for_takeoff ? 'danger' : 'primary'}" onclick="atc.clearForTakeoff()">
                        ${flight.cleared_for_takeoff ? 'Cancel Takeoff' : 'Clear for Takeoff'}
                    </button>
                `}
            </div>
            ${denialMessage}
        `;
    }
    
    async sendCommand() {
        if (!this.selectedFlight) return;
        
        const altitude = document.getElementById('cmdAltitude').value;
        const speed = document.getElementById('cmdSpeed').value;
        const heading = document.getElementById('cmdHeading').value;
        const waypoint = document.getElementById('cmdWaypoint').value;
        
        const command = {};
        if (altitude) command.altitude = parseInt(altitude);
        if (speed) command.speed = parseInt(speed);
        
        // Heading takes priority over waypoint
        if (heading) {
            command.heading = parseInt(heading);
        } else if (waypoint) {
            command.waypoint = waypoint;
        }
        
        if (Object.keys(command).length === 0) return;
        
        await fetch(`/api/flights/${this.selectedFlight.callsign}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(command)
        });
        
        // Clear heading input after sending
        document.getElementById('cmdHeading').value = '';
    }
    
    async clearToLand() {
        if (!this.selectedFlight) return;
        
        await fetch(`/api/flights/${this.selectedFlight.callsign}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clear_to_land: !this.selectedFlight.cleared_to_land })
        });
    }
    
    async clearForTakeoff() {
        if (!this.selectedFlight) return;
        
        await fetch(`/api/flights/${this.selectedFlight.callsign}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clear_for_takeoff: !this.selectedFlight.cleared_for_takeoff })
        });
    }
}

// Initialize
const atc = new ATCSimulator();
