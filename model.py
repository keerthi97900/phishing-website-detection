import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from xgboost import XGBClassifier

DATASET_PATH = r"D:\final year project\Project_folder\Feature_dataset_WITH_URL_FEATURES.csv"
RANDOM_STATE = 42

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded")
print("Shape:", df.shape)

print("\nLabel distribution:")
print(df["label"].value_counts())

df = df.drop(columns=["url"])   
df = df.fillna(-1)              

X = df.drop(columns=["label"])
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=RANDOM_STATE
)

print("\nTrain size:", X_train.shape)
print("Test size :", X_test.shape)


rf_model = RandomForestClassifier(
    n_estimators=300,
    random_state=RANDOM_STATE,
    n_jobs=-1
)

print("\nTraining Random Forest...")
rf_model.fit(X_train, y_train)

rf_preds = rf_model.predict(X_test)

print("\n===== RANDOM FOREST RESULTS =====")
print("Accuracy :", accuracy_score(y_test, rf_preds))
print("Precision:", precision_score(y_test, rf_preds))
print("Recall   :", recall_score(y_test, rf_preds))
print("F1 Score :", f1_score(y_test, rf_preds))

print("\nClassification Report:")
print(classification_report(y_test, rf_preds))

cm_rf = confusion_matrix(y_test, rf_preds)
plt.figure(figsize=(6, 5))
sns.heatmap(cm_rf, annot=True, fmt="d", cmap="Blues")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Random Forest - Confusion Matrix")
plt.tight_layout()
plt.savefig("confusion_matrix_rf.png")
plt.close()

rf_importance = pd.Series(
    rf_model.feature_importances_,
    index=X.columns
).sort_values(ascending=False)

plt.figure(figsize=(10, 6))
rf_importance.head(15).plot(kind="bar")
plt.title("Top 15 Feature Importances - Random Forest")
plt.tight_layout()
plt.savefig("feature_importance_rf.png")
plt.close()


xgb_model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=RANDOM_STATE
)

print("\nTraining XGBoost...")
xgb_model.fit(X_train, y_train)

xgb_preds = xgb_model.predict(X_test)

print("\n===== XGBOOST RESULTS =====")
print("Accuracy :", accuracy_score(y_test, xgb_preds))
print("Precision:", precision_score(y_test, xgb_preds))
print("Recall   :", recall_score(y_test, xgb_preds))
print("F1 Score :", f1_score(y_test, xgb_preds))

print("\nClassification Report:")
print(classification_report(y_test, xgb_preds))

cm_xgb = confusion_matrix(y_test, xgb_preds)
plt.figure(figsize=(6, 5))
sns.heatmap(cm_xgb, annot=True, fmt="d", cmap="Greens")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("XGBoost - Confusion Matrix")
plt.tight_layout()
plt.savefig("confusion_matrix_xgb.png")
plt.close()

xgb_importance = pd.Series(
    xgb_model.feature_importances_,
    index=X.columns
).sort_values(ascending=False)

plt.figure(figsize=(10, 6))
xgb_importance.head(15).plot(kind="bar")
plt.title("Top 15 Feature Importances - XGBoost")
plt.tight_layout()
plt.savefig("feature_importance_xgb.png")
plt.close()

# ---------------- SAVE MODEL ----------------
# joblib.dump(rf_model, "phishing_rf_model.pkl")
# joblib.dump(X.columns.tolist(), "model_features.pkl")

# print("\nModel saved as phishing_rf_model.pkl")
# print("Feature list saved as model_features.pkl")
# print("All plots saved successfully")
# print("Training completed without errors ✅")
