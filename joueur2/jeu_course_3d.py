"""
=== JEU DE COURSE 3D - SUPER MARIO AVENTURE ETOILEE ===
Ce fichier contient le jeu principal en 3D utilisant le moteur Ursina.
Version Joueur 2 - a copier sur le PC du 2eme joueur.

Modes de jeu :
  - Solo  : Course seul avec score et pieces
  - Multi : Course a 2 joueurs en reseau local (LAN)
"""

from ursina import *
import random
import sys
import math
import socket
import threading
import json

# ============== ARGUMENTS DE LIGNE DE COMMANDE ==============
# Solo  : python jeu_course_3d.py [nom]
# Multi : python jeu_course_3d.py [nom] --multi [ip_serveur] [code_salle]
player_name = "Joueur"
multiplayer = False
server_ip = "127.0.0.1"
room_code = "AYOUB-YASSMINE"
MULTI_PORT = 5556

if len(sys.argv) > 1:
    player_name = sys.argv[1]
if "--multi" in sys.argv:
    multiplayer = True
    idx = sys.argv.index("--multi")
    if idx + 1 < len(sys.argv):
        server_ip = sys.argv[idx + 1]
    if idx + 2 < len(sys.argv):
        room_code = sys.argv[idx + 2]

# ============== RESEAU (mode multijoueur uniquement) ==============
net_sock = None
net_buffer = ""
net_player_id = None
net_other_player = {}      # {x, y, z, ry, coins, score, name, finished, dead}
net_collected_coins = []   # indices of coins collected by either player
net_winner = None
net_game_started = False
net_countdown = -1          # -1 = pas de countdown, 5/4/3/2/1 = en cours, 0 = GO
net_race_started = False    # True quand le GO est donné (les joueurs peuvent bouger)
net_lock = threading.Lock()

def net_connect():
    """Connexion au serveur multijoueur avec logique de tentatives."""
    global net_sock, net_player_id
    import time as _time
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(f"[NET] Tentative {attempt}/{max_retries}...")
                _time.sleep(3)

            net_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            net_sock.settimeout(15.0)
            net_sock.connect((server_ip, MULTI_PORT))
            print(f"[NET] Connecte a {server_ip}:{MULTI_PORT}")

            # Envoyer code + nom
            join_data = json.dumps({"type": "join", "code": room_code}) + "\n"
            join_data += json.dumps({"type": "set_name", "name": player_name}) + "\n"
            net_sock.sendall(join_data.encode("utf-8"))
            print(f"[NET] Donnees envoyees, attente reponse du serveur...")

            # Attendre la réponse (welcome ou error)
            net_sock.settimeout(20.0)
            resp = b""
            deadline = _time.time() + 20
            while _time.time() < deadline:
                try:
                    chunk = net_sock.recv(4096)
                    if not chunk:
                        break
                    resp += chunk
                    if b"\n" in resp:
                        break
                except socket.timeout:
                    break

            if not resp:
                print(f"[NET] Pas de reponse du serveur (tentative {attempt})")
                net_sock.close()
                net_sock = None
                continue

            resp_str = resp.decode("utf-8")
            for line in resp_str.strip().split("\n"):
                if line.strip():
                    msg = json.loads(line)
                    if msg.get("type") == "error":
                        print(f"[NET] REFUSE: {msg.get('message')}")
                        net_sock.close()
                        net_sock = None
                        return False
                    if msg.get("type") == "welcome":
                        net_player_id = msg.get("player_id")
                        print(f"[NET] Accepte ! Tu es Joueur {net_player_id}")

            if net_player_id is not None:
                net_sock.settimeout(None)
                net_sock.setblocking(False)
                return True
            else:
                print(f"[NET] Reponse invalide du serveur (tentative {attempt})")
                net_sock.close()
                net_sock = None
                continue

        except Exception as e:
            print(f"[NET] Erreur tentative {attempt}: {e}")
            if net_sock:
                try:
                    net_sock.close()
                except:
                    pass
                net_sock = None

    print(f"[NET] Echec apres {max_retries} tentatives.")
    return False

def net_receive():
    """Recevoir les donnees du serveur (non-bloquant, appele chaque frame)."""
    global net_buffer, net_other_player, net_collected_coins, net_winner, net_game_started
    global net_countdown, net_race_started
    if not net_sock:
        return
    try:
        data = net_sock.recv(8192)
        if not data:
            return
        net_buffer += data.decode("utf-8")
        while "\n" in net_buffer:
            line, net_buffer = net_buffer.split("\n", 1)
            if not line.strip():
                continue
            msg = json.loads(line)
            if msg.get("type") == "state":
                with net_lock:
                    players = msg.get("players", {})
                    other_id = "2" if net_player_id == 1 else "1"
                    if other_id in players:
                        net_other_player = players[other_id]
                    elif int(other_id) in players:
                        net_other_player = players[int(other_id)]
                    net_collected_coins = msg.get("collected_coins", [])
                    net_winner = msg.get("winner")
            elif msg.get("type") == "countdown":
                net_countdown = msg.get("seconds", 0)
                if net_countdown == 0:
                    print("[NET] GO !")
            elif msg.get("type") == "start":
                net_game_started = True
                net_race_started = True
                print("[NET] La course commence !")
    except BlockingIOError:
        pass
    except Exception:
        pass

def net_send_position(x, y, z, ry, coins_count, score_val):
    """Envoyer la position du joueur local au serveur."""
    if not net_sock:
        return
    try:
        msg = json.dumps({"type": "position", "x": round(x, 2), "y": round(y, 2), "z": round(z, 2), "ry": round(ry, 1), "coins": coins_count, "score": score_val}) + "\n"
        net_sock.sendall(msg.encode("utf-8"))
    except:
        pass

def net_send_collect_coin(index):
    """Informer le serveur qu'on a collecte une piece."""
    if not net_sock:
        return
    try:
        net_sock.sendall((json.dumps({"type": "collect_coin", "index": index}) + "\n").encode("utf-8"))
    except:
        pass

def net_send_finished():
    """Informer le serveur qu'on a franchi la ligne d'arrivee."""
    if not net_sock:
        return
    try:
        net_sock.sendall((json.dumps({"type": "finished"}) + "\n").encode("utf-8"))
    except:
        pass

def net_send_dead():
    """Informer le serveur qu'on a touche une bombe."""
    if not net_sock:
        return
    try:
        net_sock.sendall((json.dumps({"type": "dead"}) + "\n").encode("utf-8"))
    except:
        pass

# Connexion si mode multijoueur
if multiplayer:
    print(f"[NET] Mode multijoueur - Connexion a {server_ip}...")
    if not net_connect():
        print("[NET] Impossible de se connecter. Lancement en mode solo.")
        multiplayer = False
    else:
        print("[NET] En attente du 2eme joueur (dans le jeu)...")

# Initialisation du moteur Ursina
app = Ursina(title=f'Super Mario - {player_name}', borderless=False)

# Parametres de la fenetre
window.fullscreen = False
window.size = (1400, 800)
window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.exit_button.visible = False

# Variables du jeu
score = 0
coins_collected = 0
game_won = False
game_over = False
mario_local_x = 0  # offset latéral du joueur par rapport au centre de la route

# Couleurs
GREEN = color.rgb(34, 197, 94)
BROWN = color.rgb(139, 69, 19)
GRAY = color.rgb(180, 180, 180)
GOLD = color.rgb(255, 215, 0)
DARK_BROWN = color.rgb(100, 50, 10)

# ============== SYSTEME DE ROUTE SINUEUSE ==============
# Route longue avec de grands virages (la route va a droite et avance)
def road_center_x(z):
    # Grand virage progressif vers la droite + ondulations
    return math.sin(z * 0.004) * 25 + math.sin(z * 0.012) * 12 + math.cos(z * 0.007) * 8

# Direction de la route (angle en degrés) à la position z
def road_angle_at(z):
    dz = 1.0
    dx = road_center_x(z - dz) - road_center_x(z + dz)
    return math.degrees(math.atan2(dx, 2 * dz))

# Perpendiculaire (pour décaler les objets sur les côtés)
def road_perpendicular(z):
    angle_rad = math.radians(road_angle_at(z))
    return math.cos(angle_rad), -math.sin(angle_rad)

# ============== CREATION DU SOL ==============
ground = Entity(
    model='plane',
    scale=(500, 1, 2000),
    color=GREEN,
    texture='grass',
    collider='box'
)

# ============== CREATION DES SEGMENTS DE ROUTE ==============
road_start_z = 360
road_end_z = -600
segment_length = 4

for z in range(road_end_z, road_start_z, segment_length):
    z1 = z
    z2 = z + segment_length
    x1 = road_center_x(z1)
    x2 = road_center_x(z2)
    
    cx = (x1 + x2) / 2
    cz = (z1 + z2) / 2
    
    dx = x2 - x1
    dz_val = z2 - z1
    seg_len = math.sqrt(dx * dx + dz_val * dz_val)
    angle_y = -math.degrees(math.atan2(dx, dz_val))
    
    # Route principale
    Entity(
        model='cube',
        scale=(10, 0.15, seg_len + 0.5),
        position=(cx, 0.08, cz),
        rotation=(0, angle_y, 0),
        color=BROWN,
    )
    
    # Rails gauche et droite
    Entity(
        model='cube',
        scale=(0.4, 0.6, seg_len + 0.5),
        position=(cx - 5.2 * math.cos(math.radians(angle_y)), 0.3, cz + 5.2 * math.sin(math.radians(angle_y))),
        rotation=(0, angle_y, 0),
        color=GRAY,
    )
    Entity(
        model='cube',
        scale=(0.4, 0.6, seg_len + 0.5),
        position=(cx + 5.2 * math.cos(math.radians(angle_y)), 0.3, cz - 5.2 * math.sin(math.radians(angle_y))),
        rotation=(0, angle_y, 0),
        color=GRAY,
    )

# ============== CHARGEMENT DU MODELE MARIO ==============
mario_start_z = 350
try:
    mario = Entity(
        model='assets/mario.glb',
        scale=3,
        position=(road_center_x(mario_start_z), 1, mario_start_z),
        rotation=(0, 180, 0)
    )
except:
    mario = Entity(
        model='cube',
        scale=(1, 2, 1),
        position=(road_center_x(mario_start_z), 1, mario_start_z),
        color=color.red
    )

# ============== 2EME MARIO (MULTIJOUEUR) ==============
mario2 = None
mario2_name_text = None
if multiplayer:
    try:
        mario2 = Entity(
            model='assets/mario.glb',
            scale=3,
            position=(road_center_x(mario_start_z), 1, mario_start_z - 5),
            rotation=(0, 180, 0),
            color=color.rgb(100, 200, 100),  # Teinte verte pour le distinguer
        )
    except:
        mario2 = Entity(
            model='cube',
            scale=(1, 2, 1),
            position=(road_center_x(mario_start_z), 1, mario_start_z - 5),
            color=color.green,
        )
    # Nom du 2ème joueur au-dessus de sa tête
    mario2_name_text = Text(
        text='Joueur 2',
        position=(0, 0),
        scale=1.5,
        color=color.rgb(100, 255, 100),
        origin=(0, 0),
        billboard=True,
    )

# Nom local au-dessus de notre Mario
local_name_text = None
if multiplayer:
    local_name_text = Text(
        text=player_name,
        position=(0, 0),
        scale=1.5,
        color=color.rgb(255, 200, 100),
        origin=(0, 0),
        billboard=True,
    )

# ============== CREATION DES PIECES SUR LA ROUTE ==============
coins = []
num_coins = 70
try:
    for i in range(num_coins):
        z_pos = 340 - i * 13
        cx = road_center_x(z_pos) + random.uniform(-3, 3)
        coin = Entity(
            model='assets/MarioCoin.glb',
            scale=0.015,
            position=(cx, 2, z_pos),
        )
        coins.append(coin)
except:
    for i in range(num_coins):
        z_pos = 340 - i * 13
        cx = road_center_x(z_pos) + random.uniform(-3, 3)
        coin = Entity(
            model='sphere',
            scale=0.5,
            position=(cx, 2, z_pos),
            color=GOLD
        )
        coins.append(coin)

# ============== BATIMENTS LE LONG DE LA ROUTE ==============
building_textures = [
    'assets/PNG/buildingTiles_036.png',
    'assets/PNG/buildingTiles_044.png',
    'assets/PNG/buildingTiles_050.png',
    'assets/PNG/buildingTiles_052.png',
    'assets/PNG/buildingTiles_100.png',
    'assets/PNG/buildingTiles_125.png',
]

for i in range(55):
    z_pos = 350 - i * 17
    rcx = road_center_x(z_pos)
    perp_x, perp_z = road_perpendicular(z_pos)
    
    # Maison gauche
    Entity(
        model='quad',
        texture=random.choice(building_textures),
        scale=(10, 10),
        position=(rcx - perp_x * 18, 5, z_pos - perp_z * 18),
        billboard=True,
        double_sided=True,
        unlit=True,
    )
    # Maison droite
    Entity(
        model='quad',
        texture=random.choice(building_textures),
        scale=(10, 10),
        position=(rcx + perp_x * 18, 5, z_pos + perp_z * 18),
        billboard=True,
        double_sided=True,
        unlit=True,
    )

# ============== VOITURES LE LONG DE LA ROUTE ==============
car_textures = [
    'assets/PNG/Cars/taxi.png',
    'assets/PNG/Cars/police.png',
    'assets/PNG/Cars/bus.png',
    'assets/PNG/Cars/sports_red.png',
    'assets/PNG/Cars/firetruck.png',
    'assets/PNG/Cars/ambulance.png',
    'assets/PNG/Cars/sedan_blue.png',
    'assets/PNG/Cars/sedan.png',
    'assets/PNG/Cars/truck.png',
    'assets/PNG/Cars/van.png',
    'assets/PNG/Cars/convertible.png',
    'assets/PNG/Cars/suv_green.png',
]

for i in range(30):
    z_pos = 340 - i * 30 + random.uniform(-5, 5)
    rcx = road_center_x(z_pos)
    perp_x, perp_z = road_perpendicular(z_pos)
    side = random.choice([-1, 1])
    offset = random.uniform(7, 9)
    
    Entity(
        model='quad',
        texture=random.choice(car_textures),
        scale=(4, 2),
        position=(rcx + side * perp_x * offset, 1.2, z_pos + side * perp_z * offset),
        billboard=True,
        double_sided=True,
        unlit=True,
    )

# ============== BOMBES SUR LA ROUTE ==============
bombs = []
RED = color.rgb(200, 30, 30)
DARK_RED = color.rgb(120, 10, 10)

for i in range(12):
    z_pos = 280 - i * 70 + random.uniform(-5, 5)
    rcx = road_center_x(z_pos)
    offset_x = random.uniform(-3.5, 3.5)
    
    bomb = Entity(
        model='sphere',
        scale=1.2,
        position=(rcx + offset_x, 1.2, z_pos),
        color=color.black,
    )
    # Petite sphère rouge au-dessus = mèche/flamme
    Entity(
        model='sphere',
        scale=0.4,
        position=(rcx + offset_x, 2.2, z_pos),
        color=color.red,
    )
    bombs.append(bomb)

# ============== PORTAIL DU MILIEU (transition jour vers soir) ==============
mid_z = (road_start_z + road_end_z) // 2  # milieu de la route
mid_cx = road_center_x(mid_z)
mid_angle = road_angle_at(mid_z)
mid_perp_x, mid_perp_z = road_perpendicular(mid_z)

# Portail du milieu - deux piliers orange
Entity(
    model='cube',
    scale=(1.2, 8, 1.2),
    position=(mid_cx - mid_perp_x * 6, 4, mid_z - mid_perp_z * 6),
    rotation=(0, -mid_angle, 0),
    color=color.rgb(255, 140, 0),
)
Entity(
    model='cube',
    scale=(1.2, 8, 1.2),
    position=(mid_cx + mid_perp_x * 6, 4, mid_z + mid_perp_z * 6),
    rotation=(0, -mid_angle, 0),
    color=color.rgb(255, 140, 0),
)
# Barre horizontale du portail
Entity(
    model='cube',
    scale=(13, 1, 1),
    position=(mid_cx, 8.5, mid_z),
    rotation=(0, -mid_angle, 0),
    color=color.rgb(255, 100, 0),
)
# Texte indicateur "SUNSET ZONE" au-dessus du portail
Entity(
    model='cube',
    scale=(10, 1.5, 0.3),
    position=(mid_cx, 10.5, mid_z),
    rotation=(0, -mid_angle, 0),
    color=color.rgb(80, 30, 80),
)
# Petites lumières décoratives sur le portail
for j in range(5):
    lx = mid_cx + mid_perp_x * (j - 2) * 2.5
    lz = mid_z + mid_perp_z * (j - 2) * 2.5
    Entity(
        model='sphere',
        scale=0.5,
        position=(lx, 9.5, lz),
        color=color.rgb(255, 200, 50),
        unlit=True,
    )

# ============== LIGNE D'ARRIVEE ==============
finish_z = -580
finish_cx = road_center_x(finish_z)
finish_angle = road_angle_at(finish_z)
finish_perp_x, finish_perp_z = road_perpendicular(finish_z)

# Deux grands piliers
for side in [-1, 1]:
    px = finish_cx + side * finish_perp_x * 6
    pz = finish_z + side * finish_perp_z * 6
    # Pilier principal
    Entity(
        model='cube',
        scale=(1.5, 10, 1.5),
        position=(px, 5, pz),
        rotation=(0, -finish_angle, 0),
        color=color.rgb(220, 220, 220),
    )
    # Sommet doré du pilier
    Entity(
        model='sphere',
        scale=2,
        position=(px, 10.5, pz),
        color=color.rgb(255, 215, 0),
    )
    # Base du pilier
    Entity(
        model='cube',
        scale=(2.5, 0.8, 2.5),
        position=(px, 0.4, pz),
        rotation=(0, -finish_angle, 0),
        color=color.rgb(180, 180, 180),
    )

# Barre supérieure (arche)
Entity(
    model='cube',
    scale=(14, 1.5, 1),
    position=(finish_cx, 10, finish_z),
    rotation=(0, -finish_angle, 0),
    color=color.rgb(220, 220, 220),
)

# Damier noir et blanc sur la barre
for col in range(8):
    for row in range(2):
        checker_color = color.black if (col + row) % 2 == 0 else color.white
        offset_along = (col - 3.5) * 1.6
        cx_c = finish_cx + finish_perp_x * offset_along
        cz_c = finish_z + finish_perp_z * offset_along
        Entity(
            model='cube',
            scale=(1.5, 0.7, 0.15),
            position=(cx_c, 9.3 + row * 0.75, cz_c),
            rotation=(0, -finish_angle, 0),
            color=checker_color,
        )

# Bannière "ARRIVÉE" - barre rouge sous l'arche
Entity(
    model='cube',
    scale=(12, 2, 0.3),
    position=(finish_cx, 7.5, finish_z),
    rotation=(0, -finish_angle, 0),
    color=color.rgb(200, 30, 30),
)

# Drapeaux sur les côtés
for side in [-1, 1]:
    fx = finish_cx + side * finish_perp_x * 7.5
    fz = finish_z + side * finish_perp_z * 7.5
    # Mât
    Entity(
        model='cube',
        scale=(0.2, 12, 0.2),
        position=(fx, 6, fz),
        color=color.rgb(160, 160, 160),
    )
    # Drapeau
    Entity(
        model='quad',
        scale=(2.5, 1.5),
        position=(fx + side * 1.3, 11, fz),
        color=color.rgb(255, 215, 0),
        billboard=True,
        double_sided=True,
        unlit=True,
    )

# ============== PANNEAU D'INTERFACE (HUD) ==============
hud_bg = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(0, 0, 0, 150),
    scale=(0.38, 0.16),
    position=(-0.67, 0.41),
)

hud_bar = Entity(
    parent=camera.ui,
    model='quad',
    color=GOLD,
    scale=(0.38, 0.008),
    position=(-0.67, 0.498),
)

hud_title = Text(
    text='SUPER MARIO',
    position=(-0.85, 0.485),
    scale=1.4,
    color=GOLD,
    font='VeraMono.ttf',
)

hud_sep = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(255, 215, 0, 80),
    scale=(0.34, 0.002),
    position=(-0.67, 0.455),
)

name_text = Text(
    text=f'Joueur:  {player_name}',
    position=(-0.84, 0.44),
    scale=1.3,
    color=color.rgb(200, 220, 255),
)

score_text = Text(
    text=f'Score:   {score}',
    position=(-0.84, 0.41),
    scale=1.5,
    color=GOLD,
    font='VeraMono.ttf',
)

coins_text = Text(
    text=f'Pieces:  {coins_collected}/70',
    position=(-0.84, 0.375),
    scale=1.3,
    color=color.rgb(255, 230, 100),
)

hud_bar_bottom = Entity(
    parent=camera.ui,
    model='quad',
    color=GOLD,
    scale=(0.38, 0.004),
    position=(-0.67, 0.322),
)

controls_text = Text(
    text='Fleches/WASD: Deplacer | ESC: Menu',
    position=(0, -0.45),
    origin=(0, 0),
    scale=1.2,
    color=color.rgba(200, 200, 200, 180),
)

# ============== HUD DU JOUEUR 2 (multijoueur) ==============
p2_hud_bg = None
p2_name_hud = None
p2_score_hud = None
p2_coins_hud = None
p2_status_hud = None

if multiplayer:
    # Panneau en haut à droite pour le Joueur 2
    p2_hud_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 150), scale=(0.38, 0.14), position=(0.67, 0.41))
    Entity(parent=camera.ui, model='quad', color=color.rgb(100, 255, 100), scale=(0.38, 0.008), position=(0.67, 0.475))
    p2_name_hud = Text(text='Joueur 2', position=(0.50, 0.46), scale=1.3, color=color.rgb(100, 255, 100))
    Entity(parent=camera.ui, model='quad', color=color.rgba(100, 255, 100, 80), scale=(0.34, 0.002), position=(0.67, 0.435))
    p2_score_hud = Text(text='Score:   0', position=(0.50, 0.42), scale=1.3, color=color.rgb(100, 255, 100), font='VeraMono.ttf')
    p2_coins_hud = Text(text='Pieces:  0/70', position=(0.50, 0.39), scale=1.1, color=color.rgb(180, 255, 180))
    p2_status_hud = Text(text='En course...', position=(0.50, 0.36), scale=1.0, color=color.rgb(200, 200, 200))
    Entity(parent=camera.ui, model='quad', color=color.rgb(100, 255, 100), scale=(0.38, 0.004), position=(0.67, 0.335))

    # Mode multijoueur affiché
    Text(text='MODE 2 JOUEURS', position=(0, 0.48), origin=(0, 0), scale=1.2, color=color.rgb(255, 215, 0))

# ============== AFFICHAGE DU COMPTE A REBOURS (multijoueur) ==============
countdown_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 150), scale=(3, 2), z=-20, enabled=False)
countdown_number = Text(
    text='5',
    position=(0, 0.05),
    origin=(0, 0),
    scale=8,
    color=color.rgb(255, 215, 0),
    enabled=False,
    font='VeraMono.ttf',
    z=-21,
)
countdown_label = Text(
    text='PREPAREZ-VOUS !',
    position=(0, 0.28),
    origin=(0, 0),
    scale=2.5,
    color=color.white,
    enabled=False,
    z=-21,
)
countdown_players_info = Text(
    text='',
    position=(0, -0.18),
    origin=(0, 0),
    scale=1.5,
    color=color.rgb(200, 200, 200),
    enabled=False,
    z=-21,
)
waiting_text = None
if multiplayer:
    waiting_text = Text(
        text='En attente du 2eme joueur...',
        position=(0, 0),
        origin=(0, 0),
        scale=2.5,
        color=color.rgb(255, 215, 0),
        z=-21,
    )

# ============== POPUP DE VICTOIRE (désactivée au début) ==============
# Overlay sombre plein écran (z le plus loin)
win_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 200), scale=(3, 2), z=-10, enabled=False)

# Bordure dorée (derrière le fond)
win_border = Entity(parent=camera.ui, model='quad', color=color.rgb(255, 180, 0), scale=(0.74, 0.58), position=(0, 0.02), z=-9, enabled=False)

# Fond principal sombre
win_bg = Entity(parent=camera.ui, model='quad', color=color.rgb(15, 15, 30), scale=(0.70, 0.54), position=(0, 0.02), z=-8, enabled=False)

# Bande dorée en haut
win_header = Entity(parent=camera.ui, model='quad', color=color.rgb(255, 180, 0), scale=(0.70, 0.08), position=(0, 0.27), z=-7, enabled=False)

# Titre
win_title = Text(text='VICTOIRE !', position=(0, 0.285), scale=2.8, color=color.rgb(15, 15, 30), enabled=False, origin=(0, 0), font='VeraMono.ttf', z=-6)

# Trophée emoji
win_trophy = Text(text='BRAVO', position=(0, 0.20), scale=2.2, color=color.rgb(255, 215, 0), enabled=False, origin=(0, 0), z=-6)

# Nom joueur
win_congrats = Text(text='', position=(0, 0.13), scale=1.6, color=color.rgb(150, 200, 255), enabled=False, origin=(0, 0), z=-6)

# Ligne séparatrice
win_sep = Entity(parent=camera.ui, model='quad', color=color.rgb(255, 180, 0), scale=(0.50, 0.003), position=(0, 0.08), z=-7, enabled=False)

# Score (gros)
win_score_label = Text(text='', position=(0, 0.02), scale=2.5, color=color.rgb(255, 215, 0), enabled=False, origin=(0, 0), font='VeraMono.ttf', z=-6)

# Pièces
win_coins_label = Text(text='', position=(0, -0.06), scale=1.5, color=color.rgb(200, 200, 220), enabled=False, origin=(0, 0), z=-6)

# Ligne séparatrice 2
win_sep2 = Entity(parent=camera.ui, model='quad', color=color.rgb(255, 180, 0), scale=(0.50, 0.003), position=(0, -0.12), z=-7, enabled=False)

# Instruction ESC
win_esc = Text(text='ESC pour retour au menu', position=(0, -0.18), scale=1.3, color=color.rgb(140, 140, 160), enabled=False, origin=(0, 0), z=-6)

# Bande dorée en bas
win_footer = Entity(parent=camera.ui, model='quad', color=color.rgb(255, 180, 0), scale=(0.70, 0.04), position=(0, -0.24), z=-7, enabled=False)

# Liste pour activation
win_elements = [
    win_overlay, win_border, win_bg, win_header, win_title,
    win_trophy, win_congrats, win_sep, win_score_label,
    win_coins_label, win_sep2, win_esc, win_footer,
]

# Texte de game over (créé désactivé, activé quand on touche une bombe)
game_over_text = Text(
    text='',
    position=(0, 0),
    scale=3,
    color=color.red,
    enabled=False,
    origin=(0, 0),
)

# ============== CAMERA ET SCENE ==============
camera.fov = 80
sky = Sky()
sun_light = DirectionalLight()
sun_light.look_at((0, -1, -1))

# Couleurs pour la transition jour → soir
day_sky_color = color.rgb(135, 206, 235)    # Bleu ciel
sunset_sky_color = color.rgb(40, 20, 60)    # Violet nuit
day_ambient = color.rgb(200, 200, 200)
sunset_ambient = color.rgb(255, 120, 50)    # Orange chaud
day_ground = GREEN
sunset_ground = color.rgb(30, 80, 30)       # Vert sombre
theme_changed = False

# Vitesse
move_speed = 8
forward_speed = 15
mario_z = mario_start_z  # track Mario's z position along the path

net_frame_counter = 0

def update():
    global score, coins_collected, game_won, game_over, mario_local_x, mario_z, net_frame_counter
    global net_winner

    # ============== RESEAU : reception des donnees ==============
    if multiplayer:
        net_receive()

        # ============== PHASE D'ATTENTE / COUNTDOWN ==============
        if not net_race_started:
            if net_countdown < 0:
                # En attente du 2ème joueur - fenêtre ouverte, jeu gelé
                if waiting_text:
                    waiting_text.enabled = True
                countdown_overlay.enabled = False
                countdown_number.enabled = False
                countdown_label.enabled = False
                countdown_players_info.enabled = False
                update_camera()
                return  # BLOQUER tout mouvement

            elif net_countdown > 0:
                # Countdown en cours (5, 4, 3, 2, 1)
                if waiting_text:
                    waiting_text.enabled = False
                countdown_overlay.enabled = True
                countdown_number.enabled = True
                countdown_label.enabled = True
                countdown_players_info.enabled = True
                countdown_number.text = str(net_countdown)
                countdown_number.scale = 8
                # Couleur dynamique
                if net_countdown >= 4:
                    countdown_number.color = color.rgb(255, 80, 80)
                elif net_countdown >= 2:
                    countdown_number.color = color.rgb(255, 200, 50)
                else:
                    countdown_number.color = color.rgb(100, 255, 100)
                other_name = net_other_player.get("name", "...") if net_other_player else "..."
                countdown_players_info.text = f'{player_name} (toi)  VS  {other_name}'
                update_camera()
                return  # BLOQUER tout mouvement

            else:
                # net_countdown == 0 → GO!
                if waiting_text:
                    waiting_text.enabled = False
                countdown_overlay.enabled = True
                countdown_number.enabled = True
                countdown_label.enabled = False
                countdown_players_info.enabled = False
                countdown_number.text = 'GO!'
                countdown_number.color = color.rgb(100, 255, 100)
                countdown_number.scale = 10
                update_camera()
                return  # Attendre le message "start" du serveur

        else:
            # Course lancée → cacher tout le UI d'attente
            if waiting_text:
                waiting_text.enabled = False
            countdown_overlay.enabled = False
            countdown_number.enabled = False
            countdown_label.enabled = False
            countdown_players_info.enabled = False

        # Synchroniser les coins collectés par l'autre joueur
        with net_lock:
            for idx in net_collected_coins:
                if 0 <= idx < len(coins) and coins[idx].enabled:
                    coins[idx].enabled = False

            # Mettre à jour le 2ème Mario
            if mario2 and net_other_player:
                mario2.x = net_other_player.get("x", mario2.x)
                mario2.y = net_other_player.get("y", mario2.y)
                mario2.z = net_other_player.get("z", mario2.z)
                mario2.rotation_y = net_other_player.get("ry", 180)

                # Nom au-dessus du 2ème Mario
                if mario2_name_text:
                    other_name = net_other_player.get("name", "Joueur 2")
                    mario2_name_text.text = other_name
                    mario2_name_text.world_position = Vec3(mario2.x, mario2.y + 5, mario2.z)

                # HUD du joueur 2
                if p2_name_hud:
                    p2_name_hud.text = net_other_player.get("name", "Joueur 2")
                if p2_score_hud:
                    p2_score_hud.text = f'Score:   {net_other_player.get("score", 0)}'
                if p2_coins_hud:
                    p2_coins_hud.text = f'Pieces:  {net_other_player.get("coins", 0)}/70'
                if p2_status_hud:
                    if net_other_player.get("finished"):
                        p2_status_hud.text = 'ARRIVE !'
                        p2_status_hud.color = color.rgb(255, 215, 0)
                    elif net_other_player.get("dead"):
                        p2_status_hud.text = 'ELIMINE'
                        p2_status_hud.color = color.red
                    else:
                        p2_status_hud.text = 'En course...'

            # Vérifier si l'autre joueur a gagné
            if net_winner is not None and not game_won and not game_over:
                if net_winner != net_player_id:
                    pass  # On continue à jouer

        # Nom local au-dessus de notre Mario
        if local_name_text:
            local_name_text.world_position = Vec3(mario.x, mario.y + 5, mario.z)

    if game_won or game_over:
        return

    # Rotation des pieces
    for coin in coins:
        if coin.enabled:
            coin.rotation_y += 100 * time.dt

    # Rotation des bombes pour visibilite
    for bomb in bombs:
        if bomb.enabled:
            bomb.rotation_y += 80 * time.dt

    # Avancer Mario le long de la route
    mario_z -= forward_speed * time.dt

    # Mouvement lateral (gauche/droite par rapport a la route)
    if held_keys['left arrow'] or held_keys['a']:
        mario_local_x -= move_speed * time.dt
    if held_keys['right arrow'] or held_keys['d']:
        mario_local_x += move_speed * time.dt

    mario_local_x = clamp(mario_local_x, -4, 4)

    # Calculer le centre et la direction de la route a la position de Mario
    rcx = road_center_x(mario_z)
    angle = road_angle_at(mario_z)
    angle_rad = math.radians(angle)

    # Direction perpendiculaire pour le decalage lateral
    perp_x = math.cos(angle_rad)
    perp_z = -math.sin(angle_rad)

    # Positionner Mario sur la route sinueuse
    mario.x = rcx + mario_local_x * perp_x
    mario.z = mario_z + mario_local_x * perp_z
    mario.y = 1

    # Tourner Mario dans la direction de la route
    mario.rotation_y = 180 + angle

    # ============== CAMERA toujours derrière Mario ==============
    update_camera()

    # ============== COLLECTE DES PIECES ==============
    for i, coin in enumerate(coins):
        if coin.enabled and distance(mario.position, coin.position) < 3:
            coin.enabled = False
            score += 100
            coins_collected += 1
            score_text.text = f'Score:   {score}'
            coins_text.text = f'Pieces:  {coins_collected}/70'
            if multiplayer:
                net_send_collect_coin(i)

    # ============== COLLISION AVEC BOMBE (FIN DE PARTIE) ==============
    for bomb in bombs:
        if bomb.enabled and distance(mario.position, bomb.position) < 2.5:
            bomb.enabled = False
            game_over = True
            game_over_text.enabled = True
            game_over_text.text = f'GAME OVER!\n\nBombe touchee!\nScore: {score}\n\nESC pour retour au menu'
            mario.visible = False
            if multiplayer:
                net_send_dead()
            return

    # ============== PROGRESSION ==============
    progress = clamp(int((mario_start_z - mario_z) / (mario_start_z - finish_z) * 100), 0, 100)

    # ============== TRANSITION JOUR VERS NUIT (apres 50%) ==============
    if progress >= 50:
        t = clamp((progress - 50) / 50, 0, 1)

        sky.color = color.rgb(
            int(135 * (1 - t)),
            int(206 * (1 - t)),
            int(235 * (1 - t)),
        )

        ground.color = color.rgb(
            int(50 * (1 - t) + 15 * t),
            int(150 * (1 - t) + 15 * t),
            int(50 * (1 - t) + 15 * t),
        )

        sun_light.color = color.rgb(
            int(255 * (1 - t) + 40 * t),
            int(255 * (1 - t) + 40 * t),
            int(255 * (1 - t) + 45 * t),
        )

        scene.fog_density = t * 0.01
        scene.fog_color = color.rgb(0, 0, 0)

    # ============== RESEAU : envoi de la position ==============
    if multiplayer:
        net_frame_counter += 1
        if net_frame_counter % 2 == 0:  # Envoyer toutes les 2 frames
            net_send_position(mario.x, mario.y, mario.z, mario.rotation_y, coins_collected, score)

    # ============== VICTOIRE ==============
    if mario_z <= finish_z + 5:
        game_won = True
        if multiplayer:
            net_send_finished()
            # Vérifier qui a gagné
            with net_lock:
                if net_winner is not None and net_winner != net_player_id:
                    # L'autre a gagné avant nous
                    win_trophy.text = '2EME'
                    win_congrats.text = f'{player_name}, tu es arrive 2eme !'
                else:
                    win_trophy.text = '1ER !'
                    win_congrats.text = f'Bravo {player_name}, tu es 1er !'
        else:
            win_congrats.text = f'Felicitations {player_name} !'

        for elem in win_elements:
            elem.enabled = True
        win_score_label.text = f'{score}'
        win_coins_label.text = f'Pieces collectees: {coins_collected} / 70'


def update_camera():
    """Met a jour la camera pour suivre Mario - appele chaque frame."""
    cam_behind_dist = 35
    cam_height = 22

    target_cam_x = mario.x
    target_cam_z = mario.z + cam_behind_dist
    target_cam_y = mario.y + cam_height

    smooth = 5 * time.dt
    camera.x += (target_cam_x - camera.x) * smooth
    camera.y += (target_cam_y - camera.y) * smooth
    camera.z += (target_cam_z - camera.z) * smooth

    camera.look_at(Vec3(mario.x, mario.y + 3, mario.z))

def input(key):
    if key == 'escape':
        application.quit()

print(f"Jeu demarre pour: {player_name}")
app.run()
