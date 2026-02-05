import pygame
import sys
import os
import math
import random

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Screen settings
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("⭐ Super Mario - Aventure Étoilée ⭐")

# Colors
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

# Load assets
assets_path = os.path.dirname(os.path.abspath(__file__))

# Load background
try:
    background = pygame.image.load(os.path.join(assets_path, 'assets', 'background.webp'))
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
except:
    background = None

# Load arrow image
try:
    arrow_img = pygame.image.load(os.path.join(assets_path, 'assets', 'arrow.png'))
    arrow_img = pygame.transform.scale(arrow_img, (180, 130))
except:
    arrow_img = None

# Load and play background music
try:
    pygame.mixer.music.load(os.path.join(assets_path, 'assets', '02. Menu.mp3'))
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Could not load music: {e}")

# ============== PARTICLE SYSTEM ==============
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
        
        # Draw star glow
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

# ============== UI COMPONENTS ==============
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
        
        # Smooth hover transition
        target = 1.0 if self.is_hovered else 0.0
        self.hover_progress += (target - self.hover_progress) * 0.15
        
        # Click scale animation
        self.click_scale += (1.0 - self.click_scale) * 0.2
        
        # Calculate colors
        base_color = ORANGE
        hover_color = GOLD
        r = int(base_color[0] + (hover_color[0] - base_color[0]) * self.hover_progress)
        g = int(base_color[1] + (hover_color[1] - base_color[1]) * self.hover_progress)
        b = int(base_color[2] + (hover_color[2] - base_color[2]) * self.hover_progress)
        
        # Pulse effect
        pulse = math.sin(time * 0.003) * 0.05 + 1.0
        scale = self.click_scale * (1.0 + self.hover_progress * 0.05) * pulse
        
        # Draw button with glow
        scaled_rect = pygame.Rect(
            self.rect.centerx - (self.rect.width * scale) / 2,
            self.rect.centery - (self.rect.height * scale) / 2,
            self.rect.width * scale,
            self.rect.height * scale
        )
        
        # Glow effect
        if self.hover_progress > 0.1:
            glow_surf = pygame.Surface((int(scaled_rect.width + 40), int(scaled_rect.height + 40)), pygame.SRCALPHA)
            glow_color = (*GOLD, int(60 * self.hover_progress))
            pygame.draw.rect(glow_surf, glow_color, 
                           (10, 10, scaled_rect.width + 20, scaled_rect.height + 20), 
                           border_radius=20)
            surface.blit(glow_surf, (scaled_rect.x - 20, scaled_rect.y - 20), special_flags=pygame.BLEND_ADD)
        
        # Main button
        pygame.draw.rect(surface, (r, g, b), scaled_rect, border_radius=12)
        
        # Border
        border_color = (min(255, r + 50), min(255, g + 50), min(255, b + 50))
        pygame.draw.rect(surface, border_color, scaled_rect, 3, border_radius=12)
        
        # Text with shadow
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
        # Smooth focus transition
        target = 1.0 if self.active else 0.0
        self.focus_progress += (target - self.focus_progress) * 0.15
        
        # Shake effect
        if self.shake_time > 0:
            self.shake_time -= 1
            self.shake_offset = math.sin(self.shake_time * 0.5) * 5
        else:
            self.shake_offset = 0
        
        draw_rect = self.rect.copy()
        draw_rect.x += self.shake_offset
        
        # Background with gradient effect
        bg_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        
        # Gradient background
        for i in range(draw_rect.height):
            alpha = 230 - int(i * 0.3)
            color = (255, 255, 255, alpha)
            pygame.draw.line(bg_surf, color, (0, i), (draw_rect.width, i))
        
        # Apply rounded corners mask
        pygame.draw.rect(bg_surf, (0, 0, 0, 0), (0, 0, draw_rect.width, draw_rect.height), border_radius=10)
        surface.blit(bg_surf, draw_rect.topleft)
        
        # White background
        pygame.draw.rect(surface, (255, 255, 255, 240), draw_rect, border_radius=10)
        
        # Border with focus glow
        border_color = (
            int(180 + 75 * self.focus_progress),
            int(180 + 35 * self.focus_progress),
            int(180 - 180 * self.focus_progress)
        )
        pygame.draw.rect(surface, border_color, draw_rect, 3, border_radius=10)
        
        # Focus glow
        if self.focus_progress > 0.1:
            glow_surf = pygame.Surface((draw_rect.width + 20, draw_rect.height + 20), pygame.SRCALPHA)
            glow_color = (*ORANGE, int(40 * self.focus_progress))
            pygame.draw.rect(glow_surf, glow_color, (5, 5, draw_rect.width + 10, draw_rect.height + 10), border_radius=15)
            surface.blit(glow_surf, (draw_rect.x - 10, draw_rect.y - 10), special_flags=pygame.BLEND_ADD)
        
        # Text
        if self.text:
            text_surface = font.render(self.text, True, DARK_GRAY)
        else:
            text_surface = font.render(self.placeholder, True, (150, 150, 160))
        
        text_rect = text_surface.get_rect(midleft=(draw_rect.x + 20, draw_rect.centery))
        surface.blit(text_surface, text_rect)
        
        # Animated cursor
        if self.active and self.cursor_visible:
            cursor_x = text_rect.right + 3 if self.text else draw_rect.x + 20
            cursor_height = draw_rect.height - 20
            cursor_y = draw_rect.centery - cursor_height // 2
            
            # Pulsing cursor
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
        # Animate appearance
        self.appear_progress = min(1.0, self.appear_progress + 0.02)
        
        # Glass effect background
        glass_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Gradient background
        for i in range(self.rect.height):
            progress = i / self.rect.height
            alpha = int((140 - progress * 40) * self.appear_progress)
            r = int(20 + progress * 10)
            g = int(25 + progress * 10)
            b = int(50 + progress * 20)
            pygame.draw.line(glass_surf, (r, g, b, alpha), (0, i), (self.rect.width, i))
        
        surface.blit(glass_surf, self.rect.topleft)
        
        # Glowing border
        border_alpha = int(200 * self.appear_progress)
        pygame.draw.rect(surface, (*self.border_color, border_alpha), self.rect, 2, border_radius=15)
        
        # Inner highlight
        highlight_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, 30)
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        for i in range(highlight_rect.height):
            alpha = int((40 - i * 1.3) * self.appear_progress)
            if alpha > 0:
                pygame.draw.line(highlight_surf, (255, 255, 255, alpha), (0, i), (highlight_rect.width, i))
        surface.blit(highlight_surf, highlight_rect.topleft)
        
        # Title with glow
        if self.title:
            title_surface = title_font.render(self.title, True, self.border_color)
            title_rect = title_surface.get_rect(centerx=self.rect.centerx, top=self.rect.top + 15)
            
            # Title glow
            glow_surf = pygame.Surface((title_rect.width + 40, title_rect.height + 20), pygame.SRCALPHA)
            glow_title = title_font.render(self.title, True, (*self.border_color, 100))
            glow_surf.blit(glow_title, (20, 10))
            surface.blit(glow_surf, (title_rect.x - 20, title_rect.y - 10), special_flags=pygame.BLEND_ADD)
            
            surface.blit(title_surface, title_rect)
            
            return title_rect.bottom + 20
        
        return self.rect.top + 15

# ============== FONTS ==============
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

# ============== MAIN APPLICATION ==============
class HomeScreen:
    def __init__(self):
        # Particles
        self.stars = [Star() for _ in range(100)]
        self.orbs = [GlowingOrb() for _ in range(5)]
        
        # UI Elements
        self.left_panel = GlassPanel(50, 80, 520, 520, "SUPER MARIO\n- AVENTURE ÉTOILÉE -", GOLD)
        self.right_panel = GlassPanel(830, 80, 520, 620, "", CYAN)
        
        self.text_input = ModernTextInput(900, 250, 380, 55, "✏️ Entrez votre nom...")
        self.start_button = AnimatedButton(940, 340, 300, 60, "🎮 Démarrer le Jeu")
        
        # State
        self.player_name = ""
        self.show_toast = False
        self.toast_message = ""
        self.toast_alpha = 0
        self.toast_timer = 0
        self.game_started = False
        self.start_countdown = 0
        self.time = 0
        
        # Level descriptions
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
        # Key background with gradient
        key_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Gradient
        for i in range(size):
            progress = i / size
            gray = int(255 - progress * 40)
            pygame.draw.line(key_surf, (gray, gray, gray, 240), (0, i), (size, i))
        
        # Draw on main surface
        pygame.draw.rect(surface, WHITE, (x, y, size, size), border_radius=8)
        
        # Border
        pygame.draw.rect(surface, (200, 200, 200), (x, y, size, size), 2, border_radius=8)
        
        # Shadow effect
        pygame.draw.line(surface, (180, 180, 180), (x + 5, y + size - 5), (x + size - 5, y + size - 5), 3)
        pygame.draw.line(surface, (180, 180, 180), (x + size - 5, y + 5), (x + size - 5, y + size - 5), 3)
        
        # Symbol
        symbol_font = pygame.font.Font(None, 36)
        symbol_surface = symbol_font.render(symbol, True, DARK_GRAY)
        symbol_rect = symbol_surface.get_rect(center=(x + size // 2, y + size // 2))
        surface.blit(symbol_surface, symbol_rect)
    
    def draw(self, surface):
        self.time += 1
        
        # Draw background
        if background:
            surface.blit(background, (0, 0))
        else:
            # Animated gradient fallback
            for y in range(SCREEN_HEIGHT):
                progress = y / SCREEN_HEIGHT
                wave = math.sin(self.time * 0.002 + progress * 3) * 10
                r = int(15 + wave)
                g = int(25 + progress * 20 + wave)
                b = int(60 + progress * 40)
                pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # Draw orbs (background glow)
        for orb in self.orbs:
            orb.update()
            orb.draw(surface, self.time)
        
        # Draw stars
        for star in self.stars:
            star.update()
            star.draw(surface, self.time)
        
        # Draw left panel (Game Description)
        y_offset = self.left_panel.draw(surface, subtitle_font, self.time)
        
        # Title
        title_text = subtitle_font.render("SUPER MARIO", True, GOLD)
        title_rect = title_text.get_rect(centerx=self.left_panel.rect.centerx, top=self.left_panel.rect.top + 20)
        
        # Title glow
        glow_surf = pygame.Surface((title_rect.width + 20, title_rect.height + 10), pygame.SRCALPHA)
        glow_text = subtitle_font.render("SUPER MARIO", True, (*GOLD, 80))
        glow_surf.blit(glow_text, (10, 5))
        surface.blit(glow_surf, (title_rect.x - 10, title_rect.y - 5), special_flags=pygame.BLEND_ADD)
        surface.blit(title_text, title_rect)
        
        subtitle_text = subtitle_font.render("- AVENTURE ÉTOILÉE -", True, ORANGE)
        subtitle_rect = subtitle_text.get_rect(centerx=self.left_panel.rect.centerx, top=title_rect.bottom + 5)
        surface.blit(subtitle_text, subtitle_rect)
        
        # Draw levels
        y_offset = subtitle_rect.bottom + 25
        for level in self.levels:
            # Level title
            level_title = level_title_font.render(level["title"], True, level["color"])
            surface.blit(level_title, (self.left_panel.rect.x + 20, y_offset))
            y_offset += 35
            
            # Level description
            desc_rect = pygame.Rect(self.left_panel.rect.x + 20, y_offset, self.left_panel.rect.width - 40, 80)
            y_offset = self.draw_wrapped_text(surface, level["desc"], text_font, LIGHT_GRAY, desc_rect)
            y_offset += 20
        
        # Draw right panel (Welcome)
        self.right_panel.draw(surface, subtitle_font, self.time)
        
        # Welcome title with animation
        pulse = math.sin(self.time * 0.003) * 0.05 + 1.0
        welcome_font_size = int(48 * pulse)
        
        welcome_text = title_font.render("Bienvenue dans le Jeu", True, WHITE)
        welcome_rect = welcome_text.get_rect(centerx=self.right_panel.rect.centerx, top=self.right_panel.rect.top + 30)
        
        # Glow
        glow_surf = pygame.Surface((welcome_rect.width + 30, welcome_rect.height + 20), pygame.SRCALPHA)
        glow_text = title_font.render("Bienvenue dans le Jeu", True, (*CYAN, 60))
        glow_surf.blit(glow_text, (15, 10))
        surface.blit(glow_surf, (welcome_rect.x - 15, welcome_rect.y - 10), special_flags=pygame.BLEND_ADD)
        surface.blit(welcome_text, welcome_rect)
        
        # Subtitle
        sub_text = text_font.render("Entrez votre nom pour commencer à jouer !", True, LIGHT_GRAY)
        sub_rect = sub_text.get_rect(centerx=self.right_panel.rect.centerx, top=welcome_rect.bottom + 15)
        surface.blit(sub_text, sub_rect)
        
        # Text input
        self.text_input.draw(surface, input_font, self.time)
        
        # Start button
        self.start_button.draw(surface, button_font, self.time)
        
        # How to play section
        how_to_play_y = self.start_button.rect.bottom + 40
        
        # Section title
        how_title = subtitle_font.render("🎮 Comment jouer !", True, WHITE)
        how_rect = how_title.get_rect(centerx=self.right_panel.rect.centerx, top=how_to_play_y)
        surface.blit(how_title, how_rect)
        
        # Arrow keys
        if arrow_img:
            img_rect = arrow_img.get_rect(centerx=self.right_panel.rect.centerx, top=how_rect.bottom + 20)
            surface.blit(arrow_img, img_rect)
        else:
            key_size = 50
            key_spacing = 8
            start_x = self.right_panel.rect.centerx - key_size - key_spacing // 2
            start_y = how_rect.bottom + 30
            
            # Up
            self.draw_key(surface, start_x, start_y, "↑", key_size)
            # Down row
            self.draw_key(surface, start_x - key_size - key_spacing, start_y + key_size + key_spacing, "←", key_size)
            self.draw_key(surface, start_x, start_y + key_size + key_spacing, "↓", key_size)
            self.draw_key(surface, start_x + key_size + key_spacing, start_y + key_size + key_spacing, "→", key_size)
        
        # Instructions
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
        
        # Toast notification
        if self.show_toast and self.toast_alpha > 0:
            toast_width = 600
            toast_height = 80
            toast_x = (SCREEN_WIDTH - toast_width) // 2
            toast_y = SCREEN_HEIGHT - 120
            
            # Toast background with gradient
            toast_surf = pygame.Surface((toast_width, toast_height), pygame.SRCALPHA)
            for i in range(toast_height):
                alpha = int(min(220, self.toast_alpha) * (1 - abs(i - toast_height // 2) / toast_height))
                pygame.draw.line(toast_surf, (30, 35, 60, alpha), (0, i), (toast_width, i))
            
            surface.blit(toast_surf, (toast_x, toast_y))
            pygame.draw.rect(surface, (*GOLD, min(255, self.toast_alpha)), 
                           (toast_x, toast_y, toast_width, toast_height), 2, border_radius=15)
            
            # Toast text
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
        
        # Toast fade
        if self.show_toast:
            self.toast_timer -= 1
            if self.toast_timer <= 60:
                self.toast_alpha = max(0, self.toast_alpha - 4)
            if self.toast_timer <= 0:
                self.show_toast = False
        
        # Game start countdown
        if self.game_started:
            self.start_countdown -= 1
            if self.start_countdown <= 0:
                print(f"Starting game for player: {self.player_name}")
                self.show_toast = True
                self.toast_message = "🎮 Chargement du jeu..."
                self.toast_alpha = 255
                self.toast_timer = 180
                self.game_started = False
    
    def start_game(self):
        self.player_name = self.text_input.text
        self.show_toast = True
        self.toast_message = f"✨ Bienvenue {self.player_name} !"
        self.toast_alpha = 255
        self.toast_timer = 180
        self.game_started = True
        self.start_countdown = 180

def main():
    clock = pygame.time.Clock()
    home_screen = HomeScreen()
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        home_screen.update(events, mouse_pos)
        home_screen.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
