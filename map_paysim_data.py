import pandas as pd
import numpy as np
import os
import uuid
from datetime import datetime, timedelta

def map_paysim_to_fraudshield(input_path, output_path, sample_size=100000):
    print(f"Loading PaySim dataset from {input_path}...")
    # Using chunksize or nrows because the file is large (~500MB)
    df = pd.read_csv(input_path, nrows=sample_size)
    
    print(f"Mapping {len(df)} rows...")
    
    # 1. Transaction ID
    df['transaction_id'] = [str(uuid.uuid4())[:12] for _ in range(len(df))]
    
    # 2. User ID
    df['user_id'] = df['nameOrig']
    
    # 3. Amount
    # df['amount'] is already present
    
    # 4. Map Time (step is 1 hour)
    start_date = datetime(2026, 3, 1)
    df['timestamp'] = df['step'].apply(lambda x: (start_date + timedelta(hours=x)).isoformat())
    
    # 5. Categorical mapping
    type_map = {
        'PAYMENT': 'upi',
        'TRANSFER': 'credit_card',
        'CASH_OUT': 'debit_card',
        'DEBIT': 'debit_card',
        'CASH_IN': 'upi'
    }
    df['payment_method'] = df['type'].map(type_map)
    
    category_map = {
        'PAYMENT': 'online_shopping',
        'TRANSFER': 'travel',
        'CASH_OUT': 'electronics',
        'DEBIT': 'grocery',
        'CASH_IN': 'fuel'
    }
    df['merchant_category'] = df['type'].map(category_map)
    
    # 6. Synthesize location and device (Stable per user)
    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"]
    city_coords = {
        "Mumbai": (19.07, 72.87),
        "Delhi": (28.70, 77.10),
        "Bangalore": (12.97, 77.59),
        "Hyderabad": (17.38, 78.48),
        "Chennai": (13.08, 80.27)
    }
    
    # Assign a primary city and device to each user to avoid "new device" spam
    unique_users = df['user_id'].unique()
    user_city_map = {u: np.random.choice(cities) for u in unique_users}
    user_device_map = {u: f"DEV-{np.random.randint(1000, 9999)}" for u in unique_users}
    
    df['city'] = df['user_id'].map(user_city_map)
    df['device_id'] = df['user_id'].map(user_device_map)
    
    # Add some noise/new devices (5% chance of a second device)
    new_device_mask = np.random.random(len(df)) < 0.05
    df.loc[new_device_mask, 'device_id'] = [f"DEV-{np.random.randint(1000, 9999)}" for _ in range(new_device_mask.sum())]
    
    df['latitude'] = df['city'].map(lambda x: city_coords[x][0] + np.random.normal(0, 0.01))
    df['longitude'] = df['city'].map(lambda x: city_coords[x][1] + np.random.normal(0, 0.01))
    
    # 7. Map fraud status
    df['is_fraud'] = df['isFraud']
    
    # Select final columns
    cols = [
        "transaction_id", "user_id", "amount", "merchant_category", 
        "city", "latitude", "longitude", "device_id", "payment_method", 
        "timestamp", "is_fraud"
    ]
    
    output_df = df[cols]
    
    print(f"Saving mapped dataset to {output_path}...")
    output_df.to_csv(output_path, index=False)
    print("Mapping complete.")

if __name__ == "__main__":
    paysim_path = "dataset/Synthetic_Financial_datasets_log.csv"
    output_path = "dataset/paysim_mapped.csv"
    
    if os.path.exists(paysim_path):
        # Taking 100k rows for testing to keep it manageable
        map_paysim_to_fraudshield(paysim_path, output_path, sample_size=100000)
    else:
        print(f"Error: Source file {paysim_path} not found.")
