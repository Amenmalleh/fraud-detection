# Fraud Detection - Phase 1

Systeme de detection de fraude bancaire base sur le dataset Kaggle
[Credit Card Fraud Detection](https://www.kaggle.com/mlg-ulb/creditcardfraud).

## Structure du projet

```
fraud-detection/
├── data/               # placer creditcard.csv ici (optionnel, voir config.py)
├── notebooks/
│   └── 01_eda.ipynb    # exploration des donnees
├── src/
│   ├── config.py       # chemins et hyperparametres
│   ├── preprocessing.py# classe FraudPreprocessor
│   └── train.py        # entrainement et evaluation des modeles
├── models/             # modeles sauvegardes (.pkl)
└── requirements.txt
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Dataset

Le dataset `creditcard.csv` est attendu dans `data/creditcard.csv` (voir
`KAGGLE_DATASET_PATH` dans `src/config.py`).

## Utilisation

### Exploration des donnees

Ouvre `notebooks/01_eda.ipynb` avec Jupyter :

```bash
jupyter notebook notebooks/01_eda.ipynb
```

### Entrainement des modeles

```bash
python -m src.train
```

Ce script va :
1. Charger et explorer les donnees
2. Separer train/test (stratifie)
3. Normaliser les colonnes `Amount` et `Time`
4. Rééquilibrer le train set avec SMOTE
5. Entrainer un Random Forest et un XGBoost
6. Evaluer les deux modeles (classification report, matrice de confusion, AUC-ROC)
7. Sauvegarder le meilleur modele (`models/fraud_model.pkl`) et le scaler (`models/scaler.pkl`)

A la fin, le script affiche :

```
Modele sauvegarde avec AUC-ROC = X.XX
```

## Pourquoi ces choix techniques ?

- **AUC-ROC plutot que l'accuracy** : le dataset est tres desequilibre
  (~0.17% de fraudes). Un modele qui predit toujours "legitime" aurait
  99.8% d'accuracy sans jamais detecter de fraude. L'AUC-ROC mesure la
  capacite du modele a separer les deux classes, peu importe le desequilibre.
- **SMOTE** : cree des exemples synthetiques de fraude pour equilibrer le
  train set, appliqué uniquement sur le train (jamais sur le test) pour
  garder une evaluation realiste.
- **StandardScaler sur Amount/Time seulement** : les colonnes V1..V28 sont
  deja issues d'une transformation PCA et sont sur une echelle comparable ;
  seules Amount et Time sont dans leurs unites brutes.
- **Random Forest + XGBoost** : deux modeles d'ensemble robustes aux donnees
  tabulaires desequilibrees, on garde celui avec le meilleur AUC-ROC.
