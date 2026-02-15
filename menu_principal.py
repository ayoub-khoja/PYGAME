"""
=== MENU PRINCIPAL - SUPER MARIO AVENTURE ETOILEE ===
Ce fichier est le point d'entree du jeu.
Il affiche le menu principal avec :
  - Ecran d'accueil (saisie du nom du joueur)
  - Selection du mode de jeu (Solo / Multijoueur)
  - Configuration multijoueur (Heberger / Rejoindre)

Fichiers lies :
  - jeu_course_3d.py   : Le jeu de course 3D (Ursina)
  - serveur_multijoueur.py : Le serveur pour le mode multijoueur
"""

import pygame
import sys
import os
import math
import random
import subprocess

# Initialisation de Pygame
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    print("Audio non disponible - le jeu continuera sans son")

# Parametres de l'ecran
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("⭐ Super Mario - Aventure Étoilée ⭐")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 153, 0)
GOLD = (255, 215, 0)
DARK_ORANGE = (255, 102, 0)
LIGHT_ORANGE = (255, 180, 50)
DEEP_BLUE = (15, 25, 60)
LIGHT_BLUE = (100, 150, 255)
CYAN = (0, 255, 255)
PURPLE = (150, 50, 255)
PINK = (255, 100, 200)
LIGHT_GRAY = (220, 220, 230)
DARK_GRAY = (40, 40, 50)

# Chargement des ressources
assets_path = os.path.dirname(os.path.abspath(__file__))

# Chargement de l'image de fond
try:
    background = pygame.image.load(os.path.join(assets_path, 'assets', 'background.webp'))
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    background = None

# Chargement de l'image de fleche
try:
    arrow_img = pygame.image.load(os.path.join(assets_path, 'assets', 'arrow.png'))
    arrow_img = pygame.transform.scale(arrow_img, (180, 130))
except:
    arrow_img = None

# Chargement et lecture de la musique de fond
try:
    pygame.mixer.music.load(os.path.join(assets_path, 'assets', '02. Menu.mp3'))
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Could not load music: {e}")

# ============== SYSTEME DE PARTICULES ==============
class Star:
    def __init__(self):
        self.reset()
        self.y = random.randint(0, SCREEN_HEIGHT)
    
    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(-50, -10)
        self.size = random.uniform(1, 4)
        self.speed = random.uniform(0.5, 2)
        self.brightness = random.randint(150, 255)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.twinkle_offset = random.uniform(0, math.pi * 2)
    
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT + 10:
            self.reset()
    
    def draw(self, surface, time):
        twinkle = math.sin(time * self.twinkle_speed + self.twinkle_offset) * 0.3 + 0.7
        alpha = int(self.brightness * twinkle)
        color = (alpha, alpha, int(alpha * 0.9))
        
        # Dessiner la lueur de l'etoile
        if self.size > 2:
            glow_surf = pygame.Surface((int(self.size * 6), int(self.size * 6)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, 50), (int(self.size * 3), int(self.size * 3)), int(self.size * 3))
            surface.blit(glow_surf, (self.x - self.size * 3, self.y - self.size * 3))
        
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class GlowingOrb:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.base_size = random.randint(80, 150)
        self.color = random.choice([PURPLE, CYAN, PINK, LIGHT_BLUE, GOLD])
        self.speed_x = random.uniform(-0.3, 0.3)
        self.speed_y = random.uniform(-0.3, 0.3)
        self.pulse_speed = random.uniform(0.01, 0.03)
        self.pulse_offset = random.uniform(0, math.pi * 2)
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        
        if self.x < -100 or self.x > SCREEN_WIDTH + 100:
            self.speed_x *= -1
        if self.y < -100 or self.y > SCREEN_HEIGHT + 100:
            self.speed_y *= -1
    
    def draw(self, surface, time):
        pulse = math.sin(time * self.pulse_speed + self.pulse_offset) * 0.3 + 0.7
        size = int(self.base_size * pulse)
        
        glow_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        for i in range(size, 0, -5):
            alpha = int(15 * (i / size) * pulse)
            pygame.draw.circle(glow_surf, (*self.color, alpha), (size, size), i)
        
        surface.blit(glow_surf, (int(self.x - size), int(self.y - size)), special_flags=pygame.BLEND_ADD)

# ============== COMPOSANTS D'INTERFACE ==============
class AnimatedButton:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        self.hover_progress = 0
        self.pulse_time = 0
        self.click_scale = 1.0
    
    def draw(self, surface, font, time):
        self.pulse_time = time
        
        # Transition douce au survol
        target = 1.0 if self.is_hovered else 0.0
        self.hover_progress += (target - self.hover_progress) * 0.15
        
        # Animation de clic (echelle)
        self.click_scale += (1.0 - self.click_scale) * 0.2
        
        # Calcul des couleurs
        base_color = ORANGE
        hover_color = GOLD
        r = int(base_color[0] + (hover_color[0] - base_color[0]) * self.hover_progress)
        g = int(base_color[1] + (hover_color[1] - base_color[1]) * self.hover_progress)
        b = int(base_color[2] + (hover_color[2] - base_color[2]) * self.hover_progress)
        
        # Effet de pulsation
        pulse = math.sin(time * 0.003) * 0.05 + 1.0
        scale = self.click_scale * (1.0 + self.hover_progress * 0.05) * pulse
        
        # Dessiner le bouton avec effet lumineux
        scaled_rect = pygame.Rect(
            self.rect.centerx - (self.rect.width * scale) / 2,
            self.rect.centery - (self.rect.height * scale) / 2,
            self.rect.width * scale,
            self.rect.height * scale
        )
        
        # Effet de lueur
        if self.hover_progress > 0.1:
            glow_surf = pygame.Surface((int(scaled_rect.width + 40), int(scaled_rect.height + 40)), pygame.SRCALPHA)
            glow_color = (*GOLD, int(60 * self.hover_progress))
            pygame.draw.rect(glow_surf, glow_color, 
                           (10, 10, scaled_rect.width + 20, scaled_rect.height + 20), 
                           border_radius=20)
            surface.blit(glow_surf, (scaled_rect.x - 20, scaled_rect.y - 20), special_flags=pygame.BLEND_ADD)
        
        # Bouton principal
        pygame.draw.rect(surface, (r, g, b), scaled_rect, border_radius=12)
        
        # Bordure
        border_color = (min(255, r + 50), min(255, g + 50), min(255, b + 50))
        pygame.draw.rect(surface, border_color, scaled_rect, 3, border_radius=12)
        
        # Texte avec ombre
        text_surface = font.render(self.text, True, WHITE)
        shadow_surface = font.render(self.text, True, (50, 30, 0))
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        shadow_rect = shadow_surface.get_rect(center=(scaled_rect.centerx + 2, scaled_rect.centery + 2))
        
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(text_surface, text_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def is_clicked(self, pos, click):
        if self.rect.collidepoint(pos) and click:
            self.click_scale = 0.9
            return True
        return False

class ModernTextInput:
    def __init__(self, x, y, width, height, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.focus_progress = 0
        self.shake_offset = 0
        self.shake_time = 0
    
    def draw(self, surface, font, time):
        # Transition douce de focus
        target = 1.0 if self.active else 0.0
        self.focus_progress += (target - self.focus_progress) * 0.15
        
        # Effet de tremblement
        if self.shake_time > 0:
            self.shake_time -= 1
            self.shake_offset = math.sin(self.shake_time * 0.5) * 5
        else:
            self.shake_offset = 0
        
        draw_rect = self.rect.copy()
        draw_rect.x += self.shake_offset
        
        # Fond avec effet degrade
        bg_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        
        # Fond en degrade
        for i in range(draw_rect.height):
            alpha = 230 - int(i * 0.3)
            color = (255, 255, 255, alpha)
            pygame.draw.line(bg_surf, color, (0, i), (draw_rect.width, i))
        
        # Appliquer le masque de coins arrondis
        pygame.draw.rect(bg_surf, (0, 0, 0, 0), (0, 0, draw_rect.width, draw_rect.height), border_radius=10)
        surface.blit(bg_surf, draw_rect.topleft)
        
        # Fond blanc
        pygame.draw.rect(surface, (255, 255, 255, 240), draw_rect, border_radius=10)
        
        # Bordure avec lueur de focus
        border_color = (
            int(180 + 75 * self.focus_progress),
            int(180 + 35 * self.focus_progress),
            int(180 - 180 * self.focus_progress)
        )
        pygame.draw.rect(surface, border_color, draw_rect, 3, border_radius=10)
        
        # Lueur de focus
        if self.focus_progress > 0.1:
            glow_surf = pygame.Surface((draw_rect.width + 20, draw_rect.height + 20), pygame.SRCALPHA)
            glow_color = (*ORANGE, int(40 * self.focus_progress))
            pygame.draw.rect(glow_surf, glow_color, (5, 5, draw_rect.width + 10, draw_rect.height + 10), border_radius=15)
            surface.blit(glow_surf, (draw_rect.x - 10, draw_rect.y - 10), special_flags=pygame.BLEND_ADD)
        
        # Texte
        if self.text:
            text_surface = font.render(self.text, True, DARK_GRAY)
        else:
            text_surface = font.render(self.placeholder, True, (150, 150, 160))
        
        text_rect = text_surface.get_rect(midleft=(draw_rect.x + 20, draw_rect.centery))
        surface.blit(text_surface, text_rect)
        
        # Curseur anime
        if self.active and self.cursor_visible:
            cursor_x = text_rect.right + 3 if self.text else draw_rect.x + 20
            cursor_height = draw_rect.height - 20
            cursor_y = draw_rect.centery - cursor_height // 2
            
            # Curseur pulsant
            pulse = math.sin(time * 0.01) * 0.3 + 0.7
            cursor_color = (int(255 * pulse), int(153 * pulse), 0)
            pygame.draw.rect(surface, cursor_color, (cursor_x, cursor_y, 3, cursor_height), border_radius=2)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                if self.text.strip():
                    return True
                else:
                    self.shake_time = 30
            elif len(self.text) < 20:
                if event.unicode.isprintable():
                    self.text += event.unicode
        return False
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

class GlassPanel:
    def __init__(self, x, y, width, height, title="", border_color=ORANGE):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.border_color = border_color
        self.appear_progress = 0
    
    def draw(self, surface, title_font, time):
        # Animation d'apparition
        self.appear_progress = min(1.0, self.appear_progress + 0.02)
        
        # Fond avec effet vitre
        glass_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Fond en degrade
        for i in range(self.rect.height):
            progress = i / self.rect.height
            alpha = int((140 - progress * 40) * self.appear_progress)
            r = int(20 + progress * 10)
            g = int(25 + progress * 10)
            b = int(50 + progress * 20)
            pygame.draw.line(glass_surf, (r, g, b, alpha), (0, i), (self.rect.width, i))
        
        surface.blit(glass_surf, self.rect.topleft)
        
        # Bordure lumineuse
        border_alpha = int(200 * self.appear_progress)
        pygame.draw.rect(surface, (*self.border_color, border_alpha), self.rect, 2, border_radius=15)
        
        # Surbrillance interieure
        highlight_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, 30)
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        for i in range(highlight_rect.height):
            alpha = int((40 - i * 1.3) * self.appear_progress)
            if alpha > 0:
                pygame.draw.line(highlight_surf, (255, 255, 255, alpha), (0, i), (highlight_rect.width, i))
        surface.blit(highlight_surf, highlight_rect.topleft)
        
        # Titre avec lueur
        if self.title:
            title_surface = title_font.render(self.title, True, self.border_color)
            title_rect = title_surface.get_rect(centerx=self.rect.centerx, top=self.rect.top + 15)
            
            # Lueur du titre
            glow_surf = pygame.Surface((title_rect.width + 40, title_rect.height + 20), pygame.SRCALPHA)
            glow_title = title_font.render(self.title, True, (*self.border_color, 100))
            glow_surf.blit(glow_title, (20, 10))
            surface.blit(glow_surf, (title_rect.x - 20, title_rect.y - 10), special_flags=pygame.BLEND_ADD)
            
            surface.blit(title_surface, title_rect)
            
            return title_rect.bottom + 20
        
        return self.rect.top + 15

# ============== POLICES D'ECRITURE ==============
pygame.font.init()
try:
    title_font = pygame.font.Font(None, 58)
    subtitle_font = pygame.font.Font(None, 42)
    text_font = pygame.font.Font(None, 26)
    button_font = pygame.font.Font(None, 38)
    input_font = pygame.font.Font(None, 30)
    level_title_font = pygame.font.Font(None, 32)
except:
    title_font = pygame.font.SysFont('arial', 44, bold=True)
    subtitle_font = pygame.font.SysFont('arial', 32, bold=True)
    text_font = pygame.font.SysFont('arial', 20)
    button_font = pygame.font.SysFont('arial', 28, bold=True)
    input_font = pygame.font.SysFont('arial', 22)
    level_title_font = pygame.font.SysFont('arial', 24, bold=True)

# ============== ECRAN D'ACCUEIL ==============
class HomeScreen:
    def __init__(self):
        # Particules
        self.stars = [Star() for _ in range(100)]
        self.orbs = [GlowingOrb() for _ in range(5)]
        
        # Elements d'interface
        self.left_panel = GlassPanel(50, 80, 520, 520, "SUPER MARIO\n- AVENTURE ÉTOILÉE -", GOLD)
        self.right_panel = GlassPanel(830, 80, 520, 620, "", CYAN)
        
        self.text_input = ModernTextInput(900, 250, 380, 55, "✏️ Entrez votre nom...")
        self.start_button = AnimatedButton(940, 340, 300, 60, "🎮 Démarrer le Jeu")
        
        # Etat
        self.player_name = ""
        self.show_toast = False
        self.toast_message = ""
        self.toast_alpha = 0
        self.toast_timer = 0
        self.game_started = False
        self.start_countdown = 0
        self.time = 0
        
        # Descriptions des niveaux
        self.levels = [
            {
                "title": "🌟 Niveau 1 : L'Explorer Normal",
                "desc": "Dans ce premier niveau, Mario doit récupérer toutes les étoiles disséminées sur la scène tout en évitant les pièges des bombes.",
                "color": GOLD
            },
            {
                "title": "🔥 Niveau 2 : L'Aventure en Mutation",
                "desc": "Le niveau change dynamiquement ! La scène se modifie à chaque étape, avec de nouveaux obstacles qui apparaissent.",
                "color": ORANGE
            },
            {
                "title": "💀 Niveau 3 : Le Défi Ultime",
                "desc": "Le dernier niveau est le plus difficile. Les bombes sont plus nombreuses et la scène est plus complexe.",
                "color": PINK
            }
        ]
    
    def draw_wrapped_text(self, surface, text, font, color, rect, line_spacing=5):
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= rect.width - 30:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
        
        y = rect.y
        for line in lines:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (rect.x + 15, y))
            y += font.get_height() + line_spacing
        
        return y
    
    def draw_key(self, surface, x, y, symbol, size=50):
        # Fond de touche avec degrade
        key_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Degrade
        for i in range(size):
            progress = i / size
            gray = int(255 - progress * 40)
            pygame.draw.line(key_surf, (gray, gray, gray, 240), (0, i), (size, i))
        
        # Dessiner sur la surface principale
        pygame.draw.rect(surface, WHITE, (x, y, size, size), border_radius=8)
        
        # Bordure
        pygame.draw.rect(surface, (200, 200, 200), (x, y, size, size), 2, border_radius=8)
        
        # Effet d'ombre
        pygame.draw.line(surface, (180, 180, 180), (x + 5, y + size - 5), (x + size - 5, y + size - 5), 3)
        pygame.draw.line(surface, (180, 180, 180), (x + size - 5, y + 5), (x + size - 5, y + size - 5), 3)
        
        # Symbole
        symbol_font = pygame.font.Font(None, 36)
        symbol_surface = symbol_font.render(symbol, True, DARK_GRAY)
        symbol_rect = symbol_surface.get_rect(center=(x + size // 2, y + size // 2))
        surface.blit(symbol_surface, symbol_rect)
    
    def draw(self, surface):
        self.time += 1
        
        # Dessiner le fond
        if background:
            surface.blit(background, (0, 0))
        else:
            # Degrade anime (si pas d'image de fond)
            for y in range(SCREEN_HEIGHT):
                progress = y / SCREEN_HEIGHT
                wave = math.sin(self.time * 0.002 + progress * 3) * 10
                r = int(15 + wave)
                g = int(25 + progress * 20 + wave)
                b = int(60 + progress * 40)
                pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # Dessiner les orbes (lueur de fond)
        for orb in self.orbs:
            orb.update()
            orb.draw(surface, self.time)
        
        # Dessiner les etoiles
        for star in self.stars:
            star.update()
            star.draw(surface, self.time)
        
        # Dessiner le panneau gauche (description du jeu)
        y_offset = self.left_panel.draw(surface, subtitle_font, self.time)
        
        # Titre
        title_text = subtitle_font.render("SUPER MARIO", True, GOLD)
        title_rect = title_text.get_rect(centerx=self.left_panel.rect.centerx, top=self.left_panel.rect.top + 20)
        
        # Lueur du titre
        glow_surf = pygame.Surface((title_rect.width + 20, title_rect.height + 10), pygame.SRCALPHA)
        glow_text = subtitle_font.render("SUPER MARIO", True, (*GOLD, 80))
        glow_surf.blit(glow_text, (10, 5))
        surface.blit(glow_surf, (title_rect.x - 10, title_rect.y - 5), special_flags=pygame.BLEND_ADD)
        surface.blit(title_text, title_rect)
        
        subtitle_text = subtitle_font.render("- AVENTURE ÉTOILÉE -", True, ORANGE)
        subtitle_rect = subtitle_text.get_rect(centerx=self.left_panel.rect.centerx, top=title_rect.bottom + 5)
        surface.blit(subtitle_text, subtitle_rect)
        
        # Dessiner les niveaux
        y_offset = subtitle_rect.bottom + 25
        for level in self.levels:
            # Titre du niveau
            level_title = level_title_font.render(level["title"], True, level["color"])
            surface.blit(level_title, (self.left_panel.rect.x + 20, y_offset))
            y_offset += 35
            
            # Description du niveau
            desc_rect = pygame.Rect(self.left_panel.rect.x + 20, y_offset, self.left_panel.rect.width - 40, 80)
            y_offset = self.draw_wrapped_text(surface, level["desc"], text_font, LIGHT_GRAY, desc_rect)
            y_offset += 20
        
        # Dessiner le panneau droit (bienvenue)
        self.right_panel.draw(surface, subtitle_font, self.time)
        
        # Titre de bienvenue avec animation
        pulse = math.sin(self.time * 0.003) * 0.05 + 1.0
        welcome_font_size = int(48 * pulse)
        
        welcome_text = title_font.render("Bienvenue dans le Jeu", True, WHITE)
        welcome_rect = welcome_text.get_rect(centerx=self.right_panel.rect.centerx, top=self.right_panel.rect.top + 30)
        
        # Lueur
        glow_surf = pygame.Surface((welcome_rect.width + 30, welcome_rect.height + 20), pygame.SRCALPHA)
        glow_text = title_font.render("Bienvenue dans le Jeu", True, (*CYAN, 60))
        glow_surf.blit(glow_text, (15, 10))
        surface.blit(glow_surf, (welcome_rect.x - 15, welcome_rect.y - 10), special_flags=pygame.BLEND_ADD)
        surface.blit(welcome_text, welcome_rect)
        
        # Sous-titre
        sub_text = text_font.render("Entrez votre nom pour commencer à jouer !", True, LIGHT_GRAY)
        sub_rect = sub_text.get_rect(centerx=self.right_panel.rect.centerx, top=welcome_rect.bottom + 15)
        surface.blit(sub_text, sub_rect)
        
        # Champ de texte
        self.text_input.draw(surface, input_font, self.time)
        
        # Bouton demarrer
        self.start_button.draw(surface, button_font, self.time)
        
        # Section "Comment jouer"
        how_to_play_y = self.start_button.rect.bottom + 40
        
        # Titre de la section
        how_title = subtitle_font.render("🎮 Comment jouer !", True, WHITE)
        how_rect = how_title.get_rect(centerx=self.right_panel.rect.centerx, top=how_to_play_y)
        surface.blit(how_title, how_rect)
        
        # Touches flechees
        if arrow_img:
            img_rect = arrow_img.get_rect(centerx=self.right_panel.rect.centerx, top=how_rect.bottom + 20)
            surface.blit(arrow_img, img_rect)
        else:
            key_size = 50
            key_spacing = 8
            start_x = self.right_panel.rect.centerx - key_size - key_spacing // 2
            start_y = how_rect.bottom + 30
            
            # Haut
            self.draw_key(surface, start_x, start_y, "↑", key_size)
            # Rangee du bas
            self.draw_key(surface, start_x - key_size - key_spacing, start_y + key_size + key_spacing, "←", key_size)
            self.draw_key(surface, start_x, start_y + key_size + key_spacing, "↓", key_size)
            self.draw_key(surface, start_x + key_size + key_spacing, start_y + key_size + key_spacing, "→", key_size)
        
        # Instructions de jeu
        instructions = [
            "Utilisez les flèches pour vous déplacer",
            "Collectez les ⭐ et évitez les 💣"
        ]
        inst_y = how_rect.bottom + 160
        for inst in instructions:
            inst_text = text_font.render(inst, True, LIGHT_GRAY)
            inst_rect = inst_text.get_rect(centerx=self.right_panel.rect.centerx, top=inst_y)
            surface.blit(inst_text, inst_rect)
            inst_y += 28
        
        # Notification toast
        if self.show_toast and self.toast_alpha > 0:
            toast_width = 600
            toast_height = 80
            toast_x = (SCREEN_WIDTH - toast_width) // 2
            toast_y = SCREEN_HEIGHT - 120
            
            # Fond du toast avec degrade
            toast_surf = pygame.Surface((toast_width, toast_height), pygame.SRCALPHA)
            for i in range(toast_height):
                alpha = int(min(220, self.toast_alpha) * (1 - abs(i - toast_height // 2) / toast_height))
                pygame.draw.line(toast_surf, (30, 35, 60, alpha), (0, i), (toast_width, i))
            
            surface.blit(toast_surf, (toast_x, toast_y))
            pygame.draw.rect(surface, (*GOLD, min(255, self.toast_alpha)), 
                           (toast_x, toast_y, toast_width, toast_height), 2, border_radius=15)
            
            # Texte du toast
            toast_text = subtitle_font.render(self.toast_message, True, GOLD)
            toast_text.set_alpha(min(255, self.toast_alpha))
            toast_text_rect = toast_text.get_rect(center=(SCREEN_WIDTH // 2, toast_y + toast_height // 2))
            surface.blit(toast_text, toast_text_rect)
    
    def update(self, events, mouse_pos):
        click = False
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True
            
            if self.text_input.handle_event(event):
                if self.text_input.text.strip():
                    self.start_game()
        
        self.text_input.update()
        self.start_button.check_hover(mouse_pos)
        
        if self.start_button.is_clicked(mouse_pos, click) and self.text_input.text.strip():
            self.start_game()
        
        # Disparition du toast
        if self.show_toast:
            self.toast_timer -= 1
            if self.toast_timer <= 60:
                self.toast_alpha = max(0, self.toast_alpha - 4)
            if self.toast_timer <= 0:
                self.show_toast = False
        
        # Compte a rebours avant lancement
        if self.game_started:
            self.start_countdown -= 1
            if self.start_countdown <= 0:
                return "launch_game"
        
        return None
    
    def start_game(self):
        self.player_name = self.text_input.text
        self.show_toast = True
        self.toast_message = f"✨ Bienvenue {self.player_name} !"
        self.toast_alpha = 255
        self.toast_timer = 90
        self.game_started = True
        self.start_countdown = 90


# ============== ECRAN DE SELECTION DU MODE ==============
class ModeScreen:
    """Ecran de selection : Solo ou Multijoueur"""

    def __init__(self, player_name):
        self.player_name = player_name
        self.time = 0

        # Particules
        self.stars = [Star() for _ in range(80)]
        self.orbs = [GlowingOrb() for _ in range(4)]

        # Boutons
        btn_w, btn_h = 380, 120
        cx = SCREEN_WIDTH // 2
        self.solo_btn = AnimatedButton(cx - btn_w - 40, 380, btn_w, btn_h, "1 Joueur (Solo)")
        self.multi_btn = AnimatedButton(cx + 40, 380, btn_w, btn_h, "2 Joueurs (LAN)")
        self.back_btn = AnimatedButton(cx - 100, 580, 200, 50, "Retour")

    def draw(self, surface):
        self.time += 1

        # Fond d'ecran
        if background:
            surface.blit(background, (0, 0))
        else:
            for y in range(SCREEN_HEIGHT):
                progress = y / SCREEN_HEIGHT
                r = int(15 + math.sin(self.time * 0.002 + progress * 3) * 10)
                g = int(25 + progress * 20)
                b = int(60 + progress * 40)
                pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Orbes lumineux
        for orb in self.orbs:
            orb.update()
            orb.draw(surface, self.time)

        # Etoiles
        for star in self.stars:
            star.update()
            star.draw(surface, self.time)

        # Panel de fond central
        panel_w, panel_h = 900, 520
        px = (SCREEN_WIDTH - panel_w) // 2
        py = 80
        glass = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        for i in range(panel_h):
            prog = i / panel_h
            alpha = int(150 - prog * 30)
            r = int(15 + prog * 10)
            g = int(20 + prog * 10)
            b = int(45 + prog * 20)
            pygame.draw.line(glass, (r, g, b, alpha), (0, i), (panel_w, i))
        surface.blit(glass, (px, py))
        pygame.draw.rect(surface, (*GOLD, 180), (px, py, panel_w, panel_h), 2, border_radius=15)

        # Titre
        title1 = title_font.render("SUPER MARIO", True, GOLD)
        r1 = title1.get_rect(centerx=SCREEN_WIDTH // 2, top=py + 25)
        surface.blit(title1, r1)

        title2 = subtitle_font.render("- AVENTURE ETOILEE -", True, ORANGE)
        r2 = title2.get_rect(centerx=SCREEN_WIDTH // 2, top=r1.bottom + 5)
        surface.blit(title2, r2)

        # Nom du joueur
        name_text = subtitle_font.render(f"Joueur : {self.player_name}", True, WHITE)
        name_rect = name_text.get_rect(centerx=SCREEN_WIDTH // 2, top=r2.bottom + 20)
        surface.blit(name_text, name_rect)

        # Séparateur
        sep_y = name_rect.bottom + 15
        pygame.draw.line(surface, (*GOLD, 100), (px + 50, sep_y), (px + panel_w - 50, sep_y), 1)

        # Texte "Choisissez votre mode"
        mode_text = subtitle_font.render("Choisissez votre mode de jeu", True, LIGHT_GRAY)
        mode_rect = mode_text.get_rect(centerx=SCREEN_WIDTH // 2, top=sep_y + 20)
        surface.blit(mode_text, mode_rect)

        # Icônes au-dessus des boutons
        solo_icon = title_font.render("🎮", True, WHITE)
        solo_icon_rect = solo_icon.get_rect(centerx=self.solo_btn.rect.centerx, bottom=self.solo_btn.rect.top - 10)
        surface.blit(solo_icon, solo_icon_rect)

        multi_icon = title_font.render("👥", True, WHITE)
        multi_icon_rect = multi_icon.get_rect(centerx=self.multi_btn.rect.centerx, bottom=self.multi_btn.rect.top - 10)
        surface.blit(multi_icon, multi_icon_rect)

        # Boutons
        self.solo_btn.draw(surface, button_font, self.time)
        self.multi_btn.draw(surface, button_font, self.time)
        self.back_btn.draw(surface, text_font, self.time)

        # Description sous les boutons
        solo_desc = text_font.render("Parcours solo avec coins et bombes", True, LIGHT_GRAY)
        solo_desc_rect = solo_desc.get_rect(centerx=self.solo_btn.rect.centerx, top=self.solo_btn.rect.bottom + 15)
        surface.blit(solo_desc, solo_desc_rect)

        multi_desc = text_font.render("2 joueurs en Wi-Fi local - qui collecte le plus ?", True, LIGHT_GRAY)
        multi_desc_rect = multi_desc.get_rect(centerx=self.multi_btn.rect.centerx, top=self.multi_btn.rect.bottom + 15)
        surface.blit(multi_desc, multi_desc_rect)

    def update(self, events, mouse_pos):
        click = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True

        self.solo_btn.check_hover(mouse_pos)
        self.multi_btn.check_hover(mouse_pos)
        self.back_btn.check_hover(mouse_pos)

        if self.solo_btn.is_clicked(mouse_pos, click):
            return "solo"
        if self.multi_btn.is_clicked(mouse_pos, click):
            return "multi"
        if self.back_btn.is_clicked(mouse_pos, click):
            return "back"

        return None


# ============== ECRAN DE CONFIGURATION MULTIJOUEUR ==============
class MultiScreen:
    """Ecran de configuration multijoueur : Heberger ou Rejoindre"""

    def __init__(self, player_name):
        self.player_name = player_name
        self.time = 0

        self.stars = [Star() for _ in range(80)]
        self.orbs = [GlowingOrb() for _ in range(3)]

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 380, 100

        self.host_btn = AnimatedButton(cx - btn_w - 40, 340, btn_w, btn_h, "Heberger (Serveur)")
        self.join_btn = AnimatedButton(cx + 40, 340, btn_w, btn_h, "Rejoindre (Client)")
        self.back_btn = AnimatedButton(cx - 100, 650, 200, 50, "Retour")

        # Champ IP pour rejoindre
        self.ip_input = ModernTextInput(cx - 190, 490, 380, 55, "IP du serveur (ex: 192.168.1.20)")
        # Champ code de la salle
        self.code_input = ModernTextInput(cx - 190, 560, 380, 55, "Code de la partie")
        self.connect_btn = AnimatedButton(cx - 120, 640, 240, 55, "Se connecter")

        self.mode = None  # None, "host", "join"
        self.launching = False
        self.launch_timer = 0

    def draw(self, surface):
        self.time += 1

        if background:
            surface.blit(background, (0, 0))
        else:
            for y in range(SCREEN_HEIGHT):
                progress = y / SCREEN_HEIGHT
                r = int(15)
                g = int(25 + progress * 20)
                b = int(60 + progress * 40)
                pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        for orb in self.orbs:
            orb.update()
            orb.draw(surface, self.time)
        for star in self.stars:
            star.update()
            star.draw(surface, self.time)

        # Panel
        panel_w, panel_h = 900, 600
        px = (SCREEN_WIDTH - panel_w) // 2
        py = 60
        glass = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        for i in range(panel_h):
            prog = i / panel_h
            alpha = int(150 - prog * 30)
            pygame.draw.line(glass, (15, 20, 45, alpha), (0, i), (panel_w, i))
        surface.blit(glass, (px, py))
        pygame.draw.rect(surface, (*CYAN, 180), (px, py, panel_w, panel_h), 2, border_radius=15)

        # Titre
        title1 = title_font.render("MULTIJOUEUR LAN", True, CYAN)
        r1 = title1.get_rect(centerx=SCREEN_WIDTH // 2, top=py + 20)
        surface.blit(title1, r1)

        title2 = subtitle_font.render(f"Joueur : {self.player_name}", True, GOLD)
        r2 = title2.get_rect(centerx=SCREEN_WIDTH // 2, top=r1.bottom + 10)
        surface.blit(title2, r2)

        sep_y = r2.bottom + 15
        pygame.draw.line(surface, (*CYAN, 100), (px + 50, sep_y), (px + panel_w - 50, sep_y), 1)

        if self.mode is None:
            # Choix héberger / rejoindre
            choose_text = subtitle_font.render("Choisissez votre role", True, LIGHT_GRAY)
            choose_rect = choose_text.get_rect(centerx=SCREEN_WIDTH // 2, top=sep_y + 20)
            surface.blit(choose_text, choose_rect)

            self.host_btn.draw(surface, button_font, self.time)
            self.join_btn.draw(surface, button_font, self.time)

            host_desc = text_font.render("Lance le serveur sur ce PC", True, LIGHT_GRAY)
            surface.blit(host_desc, host_desc.get_rect(centerx=self.host_btn.rect.centerx, top=self.host_btn.rect.bottom + 10))

            join_desc = text_font.render("Rejoint un serveur existant", True, LIGHT_GRAY)
            surface.blit(join_desc, join_desc.get_rect(centerx=self.join_btn.rect.centerx, top=self.join_btn.rect.bottom + 10))

        elif self.mode == "host":
            info = subtitle_font.render("Lancement du serveur...", True, GOLD)
            surface.blit(info, info.get_rect(centerx=SCREEN_WIDTH // 2, top=sep_y + 40))
            tip = text_font.render("Le serveur va demarrer. Partagez votre IP avec l'autre joueur.", True, LIGHT_GRAY)
            surface.blit(tip, tip.get_rect(centerx=SCREEN_WIDTH // 2, top=sep_y + 90))
            tip2 = text_font.render("Ensuite lancez jeu_course_3d.py sur ce PC aussi pour jouer.", True, LIGHT_GRAY)
            surface.blit(tip2, tip2.get_rect(centerx=SCREEN_WIDTH // 2, top=sep_y + 120))

        elif self.mode == "join":
            info = subtitle_font.render("Rejoindre une partie", True, CYAN)
            surface.blit(info, info.get_rect(centerx=SCREEN_WIDTH // 2, top=sep_y + 20))

            tip = text_font.render("Entrez l'IP et le code de la partie :", True, LIGHT_GRAY)
            surface.blit(tip, tip.get_rect(centerx=SCREEN_WIDTH // 2, top=sep_y + 55))

            self.ip_input.draw(surface, input_font, self.time)
            self.code_input.draw(surface, input_font, self.time)
            self.connect_btn.draw(surface, button_font, self.time)

        self.back_btn.draw(surface, text_font, self.time)

    def update(self, events, mouse_pos):
        click = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True
            if self.mode == "join":
                self.ip_input.handle_event(event)
                self.code_input.handle_event(event)

        if self.mode == "join":
            self.ip_input.update()
            self.code_input.update()
            self.connect_btn.check_hover(mouse_pos)

        self.back_btn.check_hover(mouse_pos)

        if self.launching:
            self.launch_timer -= 1
            if self.launch_timer <= 0:
                if self.mode == "host":
                    return "launch_server"
                elif self.mode == "join":
                    return "launch_client"

        if self.mode is None:
            self.host_btn.check_hover(mouse_pos)
            self.join_btn.check_hover(mouse_pos)

            if self.host_btn.is_clicked(mouse_pos, click):
                self.mode = "host"
                self.launching = True
                self.launch_timer = 60
            if self.join_btn.is_clicked(mouse_pos, click):
                self.mode = "join"
        elif self.mode == "join":
            if self.connect_btn.is_clicked(mouse_pos, click) and self.ip_input.text.strip() and self.code_input.text.strip():
                self.launching = True
                self.launch_timer = 30

        if self.back_btn.is_clicked(mouse_pos, click):
            if self.mode is not None:
                self.mode = None
                self.launching = False
            else:
                return "back"

        return None

def main():
    global screen
    clock = pygame.time.Clock()

    # Écrans
    current_screen = "home"  # "home", "mode", "multi"
    home_screen = HomeScreen()
    mode_screen = None
    multi_screen = None
    player_name = ""

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # ============== HOME SCREEN (saisie du nom) ==============
        if current_screen == "home":
            result = home_screen.update(events, mouse_pos)
            home_screen.draw(screen)

            if result == "launch_game":
                player_name = home_screen.player_name
                mode_screen = ModeScreen(player_name)
                current_screen = "mode"

        # ============== MODE SELECTION (Solo / Multijoueur) ==============
        elif current_screen == "mode":
            result = mode_screen.update(events, mouse_pos)
            mode_screen.draw(screen)

            if result == "solo":
                # Lancer le jeu solo 3D
                try:
                    pygame.mixer.music.stop()
                except:
                    pass
                pygame.quit()
                game_path = os.path.join(os.path.dirname(__file__), 'jeu_course_3d.py')
                subprocess.run(['python', game_path, player_name])
                running = False
                break

            elif result == "multi":
                multi_screen = MultiScreen(player_name)
                current_screen = "multi"

            elif result == "back":
                current_screen = "home"
                home_screen.game_started = False
                home_screen.start_countdown = 0

        # ============== MULTIPLAYER SETUP ==============
        elif current_screen == "multi":
            result = multi_screen.update(events, mouse_pos)
            multi_screen.draw(screen)

            if result == "launch_server":
                # Lancer le serveur 3D + le jeu 3D en mode multi
                try:
                    pygame.mixer.music.stop()
                except:
                    pass
                pygame.quit()
                base_dir = os.path.dirname(os.path.abspath(__file__))
                server_path = os.path.join(base_dir, 'serveur_multijoueur.py')
                game_path = os.path.join(base_dir, 'jeu_course_3d.py')
                # Tuer les anciens serveurs : par titre de fenêtre ET par port 5556
                import time as t
                try:
                    subprocess.run('taskkill /F /FI "WINDOWTITLE eq SERVEUR_3D*" 2>nul', shell=True, capture_output=True)
                except:
                    pass
                try:
                    # Trouver et tuer tout processus sur le port 5556
                    result = subprocess.run('netstat -ano | findstr :5556 | findstr LISTENING',
                                          shell=True, capture_output=True, text=True)
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split()
                            pid = parts[-1]
                            if pid.isdigit() and int(pid) > 0:
                                subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                except:
                    pass
                t.sleep(2)
                # Ouvrir le serveur 3D dans une nouvelle console
                subprocess.Popen(
                    f'start "SERVEUR_3D" cmd /k "cd /d {base_dir} && python serveur_multijoueur.py"',
                    shell=True,
                )
                t.sleep(7)  # Attendre que le serveur démarre bien
                # Lancer le jeu 3D en mode multijoueur
                subprocess.run(
                    ['python', game_path, player_name, '--multi', '127.0.0.1', 'AYOUB-YASSMINE'],
                    cwd=base_dir
                )
                running = False
                break

            elif result == "launch_client":
                try:
                    pygame.mixer.music.stop()
                except:
                    pass
                server_ip = multi_screen.ip_input.text.strip()
                room_code = multi_screen.code_input.text.strip()
                pygame.quit()
                base_dir = os.path.dirname(os.path.abspath(__file__))
                game_path = os.path.join(base_dir, 'jeu_course_3d.py')
                # Lancer le jeu 3D en mode multijoueur (client)
                subprocess.run(
                    ['python', game_path, player_name, '--multi', server_ip, room_code],
                    cwd=base_dir
                )
                running = False
                break

            elif result == "back":
                current_screen = "mode"

        pygame.display.flip()
        clock.tick(60)

    try:
        pygame.quit()
    except:
        pass
    sys.exit()

if __name__ == "__main__":
    main()
