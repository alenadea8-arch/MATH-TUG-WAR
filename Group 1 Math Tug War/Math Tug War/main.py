import pygame
import random
import sys
import operator
from fractions import Fraction
import json
import os
import time

# Utility: Terminate program cleanly 
def terminate_program():
    pygame.quit()
    sys.exit()

# Initialize Pygame and audio mixer
pygame.init()
pygame.mixer.init()

# Screen and performance config
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h
FPS = 60

# Color palette 
BG_COLOR = (248, 248, 242)
GRID_COLOR = (220, 220, 220)
WOOD_LIGHT = (233, 165, 83)
WOOD_DARK = (210, 140, 60)
WOOD_BORDER = (94, 44, 12)
TEXT_BROWN = (61, 30, 11)
TEXT_WHITE = (255, 255, 255)
COLOR_P1 = (78, 205, 196)
COLOR_P2 = (255, 107, 107)
COLOR_ROPE_DETAIL = (230, 180, 100)
BLACK_TRANSPARENT = (0, 0, 0, 180)

# Game states 
STATE_MAIN_MENU = "main_menu"
STATE_AUDIO_SETTINGS = "audio_settings"
STATE_NAME_INPUT = "name_input"
STATE_GAME_PLAY = "game_play"
STATE_LEADERBOARD = "leaderboard"
STATE_GAME_OVER = "game_over"

# Font loading
def get_font(size):
    font_files = ["BoldPixels.ttf", "BoldPixels.otf", "pixel.ttf"]
    for f in font_files:
        if os.path.exists(f):
            try:
                return pygame.font.Font(f, size)
            except:
                pass
    return pygame.font.SysFont("arial", size, bold=True)

FONT_XL = get_font(50)
FONT_L = get_font(30)
FONT_M = get_font(20)
FONT_S = get_font(16)

# Load image 
def robust_load_image(filenames, scale_size=None):
    for name in filenames:
        if os.path.exists(name):
            try:
                img = pygame.image.load(name)
                if scale_size:
                    img = pygame.transform.scale(img, scale_size)
                return img
            except Exception as e:
                print(f"Failed to load {name}: {e}")
    return None

# Load assets
WALLPAPER_IMG = robust_load_image(["wallpaper.png", "wallpaper.jpg"], (SCREEN_W, SCREEN_H))
INGAME_WALLPAPER_IMG = robust_load_image(["ingamewallpaper.png", "ingamewallpaper.jpg"], (SCREEN_W, SCREEN_H))
TARGET_LINE_IMG = robust_load_image(["target.png"], (60, 80))
INDICATOR_IMG = robust_load_image(["indicator.png"], (64, 64))
PLAYER_LEFT_IMG = robust_load_image(["character1.png", "character1.jpg"], (100, 100))
PLAYER_RIGHT_IMG = robust_load_image(["character2.png", "character2.jpg"], (100, 100))

# Load and scale rope image
ROPE_IMG = None
if os.path.exists("tali.png"):
    try:
        loaded_rope = pygame.image.load("tali.png")
        rope_h = 850
        ratio = loaded_rope.get_width() / loaded_rope.get_height()
        rope_w = int(rope_h * ratio)
        if rope_w < SCREEN_W * 1.5:
            rope_w = int(SCREEN_W * 1.5)
        ROPE_IMG = pygame.transform.scale(loaded_rope, (rope_w, rope_h))
    except:
        pass

# Global game configuration 
TARGET_PULL = 8
TIME_PER_QUESTION = 15
DIFFICULTY = 'MID'
GAME_MODE = 'PvP'
PLAYER_NAMES = {"left": "YOU", "right": "BOT"}
LEADERBOARD_FILE_PVBOT = 'pvbot_leaderboard.json'
LEADERBOARD_FILE_PVP = 'pvp_leaderboard.json'
GAME_SETTINGS = {
    'music_on': True,
    'sfx_on': True,
    'volume': 0.5
}

# Sound loading 
SOUND_CLICK = None
SOUND_CORRECT = None
SOUND_WRONG = None
SOUND_COUNTDOWN = None
SOUND_TIMEOUT = None
SOUND_WIN = None
SOUND_LOSE = None

def load_game_sounds():
    global SOUND_CLICK, SOUND_CORRECT, SOUND_WRONG, SOUND_COUNTDOWN, SOUND_TIMEOUT, SOUND_WIN, SOUND_LOSE
    try:
        if os.path.exists("maintheme.mp3"):
            pygame.mixer.music.load("maintheme.mp3")
            update_background_music()
        if os.path.exists("click.mp3"): SOUND_CLICK = pygame.mixer.Sound("click.mp3")
        if os.path.exists("correct.mp3"): SOUND_CORRECT = pygame.mixer.Sound("correct.mp3")
        if os.path.exists("incorrect.mp3"): SOUND_WRONG = pygame.mixer.Sound("incorrect.mp3")
        if os.path.exists("countdown.mp3"): SOUND_COUNTDOWN = pygame.mixer.Sound("countdown.mp3")
        if os.path.exists("timeout.mp3"): SOUND_TIMEOUT = pygame.mixer.Sound("timeout.mp3")
        if os.path.exists("win.mp3"): SOUND_WIN = pygame.mixer.Sound("win.mp3")
        if os.path.exists("lose.mp3"): SOUND_LOSE = pygame.mixer.Sound("lose.mp3")
    except:
        pass

def update_background_music():
    if GAME_SETTINGS['music_on']:
        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.play(-1)
            except:
                pass
        pygame.mixer.music.unpause()
        pygame.mixer.music.set_volume(GAME_SETTINGS['volume'])
    else:
        pygame.mixer.music.pause()

def play_sfx(sound_obj):
    if sound_obj and GAME_SETTINGS['sfx_on']:
        sound_obj.set_volume(GAME_SETTINGS['volume'])
        sound_obj.play()

def play_win_sound():
    pygame.mixer.music.stop()
    play_sfx(SOUND_WIN)

def play_lose_sound():
    pygame.mixer.music.stop()
    play_sfx(SOUND_LOSE)

def restart_bg_music():
    if not pygame.mixer.music.get_busy() and GAME_SETTINGS['music_on']:
        try:
            pygame.mixer.music.play(-1)
        except:
            pass
    update_background_music()

load_game_sounds()

# Math and leaderboard logic
def load_leaderboard(mode='PvBot'):
    filename = LEADERBOARD_FILE_PVP if mode == 'PvP' else LEADERBOARD_FILE_PVBOT
    if not os.path.exists(filename):
        return {'EASY': [], 'MID': [], 'HARD': []}
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return {'EASY': [], 'MID': [], 'HARD': []}

def save_leaderboard(data, mode='PvBot'):
    filename = LEADERBOARD_FILE_PVP if mode == 'PvP' else LEADERBOARD_FILE_PVBOT
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def add_score(player_name, session_time, difficulty, mode='PvBot', winner_name=None):
    leaderboard = load_leaderboard(mode)
    new_score = {
        'name': player_name,
        'time': round(session_time / 1000, 2),
        'date': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if mode == 'PvP' and winner_name:
        new_score['winner'] = winner_name
    if difficulty not in leaderboard:
        leaderboard[difficulty] = []
    leaderboard[difficulty].append(new_score)
    leaderboard[difficulty].sort(key=lambda x: x['time'])
    leaderboard[difficulty] = leaderboard[difficulty][:10]
    save_leaderboard(leaderboard, mode)

def _generate_integer_question(max_val):
    ops = [('+', operator.add), ('-', operator.sub), ('*', operator.mul)]
    op_sym, op_func = random.choice(ops)
    num1 = random.randint(5, max_val)
    num2 = random.randint(1, max_val // 2)
    if op_sym == '-' and num2 > num1:
        num1, num2 = num2, num1
    return f"{num1} {op_sym} {num2} = ?", str(op_func(num1, num2))

def _generate_fraction_question():
    ops = [('+', operator.add), ('-', operator.sub)]
    op_sym, op_func = random.choice(ops)
    p1 = Fraction(random.randint(1, 5), random.randint(2, 6))
    p2 = Fraction(random.randint(1, 5), random.randint(2, 6))
    if op_sym == '-' and p2 > p1:
        p1, p2 = p2, p1
    jawaban_obj = op_func(p1, p2).limit_denominator()
    return f"{p1} {op_sym} {p2} = ?", str(jawaban_obj)

def _generate_root_question():
    base_sq = random.randint(3, 10)
    bil_kuadrat = base_sq ** 2
    base_cube = random.randint(2, 5)
    bil_kubik = base_cube ** 3
    if random.choice([True, False]):
        return f"√{bil_kuadrat} + 3√{bil_kubik} = ?", str(base_sq + base_cube)
    else:
        if base_sq > base_cube:
            return f"√{bil_kuadrat} - 3√{bil_kubik} = ?", str(base_sq - base_cube)
        else:
            return f"3√{bil_kubik} - √{bil_kuadrat} = ?", str(base_cube - base_sq)

def generate_mixed_question(difficulty):
    if difficulty == 'EASY':
        return _generate_integer_question(max_val=20)
    elif difficulty == 'MID':
        return random.choice([lambda: _generate_integer_question(max_val=50), _generate_fraction_question])()
    elif difficulty == 'HARD':
        return random.choice([
            lambda: _generate_integer_question(max_val=100),
            _generate_fraction_question,
            _generate_root_question
        ])()
    else:
        return _generate_integer_question(max_val=30)

class PlayerState:
    def __init__(self, side):
        self.side = side
        self.current_input = ""
        self.last_answer_time = 0
        self.correct_count = 0
    def reset_input(self):
        self.current_input = ""

# UI Button
class Button:
    def __init__(self, rect, text="", callback=None, font=FONT_M):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = font
        self.hover = False
    def draw(self, surf):
        fill_color = WOOD_DARK if self.hover else WOOD_LIGHT
        pygame.draw.rect(surf, WOOD_BORDER, self.rect, border_radius=6)
        inner_rect = self.rect.inflate(-6, -6)
        pygame.draw.rect(surf, fill_color, inner_rect, border_radius=4)
        nail_color = (130, 70, 30)
        corners = [
            (inner_rect.left + 3, inner_rect.top + 3),
            (inner_rect.right - 7, inner_rect.top + 3),
            (inner_rect.left + 3, inner_rect.bottom - 7),
            (inner_rect.right - 7, inner_rect.bottom - 7)
        ]
        for x, y in corners:
            pygame.draw.rect(surf, nail_color, (x, y, 4, 4))
        txt = self.font.render(self.text, True, TEXT_BROWN)
        txt_r = txt.get_rect(center=self.rect.center)
        surf.blit(txt, txt_r)
    def handle_event(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                play_sfx(SOUND_CLICK)
                if self.callback:
                    self.callback()

# Fallback background if wallpaper missing
def draw_grid_background(surf):
    surf.fill(BG_COLOR)
    for x in range(0, SCREEN_W, 40):
        pygame.draw.line(surf, GRID_COLOR, (x, 0), (x, SCREEN_H), 1)
    for y in range(0, SCREEN_H, 40):
        pygame.draw.line(surf, GRID_COLOR, (0, y), (SCREEN_W, y), 1)

# Main Menu Screen
class MainMenu:
    def __init__(self, start_game_callback, leaderboard_callback, settings_callback):
        self.start_game = start_game_callback
        self.leaderboard_callback = leaderboard_callback
        self.settings_callback = settings_callback
        self.selected_mode = GAME_MODE
        self.selected_difficulty = DIFFICULTY
        self.buttons = []
        self.create_buttons()
    def create_buttons(self):
        btn_w, btn_h = 240, 55
        center_x = SCREEN_W // 2
        start_y_mode = 200
        self.buttons.append(Button((center_x - btn_w - 10, start_y_mode, btn_w, btn_h), "Player vs Player", lambda: self.select_mode('PvP')))
        self.buttons.append(Button((center_x + 10, start_y_mode, btn_w, btn_h), "Player vs BOT", lambda: self.select_mode('PvBot')))
        start_y_diff = 320
        diff_w = 160
        diff_gap = 20
        total_diff_width = (diff_w * 3) + (diff_gap * 2)
        start_diff_x = center_x - (total_diff_width // 2)
        self.buttons.append(Button((start_diff_x, start_y_diff, diff_w, btn_h), "EASY", lambda: self.select_difficulty('EASY')))
        self.buttons.append(Button((start_diff_x + diff_w + diff_gap, start_y_diff, diff_w, btn_h), "MEDIUM", lambda: self.select_difficulty('MID')))
        self.buttons.append(Button((start_diff_x + 2 * (diff_w + diff_gap), start_y_diff, diff_w, btn_h), "HARD", lambda: self.select_difficulty('HARD')))
        start_y_actions = 430
        self.buttons.append(Button((center_x - 150, start_y_actions, 300, 60), "START GAME", self.on_start, FONT_L))
        self.buttons.append(Button((center_x - 150, start_y_actions + 75, 300, 45), "LEADERBOARD", self.leaderboard_callback))
        self.buttons.append(Button((center_x - 150, start_y_actions + 130, 300, 45), "AUDIO SETTINGS", self.settings_callback))
        self.buttons.append(Button((center_x - 150, start_y_actions + 185, 300, 45), "EXIT", terminate_program))
    def select_mode(self, mode):
        self.selected_mode = mode
    def select_difficulty(self, difficulty):
        self.selected_difficulty = difficulty
    def on_start(self):
        global GAME_MODE, DIFFICULTY
        GAME_MODE = self.selected_mode
        DIFFICULTY = self.selected_difficulty
        self.start_game()
    def handle_event(self, ev):
        for b in self.buttons:
            b.handle_event(ev)
    def draw(self, surf):
        if WALLPAPER_IMG:
            surf.blit(WALLPAPER_IMG, (0, 0))
        else:
            surf.fill(BG_COLOR)
        title_txt = "MATH TUG WAR"
        t_shadow = FONT_XL.render(title_txt, True, (0, 0, 0))
        t_main = FONT_XL.render(title_txt, True, TEXT_WHITE)
        surf.blit(t_shadow, (SCREEN_W // 2 - t_shadow.get_width() // 2 + 4, 64))
        surf.blit(t_main, (SCREEN_W // 2 - t_main.get_width() // 2, 60))
        lbl_mode = FONT_L.render("SELECT MODE", True, TEXT_WHITE)
        surf.blit(lbl_mode, (SCREEN_W // 2 - lbl_mode.get_width() // 2, 160))
        lbl_diff = FONT_L.render("DIFFICULTY", True, TEXT_WHITE)
        surf.blit(lbl_diff, (SCREEN_W // 2 - lbl_diff.get_width() // 2, 280))
        for b in self.buttons:
            b.draw(surf)
            is_mode_sel = (b.text == 'Player vs Player' and self.selected_mode == 'PvP') or \
                          (b.text == 'Player vs BOT' and self.selected_mode == 'PvBot')
            is_diff_sel = (b.text == 'EASY' and self.selected_difficulty == 'EASY') or \
                          (b.text == 'MEDIUM' and self.selected_difficulty == 'MID') or \
                          (b.text == 'HARD' and self.selected_difficulty == 'HARD')
            if is_mode_sel or is_diff_sel:
                pygame.draw.rect(surf, (255, 255, 200), b.rect.inflate(6, 6), 3, border_radius=6)

# Audio Settings Screen
class AudioSettingsScreen:
    def __init__(self, return_callback):
        self.return_callback = return_callback
        self.create_buttons()
    def create_buttons(self):
        self.buttons = []
        center_x = SCREEN_W // 2
        start_y = 200
        btn_w, btn_h = 300, 55
        spacing = 20
        self.buttons.append(Button(
            (center_x - btn_w // 2, start_y, btn_w, btn_h),
            f"Music: {'ON' if GAME_SETTINGS['music_on'] else 'OFF'}",
            self.toggle_music
        ))
        self.buttons.append(Button(
            (center_x - btn_w // 2, start_y + btn_h + spacing, btn_w, btn_h),
            f"SFX: {'ON' if GAME_SETTINGS['sfx_on'] else 'OFF'}",
            self.toggle_sfx
        ))
        vol_y = start_y + (btn_h + spacing) * 2
        self.buttons.append(Button((center_x - 130, vol_y, 60, 55), "-", self.decrease_volume, FONT_L))
        self.buttons.append(Button((center_x + 70, vol_y, 60, 55), "+", self.increase_volume, FONT_L))
        self.buttons.append(Button((center_x - 100, 500, 200, 55), "BACK", self.return_callback))
    def toggle_music(self):
        GAME_SETTINGS['music_on'] = not GAME_SETTINGS['music_on']
        update_background_music()
        self.create_buttons()
    def toggle_sfx(self):
        GAME_SETTINGS['sfx_on'] = not GAME_SETTINGS['sfx_on']
        self.create_buttons()
    def increase_volume(self):
        GAME_SETTINGS['volume'] = min(1.0, GAME_SETTINGS['volume'] + 0.1)
        update_background_music()
    def decrease_volume(self):
        GAME_SETTINGS['volume'] = max(0.0, GAME_SETTINGS['volume'] - 0.1)
        update_background_music()
    def handle_event(self, ev):
        for b in self.buttons:
            b.handle_event(ev)
    def draw(self, surf):
        if WALLPAPER_IMG:
            surf.blit(WALLPAPER_IMG, (0, 0))
        else:
            surf.fill(BG_COLOR)
        title = FONT_XL.render("AUDIO SETTINGS", True, TEXT_WHITE)
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 80))
        for b in self.buttons:
            b.draw(surf)
        vol_percent = int(GAME_SETTINGS['volume'] * 100)
        vol_text = FONT_M.render(f"Volume: {vol_percent}%", True, TEXT_WHITE)
        center_x = SCREEN_W // 2
        vol_y = 200 + (55 + 20) * 2 + 15
        surf.blit(vol_text, (center_x - vol_text.get_width() // 2, vol_y))

# Name Input Screen (for PvP)
class NameInputScreen:
    def __init__(self, start_game_callback, quit_callback):
        self.start_game = start_game_callback
        self.quit_callback = quit_callback
        self.p1_input = ""
        self.p2_input = ""
        self.active_field = 1
        self.max_chars = 10
        center_x = SCREEN_W // 2
        self.input_rects = {
            1: pygame.Rect(center_x - 300, 200, 600, 50),
            2: pygame.Rect(center_x - 300, 350, 600, 50)
        }
        self.start_button = Button((center_x - 100, 500, 200, 60), "GO!", self.on_start, FONT_L)
        self.back_button = Button((20, 20, 100, 40), "BACK", self.quit_callback, FONT_S)
    def on_start(self):
        global PLAYER_NAMES
        name1 = self.p1_input.strip() or "PLAYER 1"
        name2 = self.p2_input.strip() or "PLAYER 2"
        PLAYER_NAMES["left"] = name1.upper()
        PLAYER_NAMES["right"] = name2.upper()
        self.start_game()
    def handle_event(self, ev):
        self.start_button.handle_event(ev)
        self.back_button.handle_event(ev)
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if self.input_rects[1].collidepoint(ev.pos):
                self.active_field = 1
            elif self.input_rects[2].collidepoint(ev.pos):
                self.active_field = 2
        if ev.type == pygame.KEYDOWN:
            current_input = self.p1_input if self.active_field == 1 else self.p2_input
            if ev.key == pygame.K_RETURN:
                if self.active_field == 1:
                    self.active_field = 2
                elif self.active_field == 2 and (self.p1_input or self.p2_input):
                    self.on_start()
            elif ev.key == pygame.K_BACKSPACE:
                current_input = current_input[:-1]
            elif len(current_input) < self.max_chars and (ev.unicode.isalnum() or ev.key == pygame.K_SPACE):
                current_input += ev.unicode.upper()
            if self.active_field == 1:
                self.p1_input = current_input
            else:
                self.p2_input = current_input
    def draw(self, surf):
        if WALLPAPER_IMG:
            surf.blit(WALLPAPER_IMG, (0, 0))
        else:
            surf.fill(BG_COLOR)
        title = FONT_XL.render("ENTER NAMES", True, TEXT_WHITE)
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 100))
        for i in [1, 2]:
            rect = self.input_rects[i]
            input_text = self.p1_input if i == 1 else self.p2_input
            label = FONT_L.render(f"PLAYER {i}:", True, TEXT_WHITE)
            surf.blit(label, (rect.x, rect.y - 40))
            pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=5)
            border_col = COLOR_P1 if self.active_field == i else WOOD_BORDER
            pygame.draw.rect(surf, border_col, rect, 3, border_radius=5)
            text_surface = FONT_L.render(input_text, True, TEXT_BROWN)
            surf.blit(text_surface, (rect.x + 10, rect.y + 10))
        self.start_button.draw(surf)
        self.back_button.draw(surf)

# Leaderboard Screen 
class LeaderboardScreen:
    def __init__(self, return_callback, quit_callback):
        self.return_callback = return_callback
        self.current_mode = 'PvBot'
        self.current_difficulty = 'EASY'
        self.leaderboard_data = load_leaderboard(self.current_mode)
        self.create_buttons()
    def create_buttons(self):
        btn_w = 120
        btn_h = 35
        gap = 20
        total_width = 2 * btn_w + gap
        center_x = SCREEN_W // 2
        start_x = center_x - total_width // 2
        self.buttons = [
            Button((start_x, 20, btn_w, btn_h), "PvBOT", lambda: self.set_mode('PvBOT'), FONT_S),
            Button((start_x + btn_w + gap, 20, btn_w, btn_h), "PvP", lambda: self.set_mode('PvP'), FONT_S),
            Button((center_x - 200, 60, btn_w, btn_h), "EASY", lambda: self.set_difficulty('EASY')),
            Button((center_x - 60, 60, btn_w, btn_h), "MEDIUM", lambda: self.set_difficulty('MID')),
            Button((center_x + 80, 60, btn_w, btn_h), "HARD", lambda: self.set_difficulty('HARD')),
            Button((20, 20, 100, 40), "BACK", self.return_callback, FONT_S)
        ]
    def set_mode(self, mode):
        self.current_mode = mode
        self.leaderboard_data = load_leaderboard(self.current_mode)
    def set_difficulty(self, diff):
        self.current_difficulty = diff
        self.leaderboard_data = load_leaderboard(self.current_mode)
    def handle_event(self, ev):
        for b in self.buttons:
            b.handle_event(ev)
    def draw(self, surf):
        if WALLPAPER_IMG:
            surf.blit(WALLPAPER_IMG, (0, 0))
        else:
            surf.fill(BG_COLOR)
        for b in self.buttons:
            b.draw(surf)
            if b.text == self.current_difficulty or (b.text == "MEDIUM" and self.current_difficulty == 'MID'):
                pygame.draw.rect(surf, (255, 255, 200), b.rect.inflate(4, 4), 3, border_radius=6)
        table_rect = pygame.Rect(100, 110, SCREEN_W - 200, SCREEN_H - 150)
        pygame.draw.rect(surf, (0, 0, 0, 150), table_rect, border_radius=10)
        scores = self.leaderboard_data.get(self.current_difficulty, [])
        header_font = FONT_L
        y_pos = 130
        surf.blit(header_font.render("RANK", True, TEXT_WHITE), (130, y_pos))
        surf.blit(header_font.render("NAME", True, TEXT_WHITE), (280, y_pos))
        surf.blit(header_font.render("TIME (s)", True, TEXT_WHITE), (580, y_pos))
        surf.blit(header_font.render("DATE", True, TEXT_WHITE), (780, y_pos))
        if self.current_mode == 'PvP':
            surf.blit(header_font.render("WINNER", True, TEXT_WHITE), (1000, y_pos))
        pygame.draw.line(surf, TEXT_WHITE, (120, y_pos + 40), (SCREEN_W - 120, y_pos + 40), 2)
        score_font = FONT_M
        y_start = 180
        if not scores:
            no_score = FONT_L.render("NO SCORES YET", True, (200, 200, 200))
            surf.blit(no_score, (SCREEN_W // 2 - no_score.get_width() // 2, y_start))
            return
        for i, score in enumerate(scores):
            y = y_start + i * 45
            if y > SCREEN_H - 50:
                break
            surf.blit(score_font.render(str(i + 1), True, TEXT_WHITE), (140, y))
            surf.blit(score_font.render(score.get('name', 'N/A'), True, TEXT_WHITE), (280, y))
            time_val = score.get('time')
            time_text = f"{time_val:.2f}" if time_val is not None else "N/A"
            surf.blit(score_font.render(time_text, True, TEXT_WHITE), (580, y))
            surf.blit(score_font.render(score['date'].split(' ')[0], True, TEXT_WHITE), (780, y))
            if self.current_mode == 'PvP':
                winner = score.get('winner', '—')
                win_color = COLOR_P1 if winner == score.get('name') else TEXT_WHITE
                surf.blit(score_font.render(winner, True, win_color), (1000, y))

# In-game settings panel (adjust target, exit, etc.) 
class GameplaySettingsPanel:
    def __init__(self, game_instance, quit_callback):
        self.game = game_instance
        self.quit_callback = quit_callback
        self.is_visible = False
        self.create_buttons()
    def create_buttons(self):
        def increase_target():
            global TARGET_PULL
            TARGET_PULL = min(20, TARGET_PULL + 1)
            self.game.check_winner()
        def decrease_target():
            global TARGET_PULL
            TARGET_PULL = max(3, TARGET_PULL - 1)
            self.game.check_winner()
        start_x = SCREEN_W - 245
        self.buttons = [
            Button((start_x, 120, 95, 36), "Target -", decrease_target, FONT_S),
            Button((start_x + 100, 120, 95, 36), "Target +", increase_target, FONT_S),
            Button((start_x, 170, 200, 30), "BACK TO MENU", self.quit_callback, FONT_S),
            Button((start_x, 208, 200, 30), "EXIT APP", terminate_program, FONT_S)
        ]
    def handle_event(self, ev):
        if self.is_visible:
            for b in self.buttons:
                b.handle_event(ev)
    def draw(self, surf):
        if self.is_visible:
            if not self.buttons:
                return
            button_y_top = min(b.rect.y for b in self.buttons)
            button_y_bottom = max(b.rect.y + b.rect.height for b in self.buttons)
            padding_top = 10
            padding_bottom = 10
            panel_height = button_y_bottom - button_y_top + padding_top + padding_bottom
            panel_x = SCREEN_W - 260
            panel_y = button_y_top - padding_top
            panel_rect = pygame.Rect(panel_x, panel_y, 230, panel_height)
            pygame.draw.rect(surf, (240, 240, 240), panel_rect, border_radius=10)

            pygame.draw.rect(surf, WOOD_BORDER, panel_rect, 3, border_radius=10)
            for b in self.buttons:
                b.draw(surf)

# Main Game Logic
class Game:
    def __init__(self, difficulty, mode, quit_callback):
        self.q_start_time = 0
        self.position = 0
        self.difficulty = difficulty
        self.mode = mode
        self.left = PlayerState('left')
        self.right = PlayerState('right')
        self.left_label = PLAYER_NAMES["left"]
        self.right_label = PLAYER_NAMES["right"] if mode == 'PvP' else 'BOT'
        self.quit_callback = quit_callback
        self.bot_active = (mode == 'PvBot')
        self.countdown_active = True
        self.countdown_start_time = pygame.time.get_ticks()
        self.question_text = ""
        self.correct_answer = ""
        self.game_start_time = 0
        self.winner = None
        self.game_over_reason = None
        play_sfx(SOUND_COUNTDOWN)
        self.timer_paused = False
        self.pause_start_time = 0
        self.paused_remaining_time = None  
        self.create_keypads()
        self.generate_question()
        self.settings_panel = GameplaySettingsPanel(self, self.quit_callback)
        right_label_x = SCREEN_W - 220
        self.reset_button = Button((right_label_x, 70, 100, 35), "Reset", self.reset_game_from_button, FONT_S)
        self.settings_button = Button((right_label_x + 110, 70, 50, 35), "Opt", self.toggle_settings, FONT_S)

    def reset_game_from_button(self):
        self.position = 0
        self.left = PlayerState('left')
        self.right = PlayerState('right')
        self.winner = None
        self.game_over_reason = None
        self.countdown_active = True
        self.countdown_start_time = pygame.time.get_ticks()
        self.game_start_time = 0
        play_sfx(SOUND_COUNTDOWN)
        self.generate_question()

    def toggle_settings(self):
        self.settings_panel.is_visible = not self.settings_panel.is_visible
        now = pygame.time.get_ticks()
        if self.settings_panel.is_visible:
            if self.q_start_time > 0 and not self.timer_paused:
                elapsed = now - self.q_start_time
                self.paused_remaining_time = self.time_limit - elapsed  
                self.timer_paused = True
        else:
            if self.timer_paused and self.q_start_time > 0:
                self.q_start_time = now - (self.time_limit - self.paused_remaining_time)
                self.timer_paused = False
                self.paused_remaining_time = None

    def set_bot_answer_time(self):
        base_time = TIME_PER_QUESTION * 1000
        if self.difficulty == 'HARD':
            delay_start = random.randint(int(0.2 * base_time), int(0.4 * base_time))
            self.bot_typing_delay = random.randint(100, 200)
        elif self.difficulty == 'MID':
            delay_start = random.randint(int(0.4 * base_time), int(0.7 * base_time))
            self.bot_typing_delay = random.randint(200, 350)
        else:
            delay_start = random.randint(int(0.6 * base_time), int(0.9 * base_time))
            self.bot_typing_delay = random.randint(350, 500)
        self.bot_answer_time = self.q_start_time + delay_start
        self.bot_answer_string = str(self.correct_answer)
        self.bot_char_index = 0

    def create_keypads(self):
        pad_w, pad_h = 180, 220
        left_x = 40
        right_x = SCREEN_W - pad_w - 150
        y0 = SCREEN_H - pad_h - 30
        self.buttons = []
        def make_num_callback(player, digit):
            return lambda: self.on_digit(player, str(digit))
        for side, x in [('left', left_x), ('right', right_x)]:
            if side == 'right' and self.mode == 'PvBot':
                continue
            digits = [('7', 7), ('8', 8), ('9', 9), ('/', '/'), ('4', 4), ('5', 5), ('6', 6), ('C', 'C'),
                      ('1', 1), ('2', 2), ('3', 3), ('.', '.')]
            col = 0
            row = 0
            btn_w = 52
            btn_h = 48
            spacing = 6
            for i, (label, value) in enumerate(digits):
                bx = x + col * (btn_w + spacing)
                by = y0 + row * (btn_h + spacing)
                def make_cb(val=value, sd=side):
                    if val == 'C':
                        return lambda: self.clear_input(sd)
                    elif val == '.':
                        return lambda: self.on_decimal(sd)
                    elif val == '/':
                        return lambda: self.on_digit(sd, '/')
                    else:
                        return make_num_callback(sd, val)
                self.buttons.append(Button((bx, by, btn_w, btn_h), str(label), make_cb(), FONT_M))
                col += 1
                if col > 3:
                    col = 0
                    row += 1
            ok_x = x + 2 * (btn_w + spacing)
            ok_y = y0 + 3 * (btn_h + spacing)
            self.buttons.append(Button((ok_x, ok_y, btn_w * 2 + spacing, btn_h), "ENTER", lambda s=side: self.submit_input(s), FONT_S))

    def generate_question(self):
        self.question_text, self.correct_answer = generate_mixed_question(self.difficulty)
        self.q_start_time = pygame.time.get_ticks()
        self.time_limit = TIME_PER_QUESTION * 1000
        self.left.reset_input()
        self.right.reset_input()
        if self.bot_active and not self.countdown_active:
            self.set_bot_answer_time()

    def on_digit(self, side, digit_char):
        p = self.left if side == 'left' else self.right
        if len(p.current_input) >= 6:
            return
        p.current_input += digit_char

    def on_decimal(self, side):
        p = self.left if side == 'left' else self.right
        if '.' not in p.current_input:
            p.current_input += '.'

    def clear_input(self, side):
        (self.left if side == 'left' else self.right).reset_input()

    def submit_input(self, side, is_bot=False):
        p = self.left if side == 'left' else self.right
        if not is_bot and p.current_input == "":
            return
        input_val = p.current_input
        correct_val = self.correct_answer
        is_correct = False
        try:
            if '/' in correct_val:
                correct_frac = Fraction(correct_val)
                try:
                    user_frac = Fraction(input_val).limit_denominator()
                    if user_frac == correct_frac:
                        is_correct = True
                except:
                    try:
                        if abs(float(input_val) - float(correct_frac)) < 0.001:
                            is_correct = True
                    except:
                        pass
            else:
                try:
                    if abs(float(input_val) - float(correct_val)) < 0.001:
                        is_correct = True
                except:
                    pass
        except:
            pass
        if is_correct:
            move_amount = 1
            if side == 'left':
                self.position -= move_amount
            else:
                self.position += move_amount
            p.correct_count += 1
            play_sfx(SOUND_CORRECT)
            if self.bot_active:
                self.bot_answer_string = ""
                self.bot_char_index = 0
                self.right.reset_input()
            if abs(self.position) >= TARGET_PULL:
                self.check_winner()
                return
            self.generate_question()
        else:
            if not is_bot:
                play_sfx(SOUND_WRONG)
                p.reset_input()
        self.check_winner()

    def check_winner(self):
        if self.settings_panel.is_visible:
            return
        if abs(self.position) >= TARGET_PULL:
            self.winner = self.left_label if self.position <= -TARGET_PULL else self.right_label
            session_time = (pygame.time.get_ticks() - self.game_start_time) if self.game_start_time else 0
            if self.mode == 'PvBot':
                if self.winner == self.left_label:
                    self.game_over_reason = 'win'
                    add_score(self.left_label, session_time, self.difficulty, mode='PvBot')
                    play_win_sound()
                    if hasattr(self, 'show_game_over_callback'):
                        self.show_game_over_callback('win')
                else:
                    self.game_over_reason = 'lose'
                    play_lose_sound()
                    if hasattr(self, 'show_game_over_callback'):
                        self.show_game_over_callback('lose')
            else:
                add_score(self.left_label, session_time, self.difficulty,
                          mode='PvP', winner_name=self.winner)
                add_score(self.right_label, session_time, self.difficulty,
                          mode='PvP', winner_name=self.winner)
                play_win_sound()
                if hasattr(self, 'show_game_over_callback'):
                    self.show_game_over_callback(
                        self.left_label, self.right_label,
                        self.left.correct_count, self.right.correct_count
                    )

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.settings_panel.is_visible or self.winner:
            return
        if self.countdown_active:
            if now - self.countdown_start_time > 3500:
                self.countdown_active = False
                self.q_start_time = now
                self.game_start_time = now
                if self.bot_active:
                    self.set_bot_answer_time()
            return
        if self.bot_active:
            if (self.bot_char_index < len(self.bot_answer_string) and
                now >= self.bot_answer_time):
                char = self.bot_answer_string[self.bot_char_index]
                self.right.current_input += char
                self.bot_char_index += 1
                self.bot_answer_time = now + self.bot_typing_delay
            elif (self.bot_char_index > 0 and
                  self.bot_char_index == len(self.bot_answer_string)):
                self.submit_input('right', is_bot=True)
        if (self.mode == 'PvP' and
            self.q_start_time > 0 and
            now - self.q_start_time > self.time_limit):
            play_sfx(SOUND_TIMEOUT)
            if self.position >= 0:
                self.position -= 1
            else:
                self.position += 1
            self.generate_question()
            self.check_winner()

    def draw(self, surf):
        if INGAME_WALLPAPER_IMG:
            surf.blit(INGAME_WALLPAPER_IMG, (0, 0))
        else:
            draw_grid_background(surf)
        mid_x = SCREEN_W // 2
        rope_y = SCREEN_H // 2 - 10
        if not self.countdown_active:
            left_label = FONT_L.render(self.left_label, True, COLOR_P1)
            right_label = FONT_L.render(self.right_label, True, COLOR_P2)
            surf.blit(left_label, (60, 20))
            surf.blit(right_label, (SCREEN_W - 60 - right_label.get_width(), 20))
            score_txt = f"{self.left.correct_count} - {self.right.correct_count}"
            score_s = FONT_XL.render(score_txt, True, (0, 0, 0))
            score_m = FONT_XL.render(score_txt, True, TEXT_WHITE)
            s_x = mid_x - score_m.get_width() // 2
            s_y = 20
            surf.blit(score_s, (s_x + 3, s_y + 3))
            surf.blit(score_m, (s_x, s_y))
            qtxt_main = FONT_XL.render(self.question_text, True, (0, 0, 0))
            surf.blit(qtxt_main, (SCREEN_W // 2 - qtxt_main.get_width() // 2 + 2, 182))
            qtxt_main = FONT_XL.render(self.question_text, True, TEXT_WHITE)
            surf.blit(qtxt_main, (SCREEN_W // 2 - qtxt_main.get_width() // 2, 180))
            for b in self.buttons:
                b.draw(surf)
            self.reset_button.draw(surf)
            self.settings_button.draw(surf)
            left_inp_txt = FONT_L.render(self.left.current_input or "0", True, TEXT_BROWN)
            right_inp_txt = FONT_L.render(self.right.current_input or "0", True, TEXT_BROWN)
            surf.blit(left_inp_txt, (60, SCREEN_H - 290))
            surf.blit(right_inp_txt, (SCREEN_W - 160, SCREEN_H - 290))
            if self.q_start_time > 0:
                if self.timer_paused and self.paused_remaining_time is not None:
                    rem = max(0, int(self.paused_remaining_time / 1000))
                else:
                    elapsed = pygame.time.get_ticks() - self.q_start_time
                    rem = max(0, int((self.time_limit - elapsed) / 1000))
            else:
                rem = TIME_PER_QUESTION
            timer_txt = FONT_M.render(f"Time: {rem}s", True, COLOR_P2 if rem <= 5 else TEXT_BROWN)
            surf.blit(timer_txt, (SCREEN_W // 2 - timer_txt.get_width() // 2, SCREEN_H - 320))
        rope_center_x = SCREEN_W // 2 + int(self.position * 18)
        if ROPE_IMG:
            rope_rect = ROPE_IMG.get_rect()
            rope_rect.center = (rope_center_x, rope_y)
            surf.blit(ROPE_IMG, rope_rect)
        else:
            pygame.draw.line(surf, (150, 100, 50), (0, rope_y), (SCREEN_W, rope_y), 10)
            pygame.draw.circle(surf, COLOR_ROPE_DETAIL, (rope_center_x, rope_y), 15)
        if INDICATOR_IMG:
            ind_rect = INDICATOR_IMG.get_rect()
            ind_rect.center = (rope_center_x, rope_y)
            surf.blit(INDICATOR_IMG, ind_rect)
        if TARGET_LINE_IMG:
            offset_dist = TARGET_PULL * 18
            img_width = TARGET_LINE_IMG.get_width()
            img_height = TARGET_LINE_IMG.get_height()
            target_y = rope_y - (img_height // 2)
            surf.blit(TARGET_LINE_IMG, (mid_x - offset_dist - (img_width // 2), target_y))
            surf.blit(TARGET_LINE_IMG, (mid_x + offset_dist - (img_width // 2), target_y))
        else:
            pygame.draw.line(surf, COLOR_P1, (mid_x - TARGET_PULL * 18, 0), (mid_x - TARGET_PULL * 18, SCREEN_H), 4)
            pygame.draw.line(surf, COLOR_P2, (mid_x + TARGET_PULL * 18, 0), (mid_x + TARGET_PULL * 18, SCREEN_H), 4)
        if PLAYER_LEFT_IMG:
            left_char_x = 60
            left_char_y = rope_y - (PLAYER_LEFT_IMG.get_height() // 2) - 30
            surf.blit(PLAYER_LEFT_IMG, (left_char_x, left_char_y))
        else:
            pygame.draw.ellipse(surf, COLOR_P1, (20, rope_y - 40, 80, 80))
        if PLAYER_RIGHT_IMG:
            right_char_x = SCREEN_W - 60 - PLAYER_RIGHT_IMG.get_width()
            right_char_y = rope_y - (PLAYER_RIGHT_IMG.get_height() // 2) - 30
            surf.blit(PLAYER_RIGHT_IMG, (right_char_x, right_char_y))
        else:
            pygame.draw.ellipse(surf, COLOR_P2, (SCREEN_W - 100, rope_y - 40, 80, 80))
        self.settings_panel.draw(surf)
        if self.countdown_active:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill(BLACK_TRANSPARENT)
            surf.blit(overlay, (0, 0))
            now = pygame.time.get_ticks()
            elapsed = now - self.countdown_start_time
            seconds = 3 - int(elapsed / 1000)
            if seconds > 0:
                text = str(seconds)
                col = (255, 255, 255)
            elif elapsed < 3500:
                text = "GO!"
                col = COLOR_P1
            else:
                text = ""
            if text:
                cd_txt = FONT_XL.render(text, True, col)
                scale_factor = 3 if seconds > 0 else 4
                cd_txt_large = pygame.transform.scale(cd_txt, (cd_txt.get_width() * scale_factor, cd_txt.get_height() * scale_factor))
                surf.blit(cd_txt_large, (SCREEN_W // 2 - cd_txt_large.get_width() // 2, SCREEN_H // 2 - cd_txt_large.get_height() // 2))
        if self.winner:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill(BLACK_TRANSPARENT)
            surf.blit(overlay, (0, 0))
            if self.game_over_reason == 'lose':
                msg_txt = "YOU LOSE!"
                col = COLOR_P2
            else:
                msg_txt = f"{self.winner} WINS!"
                col = COLOR_P1
            win_txt = FONT_XL.render(msg_txt, True, col)
            surf.blit(win_txt, (SCREEN_W // 2 - win_txt.get_width() // 2, SCREEN_H // 2 - 60))
            rst_txt = FONT_M.render("Press Reset to play again", True, TEXT_WHITE)
            surf.blit(rst_txt, (SCREEN_W // 2 - rst_txt.get_width() // 2, SCREEN_H // 2 + 20))

# Game Over Screen
class GameOverScreen:
    def __init__(self, reason, player_name=None, p1_name=None, p2_name=None, p1_score=0, p2_score=0, return_callback=None):
        self.reason = reason
        self.player_name = player_name
        self.p1_name = p1_name
        self.p2_name = p2_name
        self.p1_score = p1_score
        self.p2_score = p2_score
        self.return_callback = return_callback
        center_x = SCREEN_W // 2
        self.back_button = Button((center_x - 120, SCREEN_H - 160, 240, 55), "MAIN MENU", return_callback, FONT_L)
    def handle_event(self, ev):
        self.back_button.handle_event(ev)
    def draw(self, surf):
        if WALLPAPER_IMG:
            surf.blit(WALLPAPER_IMG, (0, 0))
        else:
            surf.fill(BG_COLOR)
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(BLACK_TRANSPARENT)
        surf.blit(overlay, (0, 0))
        if self.reason == 'lose':  
            title = FONT_XL.render("GAME OVER", True, COLOR_P2)
            subtitle = FONT_L.render("The BOT was faster!", True, TEXT_WHITE)
            surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 150))
            surf.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 230))
        elif self.reason == 'pvp':  
            trophy = FONT_XL.render("WINNER!", True, (255, 215, 0))
            surf.blit(trophy, (SCREEN_W // 2 - trophy.get_width() // 2, 120))
            winner_name = self.p1_name if self.p1_score > self.p2_score else self.p2_name
            win_txt = FONT_XL.render(winner_name, True, COLOR_P1)
            win_shadow = FONT_XL.render(winner_name, True, (0, 0, 0))
            surf.blit(win_shadow, (SCREEN_W // 2 - win_txt.get_width() // 2 + 3, 200 + 3))
            surf.blit(win_txt, (SCREEN_W // 2 - win_txt.get_width() // 2, 200))
            subtitle = FONT_L.render("WINS THE TUG OF WAR!", True, TEXT_WHITE)
            surf.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 280))
            score_str = f"{self.p1_score} – {self.p2_score}"
            score_txt = FONT_L.render(score_str, True, TEXT_WHITE)
            surf.blit(score_txt, (SCREEN_W // 2 - score_txt.get_width() // 2, 350))
            label = FONT_S.render("Final Score", True, (200, 200, 200))
            surf.blit(label, (SCREEN_W // 2 - label.get_width() // 2, 390))
        self.back_button.draw(surf)

# Main loop 
def main():
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Math Tug of War - Ultimate")
    clock = pygame.time.Clock()
    current_state = STATE_MAIN_MENU
    game_instance = None
    name_input_screen = None
    leaderboard_screen = None
    game_over_screen = None
    audio_settings_screen = None

    def quit_to_menu():
        nonlocal current_state, game_instance, leaderboard_screen, game_over_screen, audio_settings_screen
        current_state = STATE_MAIN_MENU
        game_instance = None
        leaderboard_screen = None
        game_over_screen = None
        audio_settings_screen = None
        restart_bg_music()

    def show_leaderboard():
        nonlocal current_state, leaderboard_screen
        leaderboard_screen = LeaderboardScreen(quit_to_menu, terminate_program)
        current_state = STATE_LEADERBOARD

    def show_audio_settings():
        nonlocal current_state, audio_settings_screen
        audio_settings_screen = AudioSettingsScreen(quit_to_menu)
        current_state = STATE_AUDIO_SETTINGS

    def start_game_play_callback():
        nonlocal current_state, game_instance
        if GAME_MODE == 'PvBot':
            def pvbot_game_over(reason):
                nonlocal current_state, game_over_screen
                if reason == 'win':
                    game_over_screen = GameOverScreen(
                        reason='pvp',
                        p1_name=PLAYER_NAMES["left"],
                        p2_name="BOT",
                        p1_score=game_instance.left.correct_count,
                        p2_score=game_instance.right.correct_count,
                        return_callback=quit_to_menu
                    )
                else:
                    game_over_screen = GameOverScreen(
                        reason='lose',
                        player_name=PLAYER_NAMES["left"],
                        return_callback=quit_to_menu
                    )
                current_state = STATE_GAME_OVER
            game_instance = Game(DIFFICULTY, GAME_MODE, quit_to_menu)
            game_instance.show_game_over_callback = pvbot_game_over
        else:
            game_instance = Game(DIFFICULTY, GAME_MODE, quit_to_menu)
            game_instance.show_game_over_callback = show_game_over_pvp
        current_state = STATE_GAME_PLAY

    def show_game_over_pvp(p1_name, p2_name, p1_score, p2_score):
        nonlocal current_state, game_over_screen
        game_over_screen = GameOverScreen(
            reason='pvp',
            p1_name=p1_name, p2_name=p2_name,
            p1_score=p1_score, p2_score=p2_score,
            return_callback=quit_to_menu
        )
        current_state = STATE_GAME_OVER

    def start_game_callback():
        nonlocal current_state, name_input_screen
        if GAME_MODE == 'PvP':
            name_input_screen = NameInputScreen(start_game_play_callback, quit_to_menu)
            current_state = STATE_NAME_INPUT
        else:
            PLAYER_NAMES["left"] = "YOU"
            PLAYER_NAMES["right"] = "BOT"
            start_game_play_callback()

    main_menu = MainMenu(start_game_callback, show_leaderboard, show_audio_settings)
    running = True
    while running:
        dt = clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                terminate_program()
            if ev.type == pygame.KEYDOWN and (ev.key == pygame.K_RETURN and ev.mod & pygame.KMOD_ALT):
                pygame.display.toggle_fullscreen()
            if current_state == STATE_MAIN_MENU:
                main_menu.handle_event(ev)
            elif current_state == STATE_AUDIO_SETTINGS:
                audio_settings_screen.handle_event(ev)
            elif current_state == STATE_NAME_INPUT:
                name_input_screen.handle_event(ev)
            elif current_state == STATE_GAME_PLAY:
                if game_instance.countdown_active:
                    continue
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if game_instance.reset_button.rect.collidepoint(ev.pos):
                        play_sfx(SOUND_CLICK)
                        game_instance.reset_game_from_button()
                        continue
                    if game_instance.settings_button.rect.collidepoint(ev.pos):
                        play_sfx(SOUND_CLICK)
                        game_instance.toggle_settings()
                        continue
                    if game_instance.settings_panel.is_visible:
                        game_instance.settings_panel.handle_event(ev)
                        continue
                if not game_instance.settings_panel.is_visible:
                    for b in game_instance.buttons:
                        b.handle_event(ev)
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                            quit_to_menu()
                            continue
                        if ev.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                            game_instance.submit_input('left')
                        elif ev.key == pygame.K_BACKSPACE:
                            game_instance.left.current_input = game_instance.left.current_input[:-1]
                        elif ev.unicode.isalnum() or ev.unicode in ['.', '/']:
                            if ev.unicode == '.':
                                game_instance.on_decimal('left')
                            elif ev.unicode == '/':
                                game_instance.on_digit('left', ev.unicode)
                            else:
                                game_instance.on_digit('left', ev.unicode)
            elif current_state == STATE_LEADERBOARD:
                leaderboard_screen.handle_event(ev)
            elif current_state == STATE_GAME_OVER:
                game_over_screen.handle_event(ev)

        if current_state == STATE_MAIN_MENU:
            main_menu.draw(screen)
        elif current_state == STATE_AUDIO_SETTINGS:
            audio_settings_screen.draw(screen)
        elif current_state == STATE_NAME_INPUT:
            name_input_screen.draw(screen)
        elif current_state == STATE_GAME_PLAY:
            if game_instance:
                game_instance.update(dt)
                game_instance.draw(screen)
        elif current_state == STATE_LEADERBOARD:
            if leaderboard_screen:
                leaderboard_screen.draw(screen)
        elif current_state == STATE_GAME_OVER:
            if game_over_screen:
                game_over_screen.draw(screen)

        pygame.display.flip()

    terminate_program()

if __name__ == "__main__":
    main()