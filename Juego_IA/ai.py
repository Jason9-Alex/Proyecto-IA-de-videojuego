# ai.py
import random
import copy
import engine
from engine import simulate_captures

def evaluate_board(board, rows, cols):
    score = 0
    for i in range(rows):
        for j in range(cols):
            if board[i][j]:
                owner = board[i][j][0]
                value = 2 if i in [1, 2] else 1
                score += value if owner == "Rojo" else -value
    return score

def get_best_greedy_move(board, bombs, hand_red, empty_cells, rows, cols):
    best_score = -999
    best_move = (empty_cells[0], 0)
    for pos in empty_cells:
        for idx, card in enumerate(hand_red):
            temp_board = copy.deepcopy(board)
            temp_bombs = copy.deepcopy(bombs)
            temp_board[pos[0]][pos[1]] = ("Rojo", copy.deepcopy(card))
            # Si la casilla tenia una mina del Bombardero, se dispara igual
            # que en una partida real antes de resolver capturas.
            engine.apply_bomb_trigger(temp_board, temp_bombs, pos[0], pos[1], "Rojo", rows, cols)
            simulate_captures(temp_board, pos[0], pos[1], "Rojo", rows, cols)
            score = evaluate_board(temp_board, rows, cols)
            if score > best_score:
                best_score = score
                best_move = (pos, idx)
    return best_move

def get_best_minimax_move(board, bombs, hand_red, empty_cells, rows, cols):
    # Por el momento comparte lógica con Greedy, escalable a Alpha-Beta Pruning
    return get_best_greedy_move(board, bombs, hand_red, empty_cells, rows, cols)

def select_ai_move(difficulty, board, bombs, hand_red, empty_cells, rows, cols, hand_blue_size=None):
    if difficulty == 1:
        pos = random.choice(empty_cells)
        card_idx = random.randint(0, len(hand_red) - 1)
        return pos, card_idx
    elif difficulty == 2:
        return get_best_greedy_move(board, bombs, hand_red, empty_cells, rows, cols)
    elif difficulty == 3:
        return get_best_minimax_move(board, bombs, hand_red, empty_cells, rows, cols)
    else:
        # Nivel IV: modo adaptativo (Machine Learning), entrenado con jugadas humanas
        import ml_agent
        opp_size = hand_blue_size if hand_blue_size is not None else len(hand_red)
        return ml_agent.get_best_adaptive_move(board, bombs, hand_red, empty_cells, rows, cols, opp_size)