"""Seed service — creates default users, signals, vehicles, notifications, incidents, settings."""

from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User
from app.models.signal import Signal
from app.models.notification import Notification
from app.models.incident import Incident
from app.models.emergency_vehicle import EmergencyVehicle
from app.models.settings import SystemSetting
import logging

logger = logging.getLogger(__name__)

COORDS = {
    "J1": ("44.9778", "-93.2650"), "J2": ("44.9750", "-93.2700"), "J3": ("44.9720", "-93.2750"),
    "J4": ("44.9690", "-93.2800"), "J5": ("44.9660", "-93.2850"), "J6": ("44.9800", "-93.2500"),
    "J7": ("44.9830", "-93.2450"), "J8": ("44.9860", "-93.2400"), "J9": ("44.9890", "-93.2350"),
    "J10": ("44.9920", "-93.2300"), "J11": ("44.9700", "-93.2900"), "J12": ("44.9670", "-93.2950"),
    "J13": ("44.9640", "-93.3000"), "J14": ("44.9610", "-93.3050"), "J15": ("44.9580", "-93.3100"),
    "J16": ("44.9550", "-93.2600"), "J17": ("44.9520", "-93.2550"), "J18": ("44.9490", "-93.2500"),
    "J19": ("44.9460", "-93.2450"), "J20": ("44.9430", "-93.2400"), "J21": ("44.9850", "-93.2600"),
    "J22": ("44.9880", "-93.2650"), "J23": ("44.9910", "-93.2700"), "J24": ("44.9940", "-93.2750"),
    "J25": ("44.9970", "-93.2800"),
}
ZONES = {
    "J1": "Commercial", "J2": "Commercial", "J3": "Commercial", "J4": "Commercial", "J5": "Commercial",
    "J6": "Residential", "J7": "Residential", "J8": "Residential", "J9": "Residential", "J10": "Residential",
    "J11": "School", "J12": "School", "J13": "School", "J14": "School", "J15": "School",
    "J16": "Industrial", "J17": "Industrial", "J18": "Industrial", "J19": "Industrial", "J20": "Industrial",
    "J21": "Hospital", "J22": "Hospital", "J23": "Hospital", "J24": "Hospital", "J25": "Hospital",
}

def seed_all(db: Session):
    # Users
    if db.query(User).count() == 0:
        db.add_all([
            User(email="admin@smartcity.com", username="admin", full_name="Traffic Administrator",
                 hashed_password=get_password_hash("Admin@123"), role="traffic_admin", department="Traffic Management"),
            User(email="officer@smartcity.com", username="officer", full_name="Traffic Control Officer",
                 hashed_password=get_password_hash("Officer@123"), role="traffic_officer", department="Traffic Control"),
            User(email="city@smartcity.com", username="cityadmin", full_name="City Administrator",
                 hashed_password=get_password_hash("City@123"), role="city_admin", department="City Administration"),
            User(email="emergency@smartcity.com", username="emergency", full_name="Emergency Services Lead",
                 hashed_password=get_password_hash("Emergency@123"), role="emergency_services", department="Emergency Response"),
            User(email="analyst@smartcity.com", username="analyst", full_name="Data Analyst",
                 hashed_password=get_password_hash("Analyst@123"), role="analyst", department="Analytics"),
        ]); db.commit(); logger.info("Seeded 5 users")
    # Signals
    if db.query(Signal).count() == 0:
        for jid, (lat, lng) in COORDS.items():
            db.add(Signal(intersection_id=jid, zone=ZONES[jid], green_duration=45, red_duration=45,
                          yellow_duration=5, mode="automatic", status="active", latitude=lat, longitude=lng))
        db.commit(); logger.info("Seeded 25 signals")
    # Emergency Vehicles
    if db.query(EmergencyVehicle).count() == 0:
        db.add_all([
            EmergencyVehicle(type="ambulance", call_sign="AMB-101", status="available", current_lat=44.9778, current_lng=-93.2650, nearest_junction="J1"),
            EmergencyVehicle(type="ambulance", call_sign="AMB-102", status="dispatched", current_lat=44.9850, current_lng=-93.2600, destination_name="City Hospital", nearest_junction="J21", eta_minutes=8, priority_active=1),
            EmergencyVehicle(type="police", call_sign="POL-201", status="en_route", current_lat=44.9700, current_lng=-93.2900, destination_name="J3 Intersection", nearest_junction="J11", eta_minutes=5, priority_active=1),
            EmergencyVehicle(type="police", call_sign="POL-202", status="available", current_lat=44.9550, current_lng=-93.2600, nearest_junction="J16"),
            EmergencyVehicle(type="fire_truck", call_sign="FIR-301", status="on_scene", current_lat=44.9660, current_lng=-93.2850, nearest_junction="J5"),
            EmergencyVehicle(type="fire_truck", call_sign="FIR-302", status="available", current_lat=44.9490, current_lng=-93.2500, nearest_junction="J18"),
            EmergencyVehicle(type="ambulance", call_sign="AMB-103", status="returning", current_lat=44.9940, current_lng=-93.2750, nearest_junction="J24"),
            EmergencyVehicle(type="police", call_sign="POL-203", status="available", current_lat=44.9830, current_lng=-93.2450, nearest_junction="J7"),
        ]); db.commit(); logger.info("Seeded 8 emergency vehicles")
    # Notifications
    if db.query(Notification).count() == 0:
        db.add_all([
            Notification(type="congestion", title="High Congestion Alert", message="Heavy traffic at J1-J5. Average speed dropped to 15 km/h.", severity="critical"),
            Notification(type="weather", title="Snow Advisory", message="Heavy snowfall expected. Reduced visibility may affect traffic flow.", severity="warning"),
            Notification(type="emergency", title="Emergency Vehicle Dispatched", message="AMB-102 dispatched to City Hospital. Priority signals activated.", severity="critical"),
            Notification(type="ai_recommendation", title="AI Signal Optimization", message="AI recommends +15s green at J3 during evening peak (16:00-20:00).", severity="info"),
            Notification(type="system", title="System Health Check", message="All 25 signals operating normally. AI engine confidence: 94%.", severity="success"),
            Notification(type="signal_failure", title="Signal Maintenance Required", message="Signal at J14 showing intermittent errors. Maintenance notified.", severity="warning"),
        ]); db.commit(); logger.info("Seeded 6 notifications")
    # Incidents
    if db.query(Incident).count() == 0:
        db.add_all([
            Incident(type="accident", title="Multi-vehicle collision on I-94", description="3-car collision near J3. Two lanes blocked.",
                     location="I-94 near J3", intersection_id="J3", latitude=44.9720, longitude=-93.2750, severity="high", status="investigating", priority=1, reported_by=2),
            Incident(type="construction", title="Road resurfacing - Oak Street", description="Scheduled road resurfacing. One lane closure for 3 days.",
                     location="Oak Street near J8", intersection_id="J8", latitude=44.9860, longitude=-93.2400, severity="medium", status="reported", priority=3, reported_by=1),
            Incident(type="weather_hazard", title="Flooded underpass at J16", description="Heavy rain caused flooding at J16 underpass.",
                     location="J16 Industrial Zone", intersection_id="J16", latitude=44.9550, longitude=-93.2600, severity="high", status="investigating", priority=2, reported_by=3),
        ]); db.commit(); logger.info("Seeded 3 incidents")
    # Settings
    if db.query(SystemSetting).count() == 0:
        db.add_all([
            SystemSetting(key="theme", value="dark", category="appearance", description="Default UI theme"),
            SystemSetting(key="congestion_threshold_low", value="2500", category="traffic", description="Low congestion threshold"),
            SystemSetting(key="congestion_threshold_high", value="5000", category="traffic", description="High congestion threshold"),
            SystemSetting(key="default_green_signal", value="45", category="signal", description="Default green signal seconds"),
            SystemSetting(key="default_red_signal", value="45", category="signal", description="Default red signal seconds"),
            SystemSetting(key="emergency_priority_extension", value="15", category="signal", description="Extra green for emergency"),
            SystemSetting(key="ai_engine_enabled", value="true", category="ai", description="Enable AI engine"),
            SystemSetting(key="ai_confidence_threshold", value="0.7", category="ai", description="Min confidence for AI recommendations"),
            SystemSetting(key="data_refresh_interval", value="60", category="general", description="Data refresh interval seconds"),
            SystemSetting(key="session_timeout", value="30", category="security", description="Session timeout minutes"),
        ]); db.commit(); logger.info("Seeded 10 settings")
    logger.info("Database seeding completed!")
