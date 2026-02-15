from ursina import *
import random
import sys
import math

# Get player name from command line
player_name = "Joueur"
if len(sys.argv) > 1:
    player_name = sys.argv[1]

# Initialize Ursina
app = Ursina(title=f'Super Mario - {player_name}', borderless=False)

# Window settings
window.fullscreen = False
window.size = (1400, 800)
window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.exit_button.visible = False

# Game variables
score = 0
coins_collected = 0
game_won = False
game_over = False
mario_local_x = 0  # offset latéral du joueur par rapport au centre de la route

# Colors
GREEN = color.rgb(34, 197, 94)
BROWN = color.rgb(139, 69, 19)
GRAY = color.rgb(180, 180, 180)
GOLD = color.rgb(255, 215, 0)
DARK_BROWN = color.rgb(100, 50, 10)

# ============== CURVED ROAD SYSTEM ==============
# Route longue avec de grands virages (la route va à droite et avance)
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

# ============== CREATE GROUND ==============
ground = Entity(
    model='plane',
    scale=(500, 1, 2000),
    color=GREEN,
    texture='grass',
    collider='box'
)

# ============== CREATE CURVED ROAD SEGMENTS ==============
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

# ============== LOAD MARIO ==============
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

# ============== CREATE COINS ON THE CURVED PATH ==============
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

# ============== BUILDINGS ALONG CURVED ROAD ==============
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

# ============== CARS ALONG CURVED ROAD ==============
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

# ============== BOMBS ON THE ROAD ==============
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

# ============== MIDPOINT MARKER (transition jour → soir) ==============
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

# ============== FINISH LINE (professionnelle) ==============
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

# ============== UI PANEL ==============
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

# ============== CAMERA & SCENE ==============
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

# Speed
move_speed = 8
forward_speed = 15
mario_z = mario_start_z  # track Mario's z position along the path

def update():
    global score, coins_collected, game_won, game_over, mario_local_x, mario_z
    if game_won or game_over:
        return
    
    # Rotate coins
    for coin in coins:
        if coin.enabled:
            coin.rotation_y += 100 * time.dt
    
    # Rotate/pulse bombs for visibility
    for bomb in bombs:
        if bomb.enabled:
            bomb.rotation_y += 80 * time.dt
    
    # Move Mario forward along path
    mario_z -= forward_speed * time.dt
    
    # Lateral movement (left/right relative to road)
    if held_keys['left arrow'] or held_keys['a']:
        mario_local_x -= move_speed * time.dt
    if held_keys['right arrow'] or held_keys['d']:
        mario_local_x += move_speed * time.dt
    
    mario_local_x = clamp(mario_local_x, -4, 4)
    
    # Calculate road center and direction at Mario's position
    rcx = road_center_x(mario_z)
    angle = road_angle_at(mario_z)
    angle_rad = math.radians(angle)
    
    # Perpendicular direction for lateral offset
    perp_x = math.cos(angle_rad)
    perp_z = -math.sin(angle_rad)
    
    # Position Mario on the curved road
    mario.x = rcx + mario_local_x * perp_x
    mario.z = mario_z + mario_local_x * perp_z
    mario.y = 1
    
    # Rotate Mario to face the road direction
    mario.rotation_y = 180 + angle
    
    # ============== CAMERA toujours derrière Mario ==============
    cam_behind_dist = 35
    cam_height = 22
    
    # La caméra suit Mario simplement : même X que Mario, derrière en Z
    target_cam_x = mario.x
    target_cam_z = mario.z + cam_behind_dist
    target_cam_y = mario.y + cam_height
    
    # Lerp fluide pour un mouvement doux
    smooth = 5 * time.dt
    camera.x += (target_cam_x - camera.x) * smooth
    camera.y += (target_cam_y - camera.y) * smooth
    camera.z += (target_cam_z - camera.z) * smooth
    
    # La caméra regarde toujours Mario
    camera.look_at(Vec3(mario.x, mario.y + 3, mario.z))
    
    # ============== COIN COLLECTION ==============
    for coin in coins:
        if coin.enabled and distance(mario.position, coin.position) < 3:
            coin.enabled = False
            score += 100
            coins_collected += 1
            score_text.text = f'Score:   {score}'
            coins_text.text = f'Pieces:  {coins_collected}/70'
    
    # ============== BOMB COLLISION (GAME OVER) ==============
    for bomb in bombs:
        if bomb.enabled and distance(mario.position, bomb.position) < 2.5:
            bomb.enabled = False
            game_over = True
            game_over_text.enabled = True
            game_over_text.text = f'GAME OVER!\n\nBombe touchee!\nScore: {score}\n\nESC pour retour au menu'
            mario.visible = False
            return
    
    # ============== PROGRESS ==============
    progress = clamp(int((mario_start_z - mario_z) / (mario_start_z - finish_z) * 100), 0, 100)
    
    # ============== TRANSITION JOUR → MODE SOMBRE (après 50%) ==============
    # Style Chrome Dino dark mode : fond noir, sol sombre, ambiance nuit
    if progress >= 50:
        t = clamp((progress - 50) / 50, 0, 1)
        
        # Ciel → noir total
        sky.color = color.rgb(
            int(135 * (1 - t)),
            int(206 * (1 - t)),
            int(235 * (1 - t)),
        )
        
        # Sol → noir/gris très sombre (style Chrome Dino)
        ground.color = color.rgb(
            int(50 * (1 - t) + 15 * t),
            int(150 * (1 - t) + 15 * t),
            int(50 * (1 - t) + 15 * t),
        )
        
        # Lumière → très faible, gris sombre
        sun_light.color = color.rgb(
            int(255 * (1 - t) + 40 * t),
            int(255 * (1 - t) + 40 * t),
            int(255 * (1 - t) + 45 * t),
        )
        
        # Fog noir pour renforcer l'ambiance sombre
        scene.fog_density = t * 0.01
        scene.fog_color = color.rgb(0, 0, 0)
    
    # ============== WIN ==============
    if mario_z <= finish_z + 5:
        game_won = True
        for elem in win_elements:
            elem.enabled = True
        win_congrats.text = f'Felicitations {player_name} !'
        win_score_label.text = f'{score}'
        win_coins_label.text = f'Pieces collectees: {coins_collected} / 70'

def input(key):
    if key == 'escape':
        application.quit()

print(f"Jeu demarre pour: {player_name}")
app.run()
