# model_training.py
import random
import csv
import os
import json
from datetime import datetime

def generate_sample_data():
    """Generate synthetic air quality data for demonstration"""
    print("Generating sample air quality data...")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Generate 200 samples of synthetic data
    samples = []
    for i in range(200):
        sample = {
            'timestamp': datetime.now().isoformat(),
            'PM2.5': max(5, random.gauss(35, 20)),
            'PM10': max(10, random.gauss(50, 25)),
            'NO2': max(5, random.gauss(25, 12)),
            'CO': max(0.1, random.gauss(1.0, 0.5)),
            'SO2': max(1, random.gauss(12, 8)),
            'O3': max(10, random.gauss(40, 15)),
            'Temperature': random.uniform(15, 35),
            'Humidity': random.uniform(30, 80)
        }
        samples.append(sample)
    
    # Save to CSV
    with open('data/air_quality.csv', 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'Temperature', 'Humidity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)
    
    print(f"Generated {len(samples)} samples and saved to data/air_quality.csv")
    return samples

def predict_aqi(pm25):
    """Predict AQI category based on PM2.5 value (simple rules)"""
    if pm25 <= 12:
        return 'Good', '#00E400'
    elif pm25 <= 35.4:
        return 'Moderate', '#FFFF00'
    elif pm25 <= 55.4:
        return 'Unhealthy for Sensitive Groups', '#FF7E00'
    elif pm25 <= 150.4:
        return 'Unhealthy', '#FF0000'
    elif pm25 <= 250.4:
        return 'Very Unhealthy', '#8F3F97'
    else:
        return 'Hazardous', '#7E0023'

def create_simple_model():
    """Create and save a simple model configuration"""
    print("Creating simple rule-based AQI model...")
    
    model_info = {
        'model_type': 'rule_based_aqi_predictor',
        'version': '1.0',
        'created_at': datetime.now().isoformat(),
        'rules': {
            'Good': {'PM2.5_max': 12, 'color': '#00E400', 'description': 'Air quality is satisfactory'},
            'Moderate': {'PM2.5_max': 35.4, 'color': '#FFFF00', 'description': 'Acceptable quality'},
            'Unhealthy for Sensitive Groups': {'PM2.5_max': 55.4, 'color': '#FF7E00', 'description': 'Members of sensitive groups may experience health effects'},
            'Unhealthy': {'PM2.5_max': 150.4, 'color': '#FF0000', 'description': 'Everyone may experience health effects'},
            'Very Unhealthy': {'PM2.5_max': 250.4, 'color': '#8F3F97', 'description': 'Health alert: everyone may experience more serious health effects'},
            'Hazardous': {'PM2.5_max': 500.4, 'color': '#7E0023', 'description': 'Health warnings of emergency conditions'}
        }
    }
    
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Save model as JSON (since we don't have joblib)
    with open('models/aqi_model.json', 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print("Model saved to models/aqi_model.json")
    return model_info

def simulate_live_reading():
    """Simulate a live sensor reading"""
    return {
        'timestamp': datetime.now().isoformat(),
        'PM2.5': max(5, random.gauss(35, 20)),
        'PM10': max(10, random.gauss(50, 25)),
        'NO2': max(5, random.gauss(25, 12)),
        'CO': max(0.1, random.gauss(1.0, 0.5)),
        'SO2': max(1, random.gauss(12, 8)),
        'O3': max(10, random.gauss(40, 15)),
        'Temperature': random.uniform(15, 35),
        'Humidity': random.uniform(30, 80)
    }

if __name__ == "__main__":
    print("=== Eco+ AQI Model Training ===")
    
    # Generate sample data
    samples = generate_sample_data()
    
    # Create and save model
    model = create_simple_model()
    
    # Test the model with some examples
    test_values = [8, 25, 45, 80, 180, 300]
    print("\nTesting model predictions:")
    for pm25 in test_values:
        category, color = predict_aqi(pm25)
        print(f"  PM2.5: {pm25:3} µg/m³ -> {category:30} (Color: {color})")
    
    print(f"\nGenerated {len(samples)} data samples")
    print("=== Model Training Complete ===")