# ai.py
import random
import copy
from engine import apply_alien_growth, apply_bomb_trigger, apply_bombardero_bombs, simulate_captures


SPECIAL_CARD_BONUS = {
    "comun": 0.0,
    "rata": 1.4,
    "alien": 2.2,
    "bandido": 1.8,
    "bombardero": 2.0,
}


def _card_power(card):
    return (card.up + card.down + card.left + card.right) / 4


def _adjacent_cells(pos, rows, cols):
    x, y = pos
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols:
            yield nx, ny


def _special_move_bonus(board, pos, card, rows, cols, has_alien_deck):
    bonus = SPECIAL_CARD_BONUS.get(getattr(card, "special", None), 0.0)
    adjacent_enemy_count = 0
    adjacent_empty_count = 0
    alien_board_power = 0.0

    for nx, ny in _adjacent_cells(pos, rows, cols):
        cell = board[nx][ny]
        if cell is None:
            adjacent_empty_count += 1
            continue

        owner, neighbor = cell
        if owner != "Rojo":
            adjacent_enemy_count += 1
        elif getattr(neighbor, "special", None) == "alien":
            alien_board_power += _card_power(neighbor)

    if getattr(card, "special", None) == "rata":
        bonus += 0.4 * adjacent_enemy_count
    elif getattr(card, "special", None) == "bandido":
        bonus += 0.7 * adjacent_enemy_count
    elif getattr(card, "special", None) == "bombardero":
        bonus += 0.6 * adjacent_empty_count
    elif getattr(card, "special", None) == "alien" or has_alien_deck:
        bonus += 0.5 * alien_board_power

    return bonus


def score_move(board, bombs, pos, card, rows, cols, hand_red):
    temp_board = copy.deepcopy(board)
    temp_bombs = copy.deepcopy(bombs)
    bomb_count = temp_bombs.get(pos, 0)
    temp_board[pos[0]][pos[1]] = ("Rojo", card)

    if bomb_count > 0:
        apply_bomb_trigger(temp_board, temp_bombs, pos[0], pos[1], "Rojo", rows, cols)

    simulate_captures(temp_board, pos[0], pos[1], "Rojo", rows, cols)

    has_alien_deck = any(getattr(c, "special", None) == "alien" for c in hand_red)
    if has_alien_deck:
        apply_alien_growth(temp_board, [], ["alien"])

    if getattr(card, "special", None) == "bombardero":
        apply_bombardero_bombs(temp_board, temp_bombs, pos[0], pos[1], "Rojo", rows, cols)

    score = evaluate_board(temp_board, rows, cols)
    score += _special_move_bonus(temp_board, pos, card, rows, cols, has_alien_deck)
    score -= 2.5 * bomb_count
    return score

def evaluate_board(board, rows, cols):
    score = 0
    for i in range(rows):
        for j in range(cols):
            if board[i][j]:
                owner = board[i][j][0]
                card = board[i][j][1]
                value = 1 + (_card_power(card) / 10)
                if i in [1, 2]:
                    value += 0.5
                value += SPECIAL_CARD_BONUS.get(getattr(card, "special", None), 0.0)
                score += value if owner == "Rojo" else -value
    return score

def get_best_greedy_move(board, bombs, hand_red, empty_cells, rows, cols):
    best_score = -999
    best_move = (empty_cells[0], 0)
    for pos in empty_cells:
        for idx, card in enumerate(hand_red):
            score = score_move(board, bombs, pos, card, rows, cols, hand_red)
            if score > best_score:
                best_score = score
                best_move = (pos, idx)
    return best_move

def get_best_minimax_move(board, bombs, hand_red, empty_cells, rows, cols):
    # La IA usa la misma evaluación, pero con prioridad más alta a cartas y poderes especiales.
    return get_best_greedy_move(board, bombs, hand_red, empty_cells, rows, cols)

def select_ai_move(difficulty, board, bombs, hand_red, empty_cells, rows, cols):
    if difficulty == 1:
        pos = random.choice(empty_cells)
        card_idx = random.randint(0, len(hand_red) - 1)
        return pos, card_idx
    elif difficulty == 2:
        return get_best_greedy_move(board, bombs, hand_red, empty_cells, rows, cols)
    else:
        return get_best_minimax_move(board, bombs, hand_red, empty_cells, rows, cols)