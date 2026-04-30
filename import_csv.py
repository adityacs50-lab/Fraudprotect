"""
Utility to import your own CSV data into the FraudShield platform.
The CSV should follow the schema: transaction_id, user_id, amount, merchant_category, 
city, latitude, longitude, device_id, payment_method, timestamp, [is_fraud].
"""

import pandas as pd
import argparse
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import FraudPipeline

def import_data(file_path, retrain=True):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    print(f"Reading {file_path}...")
    df = pd.read_csv(file_path)
    
    # Simple validation
    required = ["transaction_id", "user_id", "amount", "timestamp"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"Error: Missing required columns: {missing}")
        return

    pipeline = FraudPipeline()
    
    print("Initializing pipeline with your data...")
    # We modify the pipeline behavior slightly to accept a dataframe instead of generating one
    # For a clean implementation, we can call the pipeline steps manually
    
    print("[1/6] Engineering features...")
    featured_df = pipeline.feature_eng.compute_features(df)
    
    print("[2/6] Training/Updating models...")
    feature_cols = pipeline.feature_eng.feature_columns
    pipeline.model_trainer.train(featured_df, feature_cols)
    
    print("[3/6] Scoring batch...")
    scored_df = pipeline.model_trainer.score_batch(featured_df)
    
    print("[4/6] Applying rules...")
    scored_df = pipeline.rules_engine.evaluate_batch(scored_df)
    
    print("[5/6] Decision engine...")
    scored_df = pipeline.decision_combiner.decide_batch(scored_df)
    
    print("[6/6] Persisting to database...")
    from src import database as db
    db.init_db()
    db.insert_transactions(scored_df)
    db.insert_scored_transactions(scored_df)
    n_alerts = db.create_alerts(scored_df)
    
    print(f"\nSuccess! Imported {len(df)} transactions and created {n_alerts} alerts.")
    print("You can now view this data on the dashboard at http://localhost:3000")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import CSV data into FraudShield")
    parser.add_argument("file", help="Path to the CSV file")
    parser.add_argument("--no-retrain", action="store_true", help="Don't retrain models on this data")
    
    args = parser.parse_args()
    import_data(args.file, retrain=not args.no_retrain)
