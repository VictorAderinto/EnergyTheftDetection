import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from dotenv import load_dotenv
from PIL import Image
from google import genai

load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    process_data()
    init_gemma()
    yield

app = FastAPI(lifespan=lifespan)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
buildings_df = None
client = None
gemma_model_name = "gemma-4-26b-a4b-it"

def init_gemma():
    global client, gemma_model_name
    try:
        print("Initializing Gemini API Client...")
        client = genai.Client()
        gemma_model_name = os.environ.get("GEMINI_MODEL", "gemma-4-26b-a4b-it")
        print(f"Client loaded successfully! Model: {gemma_model_name}")
    except Exception as e:
        print(f"Failed to initialize Gemini Client: {e}")
        client = None

def process_data():
    global buildings_df
    try:
        df = pd.read_csv("data/buildings.csv")
    except FileNotFoundError:
        print("Data file not found. Please run mock_data_generator.py first.")
        return

    # In the updated pipeline, risk_score and anomaly_reason are already pre-calculated
    # by the data generator. We just load it.
    buildings_df = df

@app.get("/api/buildings")
def get_buildings():
    if buildings_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded. Run the generator script.")
    
    # Return as list of dicts
    return buildings_df.to_dict(orient="records")

@app.post("/api/analyze-building/{building_id}")
def analyze_building(building_id: str):
    if buildings_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
        
    building = buildings_df[buildings_df['building_id'] == building_id].to_dict(orient="records")
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
        
    building = building[0]
    
    if client is None:
         # Fallback if model not loaded
         return {"explanation": "Gemini client not loaded. Base reason: " + str(building.get('anomaly_reason', ''))}
    
    image_path = f"data/images/{building_id}.jpg"
    image = None
    if os.path.exists(image_path):
        image = Image.open(image_path).convert("RGB")

    prompt = f"""You are an AI Energy Theft Detection forensics analyst.
I have attached a satellite image of a building.
Step 1: Look at the image to verify its physical attributes. You must classify its size as one of [Small, Medium, Large, Huge] and its tag as one of [Residential, Commercial, Industrial].
Step 2: Acknowledge the utility baseline data reported below.
Step 3: Compare the reported consumption data with average expected data for addresses with a similar size and tag in this region.
Step 4: Factor in the blackout frequency for that region. NOTE: High blackout frequency is often a strong indicator of localized energy theft, as unmetered stolen consumption overloads neighborhood transformers.
Step 5: Synthesize a refined, numbers-backed analysis on the probability of distribution theft (bypassing the meter).

Utility Baseline Data:
- ID: {building['building_id']}
- Reported Size Category: {building['building_size_category']}
- Reported Property Tag: {building['property_tag']}
- Neighborhood Type: {building['neighborhood_type']}
- Reported Monthly Usage: {building['monthly_usage_kwh']} kWh
- Load Type: {building['load_type']}
- Regional Blackout Frequency: {building['blackout_frequency']} times/month
- Regional Avg Blackout Duration: {building['average_blackout_duration_hrs']} hrs
- Pre-calculated Risk Score: {building['risk_score']}%
- Base Heuristic Reason: {building['anomaly_reason']}

Provide a single paragraph explanation using this 5-step logic. You MUST explicitly quote the provided numeric data points (e.g., the exact kWh consumption, Risk Score percentage, and blackout frequency) in your reasoning so the conclusion is strictly data-backed and not just a generic summary.
"""
    
    try:
        contents = []
        if image:
            contents.append(image)
        contents.append(prompt)
        
        response = client.models.generate_content(
            model=gemma_model_name,
            contents=contents,
        )
        
        return {"explanation": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemma inference error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
