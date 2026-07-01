# data_logger.py
"""
Registra las jugadas del jugador humano (Azul) durante una partida y las
guarda en un archivo CSV (human_games_dataset.csv) al terminar la partida.

Cada fila del CSV representa UNA jugada humana:
  - el estado del tablero justo ANTES de esa jugada (board_json)
  - las minas del Bombardero activas en ese momento (bombs_json)
  - la mano del humano en ese momento, incluyendo la carta que jugo (hand_json)
  - cuantas cartas le quedaban a la IA (hand_size_opp)
  - la casilla elegida (row, col) y el indice de la carta elegida en su mano
    (card_idx, indice dentro de hand_json)
  - el resultado final de esa partida (result: 1 = gano el humano,
    0 = empate, -1 = perdio el humano)

El resultado se agrega recien al final de la partida porque no se conoce
antes. Este CSV es el "dataset generado con jugadas humanas" que pide el
enunciado, y es la entrada de train_model.py.
"""
import csv
import json
import os
import time
from pathlib import Path

from features import bombs_to_list

CSV_PATH = str(Path(__file__).resolve().parent / "human_games_dataset.csv")
FIELDNAMES = ["game_id", "move_number", "board_json", "bombs_json", "hand_json",
              "hand_size_opp", "row", "col", "card_idx", "result"]


class GameLogger:
    def __init__(self, csv_path=CSV_PATH):
        self.csv_path = csv_path
        self.pending = []
        self.game_id = None
        self.move_number = 0

    def start_game(self):
        """Llamar al iniciar cada partida nueva."""
        self.game_id = f"g{int(time.time() * 1000)}"
        self.move_number = 0
        self.pending = []

    def log_human_move(self, board, bombs, hand_blue, hand_red_size, row, col, card_idx, rows, cols):
        """
        Llamar justo ANTES de quitar la carta de hand_blue y colocarla en el
        tablero (es decir, con el estado tal como lo vio el humano al decidir).
        """
        board_cells = []
        for i in range(rows):
            for j in range(cols):
                cell = board[i][j]
                if cell is None:
                    board_cells.append(None)
                else:
                    owner, card = cell
                    board_cells.append({
                        "owner": owner, "up": card.up, "down": card.down,
                        "left": card.left, "right": card.right, "special": card.special
                    })

        hand_json = [
            {"up": c.up, "down": c.down, "left": c.left, "right": c.right,
             "special": c.special, "name": c.name}
            for c in hand_blue
        ]

        self.move_number += 1
        self.pending.append({
            "game_id": self.game_id,
            "move_number": self.move_number,
            "board_json": json.dumps(board_cells),
            "bombs_json": json.dumps(bombs_to_list(bombs or {})),
            "hand_json": json.dumps(hand_json),
            "hand_size_opp": hand_red_size,
            "row": row,
            "col": col,
            "card_idx": card_idx,
            "result": None,
        })

    def finalize_game(self, azul_score, rojo_score):
        """Llamar al terminar la partida, con el conteo final de casillas."""
        if azul_score > rojo_score:
            result = 1
        elif azul_score < rojo_score:
            result = -1
        else:
            result = 0

        for row in self.pending:
            row["result"] = result

        self._flush()

    def discard_game(self):
        """Por si la partida se cierra sin terminar (no se guarda)."""
        self.pending = []

    def discard_last_move(self):
        """Elimina la ultima jugada humana pendiente, por ejemplo al usar deshacer."""
        if self.pending:
            self.pending.pop()

    def _flush(self):
        if not self.pending:
            return
        file_exists = os.path.isfile(self.csv_path)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            for row in self.pending:
                writer.writerow(row)
        self.pending = []