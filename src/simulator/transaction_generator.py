"""
Transaction Simulator — generates realistic synthetic transactions with
behavioral context for fraud detection training and demo streaming.

Each user has a persistent profile (home city, device set, spending baseline,
preferred merchants) so that deviations become meaningful features.
"""

import uuid
import random
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CITIES = [
    {"name": "Mumbai", "lat": 19.076, "lon": 72.8777},
    {"name": "Delhi", "lat": 28.7041, "lon": 77.1025},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"name": "Hyderabad", "lat": 17.385, "lon": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
    {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
    {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
    {"name": "Aurangabad", "lat": 19.8762, "lon": 75.3433},
    {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
    {"name": "Goa", "lat": 15.2993, "lon": 74.124},
    {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
]

MERCHANT_CATEGORIES = [
    "grocery", "electronics", "fuel", "restaurant", "travel",
    "clothing", "pharmacy", "entertainment", "utility_bill",
    "online_shopping", "atm_withdrawal", "money_transfer",
    "subscription", "jewelry", "gaming",
]

# Merchant categories with higher fraud risk
HIGH_RISK_MERCHANTS = {"electronics", "jewelry", "gaming", "money_transfer", "online_shopping"}

PAYMENT_METHODS = ["upi", "credit_card", "debit_card", "net_banking", "wallet"]

DEVICE_TYPES = ["android", "ios", "web_desktop", "web_mobile"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lon points in kilometers."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@dataclass
class UserProfile:
    """Persistent user behavioral profile."""
    user_id: str
    home_city: dict
    devices: List[str] = field(default_factory=list)
    preferred_merchants: List[str] = field(default_factory=list)
    avg_amount: float = 0.0
    std_amount: float = 0.0
    typical_hour_start: int = 8
    typical_hour_end: int = 22
    tx_per_day: float = 3.0
    failed_logins: int = 0


class TransactionSimulator:
    """Generate realistic transaction data with controllable fraud injection."""

    def __init__(self, n_users: int = 500, fraud_rate: float = 0.035, seed: int = 42):
        self.n_users = n_users
        self.fraud_rate = fraud_rate
        self.rng = np.random.RandomState(seed)
        random.seed(seed)
        self.users: Dict[str, UserProfile] = {}
        self._create_user_profiles()

    def _create_user_profiles(self):
        for i in range(self.n_users):
            uid = f"USR-{i:05d}"
            home = random.choice(CITIES)
            n_devices = random.randint(1, 3)
            devices = [f"DEV-{uid}-{d}" for d in random.sample(DEVICE_TYPES, min(n_devices, len(DEVICE_TYPES)))]
            n_merchants = random.randint(3, 7)
            merchants = random.sample(MERCHANT_CATEGORIES, n_merchants)
            avg_amount = self.rng.lognormal(mean=6.5, sigma=1.0)  # ≈ ₹650 median
            std_amount = avg_amount * self.rng.uniform(0.2, 0.6)
            hour_start = random.randint(6, 10)
            hour_end = random.randint(20, 23)
            tx_per_day = self.rng.uniform(1.5, 8.0)

            self.users[uid] = UserProfile(
                user_id=uid,
                home_city=home,
                devices=devices,
                preferred_merchants=merchants,
                avg_amount=round(avg_amount, 2),
                std_amount=round(std_amount, 2),
                typical_hour_start=hour_start,
                typical_hour_end=hour_end,
                tx_per_day=tx_per_day,
            )

    def _generate_legit_transaction(self, user: UserProfile, ts: datetime) -> dict:
        """Generate a normal transaction consistent with user profile."""
        amount = max(10, self.rng.normal(user.avg_amount, user.std_amount))
        # Occasionally visit nearby cities (travel)
        if random.random() < 0.05:
            city = random.choice(CITIES)
        else:
            city = user.home_city

        device = random.choice(user.devices)
        merchant = random.choice(user.preferred_merchants)
        payment = random.choice(PAYMENT_METHODS)
        # Normal hours
        hour = random.randint(user.typical_hour_start, user.typical_hour_end)
        ts = ts.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))

        return {
            "transaction_id": str(uuid.uuid4())[:12],
            "user_id": user.user_id,
            "amount": round(amount, 2),
            "merchant_category": merchant,
            "city": city["name"],
            "latitude": city["lat"] + self.rng.normal(0, 0.01),
            "longitude": city["lon"] + self.rng.normal(0, 0.01),
            "device_id": device,
            "payment_method": payment,
            "timestamp": ts.isoformat(),
            "is_fraud": 0,
            "fraud_type": None,
        }

    def _generate_fraud_transaction(self, user: UserProfile, ts: datetime) -> dict:
        """Generate a fraudulent transaction with realistic fraud patterns."""
        fraud_type = random.choice([
            "account_takeover", "card_not_present", "velocity_abuse",
            "geo_impossible_travel", "high_value_anomaly", "new_device_fraud",
        ])

        tx = self._generate_legit_transaction(user, ts)
        tx["is_fraud"] = 1
        tx["fraud_type"] = fraud_type

        if fraud_type == "account_takeover":
            # New device, different city, unusual merchant
            tx["device_id"] = f"DEV-STOLEN-{random.randint(10000, 99999)}"
            far_city = random.choice([c for c in CITIES if c["name"] != user.home_city["name"]])
            tx["city"] = far_city["name"]
            tx["latitude"] = far_city["lat"]
            tx["longitude"] = far_city["lon"]
            tx["merchant_category"] = random.choice(list(HIGH_RISK_MERCHANTS))
            tx["amount"] = round(user.avg_amount * self.rng.uniform(3, 10), 2)

        elif fraud_type == "card_not_present":
            tx["payment_method"] = random.choice(["credit_card", "debit_card"])
            tx["merchant_category"] = random.choice(["online_shopping", "gaming", "electronics"])
            tx["amount"] = round(user.avg_amount * self.rng.uniform(2, 6), 2)

        elif fraud_type == "velocity_abuse":
            # Multiple rapid transactions — amount stays normal-ish
            tx["amount"] = round(user.avg_amount * self.rng.uniform(0.8, 2.0), 2)
            # Timestamp within minutes of each other (handled by caller batching)

        elif fraud_type == "geo_impossible_travel":
            far_city = random.choice([c for c in CITIES if
                                       haversine_km(c["lat"], c["lon"],
                                                    user.home_city["lat"], user.home_city["lon"]) > 500])
            tx["city"] = far_city["name"]
            tx["latitude"] = far_city["lat"]
            tx["longitude"] = far_city["lon"]
            # Transaction within 30 min of a home-city one
            tx["timestamp"] = (ts + timedelta(minutes=random.randint(10, 40))).isoformat()

        elif fraud_type == "high_value_anomaly":
            tx["amount"] = round(user.avg_amount * self.rng.uniform(5, 20), 2)
            tx["merchant_category"] = random.choice(["jewelry", "electronics", "money_transfer"])

        elif fraud_type == "new_device_fraud":
            tx["device_id"] = f"DEV-NEW-{random.randint(10000, 99999)}"
            tx["amount"] = round(user.avg_amount * self.rng.uniform(2, 8), 2)
            tx["merchant_category"] = random.choice(list(HIGH_RISK_MERCHANTS))
            # Night-time
            tx["timestamp"] = ts.replace(hour=random.randint(0, 5)).isoformat()

        return tx

    def generate_batch(self, n_transactions: int = 10000,
                       start_date: Optional[datetime] = None,
                       days: int = 30) -> pd.DataFrame:
        """Generate a batch of transactions spanning `days` days."""
        if start_date is None:
            start_date = datetime(2026, 3, 1)

        transactions = []
        n_fraud = int(n_transactions * self.fraud_rate)
        n_legit = n_transactions - n_fraud

        user_ids = list(self.users.keys())

        # Legitimate transactions
        for _ in range(n_legit):
            uid = random.choice(user_ids)
            user = self.users[uid]
            day_offset = random.randint(0, days - 1)
            ts = start_date + timedelta(days=day_offset)
            transactions.append(self._generate_legit_transaction(user, ts))

        # Fraud transactions
        for _ in range(n_fraud):
            uid = random.choice(user_ids)
            user = self.users[uid]
            day_offset = random.randint(0, days - 1)
            ts = start_date + timedelta(days=day_offset)
            transactions.append(self._generate_fraud_transaction(user, ts))

        df = pd.DataFrame(transactions)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def generate_stream(self, batch_size: int = 50) -> pd.DataFrame:
        """Generate a small batch of new transactions for near-real-time demo."""
        now = datetime.now()
        return self.generate_batch(n_transactions=batch_size, start_date=now, days=1)

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Return user profile as dict for API responses."""
        u = self.users.get(user_id)
        if not u:
            return None
        return {
            "user_id": u.user_id,
            "home_city": u.home_city["name"],
            "devices": u.devices,
            "preferred_merchants": u.preferred_merchants,
            "avg_amount": u.avg_amount,
            "std_amount": u.std_amount,
            "typical_hours": f"{u.typical_hour_start}:00-{u.typical_hour_end}:00",
            "tx_per_day": round(u.tx_per_day, 1),
        }
