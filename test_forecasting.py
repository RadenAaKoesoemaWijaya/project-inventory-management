#!/usr/bin/env python3
"""
Test script untuk validasi sistem forecasting ML
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pages.forecasting import (
    calculate_ml_forecast, 
    calculate_seed_needs, 
    calculate_fertilizer_needs,
    prepare_ml_training_data,
    train_ml_model,
    get_soil_type_score,
    get_previous_crop_score,
    get_season_score,
    encode_crop_type
)

def test_basic_functions():
    """Test fungsi-fungsi dasar forecasting"""
    print("🧪 Testing fungsi dasar forecasting...")
    
    # Test seed calculation
    seed_result = calculate_seed_needs("Padi", 2.0, 5.0)
    print(f"✅ Seed calculation: {seed_result['amount']:.1f} kg, Rp {seed_result['cost']:,.0f}")
    
    # Test fertilizer calculation
    fertilizer_result = calculate_fertilizer_needs("Padi", 2.0, "Tanah Sawah", "Jagung")
    print(f"✅ Fertilizer calculation: {fertilizer_result['amount']:.1f} kg, Rp {fertilizer_result['cost']:,.0f}")
    
    # Test helper functions
    print(f"✅ Soil score: {get_soil_type_score('Tanah Sawah')}")
    print(f"✅ Previous crop score: {get_previous_crop_score('Jagung', 'Padi')}")
    print(f"✅ Season score: {get_season_score('Musim Hujan')}")
    print(f"✅ Crop encoding: {encode_crop_type('Padi')}")

def test_ml_forecasting():
    """Test ML forecasting dengan data sample"""
    print("\n🤖 Testing ML forecasting...")
    
    # Create sample historical data
    sample_historical_data = [
        {
            'land_area': 1.0,
            'target_yield': 5.0,
            'actual_yield': 4.8,
            'seed_used': 20,
            'fertilizer_used': 375,
            'weather_factor': 1.0,
            'soil_fertility': 0.9
        },
        {
            'land_area': 2.0,
            'target_yield': 6.0,
            'actual_yield': 5.5,
            'seed_used': 40,
            'fertilizer_used': 750,
            'weather_factor': 0.9,
            'soil_fertility': 0.8
        },
        {
            'land_area': 1.5,
            'target_yield': 5.5,
            'actual_yield': 5.2,
            'seed_used': 30,
            'fertilizer_used': 562,
            'weather_factor': 1.1,
            'soil_fertility': 0.85
        }
    ]
    
    try:
        # Test ML forecast
        ml_result = calculate_ml_forecast(
            crop_type="Padi",
            land_area=1.5,
            target_yield=5.5,
            soil_type="Tanah Sawah",
            previous_crop="Jagung",
            planting_season="Musim Hujan",
            historical_data=sample_historical_data
        )
        
        print(f"✅ ML Seed prediction: {ml_result['seed_needed']['amount']:.1f} kg")
        print(f"✅ ML Fertilizer prediction: {ml_result['fertilizer_needed']['amount']:.1f} kg")
        print(f"✅ ML Accuracy: {ml_result['accuracy']:.1f}%")
        print(f"✅ ML Confidence: {ml_result['confidence']:.2f}")
        print(f"✅ Total cost: Rp {ml_result['seed_needed']['cost'] + ml_result['fertilizer_needed']['cost']:,.0f}")
        
    except Exception as e:
        print(f"❌ ML forecasting error: {e}")

def test_ml_training():
    """Test ML model training"""
    print("\n📊 Testing ML model training...")
    
    sample_data = [
        {
            'land_area': 1.0,
            'target_yield': 5.0,
            'soil_type_score': 0.9,
            'previous_crop_score': 0.8,
            'season_score': 0.9,
            'historical_yield': 4.8,
            'weather_factor': 1.0,
            'soil_fertility': 0.9,
            'crop_type_encoded': 1.0,
            'seed_needed': 20,
            'fertilizer_needed': 375
        }
    ] * 5  # Duplicate to have enough data
    
    try:
        # Test training data preparation
        training_data = prepare_ml_training_data(sample_data, "Padi", "Tanah Sawah", "Jagung", "Musim Hujan")
        print(f"✅ Training data prepared: {len(training_data)} samples")
        
        # Test model training
        model, features, scaler = train_ml_model(training_data, 'seed_needed')
        if model:
            print(f"✅ Model trained successfully")
            print(f"✅ Features: {features}")
        else:
            print("⚠️ Model training failed or insufficient data")
            
    except Exception as e:
        print(f"❌ ML training error: {e}")

if __name__ == "__main__":
    print("🚀 Starting ML Forecasting System Tests")
    print("=" * 50)
    
    test_basic_functions()
    test_ml_forecasting()
    test_ml_training()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")