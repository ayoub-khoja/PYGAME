"""
=== CLIENT 2D - SUPER MARIO MULTIJOUEUR LAN ===
Ce fichier est le client pour la version 2D du jeu (Pygame).
Se connecte au serveur 2D, envoie les touches, affiche le jeu.

Usage : python client_2d.py
  -> Entrez l'IP du serveur et votre nom au lancement.

Controles :
  Joueur 1 : A/D + W (saut)
  Joueur 2 : Fleches gauche/droite + Fleche haut (saut)
"""

import socket
import json
import pygame
import sys

# ============== CONFIGURATION ==============
PORT = 5555

# Usage : python client_2d.py [IP] [NOM] [CODE]
if len(sys.argv) >= 2:
    SERVER_IP = sys.argv[1]
else:
    print("=" * 50)
    print("  SUPER MARIO - MULTIJOUEUR LAN")
    print("=" * 50)
    SERVER_IP = input("\nIP du serveur (ex: 192.168.1.20): ").strip()

if not SERVER_IP:
    SERVER_IP = "127.0.0.1"
    print(f"  -> Utilisation de {SERVER_IP} (localhost)")

if len(sys.argv) >= 3:
    PLAYER_NAME = sys.argv[2]
else:
    PLAYER_NAME = input("Ton nom: ").strip()

if not PLAYER_NAME:
    PLAYER_NAME = "Joueur"

if len(sys.argv) >= 4:
    ROOM_CODE = sys.argv[3]
else:
    ROOM_CODE = input("Code de la partie: ").strip()

# ============== COULEURS ==============
BG_COLOR = (20, 20, 35)
GROUND_COLOR = (45, 45, 60)
PLATFORM_COLOR = (70, 130, 70)
PLATFORM_TOP = (90, 170, 90)
P1_COLOR = (255, 0, 0)        # Mario = Rouge
P1_OUTLINE = (200, 0, 0)
P2_COLOR = (0, 180, 0)        # Luigi = Vert
P2_OUTLINE = (0, 140, 0)
COIN_COLOR = (255, 215, 0)
COIN_OUTLINE = (200, 170, 0)
TEXT_COLOR = (230, 230, 230)
GOLD = (255, 215, 0)
HUD_BG = (15, 15, 25)
WHITE = (255, 255, 255)
DARK = (20, 20, 40)
SKIN_COLOR = (255, 200, 150)
BROWN = (139, 90, 43)

# ============== DIMENSIONS ==============
W, H = 900, 500
GROUND_Y = 420
PLAYER_W, PLAYER_H = 36, 48
COIN_R = 12


def recv_lines(sock, buffer):
    """Reçoit des données du serveur et les découpe en lignes JSON."""
    try:
        data = sock.recv(4096)
        if not data:
            return [], buffer, False
        buffer += data.decode("utf-8")
    except BlockingIOError:
        return [], buffer, True

    lines = []
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        if line.strip():
            lines.append(line)
    return lines, buffer, True


def draw_player(screen, x, y, col, outline_col, name, is_me):
    """Dessine un joueur style Mario/Luigi pixel art."""
    pw, ph = PLAYER_W, PLAYER_H
    cx = x + pw // 2  # centre X

    # ---- Ombre au sol ----
    shadow = pygame.Surface((pw + 4, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, pw + 4, 8))
    screen.blit(shadow, (x - 2, y + ph - 2))

    # ---- Casquette (haut) ----
    cap_h = 10
    # Visière (dépasse à droite)
    pygame.draw.rect(screen, col, (x - 2, y + 4, pw + 6, cap_h), border_radius=3)
    # Sommet de la casquette
    pygame.draw.rect(screen, col, (x + 2, y, pw - 4, cap_h + 2), border_radius=4)
    # Lettre M ou L sur la casquette
    letter_font = pygame.font.SysFont("Arial", 11, bold=True)
    letter = "M" if col[0] > 200 else "L"  # Rouge=Mario, Vert=Luigi
    letter_render = letter_font.render(letter, True, WHITE)
    screen.blit(letter_render, (cx - letter_render.get_width() // 2, y + 1))

    # ---- Visage (peau) ----
    face_y = y + cap_h + 2
    face_h = 12
    pygame.draw.rect(screen, SKIN_COLOR, (x + 4, face_y, pw - 8, face_h), border_radius=3)

    # Yeux
    eye_y = face_y + 2
    pygame.draw.rect(screen, WHITE, (x + 8, eye_y, 6, 6))
    pygame.draw.rect(screen, WHITE, (x + pw - 14, eye_y, 6, 6))
    pygame.draw.rect(screen, DARK, (x + 10, eye_y + 2, 3, 3))
    pygame.draw.rect(screen, DARK, (x + pw - 12, eye_y + 2, 3, 3))

    # Moustache
    mustache_y = face_y + face_h - 4
    pygame.draw.rect(screen, BROWN, (x + 6, mustache_y, pw - 12, 3), border_radius=1)

    # ---- Corps / Salopette ----
    body_y = face_y + face_h + 1
    body_h = 14
    # Salopette (bleu pour Mario, bleu foncé pour Luigi)
    overalls_col = (0, 0, 180) if col[0] > 200 else (0, 0, 140)
    pygame.draw.rect(screen, overalls_col, (x + 3, body_y, pw - 6, body_h), border_radius=2)
    # Bretelles
    pygame.draw.rect(screen, GOLD, (x + 8, body_y, 3, body_h - 2))
    pygame.draw.rect(screen, GOLD, (x + pw - 11, body_y, 3, body_h - 2))
    # Boutons dorés
    pygame.draw.circle(screen, GOLD, (x + 9, body_y + body_h // 2), 2)
    pygame.draw.circle(screen, GOLD, (x + pw - 10, body_y + body_h // 2), 2)

    # ---- Bras (chemise couleur) ----
    arm_y = body_y + 2
    pygame.draw.rect(screen, col, (x - 1, arm_y, 5, 10), border_radius=2)  # bras gauche
    pygame.draw.rect(screen, col, (x + pw - 4, arm_y, 5, 10), border_radius=2)  # bras droit
    # Mains
    pygame.draw.rect(screen, WHITE, (x - 1, arm_y + 8, 5, 4), border_radius=2)
    pygame.draw.rect(screen, WHITE, (x + pw - 4, arm_y + 8, 5, 4), border_radius=2)

    # ---- Chaussures ----
    shoe_y = body_y + body_h
    shoe_col = BROWN
    pygame.draw.rect(screen, shoe_col, (x + 3, shoe_y, 12, 6), border_radius=3)
    pygame.draw.rect(screen, shoe_col, (x + pw - 15, shoe_y, 12, 6), border_radius=3)

    # ---- Nom au-dessus avec fond ----
    name_font = pygame.font.SysFont("Arial", 13, bold=True)
    label = name_font.render(name, True, WHITE)
    lx = cx - label.get_width() // 2
    ly = y - 22
    # Fond semi-transparent pour le nom
    name_bg = pygame.Surface((label.get_width() + 10, label.get_height() + 4), pygame.SRCALPHA)
    name_bg.fill((0, 0, 0, 120))
    screen.blit(name_bg, (lx - 5, ly - 2))
    pygame.draw.rect(screen, col, (lx - 5, ly - 2, label.get_width() + 10, label.get_height() + 4), 1, border_radius=3)
    screen.blit(label, (lx, ly))

    # ---- Indicateur "▼ TOI" si c'est le joueur local ----
    if is_me:
        arrow_font = pygame.font.SysFont("Arial", 11, bold=True)
        arrow = arrow_font.render("▼ TOI", True, GOLD)
        ax = cx - arrow.get_width() // 2
        screen.blit(arrow, (ax, y - 38))


def draw_coin(screen, x, y, pulse):
    """Dessine un coin avec effet de brillance."""
    r = COIN_R + int(pulse * 2)
    pygame.draw.circle(screen, COIN_OUTLINE, (x, y), r + 2)
    pygame.draw.circle(screen, COIN_COLOR, (x, y), r)
    # Reflet
    pygame.draw.circle(screen, (255, 240, 150), (x - 3, y - 3), r // 3)


def draw_platform(screen, plat):
    """Dessine une plateforme avec effet 3D."""
    x, y, w, h = plat["x"], plat["y"], plat["w"], plat["h"]
    # Côté
    pygame.draw.rect(screen, PLATFORM_COLOR, (x, y, w, h + 5))
    # Dessus
    pygame.draw.rect(screen, PLATFORM_TOP, (x, y, w, h))
    # Ligne brillante
    pygame.draw.line(screen, (110, 190, 110), (x + 2, y + 2), (x + w - 2, y + 2), 1)


# ============== INITIALISATION PYGAME ==============
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Super Mario - Multijoueur LAN")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("Arial", 36, bold=True)
font_med = pygame.font.SysFont("Arial", 22, bold=True)
font_small = pygame.font.SysFont("Arial", 16)
font_hud = pygame.font.SysFont("Consolas", 20, bold=True)
font_title = pygame.font.SysFont("Arial", 48, bold=True)

# ============== ECRAN DE CONNEXION ==============
screen.fill(BG_COLOR)
connecting_text = font_big.render("Connexion au serveur...", True, GOLD)
screen.blit(connecting_text, (W // 2 - connecting_text.get_width() // 2, H // 2 - 40))
ip_text = font_small.render(f"IP: {SERVER_IP}:{PORT}", True, TEXT_COLOR)
screen.blit(ip_text, (W // 2 - ip_text.get_width() // 2, H // 2 + 20))
pygame.display.flip()

# ============== CONNEXION AU SERVEUR ==============
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, PORT))
    print(f"\n[CLIENT] Connecte au serveur {SERVER_IP}:{PORT}")

    # ============== ENVOI DU CODE DE SALLE ==============
    join_msg = json.dumps({"type": "join", "code": ROOM_CODE}) + "\n"
    join_msg += json.dumps({"type": "set_name", "name": PLAYER_NAME}) + "\n"
    sock.sendall(join_msg.encode("utf-8"))
    print(f"[CLIENT] Code envoye, attente de verification...")

    # Attendre la réponse du serveur (welcome ou error)
    sock.settimeout(10.0)
    response_data = sock.recv(4096).decode("utf-8")
    resp_lines = response_data.strip().split("\n")
    first_resp = json.loads(resp_lines[0])

    if first_resp.get("type") == "error":
        print(f"[CLIENT] REFUSE: {first_resp.get('message')}")
        sock.close()
        screen.fill(BG_COLOR)
        err_text = font_big.render("Code incorrect !", True, (255, 80, 80))
        screen.blit(err_text, (W // 2 - err_text.get_width() // 2, H // 2 - 40))
        detail_text = font_small.render("Le code de la partie est faux.", True, TEXT_COLOR)
        screen.blit(detail_text, (W // 2 - detail_text.get_width() // 2, H // 2 + 20))
        pygame.display.flip()
        pygame.time.wait(4000)
        pygame.quit()
        sys.exit()

    sock.settimeout(None)
    sock.setblocking(False)

    # Extraire player_id du message welcome
    player_id = None
    remaining_buffer = ""
    for resp_line in resp_lines:
        if resp_line.strip():
            try:
                rmsg = json.loads(resp_line)
                if rmsg.get("type") == "welcome":
                    player_id = rmsg.get("player_id")
                    print(f"[CLIENT] Code accepte ! Tu es Joueur {player_id}")
            except:
                remaining_buffer += resp_line + "\n"

except Exception as e:
    print(f"\n[ERREUR] Impossible de se connecter: {e}")
    screen.fill(BG_COLOR)
    err_text = font_big.render("Connexion echouee!", True, (255, 80, 80))
    screen.blit(err_text, (W // 2 - err_text.get_width() // 2, H // 2 - 20))
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

if player_id is None:
    player_id = None  # Will be set when welcome message arrives
buffer = remaining_buffer if 'remaining_buffer' in dir() else ""
state = None
frame_count = 0

# ============== ECRAN D'ATTENTE ==============
waiting = True
while waiting:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            sock.close()
            pygame.quit()
            sys.exit()

    lines, buffer, ok = recv_lines(sock, buffer)
    if not ok:
        break
    for line in lines:
        msg = json.loads(line)
        if msg.get("type") == "welcome":
            player_id = msg["player_id"]
            print(f"[CLIENT] Tu es le Joueur {player_id}")
        elif msg.get("type") == "state":
            state = msg["state"]
            if state.get("game_started"):
                waiting = False

    screen.fill(BG_COLOR)
    # Titre
    title = font_title.render("SUPER MARIO", True, GOLD)
    screen.blit(title, (W // 2 - title.get_width() // 2, 100))
    subtitle = font_med.render("MULTIJOUEUR LAN", True, TEXT_COLOR)
    screen.blit(subtitle, (W // 2 - subtitle.get_width() // 2, 160))

    # Info
    if player_id:
        id_text = font_med.render(f"Tu es Joueur {player_id} ({PLAYER_NAME})", True, P1_COLOR if player_id == 1 else P2_COLOR)
        screen.blit(id_text, (W // 2 - id_text.get_width() // 2, 240))

    wait_text = font_med.render("En attente du 2eme joueur...", True, TEXT_COLOR)
    screen.blit(wait_text, (W // 2 - wait_text.get_width() // 2, 300))

    # Animation points
    dots = "." * (1 + (pygame.time.get_ticks() // 500) % 3)
    dots_text = font_big.render(dots, True, GOLD)
    screen.blit(dots_text, (W // 2 - dots_text.get_width() // 2, 340))

    pygame.display.flip()
    clock.tick(30)

# ============== BOUCLE DE JEU ==============
running = True
while running:
    frame_count += 1

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            running = False

    # Recevoir l'état du serveur
    lines, buffer, ok = recv_lines(sock, buffer)
    if not ok:
        break
    for line in lines:
        try:
            msg = json.loads(line)
            if msg.get("type") == "state":
                state = msg["state"]
        except:
            pass

    # Envoyer les inputs
    keys = pygame.key.get_pressed()
    if player_id == 1:
        left = keys[pygame.K_a]
        right = keys[pygame.K_d]
        jump = keys[pygame.K_w]
    else:
        left = keys[pygame.K_LEFT]
        right = keys[pygame.K_RIGHT]
        jump = keys[pygame.K_UP]

    payload = {"type": "input", "left": left, "right": right, "jump": jump}
    try:
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
    except:
        pass

    # ============== RENDU ==============
    screen.fill(BG_COLOR)

    # Étoiles en fond
    import math
    for i in range(30):
        sx = (i * 137 + 50) % W
        sy = (i * 89 + 20) % (GROUND_Y - 50)
        brightness = 100 + int(50 * math.sin(frame_count * 0.02 + i))
        pygame.draw.circle(screen, (brightness, brightness, brightness + 20), (sx, sy), 1)

    if state:
        # Sol avec dégradé
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, W, H - GROUND_Y))
        pygame.draw.line(screen, (80, 80, 100), (0, GROUND_Y), (W, GROUND_Y), 2)
        # Herbe
        for gx in range(0, W, 20):
            pygame.draw.line(screen, (50, 100, 50), (gx, GROUND_Y), (gx + 5, GROUND_Y - 5), 2)

        # Plateformes
        for plat in state.get("platforms", []):
            draw_platform(screen, plat)

        # Coins (avec pulse)
        pulse = math.sin(frame_count * 0.08)
        for c in state.get("coins", []):
            draw_coin(screen, int(c["x"]), int(c["y"]), pulse)

        # Joueurs
        p1 = state["players"].get("1") or state["players"].get(1)
        p2 = state["players"].get("2") or state["players"].get(2)

        if p1:
            n1 = p1.get("name") or "Joueur 1"
            draw_player(screen, int(p1["x"]), int(p1["y"]), P1_COLOR, P1_OUTLINE, n1, player_id == 1)
        if p2:
            n2 = p2.get("name") or "Joueur 2"
            draw_player(screen, int(p2["x"]), int(p2["y"]), P2_COLOR, P2_OUTLINE, n2, player_id == 2)

        # ============== HUD ==============
        s1 = p1["score"] if p1 else 0
        s2 = p2["score"] if p2 else 0
        n1_name = (p1.get("name") or "J1") if p1 else "J1"
        n2_name = (p2.get("name") or "J2") if p2 else "J2"
        coins_left = len(state.get("coins", []))

        # Barre du haut
        pygame.draw.rect(screen, HUD_BG, (0, 0, W, 45))
        pygame.draw.line(screen, GOLD, (0, 45), (W, 45), 2)

        # Score J1 (gauche)
        p1_label = font_hud.render(f"{n1_name}: {s1}", True, P1_COLOR)
        screen.blit(p1_label, (15, 10))
        if player_id == 1:
            you = font_small.render("(toi)", True, GOLD)
            screen.blit(you, (20 + p1_label.get_width(), 14))

        # Coins restants (centre)
        coins_label = font_hud.render(f"Coins: {coins_left}", True, COIN_COLOR)
        screen.blit(coins_label, (W // 2 - coins_label.get_width() // 2, 10))

        # Score J2 (droite)
        p2_label = font_hud.render(f"{n2_name}: {s2}", True, P2_COLOR)
        screen.blit(p2_label, (W - p2_label.get_width() - 15, 10))
        if player_id == 2:
            you = font_small.render("(toi)", True, GOLD)
            screen.blit(you, (W - p2_label.get_width() - 55, 14))

        # Contrôles en bas
        if player_id == 1:
            ctrl = "Controles: A/D = Bouger | W = Sauter"
        else:
            ctrl = "Controles: Fleches = Bouger | Haut = Sauter"
        ctrl_text = font_small.render(ctrl, True, (120, 120, 140))
        screen.blit(ctrl_text, (W // 2 - ctrl_text.get_width() // 2, H - 25))

        # ============== ECRAN DE FIN ==============
        winner = state.get("winner")
        if winner is not None:
            # Overlay sombre
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            # Popup
            popup_w, popup_h = 500, 280
            px = W // 2 - popup_w // 2
            py = H // 2 - popup_h // 2

            # Bordure dorée
            pygame.draw.rect(screen, GOLD, (px - 4, py - 4, popup_w + 8, popup_h + 8), border_radius=12)
            # Fond sombre
            pygame.draw.rect(screen, (15, 15, 35), (px, py, popup_w, popup_h), border_radius=10)
            # Barre du haut
            pygame.draw.rect(screen, GOLD, (px, py, popup_w, 50), border_radius=10)
            pygame.draw.rect(screen, GOLD, (px, py + 30, popup_w, 20))

            # Titre
            if winner == 0:
                title_text = "EGALITE !"
                title_col = GOLD
            elif winner == player_id:
                title_text = "TU AS GAGNE !"
                title_col = (20, 20, 40)
            else:
                title_text = "TU AS PERDU"
                title_col = (20, 20, 40)

            title_render = font_big.render(title_text, True, title_col)
            screen.blit(title_render, (W // 2 - title_render.get_width() // 2, py + 8))

            # Scores
            y_offset = py + 75
            score1_text = font_med.render(f"{n1_name}: {s1} coins", True, P1_COLOR)
            screen.blit(score1_text, (W // 2 - score1_text.get_width() // 2, y_offset))

            score2_text = font_med.render(f"{n2_name}: {s2} coins", True, P2_COLOR)
            screen.blit(score2_text, (W // 2 - score2_text.get_width() // 2, y_offset + 40))

            # Ligne
            pygame.draw.line(screen, GOLD, (px + 40, y_offset + 85), (px + popup_w - 40, y_offset + 85), 1)

            # Message
            if winner == player_id:
                msg = "Bravo ! Tu es le champion !"
                msg_col = GOLD
            elif winner == 0:
                msg = "Match nul ! Revanche ?"
                msg_col = TEXT_COLOR
            else:
                msg = "Pas de chance... Retente !"
                msg_col = (180, 180, 200)

            msg_render = font_med.render(msg, True, msg_col)
            screen.blit(msg_render, (W // 2 - msg_render.get_width() // 2, y_offset + 100))

            # ESC
            esc_text = font_small.render("Appuie sur ESC pour quitter", True, (120, 120, 140))
            screen.blit(esc_text, (W // 2 - esc_text.get_width() // 2, y_offset + 145))

    else:
        # Pas encore d'état reçu
        wait = font_med.render("Connexion au serveur...", True, TEXT_COLOR)
        screen.blit(wait, (W // 2 - wait.get_width() // 2, H // 2))

    pygame.display.flip()
    clock.tick(60)

sock.close()
pygame.quit()
sys.exit()
