# Energy Theft Detection System

This project is an AI-powered Energy Theft Detection system that identifies suspicious electricity usage by correlating satellite imagery, geospatial data, and utility consumption records.

The system consists of a FastAPI backend and a React (Vite) frontend.

## Prerequisites
- Python 3.9+
- Node.js 18+
- Gemini API Key

## Setup Instructions

### 1. Backend Setup

The backend handles the data generation, API endpoints, and AI inference using the Gemini model.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables by creating a `.env` file in the `backend` directory (if not already present):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemma-4-26b-a4b-it
   ```

5. Generate the mock data and satellite imagery (required before starting the server):
   ```bash
   python mock_data_generator.py
   ```

6. Start the FastAPI server:
   ```bash
   python main.py
   ```
   The backend server will run on `http://localhost:8000`.

### 2. Frontend Setup

The frontend is a React application built with Vite that displays the interactive dashboard.

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install the Node.js dependencies:
   ```bash
   npm install
   ```

3. Ensure you have a `.env` file in the `frontend` directory with your API URL if needed (default is usually set to point to `localhost:8000`):
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

## Usage
1. Open the frontend URL (`http://localhost:5173`) in your browser.
2. The interactive map and dashboard will display the generated buildings.
3. Select a building to view its anomaly risk score.
4. Click "Analyze" to trigger the multimodal AI inference pipeline which will use the satellite image and utility metrics to generate a data-backed anomaly report.
