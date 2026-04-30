"""
Feature Engineering Layer — derives rolling, behavioral, and contextual
features from raw transaction data for fraud detection.

All features are computed per-transaction using the user's historical context.
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, Optional


MERCHANT_RISK_SCORES: Dict[str, float] = {
    "grocery": 0.05,
    "fuel": 0.08,
    "restaurant": 0.06,
    "pharmacy": 0.04,
    "utility_bill": 0.03,
    "clothing": 0.10,
    "subscription": 0.07,
    "travel": 0.15,
    "entertainment": 0.12,
    "online_shopping": 0.35,
    "electronics": 0.40,
    "atm_withdrawal": 0.20,
    "money_transfer": 0.45,
    "jewelry": 0.50,
    "gaming": 0.42,
}


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class FeatureEngineer:
    """Compute fraud-relevant features from raw transaction DataFrame."""

    def __init__(self):
        self.feature_columns = []

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all features. Expects a sorted-by-timestamp DataFrame."""
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        # ---- Time features ----
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["is_night"] = ((df["hour"] >= 0) & (df["hour"] <= 5)).astype(int)
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        # ---- Merchant risk score ----
        df["merchant_risk_score"] = df["merchant_category"].map(MERCHANT_RISK_SCORES).fillna(0.15)

        # ---- Payment method encoding ----
        payment_risk = {"upi": 0.1, "credit_card": 0.3, "debit_card": 0.25, "net_banking": 0.15, "wallet": 0.2}
        df["payment_risk_score"] = df["payment_method"].map(payment_risk).fillna(0.2)

        # ---- Rolling / user-level features (vectorized with groupby) ----
        df = self._add_rolling_features(df)

        # ---- Distance from previous transaction ----
        df = self._add_geo_features(df)

        # ---- Device features ----
        df = self._add_device_features(df)

        # ---- Amount deviation from user baseline ----
        df = self._add_amount_deviation(df)

        # ---- Log-transform amount ----
        df["log_amount"] = np.log1p(df["amount"])

        self.feature_columns = [
            "amount", "log_amount", "hour", "day_of_week", "is_night", "is_weekend",
            "merchant_risk_score", "payment_risk_score",
            "tx_count_1h", "tx_count_24h", "avg_amount_user", "std_amount_user",
            "amount_zscore", "amount_ratio_to_baseline",
            "distance_from_prev_km", "speed_kmh",
            "is_new_device", "device_count_user",
            "merchant_frequency",
        ]

        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Count transactions in last 1h and 24h per user, plus user-level stats."""
        df["ts_epoch"] = df["timestamp"].astype(np.int64) // 10 ** 9

        tx_1h = []
        tx_24h = []
        avg_amounts = []
        std_amounts = []
        merchant_freqs = []

        user_history: Dict[str, list] = {}
        user_merchant_counts: Dict[str, Dict[str, int]] = {}

        for idx, row in df.iterrows():
            uid = row["user_id"]
            ts = row["ts_epoch"]
            amt = row["amount"]
            merchant = row["merchant_category"]

            if uid not in user_history:
                user_history[uid] = []
                user_merchant_counts[uid] = {}

            history = user_history[uid]

            # Count transactions in last 1h and 24h
            count_1h = sum(1 for t, _ in history if ts - t <= 3600)
            count_24h = sum(1 for t, _ in history if ts - t <= 86400)
            tx_1h.append(count_1h)
            tx_24h.append(count_24h)

            # Running average and std of user amounts
            amounts = [a for _, a in history]
            if amounts:
                avg_amounts.append(np.mean(amounts))
                std_amounts.append(np.std(amounts) if len(amounts) > 1 else 0)
            else:
                avg_amounts.append(amt)
                std_amounts.append(0)

            # Merchant frequency for this user
            mc = user_merchant_counts[uid]
            total_mc = sum(mc.values()) if mc else 1
            merchant_freqs.append(mc.get(merchant, 0) / total_mc)

            # Update history
            history.append((ts, amt))
            mc[merchant] = mc.get(merchant, 0) + 1

        df["tx_count_1h"] = tx_1h
        df["tx_count_24h"] = tx_24h
        df["avg_amount_user"] = avg_amounts
        df["std_amount_user"] = std_amounts
        df["merchant_frequency"] = merchant_freqs

        return df

    def _add_geo_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Distance from previous transaction and implied speed."""
        distances = [0.0]
        speeds = [0.0]
        prev_by_user: Dict[str, dict] = {}

        for idx in range(len(df)):
            row = df.iloc[idx]
            uid = row["user_id"]

            if uid in prev_by_user:
                prev = prev_by_user[uid]
                dist = _haversine_km(prev["lat"], prev["lon"], row["latitude"], row["longitude"])
                time_diff_hours = (row["ts_epoch"] - prev["ts"]) / 3600
                speed = dist / time_diff_hours if time_diff_hours > 0 else 0
                if idx > 0:
                    distances.append(round(dist, 2))
                    speeds.append(round(speed, 2))
            else:
                if idx > 0:
                    distances.append(0.0)
                    speeds.append(0.0)

            prev_by_user[uid] = {
                "lat": row["latitude"],
                "lon": row["longitude"],
                "ts": row["ts_epoch"],
            }

        df["distance_from_prev_km"] = distances
        df["speed_kmh"] = speeds

        return df

    def _add_device_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Track device novelty per user."""
        is_new = []
        device_counts = []
        user_devices: Dict[str, set] = {}

        for _, row in df.iterrows():
            uid = row["user_id"]
            dev = row["device_id"]

            # Only flag as 'new' if we have seen this user before with a different device
            is_new_flag = 1 if (uid in user_devices and dev not in user_devices[uid]) else 0
            is_new.append(is_new_flag)
            
            if uid not in user_devices:
                user_devices[uid] = set()
            user_devices[uid].add(dev)
            device_counts.append(len(user_devices[uid]))

        df["is_new_device"] = is_new
        df["device_count_user"] = device_counts

        return df

    def _add_amount_deviation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Z-score and ratio of amount vs user baseline."""
        df["amount_zscore"] = np.where(
            df["std_amount_user"] > 0,
            (df["amount"] - df["avg_amount_user"]) / df["std_amount_user"],
            0,
        )
        df["amount_ratio_to_baseline"] = np.where(
            df["avg_amount_user"] > 0,
            df["amount"] / df["avg_amount_user"],
            1,
        )
        return df

    def get_model_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return only the numeric feature columns for model input."""
        available = [c for c in self.feature_columns if c in df.columns]
        return df[available].fillna(0)
