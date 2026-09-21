# datasets/train_gesture_model.py
"""
Train & Evaluate Gesture Classification Model for Cognitive Maze.
Generates:
1. datasets/gesture_scaler.pkl (StandardScaler)
2. datasets/gesture_model.pkl (RandomForestClassifier)
3. Model evaluation metrics (Confusion Matrix, Precision, Recall, F1-Score) for paper tables.
"""

import os
import glob
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

def train_gesture_pipeline(csv_pattern="datasets/*.csv", model_out="datasets/gesture_model.pkl", scaler_out="datasets/gesture_scaler.pkl"):
    csv_files = glob.glob(csv_pattern)
    if not csv_files:
        print(f"[ERROR] No CSV dataset files found matching {csv_pattern}")
        return None, None

    print(f"Loading datasets from: {csv_files}")
    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            # Remove index column if present
            if 'index' in df.columns:
                df = df.drop(columns=['index'])
            dfs.append(df)
            print(f"  - {f}: {len(df)} rows, columns: {df.shape[1]}")
        except Exception as e:
            print(f"  [WARN] Failed to read {f}: {e}")

    if not dfs:
        print("[ERROR] No data loaded.")
        return None, None

    data = pd.concat(dfs, ignore_index=True).dropna()
    print(f"\n[OK] Total Combined Dataset: {len(data)} samples across classes:")
    print(data['label'].value_counts())

    # Features: 63 landmark coordinates (x0, y0, z0 ... x20, y20, z20)
    X = data.drop(columns=['label']).values
    y = data['label'].values

    if X.shape[1] != 63:
        print(f"[WARN] Feature dimension is {X.shape[1]}, expected 63.")

    # Train / Test split (80% train, 20% test for evaluation in paper)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    # 1. Feature Normalization (StandardScaler)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 2. Train Random Forest Classifier
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)

    # 3. Model Evaluation for Research Paper
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)

    print("\n==================================================")
    print("      RESEARCH PAPER MODEL EVALUATION REPORT      ")
    print("==================================================")
    print(f"Overall Test Accuracy: {acc * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("Classes in model:", model.classes_)
    print("==================================================\n")

    # 4. Save trained artifacts
    joblib.dump(scaler, scaler_out)
    joblib.dump(model, model_out)
    print(f"[SUCCESS] Saved scaler to: {scaler_out}")
    print(f"[SUCCESS] Saved model to: {model_out}")

    return model, scaler

if __name__ == "__main__":
    train_gesture_pipeline()
