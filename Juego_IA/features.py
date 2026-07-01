# features.py
"""
Modulo compartido de "ingenieria de caracteristicas" (feature engineering).

Convierte un estado del juego (tablero + minas del Bombardero + jugada
candidata) en un vector numerico que puede usar un modelo de scikit-learn.
Este mismo modulo lo usan:

  - train_model.py  -> para reconstruir ejemplos de entrenamiento a partir
                        del CSV generado por data_logger.py
  - ml_agent.py      -> para evaluar, en tiempo real, cada jugada candidata
                        de la IA con el modelo ya entrenado

Es fundamental que ambos usen EXACTAMENTE la misma codificacion, o el modelo
entrenado no tendria sentido al aplicarlo en el juego.
"""
import copy

from models import Card
import engine
import ai as ai_module

MAX_STAT = 10
MAX_BOMBS = 4  # tope razonable para normalizar el conteo de minas por casilla
SPECIALS = ["comun", "rata", "alien", "bandido", "bombardero"]
SPECIAL_INDEX = {s: i for i, s in enumerate(SPECIALS)}


def card_from_dict(d):
    """Reconstruye un objeto Card a partir del diccionario guardado en el CSV."""
    return Card(d["up"], d["down"], d["left"], d["right"],
                d.get("name", "?"), special=d.get("special"))


def reconstruct_board(board_cells, rows, cols):
    """
    board_cells: lista plana (row-major) de longitud rows*cols, cada elemento
    es None o un dict {"owner","up","down","left","right","special"}.
    Devuelve el tablero en el mismo formato que usa engine.py:
    board[i][j] = (owner, Card) o None.
    """
    board = [[None] * cols for _ in range(rows)]
    idx = 0
    for i in range(rows):
        for j in range(cols):
            cell = board_cells[idx]
            idx += 1
            if cell is not None:
                board[i][j] = (cell["owner"], card_from_dict(cell))
    return board


def board_to_cells(board, rows, cols):
    """Inverso de reconstruct_board: usado por data_logger para serializar."""
    cells = []
    for i in range(rows):
        for j in range(cols):
            cell = board[i][j]
            if cell is None:
                cells.append(None)
            else:
                owner, card = cell
                cells.append({
                    "owner": owner, "up": card.up, "down": card.down,
                    "left": card.left, "right": card.right, "special": card.special
                })
    return cells


def bombs_to_list(bombs):
    """dict {(row,col): count} -> lista serializable en JSON."""
    return [{"row": r, "col": c, "count": cnt} for (r, c), cnt in bombs.items()]


def reconstruct_bombs(bombs_list):
    """Inverso de bombs_to_list."""
    return {(item["row"], item["col"]): item["count"] for item in bombs_list}


def encode_card_stats(card):
    """9 dimensiones: 4 valores normalizados + one-hot de personaje especial."""
    vec = [card.up / MAX_STAT, card.down / MAX_STAT,
           card.left / MAX_STAT, card.right / MAX_STAT]
    onehot = [0.0] * len(SPECIALS)
    if card.special in SPECIAL_INDEX:
        onehot[SPECIAL_INDEX[card.special]] = 1.0
    return vec + onehot


def encode_board_state(board, bombs, mover, rows, cols):
    """
    rows*cols*6 dimensiones. Por casilla:
      - ocupada:  [dueno_relativo, up, down, left, right, 0.0]
      - vacia:    [0, 0, 0, 0, 0, minas_normalizadas]
    Incluir las minas es importante porque una casilla vacia "minada" por el
    Bombardero no es una jugada neutral: coloca ahi y tu carta pierde stats.
    """
    feats = []
    for i in range(rows):
        for j in range(cols):
            cell = board[i][j]
            if cell is None:
                bomb_count = bombs.get((i, j), 0) if bombs else 0
                feats.extend([0.0, 0.0, 0.0, 0.0, 0.0, min(bomb_count, MAX_BOMBS) / MAX_BOMBS])
            else:
                owner, card = cell
                owner_rel = 1.0 if owner == mover else -1.0
                feats.extend([owner_rel, card.up / MAX_STAT, card.down / MAX_STAT,
                              card.left / MAX_STAT, card.right / MAX_STAT, 0.0])
    return feats


def encode_move_position(row, col, rows, cols):
    """rows*cols dimensiones: one-hot de la casilla elegida."""
    onehot = [0.0] * (rows * cols)
    onehot[row * cols + col] = 1.0
    return onehot


def heuristic_delta(board, bombs, row, col, mover, card, rows, cols):
    """
    Cuanto mejora (o empeora) la heuristica evaluate_board de ai.py si se
    coloca esa carta en esa casilla, orientado desde el punto de vista de
    'mover' (positivo = bueno para quien mueve). Incluye el disparo de una
    posible mina en esa casilla, igual que en una partida real.
    """
    before = ai_module.evaluate_board(board, rows, cols)
    trial = copy.deepcopy(board)
    trial_bombs = copy.deepcopy(bombs) if bombs else {}
    trial[row][col] = (mover, copy.deepcopy(card))
    engine.apply_bomb_trigger(trial, trial_bombs, row, col, mover, rows, cols)
    engine.simulate_captures(trial, row, col, mover, rows, cols)
    after = ai_module.evaluate_board(trial, rows, cols)
    sign = 1.0 if mover == "Rojo" else -1.0
    return (after - before) * sign


def build_feature_vector(board, bombs, mover, hand_mover_size, hand_opp_size,
                          row, col, card, rows, cols):
    """
    Vector final para una jugada candidata (mover coloca `card` en (row,col)).
    Dimension total = rows*cols*6 + rows*cols + 9 + 1 + 1 + 1
    Para 4x5 => 120 + 20 + 9 + 1 + 1 + 1 = 152
    """
    feats = []
    feats.extend(encode_board_state(board, bombs, mover, rows, cols))
    feats.extend(encode_move_position(row, col, rows, cols))
    feats.extend(encode_card_stats(card))
    feats.append(heuristic_delta(board, bombs, row, col, mover, card, rows, cols) / MAX_STAT)
    feats.append(hand_mover_size / 8.0)
    feats.append(hand_opp_size / 8.0)
    return feats


def feature_dim(rows=4, cols=5):
    return rows * cols * 6 + rows * cols + 9 + 1 + 1 + 1