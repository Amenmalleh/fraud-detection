"""
Modeles Pydantic : definissent la forme des donnees qui entrent et sortent de l'API.

Pourquoi Pydantic (via FastAPI) ?
- Validation automatique : si un champ a un mauvais type (ex: texte au lieu de
  nombre), FastAPI renvoie une erreur 422 claire AVANT que notre code de
  prediction ne s'execute.
- Documentation automatique : ces classes generent le schema Swagger visible
  sur /docs, donc pas besoin de documenter les champs a la main.
- Valeurs par defaut : permet de tester l'API depuis /docs sans remplir
  les 30 champs a la main (V1..V28 sont rarement connues a l'avance par un humain).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TransactionInput(BaseModel):
    """
    Une transaction a analyser.

    V1..V28 viennent d'une transformation PCA (anonymisation) appliquee par
    Kaggle sur les donnees originales : on ne connait pas leur sens metier,
    mais leurs valeurs sont centrees autour de 0 pour une transaction "moyenne".
    On utilise donc 0.0 comme valeur par defaut realiste.
    """

    Time: float = Field(default=0.0, description="Secondes ecoulees depuis la premiere transaction du dataset")
    V1: float = 0.0
    V2: float = 0.0
    V3: float = 0.0
    V4: float = 0.0
    V5: float = 0.0
    V6: float = 0.0
    V7: float = 0.0
    V8: float = 0.0
    V9: float = 0.0
    V10: float = 0.0
    V11: float = 0.0
    V12: float = 0.0
    V13: float = 0.0
    V14: float = 0.0
    V15: float = 0.0
    V16: float = 0.0
    V17: float = 0.0
    V18: float = 0.0
    V19: float = 0.0
    V20: float = 0.0
    V21: float = 0.0
    V22: float = 0.0
    V23: float = 0.0
    V24: float = 0.0
    V25: float = 0.0
    V26: float = 0.0
    V27: float = 0.0
    V28: float = 0.0
    Amount: float = Field(default=100.0, description="Montant de la transaction en euros")


class PredictionOutput(BaseModel):
    """Reponse renvoyee par /predict."""

    is_fraud: bool = Field(description="True si confidence >= seuil de decision")
    confidence: float = Field(ge=0.0, le=1.0, description="Probabilite de fraude estimee par le modele (0 a 1)")
    transaction_id: str = Field(description="Identifiant de la transaction loggee en base")
    timestamp: datetime = Field(description="Date/heure de la prediction")


class FeatureImportance(BaseModel):
    """Une feature et son importance dans le modele (cf. ExplainOutput)."""

    feature: str = Field(description="Nom de la colonne (ex: V14)")
    importance: float = Field(ge=0.0, description="Importance de cette feature dans le modele")


class PredictionSummary(BaseModel):
    """Resume de la prediction, imbrique dans ExplainOutput."""

    is_fraud: bool
    confidence: float = Field(ge=0.0, le=1.0)


class ExplainOutput(BaseModel):
    """
    Reponse renvoyee par /explain.

    Note : "explanation" reflete l'importance GLOBALE des features pour le
    modele (model.feature_importances_), pas une contribution propre a cette
    transaction precise. Les Random Forest / XGBoost n'exposent pas nativement
    d'explication par prediction individuelle ; une vraie explication locale
    necessiterait une librairie dediee comme SHAP (cf. README).
    """

    prediction: PredictionSummary
    explanation: list[FeatureImportance] = Field(description="Top features les plus importantes du modele")
    interpretation: str = Field(description="Phrase resumant les features qui ont le plus pese sur la decision")
