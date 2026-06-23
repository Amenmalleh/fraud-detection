"""
Entrainement et evaluation des modeles de detection de fraude.

On entraine deux modeles (Random Forest et XGBoost) et on garde le meilleur
des deux selon l'AUC-ROC, une metrique adaptee aux donnees desequilibrees
(contrairement a l'accuracy, qui serait trompeuse ici - cf. preprocessing.py).
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from xgboost import XGBClassifier

from src.config import (
    KAGGLE_DATASET_PATH,
    MODEL_PATH,
    SCALER_PATH,
    RF_PARAMS,
    XGB_PARAMS,
)
from src.preprocessing import FraudPreprocessor


def evaluate_model(name, model, X_test, y_test):
    """Affiche classification_report, confusion_matrix et AUC-ROC pour un modele."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]  # probabilite de la classe "fraude"

    auc = roc_auc_score(y_test, y_proba)

    print(f"\n=== Resultats : {name} ===")
    print("Classification report :")
    print(classification_report(y_test, y_pred, target_names=["Legitime", "Fraude"]))
    print("Matrice de confusion :")
    print(confusion_matrix(y_test, y_pred))
    print(f"AUC-ROC : {auc:.4f}")

    return auc


def print_feature_importance(name, model, feature_names, top_n=10):
    """Affiche les top_n features les plus importantes pour le modele."""
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).head(top_n)

    print(f"\n--- Top {top_n} features importantes ({name}) ---")
    print(importance_df.to_string(index=False))


def main():
    # --- 1. Pretraitement ---
    preprocessor = FraudPreprocessor()
    preprocessor.load_data(KAGGLE_DATASET_PATH)
    preprocessor.explore_data()
    preprocessor.prepare_features()
    preprocessor.scale_features()
    preprocessor.apply_smote()

    X_train, y_train = preprocessor.X_train, preprocessor.y_train
    X_test, y_test = preprocessor.X_test, preprocessor.y_test

    # --- 2. Entrainement Random Forest ---
    print("\nEntrainement du Random Forest...")
    rf_model = RandomForestClassifier(**RF_PARAMS)
    rf_model.fit(X_train, y_train)
    rf_auc = evaluate_model("Random Forest", rf_model, X_test, y_test)
    print_feature_importance("Random Forest", rf_model, X_train.columns)

    # --- 3. Entrainement XGBoost ---
    print("\nEntrainement du XGBoost...")
    xgb_model = XGBClassifier(**XGB_PARAMS)
    xgb_model.fit(X_train, y_train)
    xgb_auc = evaluate_model("XGBoost", xgb_model, X_test, y_test)
    print_feature_importance("XGBoost", xgb_model, X_train.columns)

    # --- 4. Selection et sauvegarde du meilleur modele ---
    if rf_auc >= xgb_auc:
        best_name, best_model, best_auc = "Random Forest", rf_model, rf_auc
    else:
        best_name, best_model, best_auc = "XGBoost", xgb_model, xgb_auc

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(preprocessor.scaler, SCALER_PATH)

    print(f"\nMeilleur modele : {best_name} (AUC-ROC = {best_auc:.4f})")
    print(f"Modele sauvegarde dans : {MODEL_PATH}")
    print(f"Scaler sauvegarde dans : {SCALER_PATH}")
    print(f"\nModele sauvegarde avec AUC-ROC = {best_auc:.2f}")


if __name__ == "__main__":
    main()
