# AI Energy Theft Detection System
## Identifying non-technical losses with multimodal AI

### Motivation
Distribution theft and meter bypassing cause massive non-technical losses for utility companies globally. Discovering these anomalies traditionally requires expensive manual audits and unpredictable "truck rolls." The goal of this project is to create an automated, AI-driven pipeline that correlates real-world satellite imagery with utility consumption records. By comparing the physical footprint of a building with its reported energy usage, we can identify mathematically suspicious discrepancies and generate actionable forensic reports for utility inspectors.

To achieve this, I decided to deploy the system as a self-contained Kaggle Notebook, allowing us to leverage cloud GPU resources for local vision model inference while avoiding the memory constraints of local hardware.

### Developing the AI Pipeline
To detect anomalies, the system uses a multimodal approach combining geospatial data, computer vision, and statistical analysis.

#### Simulating the Utility Database
In a real-world scenario, consumption data is exported directly from an Advanced Metering Infrastructure (AMI). For this project, I used the Overpass API to fetch real building coordinates in Lagos, Nigeria. I then generated synthetic usage data (kWh, load type, regional blackout frequencies) and purposefully simulated "theft" for a small percentage of the buildings to test the system.

#### Gemma-4 Vision Implementation
To understand the physical characteristics of each building, I used the Google Maps Static API to fetch satellite imagery for each coordinate. I loaded the `gemma-4-e2b` local vision model into Kaggle's GPU memory using the `kagglehub` library. The model analyzes each image to classify the building's size (Small, Medium, Large, Huge), property tag (Residential, Commercial, Industrial), and neighborhood type.

#### Statistical Peer Analysis
Once the physical traits are verified by the vision model, the buildings are grouped into peer sets. The system calculates the mean consumption for each group and assigns a Z-score to every building. If a building's usage is drastically below its peers (e.g., a "Large Industrial" building reporting the usage of a "Small Residential" one), it is flagged with a high risk score.

#### Interactive Demonstration Dashboard
To visualize the generated data and risk scores, I developed a full-stack local demonstration environment. 
- **Backend (FastAPI):** Serves the pre-calculated dataset and handles API routes that trigger the final AI forensic reports on-demand using the Google Gemini API.
- **Frontend (React & Leaflet):** Provides an interactive map interface, allowing users to visually spot high-risk buildings (red pins) across Lagos, click to view their satellite imagery, and instantly generate the numbers-backed AI report explaining the suspected anomaly.

### Challenges I faced

#### Validating Satellite Imagery
One of the first issues with automated geospatial analysis is the quality of the imagery. Not all coordinates yield a perfectly centered, clear view of a building; some might be obscured by clouds, trees, or simply be misaligned.
To solve this, I added a pre-validation step using the Gemma-4 vision model. Before analyzing the building's traits, the model is prompted: *"Is this a clear, top-down satellite view of a single primary building?"* If the model answers "NO", the image is discarded, preventing garbage data from skewing the statistical baseline.

#### Providing Actionable Intelligence
Calculating a risk score tells us the probability of theft, but it doesn't give a utility inspector the context they need to authorize a truck roll. I needed the system to explain *why* a building was flagged.
To address this, I implemented an automated forensic synthesis step. The highest-risk building profiles—along with their satellite images, reported usage, and peer baselines—are fed into the larger `gemma-4-26b-a4b-it` model via the Gemini API. The model synthesizes a refined, numbers-backed analysis that explicitly quotes the provided numeric data points. This creates a detailed, evidence-backed report that inspectors can actually use.

#### Prioritizing High-Volume Targets
A high probability of theft doesn't always equal a high financial impact. A small residential building stealing 100% of its power might be less impactful than a large industrial complex stealing 20% of its power.
To solve this, I added a final financial impact calculation that estimates the absolute stolen volume in MWh. This allows the utility company to sort their dashboards and prioritize investigations by maximum revenue impact rather than just the highest statistical risk score.
