# config.py

DECK_DEFS = {
    "comun": [
        (6, 7, 6, 7),
        (7, 6, 7, 6),
        (6, 7, 7, 6),
        (7, 6, 6, 7),
    ],
    "rata": [
        (6, 6, 7, 1),
        (6, 6, 1, 7),
        (7, 1, 6, 6),
        (1, 7, 6, 6),
    ],
    "alien": [
        (2, 3, 2, 4),
        (2, 4, 2, 3),
        (4, 2, 3, 2),
        (3, 2, 4, 2),
    ],
    "bandido": [
        (5, 6, 6, 3),
        (6, 5, 6, 3),
        (5, 6, 3, 6),
        (6, 5, 3, 6),
    ],
    "bombardero": [
        (6, 4, 5, 5),
        (5, 5, 4, 6),
        (4, 6, 5, 5),
        (5, 5, 6, 4),
    ],
}

DECK_LABELS = {
    "comun": "Común",
    "rata": "La Rata",
    "alien": "El Alien",
    "bandido": "El Bandido",
    "bombardero": "El Bombardero",
}

DECK_ICONS = {
    "comun": "⚔️",
    "rata": "🐀",
    "alien": "👽",
    "bandido": "🔪",
    "bombardero": "💣",
}

MAX_STAT = 10

# PALETA VISUAL "LEGIONS"
BG_DARK = "#0c0a12"
BG_PANEL = "#181620"
BG_PANEL_LIGHT = "#221e2a"
BORDER_GOLD = "#c9a86a"
BORDER_GOLD_DIM = "#7a6438"
TEXT_GOLD = "#e6d7b8"
TEXT_RUNE = "#ffd700"
TEXT_MUTED = "#a8978a"

BLUE_BG = "#0e1c36"
BLUE_BORDER = "#4a6082"
BLUE_TEXT = "#78befe"
BLUE_ACCENT = "#5ca8ff"

RED_BG = "#360e0e"
RED_BORDER = "#824a4a"
RED_TEXT = "#ff8e8e"
RED_ACCENT = "#ff5c5c"

SELECT_GOLD = "#ffd700"
SELECT_BG = "#3a2f10"

FONT_TITLE = ("Georgia", 20, "bold")
FONT_SUBTITLE = ("Georgia", 12, "italic")
FONT_BANNER = ("Georgia", 14, "bold")
FONT_BTN = ("Georgia", 11, "bold")
FONT_BTN_SUB = ("Georgia", 9, "italic")
FONT_CARD_NAME = ("Georgia", 10, "bold")
FONT_CARD_NUM = ("Georgia", 12, "bold")
FONT_STATUS = ("Georgia", 13, "italic")