# models.py

class Card:
    def __init__(self, up, down, left, right, name, special=None):
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.name = name
        self.special = special  # "rata", "alien", "bandido", "bombardero" o None