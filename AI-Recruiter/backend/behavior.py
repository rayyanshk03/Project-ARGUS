import os
import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from bson import ObjectId

# Ensure we can import parser if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser import connect_db

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "lightgbm_behavior.pkl")

def _parse_date(date_val):
    if not date_val or pd.isna(date_val):
        return datetime.utcnow()
    if isinstance(date_val, datetime):
        return date_val
    try:
        return pd.to_datetime(date_val).to_pydatetime()
    except Exception:
        return datetime.utcnow()

def build_behavior_features(doc: dict) -> dict:
    """
    Converts raw candidate behavior fields into ML-ready numerical features.
    """
    now = datetime.utcnow()
    last_active = _parse_date(doc.get("last_active_date"))
    profile_updated = _parse_date(doc.get("profile_updated_date"))
    
    days_since_active = max(0, (now - last_active).days)
    days_since_update = max(0, (now - profile_updated).days)
    
    # Cap days to 365 so scaling doesn't break for extremely old dates
    days_since_active = min(days_since_active, 365)
    days_since_update = min(days_since_update, 365)
    
    courses = doc.get("courses_completed", [])
    num_courses = len(courses) if isinstance(courses, list) else 0
    
    return {
        "candidate_id": str(doc.get("candidate_id", doc.get("_id", ""))),
        "days_since_last_active": float(days_since_active),
        "days_since_profile_update": float(days_since_update),
        "applications_last_30_days": float(doc.get("applications_last_30_days", 0.0)),
        "interview_response_rate": float(doc.get("interview_response_rate", 0.0)),
        "profile_completeness": float(doc.get("profile_completeness", 0.0)),
        "num_courses_completed": float(num_courses),
        "login_frequency_per_week": float(doc.get("login_frequency_per_week", 0.0))
    }

def generate_synthetic_labels(df: pd.DataFrame) -> pd.Series:
    """
    Creates a weak-supervision heuristic label (0-1) based on engagement proxies.
    
    NOTE: Weak-Supervision Bootstrap Approach
    Since we lack labeled "good hire" or "responded_to_recruiter" data for this hackathon PoC, 
    we combine the available features into a logical heuristic engagement score.
    This provides a continuous target variable so we can train a real LightGBM model 
    and maintain the ML pipeline architecture end-to-end. 
    
    In a real production environment, this heuristic target would be replaced 
    with actual historical hiring/interview outcome labels.
    """
    # Scale days from 0-365 down to a 0-1 continuous scale (recent = 1.0)
    recent_activity_score = 1.0 - (df["days_since_last_active"] / 365.0)
    recent_update_score = 1.0 - (df["days_since_profile_update"] / 365.0)
    
    app_score = (df["applications_last_30_days"] / 10.0).clip(upper=1.0)
    login_score = (df["login_frequency_per_week"] / 7.0).clip(upper=1.0)
    
    # Combine scores with domain-weighted logic to simulate a real response probability
    label = (
        0.30 * recent_activity_score +
        0.25 * df["interview_response_rate"] +
        0.15 * df["profile_completeness"] +
        0.10 * login_score +
        0.10 * app_score +
        0.05 * recent_update_score +
        0.05 * (df["num_courses_completed"] / 5.0).clip(upper=1.0)
    )
    
    return label.clip(lower=0.0, upper=1.0)

def train_behavior_model():
    """
    Trains a LightGBM Regressor on the engineered features vs synthetic labels,
    and saves the model to models/lightgbm_behavior.pkl.
    """
    db = connect_db()
    behavior_docs = list(db["candidate_behavior"].find())
    
    if len(behavior_docs) < 10:
        print("Not enough candidate behavior data found. Please run parser.py ingestion first.")
        return
        
    print(f"Engineering features for {len(behavior_docs)} behavior records...")
    features_list = [build_behavior_features(d) for d in behavior_docs]
    df = pd.DataFrame(features_list)
    
    X = df.drop(columns=["candidate_id"])
    y = generate_synthetic_labels(df)
    
    # Train / Val Split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training LightGBM Regressor (Weak-Supervision)...")
    
    # Basic LightGBM regressor configuration
    model = lgb.LGBMRegressor(
        objective='regression',
        n_estimators=150,
        learning_rate=0.05,
        max_depth=5,
        random_state=42,
        verbosity=-1
    )
    
    # Train with early stopping to avoid overfitting our synthetic labels
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=15, verbose=False)]
    )
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
        
    # Validation Metrics
    y_train_pred = model.predict(X_train)
    y_val_pred = model.predict(X_val)
    
    train_mse = mean_squared_error(y_train, y_train_pred)
    val_mse = mean_squared_error(y_val, y_val_pred)
    
    print("\n--- LightGBM Model Training Metrics ---")
    print(f"Train MSE : {train_mse:.6f}")
    print(f"Val MSE   : {val_mse:.6f}")
    
    # Extract Feature Importance
    importances = model.feature_importances_
    features = X.columns
    sorted_idx = np.argsort(importances)[::-1]
    
    print("\nFeature Importances (split count):")
    for idx in sorted_idx:
        print(f"  {features[idx]:<25}: {importances[idx]}")
        
    print(f"\nModel successfully saved to {MODEL_PATH}")

def predict_behavior_score(candidate_id: str) -> float:
    """
    Loads the saved model, builds features for a specific candidate, 
    and returns a 0-1 predicted behavior/engagement score.
    """
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Triggering training...")
        train_behavior_model()
        
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    db = connect_db()
    
    # Support both string and ObjectId lookups
    doc = db["candidate_behavior"].find_one({"candidate_id": ObjectId(candidate_id)})
    if not doc:
        doc = db["candidate_behavior"].find_one({"candidate_id": str(candidate_id)})
        
    if not doc:
        # Default neutral/low score if no behavioral data exists for candidate
        return 0.5 
        
    features = build_behavior_features(doc)
    df = pd.DataFrame([features])
    X = df.drop(columns=["candidate_id"])
    
    # Predict and bound between 0 and 1
    score = model.predict(X)[0]
    return float(max(0.0, min(1.0, score)))

if __name__ == "__main__":
    train_behavior_model()
