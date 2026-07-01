# train_model.py
"""
Entrena, a partir de human_games_dataset.csv (generado jugando en modo
clasico con data_logger.py):

  1) Un modelo SUPERVISADO (RandomForestClassifier) que aprende a distinguir
     "jugadas que un humano elegiria" de "jugadas alternativas disponibles
     en ese mismo turno pero no elegidas". Esto es lo que despues usa
     ml_agent.py para el modo adaptativo.

  2) Un analisis NO SUPERVISADO (KMeans + PCA) sobre las jugadas realmente
     elegidas por humanos, para agrupar "estilos de juego" y graficarlos.

Uso:
    python train_model.py

Genera:
    ml_model.pkl   -> modelo entrenado (RandomForestClassifier)
    scaler.pkl     -> normalizador de features (StandardScaler)
    clusters.png   -> grafico de clusters de estilos de juego (PCA 2D)
"""
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, silhouette_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from features import reconstruct_board, reconstruct_bombs, card_from_dict, build_feature_vector

CSV_PATH = str(Path(__file__).resolve().parent / "human_games_dataset.csv")
ROWS, COLS = 4, 5
MAX_NEG_PER_MOVE = 6  # cuantas jugadas alternativas (negativas) se muestrean por turno
RANDOM_STATE = 42


def load_rows(csv_path=CSV_PATH):
    df = pd.read_csv(csv_path)
    return df


def build_dataset(df):
    """
    Convierte cada fila del CSV (una jugada humana) en:
      - 1 ejemplo positivo (label=1): la jugada que el humano realmente hizo
      - hasta MAX_NEG_PER_MOVE ejemplos negativos (label=0): otras jugadas
        legales disponibles en ese mismo turno que el humano NO eligio
    """
    X, y = [], []
    rng = random.Random(RANDOM_STATE)

    for _, row in df.iterrows():
        board_cells = json.loads(row["board_json"])
        bombs_list = json.loads(row["bombs_json"]) if "bombs_json" in row and pd.notna(row["bombs_json"]) else []
        hand = json.loads(row["hand_json"])
        board = reconstruct_board(board_cells, ROWS, COLS)
        bombs = reconstruct_bombs(bombs_list)
        mover = "Azul"
        hand_opp_size = int(row["hand_size_opp"])
        chosen_row, chosen_col, chosen_idx = int(row["row"]), int(row["col"]), int(row["card_idx"])

        empty_cells = [(i, j) for i in range(ROWS) for j in range(COLS) if board[i][j] is None]

        chosen_card = card_from_dict(hand[chosen_idx])
        feat_pos = build_feature_vector(board, bombs, mover, len(hand), hand_opp_size,
                                         chosen_row, chosen_col, chosen_card, ROWS, COLS)
        X.append(feat_pos)
        y.append(1)

        alternatives = [
            (i, j, idx) for (i, j) in empty_cells for idx in range(len(hand))
            if not (i == chosen_row and j == chosen_col and idx == chosen_idx)
        ]
        rng.shuffle(alternatives)
        for (i, j, idx) in alternatives[:MAX_NEG_PER_MOVE]:
            card = card_from_dict(hand[idx])
            feat_neg = build_feature_vector(board, bombs, mover, len(hand), hand_opp_size,
                                             i, j, card, ROWS, COLS)
            X.append(feat_neg)
            y.append(0)

    return np.array(X, dtype=float), np.array(y, dtype=int)


def train_supervised(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clf = RandomForestClassifier(
        n_estimators=300, max_depth=12, random_state=RANDOM_STATE, class_weight="balanced"
    )
    clf.fit(X_train_s, y_train)

    y_pred = clf.predict(X_test_s)
    print(f"Accuracy en test: {accuracy_score(y_test, y_pred):.3f}")
    print(classification_report(y_test, y_pred, target_names=["no_elegida", "elegida"]))

    joblib.dump(clf, "ml_model.pkl")
    joblib.dump(scaler, "scaler.pkl")
    print("Modelo guardado en ml_model.pkl / scaler.pkl")
    return clf, scaler


def cluster_playstyles(X, y):
    """
    Agrupa (KMeans) las jugadas que el humano SI eligio, para detectar
    'estilos de juego' (por ejemplo: jugadas agresivas de alto valor vs.
    jugadas conservadoras en los bordes, uso de habilidades especiales, etc).
    """
    mask = y == 1
    X_pos = X[mask]
    if len(X_pos) < 8:
        print("Muy pocas jugadas humanas registradas todavia para clustering "
              "(se necesitan mas partidas jugadas en modo clasico).")
        return

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_pos)

    k = min(4, max(2, len(X_pos) // 5))
    kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    if len(set(labels)) > 1:
        sil = silhouette_score(X_scaled, labels)
        print(f"Silhouette score del clustering (k={k}): {sil:.3f}")

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(X_scaled)

    plt.figure(figsize=(7, 6))
    scatter = plt.scatter(coords[:, 0], coords[:, 1], c=labels, cmap="tab10", s=45, alpha=0.85)
    plt.title(f"Clusters de estilos de juego humano (k={k}, PCA 2D)")
    plt.xlabel("Componente principal 1")
    plt.ylabel("Componente principal 2")
    plt.legend(*scatter.legend_elements(), title="Cluster")
    plt.tight_layout()
    plt.savefig("clusters.png", dpi=150)
    plt.close()
    print("Grafico de clusters guardado en clusters.png")


def main():
    df = load_rows()
    print(f"Filas (jugadas humanas) cargadas del CSV: {len(df)}")

    X, y = build_dataset(df)
    print(f"Ejemplos construidos: {len(X)} "
          f"(positivos={int((y == 1).sum())}, negativos={int((y == 0).sum())})")

    train_supervised(X, y)
    cluster_playstyles(X, y)


if __name__ == "__main__":
    main()