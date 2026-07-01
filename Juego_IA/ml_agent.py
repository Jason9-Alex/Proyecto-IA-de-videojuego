# ml_agent.py
"""
Agente adaptativo (Nivel IV de dificultad).

En vez de una heuristica fija, usa el modelo de scikit-learn entrenado por
train_model.py (ml_model.pkl + scaler.pkl) para elegir, entre todas las
jugadas legales, la que el modelo considera mas "parecida a como jugaria un
humano". Se calcula la probabilidad de la clase "elegida" para cada jugada
candidata y se toma la de mayor probabilidad.

Si el modelo todavia no fue entrenado (no existen los archivos .pkl), este
agente cae automaticamente al modo Greedy para que el juego nunca se rompa.
"""
import os
import joblib

from features import build_feature_vector

MODEL_PATH = "ml_model.pkl"
SCALER_PATH = "scaler.pkl"

_model = None
_scaler = None
_load_attempted = False


def _load_model():
    global _model, _scaler, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True
    if os.path.isfile(MODEL_PATH) and os.path.isfile(SCALER_PATH):
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)


def is_available():
    """Util para que la GUI avise si el modo adaptativo ya tiene modelo entrenado."""
    _load_model()
    return _model is not None


def get_best_adaptive_move(board, bombs, hand_red, empty_cells, rows, cols, hand_opp_size):
    """
    mover se asume 'Rojo' (la IA).
    Devuelve (pos, card_idx) igual que las demas funciones de ai.py.
    """
    _load_model()

    if _model is None:
        # Sin modelo entrenado todavia -> se usa Greedy como respaldo seguro.
        from ai import get_best_greedy_move
        return get_best_greedy_move(board, bombs, hand_red, empty_cells, rows, cols)

    best_score = -1.0
    best_move = (empty_cells[0], 0)

    for (i, j) in empty_cells:
        for idx, card in enumerate(hand_red):
            feat = build_feature_vector(board, bombs, "Rojo", len(hand_red), hand_opp_size,
                                         i, j, card, rows, cols)
            X = _scaler.transform([feat])
            proba = _model.predict_proba(X)[0][1]  # prob. de clase "elegida"
            if proba > best_score:
                best_score = proba
                best_move = ((i, j), idx)

    return best_move