# 🚦 Smart City Traffic Optimisation System

An AI-powered traffic management platform designed to optimize urban traffic flow, reduce congestion, and prioritize emergency vehicles using real-time data and advanced machine learning algorithms.

## ✨ Features

- **Real-Time Traffic Monitoring:** Visualize live traffic conditions, congestion heatmaps, and intersection statuses.
- **AI-Powered Signal Optimization:** Adaptive traffic lights that adjust timings dynamically based on current flow and predicted patterns.
- **Emergency Vehicle Priority:** Automatically clears paths for emergency responders, reducing response times.
- **Comprehensive Analytics:** Detailed insights into peak hours, traffic distribution, weather impacts, and historical trends.
- **Incident Management:** Track, report, and manage road accidents, roadworks, and other traffic disruptions.
- **Notification System:** Real-time alerts for system health, anomalies, and active incidents.

## 🛠️ Tech Stack

**Frontend**
- [Next.js](https://nextjs.org/) (React Framework)
- TypeScript
- CSS/TailwindCSS (for responsive UI styling)

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) (High-performance Python web framework)
- SQLite / SQLAlchemy (Database)
- Python 3.10+

**AI & Simulation**
- Machine Learning models for predictive analytics (`ai_engine`)
- Custom Python simulations for baseline comparisons

**Deployment**
- Docker & Docker Compose
- Vercel (Frontend Hosting)

## 📁 Project Structure

```text
├── frontend/                # Next.js web application
├── backend/                 # FastAPI server & API endpoints
├── ai_engine/               # AI & ML models for traffic prediction
├── Dataset/                 # Raw data and datasets
├── docker-compose.yml       # Container orchestration
└── simulation.py            # Core traffic simulation script
```

## 🚀 Getting Started

### Prerequisites
- Node.js (v18 or higher)
- Python (v3.10 or higher)
- Docker (Optional, for containerized deployment)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/smart-city-traffic.git
cd smart-city-traffic
```

### 2. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
```
*The backend API will be available at `http://localhost:8000`. API documentation is automatically generated at `http://localhost:8000/docs`.*

### 3. Frontend Setup (Next.js)
Open a new terminal window:
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
*The frontend application will be available at `http://localhost:3000`.*

### 4. Running with Docker (Alternative)
You can spin up the entire stack using Docker Compose:
```bash
docker-compose up --build
```

## 🔐 Demo Credentials

To access the dashboard in a local or demo environment, use the following credentials:
- **Admin Role:** `admin@smartcity.com` / `Admin@123`
- **Officer Role:** `officer@smartcity.com` / `Officer@123`

## 🧠 AI Simulation

To run the custom traffic simulation and evaluate the AI controller against baseline fixed-timing models:
```bash
python simulation.py
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Rish-0/smart-city-traffic/issues).
