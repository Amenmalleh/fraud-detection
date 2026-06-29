"""
Entrainement et evaluation des modeles de detection de fraude.

On entraine un Random Forest (hyperparametres fixes) et un XGBoost dont les
hyperparametres sont optimises par GridSearchCV, puis on garde le meilleur
des deux selon l'AUC-ROC, une metrique adaptee aux donnees desequilibrees
(contrairement a l'accuracy, qui serait trompeuse ici - cf. preprocessing.py).
"""

import matplotlib

matplotlib.use("Agg")  # pas d'affichage interactif : on sauvegarde directement en PNG

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV
from xgboost import XGBClassifier

from src.config import (
    EVALUATION_REPORT_PATH,
    KAGGLE_DATASET_PATH,
    MODEL_PATH,
    RF_PARAMS,
    ROC_CURVE_PATH,
    SCALER_PATH,
    XGB_BASE_PARAMS,
    XGB_PARAM_GRID,
)
from src.preprocessing import FraudPreprocessor


def evaluate_model(name, model, X_test, y_test):
    """Affiche classification_report/confusion_matrix et retourne les metriques cles."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]  # probabilite de la classe "fraude"

    auc = roc_auc_score(y_test, y_proba)

    print(f"\n=== Resultats : {name} ===")
    print("Classification report :")
    print(classification_report(y_test, y_pred, target_names=["Legitime", "Fraude"]))
    print("Matrice de confusion :")
    print(confusion_matrix(y_test, y_pred))
    print(f"AUC-ROC : {auc:.4f}")

    metrics = {
        "auc": auc,
        "f1": f1_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
        "y_proba": y_proba,
    }
    return metrics


def print_feature_importance(name, model, feature_names, top_n=10):
    """Affiche les top_n features les plus importantes pour le modele."""
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).head(top_n)

    print(f"\n--- Top {top_n} features importantes ({name}) ---")
    print(importance_df.to_string(index=False))


def tune_xgboost(X_train, y_train):
    """
    Recherche les meilleurs hyperparametres XGBoost par grid search.

    cv=3 : le train set (deja reequilibre par SMOTE) est decoupe en 3 plis ;
    chaque combinaison de la grille est entrainee 3 fois (un pli different en
    validation chaque fois) et evaluee en moyenne. scoring="roc_auc" : on
    optimise directement la metrique qui nous interesse, pas l'accuracy.
    n_jobs=-1 : les combinaisons de la grille tournent en parallele sur tous
    les coeurs CPU disponibles (8 combinaisons x 3 plis = 24 entrainements).
    """
    print("\nRecherche des meilleurs hyperparametres XGBoost (GridSearchCV)...")
    grid_search = GridSearchCV(
        estimator=XGBClassifier(**XGB_BASE_PARAMS),
        param_grid=XGB_PARAM_GRID,
        cv=3,
        scoring="roc_auc",
        n_jobs=-1,
    )
    grid_search.fit(X_train, y_train)

    print(f"Meilleurs parametres : {grid_search.best_params_}")
    print(f"Meilleur score CV (AUC-ROC) : {grid_search.best_score_:.4f}")

    return grid_search.best_estimator_, grid_search.best_params_


def plot_roc_curve(results, path):
    """Trace les courbes ROC de tous les modeles evalues sur un seul graphe."""
    plt.figure(figsize=(7, 6))

    for name, y_test, metrics in results:
        fpr, tpr, _ = roc_curve(y_test, metrics["y_proba"])
        plt.plot(fpr, tpr, label=f"{name} (AUC = {metrics['auc']:.4f})")

    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Hasard (AUC = 0.50)")
    plt.xlabel("Taux de faux positifs")
    plt.ylabel("Taux de vrais positifs")
    plt.title("Courbe ROC - Random Forest vs XGBoost")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Courbe ROC sauvegardee dans : {path}")


def write_evaluation_report(path, best_params, results, best_name):
    """Ecrit un rapport texte lisible avec les metriques de chaque modele."""
    lines = ["=== Rapport d'evaluation - Detection de fraude ===", ""]

    lines.append("--- Meilleurs hyperparametres XGBoost (GridSearchCV, cv=3, scoring=roc_auc) ---")
    lines.append(str(best_params))
    lines.append("")

    lines.append("--- AUC-ROC : Random Forest vs XGBoost ---")
    for name, _, metrics in results:
        lines.append(f"{name:<20s} : {metrics['auc']:.4f}")
    lines.append("")

    for name, _, metrics in results:
        lines.append(f"--- {name} ---")
        lines.append(f"AUC-ROC   : {metrics['auc']:.4f}")
        lines.append(f"F1-Score  : {metrics['f1']:.4f}")
        lines.append(f"Precision : {metrics['precision']:.4f}")
        lines.append(f"Recall    : {metrics['recall']:.4f}")
        lines.append("Matrice de confusion :")
        lines.append(str(metrics["confusion_matrix"]))
        lines.append("")

    best_auc = next(metrics["auc"] for name, _, metrics in results if name == best_name)
    lines.append(f"--- Modele retenu : {best_name} (AUC-ROC = {best_auc:.4f}) ---")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rapport d'evaluation sauvegarde dans : {path}")


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

    # --- 2. Entrainement Random Forest (hyperparametres fixes) ---
    print("\nEntrainement du Random Forest...")
    rf_model = RandomForestClassifier(**RF_PARAMS)
    rf_model.fit(X_train, y_train)
    rf_metrics = evaluate_model("Random Forest", rf_model, X_test, y_test)
    print_feature_importance("Random Forest", rf_model, X_train.columns)

    # --- 3. XGBoost tune par GridSearchCV ---
    xgb_model, best_params = tune_xgboost(X_train, y_train)
    xgb_metrics = evaluate_model("XGBoost (tune)", xgb_model, X_test, y_test)
    print_feature_importance("XGBoost (tune)", xgb_model, X_train.columns)

    results = [
        ("Random Forest", y_test, rf_metrics),
        ("XGBoost (tune)", y_test, xgb_metrics),
    ]

    # --- 4. Selection du meilleur modele ---
    if rf_metrics["auc"] >= xgb_metrics["auc"]:
        best_name, best_model, best_auc = "Random Forest", rf_model, rf_metrics["auc"]
    else:
        best_name, best_model, best_auc = "XGBoost (tune)", xgb_model, xgb_metrics["auc"]

    # --- 5. Rapport + courbe ROC ---
    write_evaluation_report(EVALUATION_REPORT_PATH, best_params, results, best_name)
    plot_roc_curve(results, ROC_CURVE_PATH)

    # --- 6. Sauvegarde du modele retenu + du scaler ---
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(preprocessor.scaler, SCALER_PATH)

    print(f"\nMeilleur modele : {best_name} (AUC-ROC = {best_auc:.4f})")
    print(f"Modele sauvegarde dans : {MODEL_PATH}")
    print(f"Scaler sauvegarde dans : {SCALER_PATH}")
    print(f"\nModele sauvegarde avec AUC-ROC = {best_auc:.2f}")


if __name__ == "__main__":
    main()
