
from config import MAX_STAT

def apply_rata_swap(board, x, y, owner, rows, cols):
    if not board[x][y] or board[x][y][0] != owner:
        return
    card = board[x][y][1]
    if getattr(card, 'special', None) != 'rata':
        return

    directions = [(-1, 0, 'up', 'down'), (1, 0, 'down', 'up'),
                  (0, -1, 'left', 'right'), (0, 1, 'right', 'left')]

    for dx, dy, my_side, opp_side in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and board[nx][ny]:
            n_owner, n_card = board[nx][ny]
            if n_owner != owner:
                my_val = getattr(card, my_side)
                opp_val = getattr(n_card, opp_side)
                setattr(card, my_side, opp_val)
                setattr(n_card, opp_side, my_val)

def apply_bandido_attack(board, x, y, owner, rows, cols):
    if not board[x][y] or board[x][y][0] != owner:
        return
    card = board[x][y][1]
    if getattr(card, 'special', None) != 'bandido':
        return

    directions = [(-1, 0, 'up', 'down'), (1, 0, 'down', 'up'),
                  (0, -1, 'left', 'right'), (0, 1, 'right', 'left')]

    for dx, dy, my_side, opp_side in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and board[nx][ny]:
            n_owner, n_card = board[nx][ny]
            if n_owner != owner:
                setattr(n_card, opp_side, max(0, getattr(n_card, opp_side) - 1))
                setattr(card, my_side, min(MAX_STAT, getattr(card, my_side) + 1))

def apply_bomb_trigger(board, bombs, x, y, owner, rows, cols):
    bomb_count = bombs.pop((x, y), 0)
    if bomb_count <= 0 or not board[x][y]:
        return

    card = board[x][y][1]
    card.up = max(0, card.up - bomb_count)
    card.down = max(0, card.down - bomb_count)
    card.left = max(0, card.left - bomb_count)
    card.right = max(0, card.right - bomb_count)

    directions = [(-1, 0, 'up', 'down'), (1, 0, 'down', 'up'),
                  (0, -1, 'left', 'right'), (0, 1, 'right', 'left')]
    for dx, dy, my_side, opp_side in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and board[nx][ny]:
            n_owner, n_card = board[nx][ny]
            if n_owner != owner:
                if getattr(n_card, opp_side) > getattr(card, my_side):
                    board[x][y] = (n_owner, card)
                    break

def apply_bombardero_bombs(board, bombs, x, y, owner, rows, cols):
    if not board[x][y] or board[x][y][0] != owner:
        return
    card = board[x][y][1]
    if getattr(card, 'special', None) != 'bombardero':
        return

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and board[nx][ny] is None:
            bombs[(nx, ny)] = bombs.get((nx, ny), 0) + 1

def _grow_hand_aliens(hand):
    for card in hand:
        if getattr(card, 'special', None) == 'alien':
            card.up = min(MAX_STAT, card.up + 1)
            card.down = min(MAX_STAT, card.down + 1)
            card.left = min(MAX_STAT, card.left + 1)
            card.right = min(MAX_STAT, card.right + 1)

def apply_alien_growth(hand_blue, hand_red):
    # Las cartas alien solo crecen mientras siguen en la mano/mazo (sin jugar).
    # Una vez colocadas en el tablero, dejan de subir de nivel.
    _grow_hand_aliens(hand_blue)
    _grow_hand_aliens(hand_red)

def process_captures_from_new_card(board, x, y, owner, rows, cols):
    if not board[x][y] or board[x][y][0] != owner:
        return
    curr_card = board[x][y][1]
    directions = [(-1, 0, 'up', 'down'), (1, 0, 'down', 'up'),
                  (0, -1, 'left', 'right'), (0, 1, 'right', 'left')]

    for dx, dy, my_side, opp_side in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and board[nx][ny]:
            n_owner, n_card = board[nx][ny]
            if n_owner != owner:
                if getattr(curr_card, my_side) > getattr(n_card, opp_side):
                    board[nx][ny] = (owner, n_card)

def simulate_captures(board, x, y, owner, rows, cols):
    apply_rata_swap(board, x, y, owner, rows, cols)
    apply_bandido_attack(board, x, y, owner, rows, cols)
    process_captures_from_new_card(board, x, y, owner, rows, cols)