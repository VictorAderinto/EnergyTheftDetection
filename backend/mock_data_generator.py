import pandas as pd
import numpy as np
import random
import os
import requests
import json
import torch
import kagglehub
from transformers import AutoProcessor, AutoModelForCausalLM
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import time

# Load env
load_dotenv()

# Configuration
NUM_BUILDINGS = 250
LAGOS_LAT = 6.5244
LAGOS_LNG = 3.3792
DATA_DIR = 'data'
IMAGES_DIR = os.path.join(DATA_DIR, 'images')

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

def fetch_satellite_image(lat, lng, building_id, maps_api_key):
    """Fetches a satellite image from Google Maps Static API and saves it locally."""
    image_path = os.path.join(IMAGES_DIR, f"{building_id}.jpg")
    
    # If we already have the image, skip downloading
    if os.path.exists(image_path):
        return image_path
        
    if not maps_api_key:
        print(f"Warning: No MAPS_API_KEY. Skipping image download for {building_id}.")
        return None
        
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=21&size=400x400&maptype=satellite&key={maps_api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return image_path
    else:
        print(f"Failed to fetch image for {building_id}: {response.status_code} - {response.text}")
        return None

def validate_image_with_gemini(processor, model, image_path):
    """Uses Gemma-4 Vision to act as a bouncer, validating if the image is a clear single building."""
    if not processor or not model or not image_path:
        return True
    try:
        img = Image.open(image_path).convert("RGB")
        prompt = "Is this a clear, top-down satellite view of a single primary building? Answer only YES or NO."
        messages = [
            {"role": "user", "content": [
                {"type": "image"},
                {"type": "text", "text": prompt}
            ]}
        ]
        
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        
        inputs = processor(text=text, images=img, return_tensors="pt").to(model.device)
        input_len = inputs["input_ids"].shape[-1]
        
        outputs = model.generate(**inputs, max_new_tokens=10)
        response_text = processor.decode(outputs[0][input_len:], skip_special_tokens=True).strip().upper()
        
        return "YES" in response_text
    except Exception as e:
        print(f"Error validating image with Gemma-4: {e}")
        return True

def analyze_image_with_gemini(processor, model, image_path):
    """Uses Local Gemma-4 Vision to estimate building size, tag, and neighborhood type."""
    if not processor or not model or not image_path:
        return {
            "building_size_category": random.choice(['Small', 'Medium', 'Large', 'Huge']),
            "property_tag": random.choice(['Residential', 'Commercial', 'Industrial']),
            "neighborhood_type": random.choice(['Slum', 'Dense Urban', 'Suburb', 'Commercial District'])
        }
    
    try:
        img = Image.open(image_path).convert("RGB")
        prompt = """Analyze this satellite image of a building in Lagos, Nigeria.
Return ONLY a JSON object with the following three keys exactly, and nothing else:
- "building_size_category": one of ["Small", "Medium", "Large", "Huge"]
- "property_tag": one of ["Residential", "Commercial", "Industrial"]
- "neighborhood_type": one of ["Slum", "Dense Urban", "Suburb", "Commercial District"]
"""
        messages = [
            {"role": "user", "content": [
                {"type": "image"},
                {"type": "text", "text": prompt}
            ]}
        ]
        
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        
        inputs = processor(text=text, images=img, return_tensors="pt").to(model.device)
        input_len = inputs["input_ids"].shape[-1]
        
        outputs = model.generate(**inputs, max_new_tokens=150)
        response_text = processor.decode(outputs[0][input_len:], skip_special_tokens=True)
        
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text)
        return data
        
    except Exception as e:
        print(f"Error analyzing image with Gemma-4: {e}")
        return {
            "building_size_category": "Medium",
            "property_tag": "Residential",
            "neighborhood_type": "Dense Urban"
        }

def generate_energy_and_blackout_data(vision_data):
    """Generates synthetic energy usage and blackout frequency based on the vision data."""
    size = vision_data.get('building_size_category', 'Medium')
    tag = vision_data.get('property_tag', 'Residential')
    neighborhood = vision_data.get('neighborhood_type', 'Dense Urban')
    
    # Energy Usage Base
    size_multiplier = {'Small': 50, 'Medium': 150, 'Large': 400, 'Huge': 1000}
    tag_multiplier = {'Residential': 1.0, 'Commercial': 2.5, 'Industrial': 5.0}
    
    base_usage = size_multiplier.get(size, 150) * tag_multiplier.get(tag, 1.0)
    monthly_usage_kwh = round(base_usage * random.uniform(0.8, 1.2), 2)
    
    # Load Type
    if tag == 'Residential':
        load_type = random.choices(['Morning/Evening Peak', 'Constant', 'Erratic'], weights=[0.7, 0.2, 0.1])[0]
    elif tag == 'Commercial':
        load_type = random.choices(['Daytime Peak', 'Constant'], weights=[0.8, 0.2])[0]
    else:
        load_type = 'Constant Heavy'
        
    # Blackout Data based on neighborhood
    if neighborhood == 'Slum':
        blackout_freq = random.randint(15, 30)  # times per month
        blackout_dur = random.randint(4, 12)    # hours average
    elif neighborhood == 'Dense Urban':
        blackout_freq = random.randint(5, 15)
        blackout_dur = random.randint(2, 6)
    elif neighborhood == 'Commercial District':
        blackout_freq = random.randint(1, 5)
        blackout_dur = random.randint(1, 3)
    else: # Suburb
        blackout_freq = random.randint(2, 10)
        blackout_dur = random.randint(2, 5)
        
    return {
        "monthly_usage_kwh": monthly_usage_kwh,
        "load_type": load_type,
        "blackout_frequency": blackout_freq,
        "average_blackout_duration_hrs": blackout_dur
    }

def fetch_real_building_coordinates(limit=250):
    """Fetches real building coordinates in Lagos using Overpass API."""
    print("Fetching real building coordinates from Overpass API...")
    overpass_url = "http://overpass-api.de/api/interpreter"
    # We fetch 3x the limit because the Gemma Bouncer might reject many images
    fetch_amount = limit * 3 
    
    # Using a bounding box around central Lagos is much faster and less prone to timeout/syntax errors
    # Box: min_lat, min_lng, max_lat, max_lng (Lagos Island/Mainland area)
    overpass_query = f"""
    [out:json][timeout:25];
    way["building"](6.4, 3.3, 6.6, 3.5);
    out {fetch_amount} center;
    """
    try:
        headers = {'User-Agent': 'EnergyTheftSystem/1.0'}
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
        response.raise_for_status()
        data = response.json()
        coords = []
        for element in data.get('elements', []):
            if 'center' in element:
                coords.append((element['center']['lat'], element['center']['lon']))
        
        if len(coords) < fetch_amount:
            print(f"Warning: Only found {len(coords)} buildings. Padding with random coords.")
            while len(coords) < fetch_amount:
                coords.append((LAGOS_LAT + random.uniform(-0.05, 0.05), LAGOS_LNG + random.uniform(-0.05, 0.05)))
                
        # Shuffle coordinates to ensure we get a random spread within the box
        random.shuffle(coords)
        return coords
    except Exception as e:
        print(f"Failed to fetch from Overpass API: {e}. Falling back to random coords.")
        return [(LAGOS_LAT + random.uniform(-0.05, 0.05), LAGOS_LNG + random.uniform(-0.05, 0.05)) for _ in range(fetch_amount)]

def generate_data():
    ensure_dirs()
    maps_api_key = os.getenv("MAPS_API_KEY")
    
    print("Loading Local Gemma-4-E2B Model...")
    try:
        # We use the E2B model as requested
        MODEL_PATH = kagglehub.model_download("google/gemma-4/transformers/gemma-4-e2b")
        processor = AutoProcessor.from_pretrained(MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            dtype=torch.bfloat16,
            device_map="auto"
        )
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Failed to load model locally: {e}")
        processor, model = None, None

    buildings = []
    
    # 5% theft ratio
    num_theft = int(NUM_BUILDINGS * 0.05)
    theft_indices = set(random.sample(range(NUM_BUILDINGS), num_theft))

    print(f"Generating data for {NUM_BUILDINGS} buildings...")
    building_coords = fetch_real_building_coordinates(NUM_BUILDINGS)
    
    valid_buildings_count = 0
    coord_index = 0
    
    while valid_buildings_count < NUM_BUILDINGS and coord_index < len(building_coords):
        building_id = f'B{valid_buildings_count:04d}'
        lat, lng = building_coords[coord_index]
        coord_index += 1
        
        # 1. Fetch Image
        image_path = fetch_satellite_image(lat, lng, building_id, maps_api_key)
        
        # Validate with Gemma Bouncer
        if not validate_image_with_gemini(processor, model, image_path):
            print(f"Rejected {building_id} (not a clear single building). Fetching new coordinate...")
            if os.path.exists(image_path):
                os.remove(image_path)
            continue
            
        # 2. Analyze with Local Gemma Vision
        vision_data = analyze_image_with_gemini(processor, model, image_path)
        
        # 3. Generate Energy and Blackout Data
        energy_data = generate_energy_and_blackout_data(vision_data)
        
        # 4. Combine and simulate theft
        is_theft = valid_buildings_count in theft_indices
        
        monthly_usage = energy_data['monthly_usage_kwh']
        if is_theft:
            # We manually tank their usage to simulate theft
            monthly_usage = round(monthly_usage * random.uniform(0.1, 0.2), 2)
        
        building_record = {
            'building_id': building_id,
            'lat': lat,
            'lng': lng,
            'building_size_category': vision_data.get('building_size_category'),
            'property_tag': vision_data.get('property_tag'),
            'neighborhood_type': vision_data.get('neighborhood_type'),
            'monthly_usage_kwh': monthly_usage,
            'load_type': energy_data['load_type'],
            'blackout_frequency': energy_data['blackout_frequency'],
            'average_blackout_duration_hrs': energy_data['average_blackout_duration_hrs'],
            'is_theft_simulated': is_theft
        }
        
        buildings.append(building_record)
        valid_buildings_count += 1
        
        if valid_buildings_count % 5 == 0:
            print(f"Processed {valid_buildings_count}/{NUM_BUILDINGS}")
            
    df = pd.DataFrame(buildings)
    
    # --- Statistical Outlier Detection ---
    print("Calculating statistical outliers...")
    
    # Calculate group statistics based on building size and property tag
    group_stats = df.groupby(['building_size_category', 'property_tag'])['monthly_usage_kwh'].agg(['mean', 'std']).reset_index()
    
    # Merge stats back into the main dataframe
    df = df.merge(group_stats, on=['building_size_category', 'property_tag'], how='left')
    
    # Handle cases where std is NaN (e.g., only one building in the group) or 0
    df['std'] = df['std'].fillna(1.0)
    df['std'] = df['std'].replace(0, 1.0)
    
    # Calculate Z-score
    df['z_score'] = (df['monthly_usage_kwh'] - df['mean']) / df['std']
    
    # Define risk score and anomaly reason based on Z-score
    def calculate_risk(row):
        score = 10.0 # Base score
        reasons = []
        
        if row['z_score'] < -2.0:
            score += 80.0
            reasons.append(f"Suspiciously low usage. More than 2 std devs below average ({round(row['mean'], 1)} kWh) for {row['building_size_category']} {row['property_tag']} buildings.")
        elif row['z_score'] < -1.0:
            score += 40.0
            reasons.append(f"Noticeably below average ({round(row['mean'], 1)} kWh) for {row['building_size_category']} {row['property_tag']} buildings.")
            
        if row['load_type'] == 'Erratic' and row['property_tag'] != 'Industrial':
            score += 20.0
            reasons.append("Erratic load type is unusual for this property tag.")
            
        if row['blackout_frequency'] > 15:
            score += 10.0
            
        score = min(100.0, score + random.uniform(-5, 5))
        reason = " ".join(reasons) if reasons else "Usage is within normal expected range compared to peers."
        return pd.Series([round(score, 1), reason])

    df[['risk_score', 'anomaly_reason']] = df.apply(calculate_risk, axis=1)
    
    # Rename mean to expected_monthly_usage_kwh
    df = df.rename(columns={'mean': 'expected_monthly_usage_kwh'})
    
    # Drop the temporary stat columns
    df = df.drop(columns=['std', 'z_score'])
    
    df.to_csv(os.path.join(DATA_DIR, 'buildings.csv'), index=False)
    print(f"Saved {NUM_BUILDINGS} records to {os.path.join(DATA_DIR, 'buildings.csv')}")

if __name__ == "__main__":
    generate_data()

