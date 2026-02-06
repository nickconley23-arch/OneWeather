/**
 * OneWeather Dashboard - Apple/Tesla Style
 * API Integration for Ardmore, PA
 */

const ARDMORE_COORDS = {
    lat: 40.0048,
    lon: -75.2923
};

const API_BASE_URL = 'http://localhost:8000'; // Local FastAPI backend

// Weather icon mapping
const WEATHER_ICONS = {
    'clear': 'fa-sun',
    'clouds': 'fa-cloud',
    'rain': 'fa-cloud-rain',
    'snow': 'fa-snowflake',
    'thunderstorm': 'fa-bolt',
    'drizzle': 'fa-cloud-rain',
    'mist': 'fa-smog',
    'default': 'fa-cloud'
};

class OneWeatherDashboard {
    constructor() {
        this.forecastData = null;
        this.sources = [];
        this.init();
    }
    
    init() {
        console.log('OneWeather Dashboard initialized for Ardmore, PA');
        this.loadForecast();
        this.setupEventListeners();
    }
    
    async loadForecast() {
        try {
            this.showLoading(true);
            
            // REAL API call - using simple forecast endpoint
            const response = await fetch(`${API_BASE_URL}/api/v1/forecast/${ARDMORE_COORDS.lat}/${ARDMORE_COORDS.lon}?hours=24`);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            this.forecastData = await response.json();
            
            this.renderDashboard();
            this.showLoading(false);
            
        } catch (error) {
            console.error('Error loading forecast:', error);
            this.showError('Backend API not running. Start with: cd /home/ubuntu/OneWeather/api && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000');
            this.showLoading(false);
            
            // Show connection instructions
            this.showConnectionInstructions();
        }
    }
    
    showConnectionInstructions() {
        const container = document.querySelector('.hourly-scroll');
        if (!container) return;
        
        container.innerHTML = '';
        
        const instructionCard = document.createElement('div');
        instructionCard.className = 'flex-shrink-0 w-full glass-card rounded-2xl p-6 text-center';
        instructionCard.innerHTML = `
            <i class="fas fa-plug text-4xl text-blue-400 mb-4"></i>
            <h3 class="text-xl font-light mb-2">Backend Not Connected</h3>
            <p class="text-gray-400 mb-4">The weather API backend needs to be started.</p>
            <div class="bg-gray-800 rounded-lg p-4 text-left font-mono text-sm">
                <code class="text-green-400">cd /home/ubuntu/OneWeather</code><br>
                <code class="text-green-400">docker-compose up -d</code><br>
                <code class="text-gray-500"># Then refresh this page</code>
            </div>
        `;
        
        container.appendChild(instructionCard);
        
        // Update other UI elements to show connection needed
        document.getElementById('currentTemp').textContent = '--°';
        document.getElementById('currentCondition').textContent = 'API Offline';
        document.getElementById('feelsLike').textContent = 'Start backend';
        document.getElementById('weatherIcon').className = 'fas fa-plug text-6xl text-gray-500';
    }
    
    renderDashboard() {
        if (!this.forecastData || !this.forecastData.points.length) return;
        
        const current = this.forecastData.points[0];
        const hourly = this.forecastData.points.slice(0, 12); // Next 12 hours
        
        // Update current conditions
        this.updateCurrentConditions(current);
        
        // Update hourly forecast
        this.updateHourlyForecast(hourly);
        
        // Update metrics
        this.updateMetrics(current);
        
        // Update sources
        this.updateSources();
        
        // Update timestamp
        this.updateTimestamp();
    }
    
    updateCurrentConditions(point) {
        // Temperature
        document.getElementById('currentTemp').textContent = `${Math.round(point.temperature_c)}°`;
        
        // Condition based on precipitation and clouds
        let condition = 'Clear';
        let icon = 'clear';
        
        if (point.precipitation_mm > 0) {
            condition = point.precipitation_mm < 2.5 ? 'Light Rain' : 'Rain';
            icon = 'rain';
        } else if (point.cloud_cover_percent > 70) {
            condition = 'Cloudy';
            icon = 'clouds';
        } else if (point.cloud_cover_percent > 30) {
            condition = 'Partly Cloudy';
            icon = 'clouds';
        }
        
        document.getElementById('currentCondition').textContent = condition;
        document.getElementById('weatherIcon').className = `fas ${WEATHER_ICONS[icon] || WEATHER_ICONS.default} text-6xl ${this.getIconColor(icon)}`;
        
        // Feels like (simplified)
        const feelsLike = point.temperature_c - (point.wind_speed_mps * 0.1); // Wind chill approximation
        document.getElementById('feelsLike').textContent = `Feels like ${Math.round(feelsLike)}°`;
    }
    
    updateHourlyForecast(hourlyPoints) {
        const container = document.querySelector('.hourly-scroll');
        container.innerHTML = '';
        
        hourlyPoints.forEach((point, index) => {
            const time = new Date(point.timestamp);
            const hour = time.getHours();
            const ampm = hour >= 12 ? 'PM' : 'AM';
            const displayHour = hour % 12 || 12;
            
            // Determine icon based on conditions
            let icon = 'fa-cloud';
            if (point.precipitation_mm > 0) icon = 'fa-cloud-rain';
            else if (point.cloud_cover_percent < 30) icon = 'fa-sun';
            else if (point.cloud_cover_percent < 70) icon = 'fa-cloud-sun';
            
            const card = document.createElement('div');
            card.className = 'flex-shrink-0 w-20 glass-card rounded-2xl p-4 text-center transition-smooth hover:scale-105';
            card.innerHTML = `
                <div class="text-gray-400 text-sm mb-2">${displayHour}${ampm}</div>
                <i class="fas ${icon} text-2xl ${this.getIconColor(icon)} mb-2"></i>
                <div class="text-xl font-light">${Math.round(point.temperature_c)}°</div>
                <div class="text-xs text-gray-400 mt-1">${point.precipitation_mm > 0 ? '💧' : ''}</div>
            `;
            
            container.appendChild(card);
        });
    }
    
    updateMetrics(point) {
        // Precipitation
        const precipProb = point.precipitation_probability ? Math.round(point.precipitation_probability * 100) : 0;
        document.getElementById('precipitation').textContent = `${precipProb}%`;
        document.getElementById('precipitationAmount').textContent = point.precipitation_mm ? `${point.precipitation_mm.toFixed(1)} mm` : '-- mm';
        
        // Wind
        document.getElementById('windSpeed').textContent = `${point.wind_speed_mps.toFixed(1)} m/s`;
        document.getElementById('windDirection').textContent = this.getWindDirection(point.wind_direction_deg);
        
        // Humidity
        document.getElementById('humidity').textContent = `${Math.round(point.humidity_percent)}%`;
        
        // Pressure
        document.getElementById('pressure').textContent = `${Math.round(point.pressure_hpa)}`;
        
        // Accuracy metrics (mock for now)
        document.getElementById('accuracyScore').textContent = '92%';
        document.getElementById('accuracyBar').style.width = '92%';
        document.getElementById('improvement').textContent = '15%';
    }
    
    updateSources() {
        const sources = this.forecastData.sources_used || [];
        document.getElementById('sourceCount').textContent = sources.length;
        
        const sourceList = document.getElementById('sourceList');
        sourceList.innerHTML = '';
        
        const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-yellow-500', 'bg-pink-500'];
        
        sources.forEach((source, index) => {
            const displayName = this.formatSourceName(source);
            const weight = Math.round(100 / sources.length); // Equal weighting for now
            
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between';
            item.innerHTML = `
                <div class="flex items-center">
                    <div class="w-3 h-3 rounded-full ${colors[index % colors.length]} mr-3"></div>
                    <span class="text-sm">${displayName}</span>
                </div>
                <span class="text-gray-400 text-sm">${weight}%</span>
            `;
            
            sourceList.appendChild(item);
        });
    }
    
    updateTimestamp() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        document.getElementById('updateTime').textContent = `Updated ${timeStr}`;
    }
    
    formatSourceName(source) {
        const names = {
            'openmeteo_gfs': 'GFS Model',
            'openmeteo_ecmwf': 'ECMWF',
            'openmeteo_gem': 'Canadian',
            'noaa_weathergov': 'NOAA',
            'meteomatics': 'Meteomatics',
            'tomorrowio': 'Tomorrow.io',
            'visualcrossing': 'Visual Crossing'
        };
        
        return names[source] || source.replace(/_/g, ' ').toUpperCase();
    }
    
    getWindDirection(degrees) {
        if (degrees >= 337.5 || degrees < 22.5) return 'N';
        if (degrees >= 22.5 && degrees < 67.5) return 'NE';
        if (degrees >= 67.5 && degrees < 112.5) return 'E';
        if (degrees >= 112.5 && degrees < 157.5) return 'SE';
        if (degrees >= 157.5 && degrees < 202.5) return 'S';
        if (degrees >= 202.5 && degrees < 247.5) return 'SW';
        if (degrees >= 247.5 && degrees < 292.5) return 'W';
        return 'NW';
    }
    
    getIconColor(iconType) {
        const colors = {
            'fa-sun': 'text-yellow-300',
            'fa-cloud-sun': 'text-yellow-200',
            'fa-cloud': 'text-gray-300',
            'fa-cloud-rain': 'text-blue-300',
            'fa-snowflake': 'text-cyan-300',
            'fa-bolt': 'text-yellow-400',
            'fa-smog': 'text-gray-400'
        };
        
        return colors[iconType] || 'text-gray-300';
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.style.display = 'flex';
            setTimeout(() => {
                overlay.style.opacity = '1';
            }, 10);
        } else {
            overlay.style.opacity = '0';
            setTimeout(() => {
                overlay.style.display = 'none';
            }, 300);
        }
    }
    
    showError(message) {
        // Create error toast (Apple style)
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 glass-card rounded-2xl p-4 max-w-sm z-50 transform transition-transform translate-x-full';
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-triangle text-red-400 mr-3 text-xl"></i>
                <div>
                    <div class="font-medium">Forecast Error</div>
                    <div class="text-sm text-gray-400">${message}</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after 5 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 5000);
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.loadForecast();
        });
        
        // Auto-refresh every 5 minutes
        setInterval(() => {
            this.loadForecast();
        }, 5 * 60 * 1000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.weatherDashboard = new OneWeatherDashboard();
});