# app.py
from flask import Flask, render_template, jsonify, request, send_file
import json
import random
import csv
import os
from datetime import datetime, timedelta
import time
import threading
from io import StringIO

app = Flask(__name__)

# Global variables to store current readings and history
current_readings = {}  # Dictionary with city keys
reading_history = {}
cities = ['New York', 'London', 'Tokyo', 'Delhi', 'Beijing', 'Paris', 'Sydney', 'Dubai']
MAX_HISTORY = 50

# Alert thresholds
ALERT_THRESHOLDS = {
    'PM2_5': 35,
    'PM10': 50,
    'NO2': 40,
    'CO': 2.0,
    'SO2': 20
}

# Load the model
def load_model():
    try:
        with open('models/aqi_model.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# AQI prediction function
def predict_aqi(pm25):
    """Predict AQI category based on PM2.5 value"""
    if pm25 <= 12:
        return 'Good', '#00E400', 'Air quality is satisfactory'
    elif pm25 <= 35.4:
        return 'Moderate', '#FFFF00', 'Acceptable quality'
    elif pm25 <= 55.4:
        return 'Unhealthy for Sensitive Groups', '#FF7E00', 'Members of sensitive groups may experience health effects'
    elif pm25 <= 150.4:
        return 'Unhealthy', '#FF0000', 'Everyone may experience health effects'
    elif pm25 <= 250.4:
        return 'Very Unhealthy', '#8F3F97', 'Health alert: everyone may experience more serious health effects'
    else:
        return 'Hazardous', '#7E0023', 'Health warnings of emergency conditions'

# Check for alerts
def check_alerts(reading):
    """Check if any pollutant exceeds safe thresholds"""
    alerts = []
    for pollutant, threshold in ALERT_THRESHOLDS.items():
        value = reading.get(pollutant, 0)
        if value > threshold:
            alerts.append({
                'pollutant': pollutant,
                'value': value,
                'threshold': threshold,
                'severity': 'high' if value > threshold * 1.5 else 'medium'
            })
    return alerts

# Simulate live sensor reading for different cities
def simulate_sensor_reading(city):
    """Generate realistic sensor data for different cities with unique profiles"""
    # Different base levels for different cities (realistic profiles)
    city_profiles = {
        'New York': {'pm25_base': 25, 'variation': 10, 'temp_base': 22, 'humidity_base': 60},
        'London': {'pm25_base': 20, 'variation': 8, 'temp_base': 15, 'humidity_base': 75},
        'Tokyo': {'pm25_base': 30, 'variation': 12, 'temp_base': 18, 'humidity_base': 65},
        'Delhi': {'pm25_base': 80, 'variation': 30, 'temp_base': 28, 'humidity_base': 45},
        'Beijing': {'pm25_base': 60, 'variation': 25, 'temp_base': 20, 'humidity_base': 50},
        'Paris': {'pm25_base': 22, 'variation': 9, 'temp_base': 17, 'humidity_base': 70},
        'Sydney': {'pm25_base': 18, 'variation': 7, 'temp_base': 25, 'humidity_base': 55},
        'Dubai': {'pm25_base': 45, 'variation': 15, 'temp_base': 32, 'humidity_base': 40}
    }
    
    profile = city_profiles.get(city, {'pm25_base': 30, 'variation': 15, 'temp_base': 22, 'humidity_base': 60})
    
    # Add some realistic trends (time-based variations)
    hour = datetime.now().hour
    time_factor = 1.0
    
    # Higher pollution during rush hours
    if (7 <= hour <= 9) or (16 <= hour <= 18):
        time_factor = 1.3
    # Lower pollution at night
    elif 0 <= hour <= 5:
        time_factor = 0.7
    
    base_pm25 = profile['pm25_base'] * time_factor + random.uniform(-profile['variation'], profile['variation'])
    
    reading = {
        'city': city,
        'timestamp': datetime.now().isoformat(),
        'PM2_5': max(5, base_pm25),
        'PM10': max(10, base_pm25 * 1.5 + random.uniform(-10, 10)),
        'NO2': max(5, 20 + random.uniform(-8, 8) * time_factor),
        'CO': max(0.1, 0.8 + random.uniform(-0.3, 0.3) * time_factor),
        'SO2': max(1, 10 + random.uniform(-5, 5)),
        'O3': max(10, 35 + random.uniform(-15, 15)),
        'Temperature': round(profile['temp_base'] + random.uniform(-5, 5), 1),
        'Humidity': round(profile['humidity_base'] + random.uniform(-15, 15), 1)
    }
    
    # Predict AQI
    category, color, description = predict_aqi(reading['PM2_5'])
    reading['AQI_Category'] = category
    reading['AQI_Color'] = color
    reading['AQI_Description'] = description
    reading['PM2.5'] = reading['PM2_5']  # For compatibility
    
    # Check for alerts
    reading['alerts'] = check_alerts(reading)
    
    return reading

# Background thread to update readings for all cities
def update_readings():
    """Background thread to continuously update sensor readings for all cities"""
    global current_readings, reading_history
    
    while True:
        for city in cities:
            new_reading = simulate_sensor_reading(city)
            current_readings[city] = new_reading
            
            # Add to history
            if city not in reading_history:
                reading_history[city] = []
            reading_history[city].append(new_reading)
            if len(reading_history[city]) > MAX_HISTORY:
                reading_history[city].pop(0)
        
        # Update every 3 seconds
        time.sleep(3)

# Start background thread
reading_thread = threading.Thread(target=update_readings, daemon=True)
reading_thread.start()

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    model = load_model()
    return render_template('index.html', model=model)

@app.route('/api/current')
def get_current_readings():
    """API endpoint for current sensor readings - all cities"""
    return jsonify(current_readings)

@app.route('/api/current/<city>')
def get_city_reading(city):
    """API endpoint for specific city"""
    if city in current_readings:
        return jsonify(current_readings[city])
    return jsonify({'error': 'City not found'}), 404

@app.route('/api/history')
def get_history():
    """API endpoint for reading history of all cities"""
    return jsonify(reading_history)

@app.route('/api/history/<city>')
def get_city_history(city):
    """API endpoint for specific city history"""
    if city in reading_history:
        return jsonify(reading_history[city][-20:])  # Last 20 readings
    return jsonify({'error': 'City not found'}), 404

@app.route('/api/cities')
def get_cities():
    """API endpoint for available cities"""
    return jsonify(cities)

@app.route('/api/predict', methods=['POST'])
def predict_aqi_endpoint():
    """API endpoint for AQI prediction"""
    try:
        data = request.get_json()
        pm25 = float(data.get('PM2.5', 0))
        category, color, description = predict_aqi(pm25)
        
        return jsonify({
            'prediction': category,
            'color': color,
            'description': description,
            'PM2.5': pm25
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/model_info')
def get_model_info():
    """API endpoint for model information"""
    model = load_model()
    if model:
        return jsonify(model)
    else:
        return jsonify({'error': 'Model not found'}), 404

@app.route('/api/alerts')
def get_active_alerts():
    """API endpoint for active alerts across all cities"""
    alerts = []
    for city, reading in current_readings.items():
        if reading.get('alerts'):
            for alert in reading['alerts']:
                alerts.append({
                    'city': city,
                    **alert,
                    'timestamp': reading['timestamp']
                })
    return jsonify(alerts)

@app.route('/api/export/csv')
def export_csv():
    """API endpoint to export current data as CSV"""
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['City', 'Timestamp', 'PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'Temperature', 'Humidity', 'AQI_Category'])
        
        # Write data
        for city, reading in current_readings.items():
            writer.writerow([
                city,
                reading['timestamp'],
                reading['PM2_5'],
                reading['PM10'],
                reading['NO2'],
                reading['CO'],
                reading['SO2'],
                reading['O3'],
                reading['Temperature'],
                reading['Humidity'],
                reading['AQI_Category']
            ])
        
        output.seek(0)
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'eco_plus_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/city/<city>/csv')
def export_city_csv(city):
    """API endpoint to export city history as CSV"""
    try:
        if city not in reading_history:
            return jsonify({'error': 'City not found'}), 404
            
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'Temperature', 'Humidity', 'AQI_Category'])
        
        # Write data
        for reading in reading_history[city]:
            writer.writerow([
                reading['timestamp'],
                reading['PM2_5'],
                reading['PM10'],
                reading['NO2'],
                reading['CO'],
                reading['SO2'],
                reading['O3'],
                reading['Temperature'],
                reading['Humidity'],
                reading['AQI_Category']
            ])
        
        output.seek(0)
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'eco_plus_{city}_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_system_stats():
    """API endpoint for system statistics"""
    total_readings = sum(len(history) for history in reading_history.values())
    active_alerts = sum(len(reading.get('alerts', [])) for reading in current_readings.values())
    
    # Calculate average AQI across cities
    aqi_values = [reading['PM2_5'] for reading in current_readings.values()]
    avg_aqi = sum(aqi_values) / len(aqi_values) if aqi_values else 0
    
    # Find best and worst cities
    if current_readings:
        best_city = min(current_readings.items(), key=lambda x: x[1]['PM2_5'])[0]
        worst_city = max(current_readings.items(), key=lambda x: x[1]['PM2_5'])[0]
    else:
        best_city = worst_city = "N/A"
    
    stats = {
        'total_cities': len(cities),
        'total_readings': total_readings,
        'active_alerts': active_alerts,
        'average_aqi': round(avg_aqi, 1),
        'best_city': best_city,
        'worst_city': worst_city,
        'system_uptime': str(datetime.now() - datetime.fromtimestamp(time.time() - (time.time() % 3)))
    }
    
    return jsonify(stats)

@app.route('/api/health')
def health_check():
    """API endpoint for health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cities_monitored': len(current_readings),
        'system': 'Eco+ Air Quality Monitoring System',
        'version': '2.0'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("=== Starting Eco+ Global Air Quality Monitoring System ===")
    print("🌍 Monitoring Cities:", ", ".join(cities))
    print("📊 Dashboard: http://127.0.0.1:5000")
    print("🔧 API endpoints:")
    print("   - GET  /api/current           (All cities current data)")
    print("   - GET  /api/current/<city>    (Specific city data)")
    print("   - GET  /api/history           (All cities history)")
    print("   - GET  /api/cities            (Available cities)")
    print("   - GET  /api/alerts            (Active alerts)")
    print("   - GET  /api/stats             (System statistics)")
    print("   - GET  /api/export/csv        (Export all data)")
    print("   - POST /api/predict           (AQI prediction)")
    print("   - GET  /api/health            (System health check)")
    print("==========================================================")
    
    # Generate initial data
    print("🔄 Generating initial sensor data...")
    for city in cities:
        current_readings[city] = simulate_sensor_reading(city)
        reading_history[city] = [current_readings[city]]
    
    print("✅ System initialized successfully!")
    app.run(debug=True, host='127.0.0.1', port=5000)