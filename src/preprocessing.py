"""
Pretraitement des donnees de detection de fraude.

Pourquoi une classe et pas des fonctions separees ?
Parce que plusieurs etapes partagent le meme etat (le DataFrame charge, le
scaler entraine, X_train/X_test...). Une classe permet de garder cet etat
entre les appels de methodes sans le repasser en parametre a chaque fois.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

from src.config import RANDOM_STATE, TEST_SIZE, TARGET_COLUMN, COLUMNS_TO_SCALE


class FraudPreprocessor:
    """Regroupe toutes les etapes de preparation des donnees avant entrainement."""

    def __init__(self):
        self.df = None
        self.scaler = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

    def load_data(self, path):
        """
        Charge le CSV et affiche un resume rapide.

        On affiche le shape et le % de fraudes tout de suite : sur ce dataset,
        les fraudes representent environ 0.17% des lignes. C'est un dataset
        tres desequilibre (imbalanced), ce qui justifiera l'usage de SMOTE
        plus loin.
        """
        print(f"Chargement des donnees depuis : {path}")
        self.df = pd.read_csv(path)

        n_rows, n_cols = self.df.shape
        n_fraud = (self.df[TARGET_COLUMN] == 1).sum()
        pct_fraud = n_fraud / n_rows * 100

        print(f"Shape du dataset : {n_rows} lignes, {n_cols} colonnes")
        print(f"Nombre de fraudes : {n_fraud} ({pct_fraud:.3f}% du total)")

        return self.df

    def explore_data(self):
        """
        Affiche des statistiques de base pour se familiariser avec les donnees.

        describe() montre min/max/moyenne/quartiles de chaque colonne numerique.
        value_counts() montre la repartition exacte des classes (0 = legitime, 1 = fraude).
        """
        if self.df is None:
            raise ValueError("Aucune donnee chargee. Appelle load_data() d'abord.")

        print("\n--- Statistiques descriptives ---")
        print(self.df.describe())

        print("\n--- Repartition des classes (Class) ---")
        print(self.df[TARGET_COLUMN].value_counts())
        print(self.df[TARGET_COLUMN].value_counts(normalize=True) * 100)

    def prepare_features(self):
        """
        Separe les features (X) de la cible (y), puis split train/test.

        stratify=y est important : il garantit que le train set et le test set
        ont la meme proportion de fraudes que le dataset original. Sans ca,
        un split aleatoire pourrait par hasard mettre tres peu (ou zero) de
        fraudes dans le test set, vu qu'elles sont rares.
        """
        if self.df is None:
            raise ValueError("Aucune donnee chargee. Appelle load_data() d'abord.")

        X = self.df.drop(columns=[TARGET_COLUMN])
        y = self.df[TARGET_COLUMN]

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=y,
        )

        print(f"\nTrain set : {self.X_train.shape[0]} lignes "
              f"({(self.y_train == 1).sum()} fraudes)")
        print(f"Test set  : {self.X_test.shape[0]} lignes "
              f"({(self.y_test == 1).sum()} fraudes)")

        return self.X_train, self.X_test, self.y_train, self.y_test

    def scale_features(self):
        """
        Normalise uniquement les colonnes Amount et Time avec StandardScaler.

        Pourquoi seulement ces deux colonnes ? Le dataset Kaggle fournit les
        colonnes V1..V28 deja transformees par PCA (donc deja sur une echelle
        comparable). Amount et Time, elles, sont dans leurs unites brutes
        (euros, secondes) et doivent etre standardisees (moyenne 0, ecart-type 1)
        pour ne pas dominer les autres features dans le modele.

        Le scaler est entraine (fit) uniquement sur le train set, puis applique
        (transform) au train ET au test, pour eviter une fuite de donnees
        (data leakage) depuis le test set.
        """
        if self.X_train is None or self.X_test is None:
            raise ValueError("Appelle prepare_features() avant scale_features().")

        self.scaler = StandardScaler()

        self.X_train = self.X_train.copy()
        self.X_test = self.X_test.copy()

        self.X_train[COLUMNS_TO_SCALE] = self.scaler.fit_transform(self.X_train[COLUMNS_TO_SCALE])
        self.X_test[COLUMNS_TO_SCALE] = self.scaler.transform(self.X_test[COLUMNS_TO_SCALE])

        print(f"\nColonnes normalisees : {COLUMNS_TO_SCALE}")

        return self.X_train, self.X_test

    def apply_smote(self):
        """
        Reequilibre le train set avec SMOTE (Synthetic Minority Over-sampling).

        Pourquoi SMOTE ? Avec seulement ~0.17% de fraudes, un modele entraine
        tel quel aurait tendance a predire "legitime" presque toujours (ca
        suffirait pour avoir 99.8% de bonne reponse, sans jamais detecter de
        fraude). SMOTE cree de nouveaux exemples synthetiques de fraude
        (en interpolant entre des fraudes existantes) pour equilibrer les
        classes dans le train set.

        Important : on applique SMOTE seulement sur le train set, jamais sur
        le test set, pour evaluer le modele sur une distribution realiste.
        """
        if self.X_train is None or self.y_train is None:
            raise ValueError("Appelle prepare_features() avant apply_smote().")

        print(f"\nAvant SMOTE : {self.y_train.value_counts().to_dict()}")

        smote = SMOTE(random_state=RANDOM_STATE)
        self.X_train, self.y_train = smote.fit_resample(self.X_train, self.y_train)

        print(f"Apres SMOTE : {pd.Series(self.y_train).value_counts().to_dict()}")

        return self.X_train, self.y_train
