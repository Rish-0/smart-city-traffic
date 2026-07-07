"""TomTom Live Traffic Service — Fetches real-time traffic data."""

import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class TomTomService:
    BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

    def __init__(self):
        self.api_key = settings.TOMTOM_API_KEY

    async def get_traffic_flow(self, lat: float, lng: float):
        """Fetch live traffic flow data for a specific coordinate point."""
        if not self.api_key or self.api_key == "your_tomtom_api_key_here":
            logger.warning("TomTom API key not configured properly.")
            return None

        url = f"{self.BASE_URL}?key={self.api_key}&point={lat},{lng}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("flowSegmentData")
                else:
                    logger.error(f"TomTom API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch TomTom traffic: {e}")
            return None

    def estimate_metrics(self, flow_data: dict) -> dict:
        """Estimate volume and congestion from TomTom speed data."""
        if not flow_data:
            return {"volume": 3000, "congestion": "Low", "speed": 40}

        current = flow_data.get("currentSpeed", 40)
        free_flow = flow_data.get("freeFlowSpeed", 50)
        
        # Prevent division by zero
        free_flow = max(free_flow, 1)
        ratio = current / free_flow

        if ratio >= 0.8:
            congestion = "Low"
            volume = 1200
        elif ratio >= 0.6:
            congestion = "Moderate"
            volume = 3500
        elif ratio >= 0.4:
            congestion = "High"
            volume = 5500
        else:
            congestion = "Critical"
            volume = 7500

        return {
            "volume": volume,
            "congestion": congestion,
            "speed": current
        }

tomtom_service = TomTomService()
