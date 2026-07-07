# gui.py
import tkinter as tk
from tkinter import messagebox, ttk
import random
import copy
import subprocess
import sys
import threading
from pathlib import Path
from PIL import Image, ImageTk
import pygame

import engine
import ai
from models import Card
from data_logger import GameLogger
from config import *

class TripleTriadGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Legions - Triple Triad (4×5)")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        self.is_fullscreen = False
        self.center_window()
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.root.withdraw()
        self.difficulty = None
        self.deck_blue = None
        self.deck_red = None
        self.last_move = None
        self.asset_dir = Path(__file__).resolve().parent
        self.game_logger = GameLogger()
        self.choice_image_cache = {}
        self.card_image_cache = {}
        self.sound_cache = {}
        self.audio_ready = False
        self.model_training_in_progress = False
        self.init_audio()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.after(100, self.show_welcome_screen)

    def init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.audio_ready = True
        except Exception:
            self.audio_ready = False

    def schedule_model_retraining(self):
        if self.model_training_in_progress:
            return

        self.model_training_in_progress = True

        def run_training():
            try:
                subprocess.run(
                    [sys.executable, str(self.asset_dir / "train_model.py")],
                    cwd=str(self.asset_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except Exception as exc:
                print(f"Auto-entrenamiento fallo: {exc}")
            finally:
                self.model_training_in_progress = False
                try:
                    import ml_agent
                    ml_agent.refresh_model()
                except Exception:
                    pass

        threading.Thread(target=run_training, daemon=True).start()

    def get_card_sound_path(self, card):
        special = getattr(card, "special", None)
        if special == "comun":
            return self.asset_dir / "caballero comun.mp3"
        if special:
            return self.asset_dir / f"{special}.mp3"
        return None

    def play_card_sound(self, card):
        if not self.audio_ready:
            return

        sound_path = self.get_card_sound_path(card)
        if not sound_path or not sound_path.exists():
            return

        cache_key = str(sound_path)
        try:
            sound = self.sound_cache.get(cache_key)
            if sound is None:
                sound = pygame.mixer.Sound(cache_key)
                self.sound_cache[cache_key] = sound
            sound.play()
        except Exception:
            self.audio_ready = False

    def center_window(self, width=None, height=None):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if width is None:
            width = min(1520, max(1280, int(screen_w * 0.94)))
        if height is None:
            height = min(960, max(820, int(screen_h * 0.92)))
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def center_toplevel(self, window, width, height):
        window.update_idletasks()
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)

    def styled_dialog(self, title, width, height):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        width = min(width, screen_w - 40)
        height = min(height, screen_h - 80)
        dialog.geometry(f"{width}x{height}")
        dialog.configure(bg=BG_DARK, highlightbackground=BORDER_GOLD, highlightthickness=2)
        self.center_toplevel(dialog, width, height)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: self.root.quit())
        return dialog

    def gold_header(self, parent, text, sub=None, fg=TEXT_RUNE):
        tk.Label(parent, text=text, font=FONT_TITLE, fg=fg, bg=BG_DARK).pack(pady=(16, 4))
        rule = tk.Frame(parent, bg=BORDER_GOLD_DIM, height=2, width=320)
        rule.pack(pady=(0, 8))
        if sub:
            tk.Label(parent, text=sub, font=FONT_SUBTITLE, fg=TEXT_MUTED, bg=BG_DARK,
                     wraplength=400, justify="center").pack(pady=4)

    def styled_button(self, parent, text, command, primary=False, danger=False, width=20, height=2, font=FONT_BTN):
        if danger:
            bg, fg, active_bg = "#3d1414", RED_TEXT, "#5a1c1c"
        elif primary:
            bg, fg, active_bg = "#1c3d1c", "#9fffb0", "#27522a"
        else:
            bg, fg, active_bg = BG_PANEL_LIGHT, TEXT_GOLD, "#2e2838"
        btn = tk.Button(parent, text=text, width=width, height=height, bg=bg, fg=fg,
                        activebackground=active_bg, activeforeground=fg,
                        font=font, relief="ridge", bd=2,
                        highlightbackground=BORDER_GOLD_DIM, highlightthickness=1,
                        command=command, cursor="hand2")
        return btn

    def show_welcome_screen(self, next_action=None, duration=1600):
        if next_action is None:
            next_action = self.ask_difficulty

        splash = tk.Toplevel(self.root)
        splash.title("Legions")
        splash.geometry("520x300")
        splash.configure(bg=BG_DARK, highlightbackground=BORDER_GOLD, highlightthickness=2)
        splash.resizable(False, False)
        splash.transient(self.root)
        splash.grab_set()

        self.center_toplevel(splash, 520, 300)

        tk.Label(splash, text="Bienvenido a Legions", font=FONT_TITLE, fg=TEXT_RUNE, bg=BG_DARK).pack(pady=(44, 10))
        tk.Label(splash, text="Preparando el tablero y las fuerzas especiales...", font=FONT_SUBTITLE,
                 fg=TEXT_MUTED, bg=BG_DARK).pack(pady=(0, 24))

        bar = ttk.Progressbar(splash, mode="indeterminate", length=300)
        bar.pack(pady=12)
        bar.start(10)

        def finish():
            try:
                bar.stop()
                splash.grab_release()
                splash.destroy()
            finally:
                next_action()

        splash.after(duration, finish)

    def load_choice_image(self, deck_name, size=(96, 96)):
        cache_key = (deck_name, size)
        if cache_key in self.choice_image_cache:
            return self.choice_image_cache[cache_key]

        image_name = "caballero.jpg" if deck_name == "comun" else f"{deck_name}.jpg"
        image_path = self.asset_dir / image_name
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", size, color=BG_PANEL_LIGHT)
        
        resample = getattr(Image, "Resampling", Image).LANCZOS
        image.thumbnail(size, resample)
        photo = ImageTk.PhotoImage(image)
        self.choice_image_cache[cache_key] = photo
        return photo

    def create_choice_option(self, parent, variable, value, title, subtitle, accent_fg, on_select=None):
        option = tk.Frame(parent, bg=BG_PANEL, highlightbackground=BORDER_GOLD_DIM, highlightthickness=1)
        option.pack(fill="x", padx=18, pady=7)

        image = self.load_choice_image(value)
        image_label = tk.Label(option, image=image, bg=BG_PANEL)
        image_label.image = image
        image_label.pack(side="left", padx=10, pady=10)

        text_frame = tk.Frame(option, bg=BG_PANEL)
        text_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        rb = tk.Radiobutton(text_frame, text=title, variable=variable, value=value,
                            bg=BG_PANEL, fg=TEXT_GOLD, selectcolor=SELECT_BG,
                            font=FONT_BTN, activebackground=BG_PANEL_LIGHT,
                            activeforeground=TEXT_RUNE, anchor="w", justify="left",
                            indicatoron=True, relief="flat", bd=0, wraplength=280)
        rb.pack(anchor="w")

        subtitle_label = tk.Label(text_frame, text=subtitle, bg=BG_PANEL, fg=accent_fg,
                                  font=FONT_BTN_SUB, anchor="w", justify="left", wraplength=280)
        subtitle_label.pack(anchor="w", pady=(4, 0))

        def select_value(event=None):
            variable.set(value)
            if on_select:
                on_select(value)

        rb.config(command=select_value)

        for widget in (option, image_label, text_frame, rb, subtitle_label):
            widget.bind("<Button-1>", lambda e, v=value: select_value())

        return option

    def get_card_number(self, card):
        try:
            return int(card.name[1:])
        except (TypeError, ValueError, IndexError):
            return None

    def get_owner_display_deck(self, owner):
        if owner == "Azul" and self.deck_blue:
            return self.deck_blue[1]
        if owner == "Rojo" and self.deck_red:
            return self.deck_red[1]
        return None

    def load_deck_card_image(self, deck_name, card_index, size=(180, 270)):
        cache_key = (deck_name, card_index, size)
        if cache_key in self.card_image_cache:
            return self.card_image_cache[cache_key]

        if deck_name == "comun":
            image_path = self.asset_dir / "caballero.jpg"
        else:
            image_path = self.asset_dir / f"{deck_name}_8" / f"{deck_name}_{card_index}.jpg"
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", size, color=BG_PANEL_LIGHT)

        resample = getattr(Image, "Resampling", Image).LANCZOS
        image.thumbnail(size, resample)
        photo = ImageTk.PhotoImage(image)
        self.card_image_cache[cache_key] = photo
        return photo

    def load_card_image(self, card, size=(96, 64), display_deck_name=None):
        special = getattr(card, "special", None)
        deck_name = special if special else display_deck_name
        if not deck_name:
            return None

        card_index = self.get_card_number(card)
        if card_index is None or card_index < 1 or card_index > 8:
            return None

        return self.load_deck_card_image(deck_name, card_index, size=size)

    def render_deck_preview(self, parent, deck_name, card_size=(96, 144), per_row=2):
        for child in parent.winfo_children():
            child.destroy()

        title = DECK_LABELS.get(deck_name, deck_name.title())
        tk.Label(parent, text=f"Vista previa · {title}", font=FONT_BTN, fg=TEXT_RUNE, bg=BG_DARK).pack(pady=(0, 8))

        cards_frame = tk.Frame(parent, bg=BG_DARK)
        cards_frame.pack()

        for row_index in range(4 if per_row == 2 else 2):
            row = tk.Frame(cards_frame, bg=BG_DARK)
            row.pack()
            for col_index in range(per_row):
                card_number = row_index * per_row + col_index + 1
                if card_number > 8:
                    continue
                photo = self.load_deck_card_image(deck_name, card_number, size=card_size)

                card_box = tk.Frame(row, bg=BG_PANEL, highlightbackground=BORDER_GOLD_DIM, highlightthickness=1)
                card_box.pack(side="left", padx=4, pady=4)
                if photo:
                    label = tk.Label(card_box, image=photo, bg=BG_PANEL)
                    label.image = photo
                    label.pack(padx=3, pady=3)
                else:
                    tk.Label(card_box, text=f"{deck_name}_{card_number}", bg=BG_PANEL, fg=TEXT_MUTED,
                             font=FONT_BTN_SUB, width=12, height=7).pack(padx=3, pady=3)

    def build_character_preview(self, parent, deck_var, compact=False):
        preview_frame = tk.Frame(parent, bg=BG_DARK, highlightbackground=BORDER_GOLD_DIM, highlightthickness=1)
        preview_frame.pack(fill="both", expand=True, padx=12, pady=12)

        def show_placeholder():
            for child in preview_frame.winfo_children():
                child.destroy()
            tk.Label(preview_frame, text="Selecciona un personaje para ver sus cartas", font=FONT_BTN_SUB,
                     fg=TEXT_MUTED, bg=BG_DARK).pack(pady=10)

        def update_preview(*args):
            chosen = deck_var.get()
            if not chosen:
                show_placeholder()
                return
            if compact:
                self.render_deck_preview(preview_frame, chosen, card_size=(76, 114), per_row=2)
            else:
                self.render_deck_preview(preview_frame, chosen)

        deck_var.trace_add("write", update_preview)
        show_placeholder()
        return preview_frame

    def ask_difficulty(self):
        dialog = self.styled_dialog("Dificultad - Triple Triad", 460, 380)
        self.gold_header(dialog, "LEGIONS · TRIPLE TRIAD", "Selecciona la dificultad de la IA")

        def set_diff(level):
            self.difficulty = level
            dialog.destroy()
            self.ask_deck_blue()

        self.styled_button(dialog, "Nivel I · Aprendiz Arcano (Aleatorio)", lambda: set_diff(1), width=38, height=2).pack(pady=6)
        self.styled_button(dialog, "Nivel II · Hechicero (Greedy)", lambda: set_diff(2), width=38, height=2).pack(pady=6)
        self.styled_button(dialog, "Nivel III · Señor Oscuro (Minimax)", lambda: set_diff(3), danger=True, width=38, height=2).pack(pady=6)
        self.styled_button(dialog, "Nivel IV · Aprendizaje Automático (ML)", lambda: set_diff(4), primary=True, width=38, height=2).pack(pady=6)

    def ask_deck_blue(self):
        dialog = self.styled_dialog("Elige tu personaje", 800, 860)
        self.gold_header(dialog, "✦ ELIGE 1 PERSONAJE ESPECIAL ✦",
                         "Tu mano (Azul 🔵) tendrá 8 cartas: 4 del personaje Común (por defecto)\n"
                         "+ 4 del personaje especial que elijas", fg=BLUE_ACCENT)

        content = tk.Frame(dialog, bg=BG_DARK)
        content.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        left_col = tk.Frame(content, bg=BG_DARK)
        left_col.pack(side="left", fill="both", expand=True)

        right_col = tk.Frame(content, bg=BG_DARK, width=310)
        right_col.pack(side="right", fill="y")
        right_col.pack_propagate(False)

        special_keys = [k for k in DECK_DEFS.keys() if k != "comun"]
        choice_var = tk.StringVar(value="")
        error_label = tk.Label(left_col, text="", font=FONT_BTN_SUB, fg=RED_TEXT, bg=BG_DARK)

        titles = {"rata": "La Rata", "alien": "El Alien", "bandido": "El Bandido", "bombardero": "El Bombardero"}
        subtitles = {
            "rata": "Intercambia números al chocar",
            "alien": "Sus números suben +1 en el tablero",
            "bandido": "Roba +1 a su lado, resta -1 al rival",
            "bombardero": "Coloca minas en casillas vacías adyacentes"
        }

        self.build_character_preview(right_col, choice_var, compact=True)

        for key in special_keys:
            self.create_choice_option(left_col, choice_var, key, titles[key], subtitles[key], BLUE_ACCENT)

        def confirm():
            chosen = choice_var.get()
            if not chosen:
                error_label.config(text="⚠ Debes elegir un personaje especial")
                error_label.pack(pady=4)
                return
            self.deck_blue = ["comun", chosen]
            dialog.destroy()
            self.ask_deck_red()

        self.styled_button(left_col, "Continuar →", confirm, primary=True, width=22, height=2).pack(pady=12)
        error_label.pack(pady=(4, 0))

    def ask_deck_red(self):
        dialog = self.styled_dialog("Personaje de la IA", 800, 920)
        self.gold_header(dialog, "✦ PERSONAJE ESPECIAL DE LA IA ✦",
                         "La mano de la IA (Rojo 🔴) tendrá 8 cartas: 4 del personaje Común (por defecto)\n"
                         "+ 4 del personaje especial que elijas", fg=RED_ACCENT)

        content = tk.Frame(dialog, bg=BG_DARK)
        content.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        left_col = tk.Frame(content, bg=BG_DARK)
        left_col.pack(side="left", fill="both", expand=True)

        right_col = tk.Frame(content, bg=BG_DARK, width=310)
        right_col.pack(side="right", fill="y")
        right_col.pack_propagate(False)

        special_keys = [k for k in DECK_DEFS.keys() if k != "comun"]
        choice_var = tk.StringVar(value="")
        error_label = tk.Label(left_col, text="", font=FONT_BTN_SUB, fg=RED_TEXT, bg=BG_DARK)

        titles = {"rata": "La Rata", "alien": "El Alien", "bandido": "El Bandido", "bombardero": "El Bombardero"}
        subtitles = {
            "rata": "🐀  Opción rápida y engañosa",
            "alien": "👽  Escala con el avance de la partida",
            "bandido": "🔪  Presiona con robo y castigo",
            "bombardero": "💣  Control de tablero con minas"
        }

        self.build_character_preview(right_col, choice_var, compact=True)

        for key in special_keys:
            self.create_choice_option(left_col, choice_var, key, titles[key], subtitles[key], RED_ACCENT)

        def confirm():
            chosen = choice_var.get()
            if not chosen:
                error_label.config(text="⚠ Debes elegir un personaje especial")
                error_label.pack(pady=4)
                return
            self.deck_red = ["comun", chosen]
            dialog.destroy()
            self.start_game()

        def confirm_random():
            self.deck_red = ["comun", random.choice(special_keys)]
            dialog.destroy()
            self.start_game()

        self.styled_button(left_col, "Continuar →", confirm, primary=True, width=22, height=2).pack(pady=(10, 6))
        self.styled_button(left_col, "🎲 Aleatorio", confirm_random, width=22, height=2).pack(pady=(0, 6))
        error_label.pack(pady=(4, 0))

    def start_game(self):
        try:
            self.clear_game_ui()
            self.root.deiconify()
            self.current_player = "Azul"
            self.selected_card_idx = None
            self.last_move = None

            self.ROWS, self.COLS = 4, 5
            self.board = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
            self.bombs = {}

            self.hand_blue = self.build_hand(self.deck_blue, "A")
            self.hand_red = self.build_hand(self.deck_red, "R")
            self.HAND_SIZE = max(len(self.hand_blue), len(self.hand_red))
            self.game_logger.start_game()

            self.create_interface()
        except Exception as e:
            messagebox.showerror("Error al iniciar", str(e))

    def clear_game_ui(self):
        for child in self.root.winfo_children():
            child.destroy()

    def restart_game(self):
        self.game_logger.discard_game()
        self.clear_game_ui()
        self.root.withdraw()
        self.show_welcome_screen(self.ask_difficulty)

    def on_close(self):
        self.game_logger.discard_game()
        self.root.quit()

    def build_hand(self, deck_names, prefix):
        cards = []
        counter = 1
        for deck_name in deck_names:
            for (up, down, left, right) in DECK_DEFS[deck_name]:
                cards.append(Card(up, down, left, right, f"{prefix}{counter}", special=deck_name))
                counter += 1
        return cards

    def deck_combo_label(self, deck_names):
        return " + ".join(DECK_LABELS[d] for d in deck_names)

    def create_card_frame(self, parent, card=None, owner=None, is_selected=False, small=False):
        width = 115 if small else 130
        height = 110 if small else 126
        outer_border = SELECT_GOLD if is_selected else (BLUE_BORDER if owner == "Azul" else (RED_BORDER if owner == "Rojo" else BORDER_GOLD_DIM))

        frame = tk.Frame(parent, bg=BG_PANEL, width=width, height=height,
                         highlightbackground=outer_border, highlightcolor=outer_border,
                         highlightthickness=3 if is_selected else 2, bd=0)
        frame.pack_propagate(False)

        if not card:
            tk.Label(frame, text="✥ VACÍA ✥", bg=BG_PANEL, fg="#4a4654",
                     font=("Georgia", 9 if small else 11, "italic")).place(relx=0.5, rely=0.5, anchor="center")
            return frame

        color_bg, name_fg_normal = (BLUE_BG, BLUE_TEXT) if owner == "Azul" else (RED_BG, RED_TEXT)
        if is_selected:
            frame.config(bg=SELECT_GOLD)
            name_bg, name_fg, inner_bg = SELECT_GOLD, "#1a1408", SELECT_GOLD
        else:
            name_bg, name_fg, inner_bg = ("#241f30" if owner not in ("Azul", "Rojo") else color_bg), name_fg_normal, color_bg

        icon = DECK_ICONS.get(card.special, "")
        tk.Label(frame, text=f"~ {card.name} {icon} ~", bg=name_bg, fg=name_fg, font=FONT_CARD_NAME).pack(pady=2, fill="x")

        card_image = self.load_card_image(card, size=(108, 54) if small else (120, 62), display_deck_name=self.get_owner_display_deck(owner))
        face = tk.Frame(frame, bg=inner_bg, highlightbackground=BORDER_GOLD_DIM, highlightthickness=1)
        face.pack(expand=True, fill="both", padx=6, pady=3)

        if card_image:
            image_label = tk.Label(face, image=card_image, bg=inner_bg)
            image_label.image = card_image
            image_label.place(relx=0.5, rely=0.54, anchor="center")

        tk.Label(face, text=str(card.up), bg=inner_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.5, rely=0.06, anchor="n")
        tk.Label(face, text=str(card.down), bg=inner_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.5, rely=0.94, anchor="s")
        tk.Label(face, text=str(card.left), bg=inner_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.08, rely=0.5, anchor="w")
        tk.Label(face, text=str(card.right), bg=inner_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.92, rely=0.5, anchor="e")

        return frame

    def create_hand_card_frame(self, parent, card=None, owner=None, is_selected=False, small=False):
        width = 120 if small else 228
        height = 168 if small else 332
        outer_border = SELECT_GOLD if is_selected else (BLUE_BORDER if owner == "Azul" else (RED_BORDER if owner == "Rojo" else BORDER_GOLD_DIM))

        frame = tk.Frame(parent, bg=BG_PANEL, width=width, height=height,
                         highlightbackground=outer_border, highlightcolor=outer_border,
                         highlightthickness=3 if is_selected else 2, bd=0)
        frame.pack_propagate(False)

        if not card:
            tk.Label(frame, text="✥ VACÍA ✥", bg=BG_PANEL, fg="#4a4654",
                     font=("Georgia", 9 if small else 11, "italic")).place(relx=0.5, rely=0.5, anchor="center")
            return frame

        color_bg, name_fg_normal = (BLUE_BG, BLUE_TEXT) if owner == "Azul" else (RED_BG, RED_TEXT)
        if is_selected:
            frame.config(bg=SELECT_GOLD)
            name_bg, name_fg = SELECT_GOLD, "#1a1408"
        else:
            name_bg, name_fg = ("#241f30" if owner not in ("Azul", "Rojo") else color_bg), name_fg_normal

        icon = DECK_ICONS.get(card.special, "")
        tk.Label(frame, text=f"~ {card.name} {icon} ~", bg=name_bg, fg=name_fg, font=FONT_CARD_NAME).pack(fill="x")

        card_image = self.load_card_image(card, size=(102, 122) if small else (184, 276), display_deck_name=self.get_owner_display_deck(owner))
        face = tk.Frame(frame, bg=name_bg, highlightbackground=BORDER_GOLD_DIM, highlightthickness=1)
        face.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        if card_image:
            image_label = tk.Label(face, image=card_image, bg=name_bg)
            image_label.image = card_image
            image_label.place(relx=0.5, rely=0.52, anchor="center")
        else:
            tk.Label(face, text="Sin imagen", bg=name_bg, fg=name_fg,
                     font=FONT_BTN_SUB, width=20, height=10).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(face, text=str(card.up), bg=name_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.5, rely=0.04, anchor="n")
        tk.Label(face, text=str(card.down), bg=name_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.5, rely=0.96, anchor="s")
        tk.Label(face, text=str(card.left), bg=name_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.08, rely=0.5, anchor="w")
        tk.Label(face, text=str(card.right), bg=name_bg, fg=name_fg, font=FONT_CARD_NUM).place(relx=0.92, rely=0.5, anchor="e")

        return frame

    def bind_card_click(self, widget, callback):
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self.bind_card_click(child, callback)

    def create_interface(self):
        top_bar = tk.Frame(self.root, bg=BG_PANEL)
        top_bar.pack(fill="x")
        tk.Frame(self.root, bg=BORDER_GOLD, height=2).pack(fill="x")

        title_text = f"⚜ LEGIONS · TRIPLE TRIAD (4×5)  |  Nivel {self.difficulty}  |  Tú: {self.deck_combo_label(self.deck_blue)}  vs  IA: {self.deck_combo_label(self.deck_red)} ⚜"
        tk.Label(top_bar, text=title_text, font=FONT_BANNER, fg=TEXT_RUNE, bg=BG_PANEL).pack(side="left", padx=20, pady=10)

        self.undo_button = self.styled_button(top_bar, "⟲ Deshacer Jugada", self.undo_last_move, width=18, height=1, font=FONT_BTN_SUB)
        self.undo_button.config(state="disabled")
        self.undo_button.pack(side="right", padx=20, pady=10)

        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(expand=True, fill="both")

        left_frame = tk.Frame(main, bg=BG_DARK, width=250)
        left_frame.pack(side="left", fill="y", padx=(10, 4))
        tk.Label(left_frame, text="TUS FUERZAS 🔵", font=FONT_BTN, fg=BLUE_ACCENT, bg=BG_DARK).pack(pady=8)
        self.create_scrollable_hand(left_frame, is_blue=True)

        center_frame = tk.Frame(main, bg=BG_DARK)
        center_frame.pack(side="left", expand=True, fill="both")

        board_wrap = tk.Frame(center_frame, bg=BG_DARK)
        board_wrap.place(relx=0.5, rely=0.5, anchor="center")

        board_cont = tk.Frame(board_wrap, bg=BG_PANEL, padx=20, pady=20, highlightbackground=BORDER_GOLD, highlightthickness=2)
        board_cont.pack()
        
        self.board_frames = [[None]*self.COLS for _ in range(self.ROWS)]
        for i in range(self.ROWS):
            row = tk.Frame(board_cont, bg=BG_PANEL)
            row.pack()
            for j in range(self.COLS):
                cell = tk.Frame(row, bg=BG_DARK, width=148, height=130, highlightbackground=BORDER_GOLD_DIM, highlightthickness=1)
                cell.pack(side="left", padx=6, pady=6)
                cell.pack_propagate(False)
                self.board_frames[i][j] = cell

        right_frame = tk.Frame(main, bg=BG_DARK, width=250)
        right_frame.pack(side="right", fill="y", padx=(4, 10))
        tk.Label(right_frame, text="LEGIÓN OSCURA 🔴", font=FONT_BTN, fg=RED_ACCENT, bg=BG_DARK).pack(pady=8)
        self.create_scrollable_hand(right_frame, is_blue=False)

        status_bar = tk.Frame(self.root, bg=BG_PANEL, highlightbackground=BORDER_GOLD, highlightthickness=1)
        status_bar.pack(fill="x", side="bottom")
        self.status_label = tk.Label(status_bar, text="✧ Tu turno — Selecciona una carta de tus fuerzas ✧", font=FONT_STATUS, fg=TEXT_RUNE, bg=BG_PANEL, pady=10)
        self.status_label.pack()

        self.refresh_all()

    def create_scrollable_hand(self, parent, is_blue=True):
        canvas = tk.Canvas(parent, bg=BG_DARK, height=690, width=235, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        container = tk.Frame(canvas, bg=BG_DARK)
        window_id = canvas.create_window((0, 0), window=container, anchor="nw")

        if is_blue:
            self.hand_frames = []
            self.hand_canvas = canvas
        else:
            self.red_frames = []
            self.red_canvas = canvas

        for i in range(self.HAND_SIZE):
            f = tk.Frame(container, bg=BG_DARK)
            row = i // 2
            col = i % 2
            f.grid(row=row, column=col, padx=5, pady=5, sticky="n")
            if is_blue: self.hand_frames.append(f)
            else: self.red_frames.append(f)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        def update_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(window_id, width=canvas.winfo_width())

        container.bind("<Configure>", update_scroll)
        canvas.bind("<Configure>", update_scroll)

    def refresh_hand(self):
        for i, frame in enumerate(self.hand_frames):
            for w in frame.winfo_children(): w.destroy()
            if i < len(self.hand_blue):
                is_sel = (i == self.selected_card_idx)
                cf = self.create_hand_card_frame(frame, self.hand_blue[i], "Azul", is_sel, small=True)
                self.bind_card_click(cf, lambda e, idx=i: self.select_card(idx))
                cf.pack()

    def refresh_red_hand(self):
        for i, frame in enumerate(self.red_frames):
            for w in frame.winfo_children(): w.destroy()
            if i < len(self.hand_red):
                cf = self.create_hand_card_frame(frame, self.hand_red[i], "Rojo", small=True)
                cf.pack()
            else:
                tk.Label(frame, text="†", bg=BG_PANEL, fg="#4a2424", font=("Georgia", 16, "bold"), width=15, height=5).pack()

    def refresh_board(self):
        for i in range(self.ROWS):
            for j in range(self.COLS):
                cell = self.board_frames[i][j]
                for w in cell.winfo_children(): w.destroy()
                if self.board[i][j]:
                    owner, card = self.board[i][j]
                    cf = self.create_card_frame(cell, card, owner)
                    cf.pack(fill="both", expand=True)
                else:
                    bomb_count = self.bombs.get((i, j), 0)
                    text, fg, fsize = ("💣" if bomb_count == 1 else f"💣×{bomb_count}", "#ff9933", 16) if bomb_count > 0 else ("✥", "#322c3c", 18)
                    empty = tk.Label(cell, text=text, bg=BG_DARK, fg=fg, font=("Georgia", fsize, "bold"))
                    empty.pack(fill="both", expand=True)
                    empty.bind("<Button-1>", lambda e, x=i, y=j: self.place_card(x, y))

    def refresh_all(self):
        self.refresh_hand()
        self.refresh_board()
        self.refresh_red_hand()

    def select_card(self, idx):
        if self.current_player != "Azul": return
        self.selected_card_idx = idx
        self.refresh_hand()
        self.status_label.config(text=f"✧ Carta {self.hand_blue[idx].name} imbuida → Elige una casilla ✧", fg=SELECT_GOLD)

    def place_card(self, x, y):
        if self.current_player != "Azul" or self.selected_card_idx is None: return
        if self.board[x][y] is not None: return

        self.game_logger.log_human_move(self.board, self.bombs, self.hand_blue, len(self.hand_red),
                                        x, y, self.selected_card_idx, self.ROWS, self.COLS)

        self.last_move = {
            'hand_blue': copy.deepcopy(self.hand_blue), 'hand_red': copy.deepcopy(self.hand_red),
            'board': copy.deepcopy(self.board), 'bombs': copy.deepcopy(self.bombs)
        }

        card = self.hand_blue.pop(self.selected_card_idx)
        self.board[x][y] = ("Azul", card)
        self.selected_card_idx = None
        self.play_card_sound(card)

        self.resolve_and_update(x, y, "Azul")

        if len(self.hand_blue) == 0 and len(self.hand_red) == 0:
            self.end_game()
            return

        self.current_player = "Rojo"
        self.status_label.config(text="✧ La Legión Oscura está calculando su estrategia... ✧", fg=RED_ACCENT)
        self.root.after(600, self.ai_play)

    def resolve_and_update(self, x, y, owner):
        engine.apply_bomb_trigger(self.board, self.bombs, x, y, owner, self.ROWS, self.COLS)
        engine.apply_rata_swap(self.board, x, y, owner, self.ROWS, self.COLS)
        engine.apply_bandido_attack(self.board, x, y, owner, self.ROWS, self.COLS)
        engine.process_captures_from_new_card(self.board, x, y, owner, self.ROWS, self.COLS)
        engine.apply_bombardero_bombs(self.board, self.bombs, x, y, owner, self.ROWS, self.COLS)
        if owner == "Azul":
            engine.apply_alien_growth(self.hand_blue, self.hand_red)
        self.refresh_board()
        self.undo_button.config(state="normal" if owner == "Azul" else "disabled")

    def ai_play(self):
        if not self.hand_red:
            self.end_game()
            return

        empty_cells = [(i, j) for i in range(self.ROWS) for j in range(self.COLS) if self.board[i][j] is None]
        pos, card_idx = ai.select_ai_move(
            self.difficulty,
            self.board,
            self.bombs,
            self.hand_red,
            empty_cells,
            self.ROWS,
            self.COLS,
            len(self.hand_blue),
        )

        card = self.hand_red.pop(card_idx)
        self.board[pos[0]][pos[1]] = ("Rojo", card)
        self.play_card_sound(card)

        self.resolve_and_update(pos[0], pos[1], "Rojo")

        if len(self.hand_blue) == 0 and len(self.hand_red) == 0:
            self.end_game()
            return

        self.current_player = "Azul"
        self.status_label.config(text="✧ Tu turno (Azul). Defiende tu posición. ✧", fg=TEXT_RUNE)
        self.refresh_all()

    def undo_last_move(self):
        if not self.last_move or self.current_player != "Azul": return
        self.game_logger.discard_last_move()
        self.hand_blue = self.last_move['hand_blue']
        self.hand_red = self.last_move['hand_red']
        self.board = self.last_move['board']
        self.bombs = self.last_move['bombs']
        self.selected_card_idx = None
        self.last_move = None
        self.refresh_all()
        self.status_label.config(text="✧ El tiempo ha retrocedido. Selecciona otra estrategia. ✧", fg=SELECT_GOLD)

    def end_game(self):
        azul = sum(1 for r in self.board for c in r if c and c[0] == "Azul")
        rojo = sum(1 for r in self.board for c in r if c and c[0] == "Rojo")
        self.game_logger.finalize_game(azul, rojo)
        self.schedule_model_retraining()
        if azul > rojo:
            winner_text = "Ganaste tú (Azul)"
            loser_text = "Perdió la IA (Rojo)"
            summary = f"Azul {azul} - {rojo} Rojo"
        elif rojo > azul:
            winner_text = "Ganó la IA (Rojo)"
            loser_text = "Perdiste tú (Azul)"
            summary = f"Rojo {rojo} - {azul} Azul"
        else:
            winner_text = "Empate"
            loser_text = "Ninguno perdió ni ganó"
            summary = f"Azul {azul} - {rojo} Rojo"

        dialog = self.styled_dialog("Resolución de la Batalla", 620, 400)
        self.gold_header(dialog, "FIN DE LA PARTIDA", summary, fg=TEXT_RUNE)

        tk.Label(dialog, text=winner_text, font=FONT_TITLE, fg=BLUE_ACCENT if azul >= rojo else RED_ACCENT, bg=BG_DARK).pack(pady=(20, 6))
        tk.Label(dialog, text=loser_text, font=FONT_SUBTITLE, fg=TEXT_MUTED, bg=BG_DARK).pack(pady=(0, 18))

        button_row = tk.Frame(dialog, bg=BG_DARK)
        button_row.pack(pady=10)

        def play_again():
            dialog.destroy()
            self.restart_game()

        def exit_game():
            dialog.destroy()
            self.root.quit()

        self.styled_button(button_row, "Jugar de nuevo", play_again, primary=True, width=18, height=2).pack(side="left", padx=10)
        self.styled_button(button_row, "Salir", exit_game, danger=True, width=12, height=2).pack(side="left", padx=10)