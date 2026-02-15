"""
=== SERVEUR 2D - SUPER MARIO MULTIJOUEUR LAN ===
Ce fichier est le serveur pour la version 2D du jeu (Pygame).
Le serveur est l'arbitre : il gere les positions, collisions, pieces et scores.
Chaque client envoie seulement ses touches (gauche/droite/saut).
Le serveur simule le jeu et renvoie l'etat aux 2 joueurs.

Usage : python serveur_2d.py
"""

import socket
import threading
import json
import time
import random

HOST = "0.0.0.0"
PORT = 5555
ROOM_CODE = "AYOUB-YASSMINE"
TICK = 1 / 60  # 60 fps serveur

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(2)

# Afficher l'IP locale pour que les joueurs puissent se connecter
import subprocess
try:
    result = subprocess.run(["ipconfig"], capture_output=True, text=True, encoding="cp850")
    for line in result.stdout.split("\n"):
        if "IPv4" in line:
            print(f"   -> {line.strip()}")
except:
    pass

print(f"\n[SERVEUR] Pret sur {HOST}:{PORT}")
print("[SERVEUR] En attente de 2 joueurs...\n")

clients = {}              # pid -> conn
inputs = {1: {}, 2: {}}   # pid -> {left, right, jump}
lock = threading.Lock()

# ============== MONDE DU JEU ==============
W, H = 900, 500
GROUND_Y = 420
SPEED = 4.0
JUMP_V = -12.0
GRAVITY = 0.6
PLAYER_W, PLAYER_H = 30, 40
COIN_R = 12
TOTAL_COINS = 15


def clamp(v, a, b):
    return max(a, min(b, v))


# État initial du jeu
state = {
    "players": {
        1: {"x": 150, "y": GROUND_Y - PLAYER_H, "vx": 0, "vy": 0, "score": 0, "on_ground": True, "name": ""},
        2: {"x": 700, "y": GROUND_Y - PLAYER_H, "vx": 0, "vy": 0, "score": 0, "on_ground": True, "name": ""},
    },
    "coins": [],
    "platforms": [],
    "winner": None,
    "game_started": False,
}

# Créer des plateformes
platforms = [
    {"x": 100, "y": 300, "w": 120, "h": 15},
    {"x": 350, "y": 250, "w": 120, "h": 15},
    {"x": 600, "y": 300, "w": 120, "h": 15},
    {"x": 200, "y": 180, "w": 100, "h": 15},
    {"x": 500, "y": 180, "w": 100, "h": 15},
    {"x": 700, "y": 220, "w": 100, "h": 15},
    {"x": 50,  "y": 350, "w": 80,  "h": 15},
    {"x": 770, "y": 350, "w": 80,  "h": 15},
]
state["platforms"] = platforms

# Créer des coins sur les plateformes et au sol
coin_id = 0
for plat in platforms:
    state["coins"].append({
        "id": coin_id,
        "x": plat["x"] + plat["w"] // 2,
        "y": plat["y"] - 20
    })
    coin_id += 1

# Coins supplémentaires au sol et en l'air
for i in range(TOTAL_COINS - len(state["coins"])):
    state["coins"].append({
        "id": coin_id,
        "x": random.randint(60, W - 60),
        "y": random.randint(150, GROUND_Y - 60)
    })
    coin_id += 1


def send_json(conn, obj):
    """Envoie un objet JSON suivi d'un newline."""
    try:
        conn.sendall((json.dumps(obj) + "\n").encode("utf-8"))
    except:
        pass


def broadcast(obj):
    """Envoie l'état à tous les clients connectés."""
    dead = []
    with lock:
        for pid, conn in clients.items():
            try:
                send_json(conn, obj)
            except:
                dead.append(pid)
        for pid in dead:
            clients.pop(pid, None)


def handle_client(pid, conn):
    """Gère la connexion d'un client."""
    conn.settimeout(5.0)

    # ============== VÉRIFICATION DU CODE DE SALLE ==============
    try:
        data = conn.recv(4096).decode("utf-8")
        # Peut contenir plusieurs messages (join + set_name), on prend le premier
        lines = data.strip().split("\n")
        join_msg = json.loads(lines[0])

        if join_msg.get("type") != "join" or join_msg.get("code") != ROOM_CODE:
            send_json(conn, {"type": "error", "message": "Code incorrect"})
            conn.close()
            print(f"[SERVEUR] Connexion refusee (mauvais code) pour Joueur {pid}")
            with lock:
                clients.pop(pid, None)
            return
        else:
            print(f"[SERVEUR] Code correct pour Joueur {pid}")
    except Exception as e:
        send_json(conn, {"type": "error", "message": "Erreur de verification"})
        conn.close()
        print(f"[SERVEUR] Erreur verification code Joueur {pid}: {e}")
        with lock:
            clients.pop(pid, None)
        return

    buffer = ""
    send_json(conn, {"type": "welcome", "player_id": pid})

    # Traiter les messages restants du premier paquet (set_name, etc.)
    for line in lines[1:]:
        if line.strip():
            try:
                msg = json.loads(line)
                if msg.get("type") == "set_name":
                    with lock:
                        state["players"][pid]["name"] = msg.get("name", f"Joueur {pid}")
                        print(f"   Joueur {pid} = '{state['players'][pid]['name']}'")
            except:
                pass

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                msg = json.loads(line)
                if msg.get("type") == "input":
                    with lock:
                        inputs[pid] = {
                            "left": bool(msg.get("left", False)),
                            "right": bool(msg.get("right", False)),
                            "jump": bool(msg.get("jump", False)),
                        }
                elif msg.get("type") == "set_name":
                    with lock:
                        state["players"][pid]["name"] = msg.get("name", f"Joueur {pid}")
                        print(f"   Joueur {pid} = '{state['players'][pid]['name']}'")
        except socket.timeout:
            continue
        except Exception as e:
            break

    with lock:
        clients.pop(pid, None)
    conn.close()
    print(f"[SERVEUR] Joueur {pid} deconnecte")


def rects_collide(ax, ay, aw, ah, bx, by, bw, bh):
    """Vérifie la collision entre deux rectangles."""
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


# ============== ACCEPTER 2 JOUEURS ==============
print(f"[SERVEUR] Code de la salle : {ROOM_CODE}\n")
next_id = 1
while next_id <= 2:
    conn, addr = server.accept()
    print(f"[SERVEUR] Connexion depuis {addr}...")
    with lock:
        clients[next_id] = conn
    t = threading.Thread(target=handle_client, args=(next_id, conn), daemon=True)
    t.start()
    # Attendre un peu pour voir si le code est accepté
    time.sleep(1)
    with lock:
        if next_id in clients:
            # Le client est toujours connecté = code accepté
            print(f"[SERVEUR] Joueur {next_id} accepte !")
            next_id += 1
        else:
            print(f"[SERVEUR] Connexion refusee, en attente d'un autre joueur...")

print("\n[SERVEUR] 2 joueurs connectes ! Demarrage du jeu...\n")
state["game_started"] = True

# ============== BOUCLE DE SIMULATION ==============
while True:
    with lock:
        for pid in (1, 2):
            p = state["players"][pid]
            inp = inputs.get(pid, {})

            # Mouvement horizontal
            vx = 0
            if inp.get("left"):
                vx -= SPEED
            if inp.get("right"):
                vx += SPEED
            p["vx"] = vx

            # Saut
            if inp.get("jump") and p["on_ground"]:
                p["vy"] = JUMP_V
                p["on_ground"] = False

            # Gravité
            p["vy"] += GRAVITY

            # Intégration
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            # Limites horizontales
            p["x"] = clamp(p["x"], 0, W - PLAYER_W)

            # Collision avec le sol
            if p["y"] >= GROUND_Y - PLAYER_H:
                p["y"] = GROUND_Y - PLAYER_H
                p["vy"] = 0
                p["on_ground"] = True

            # Collision avec les plateformes (seulement en tombant)
            if p["vy"] >= 0:
                for plat in platforms:
                    if (p["x"] + PLAYER_W > plat["x"] and
                        p["x"] < plat["x"] + plat["w"] and
                        p["y"] + PLAYER_H >= plat["y"] and
                        p["y"] + PLAYER_H <= plat["y"] + plat["h"] + p["vy"] + 2):
                        p["y"] = plat["y"] - PLAYER_H
                        p["vy"] = 0
                        p["on_ground"] = True

        # Ramassage des coins (le serveur décide)
        remaining = []
        for c in state["coins"]:
            picked = False
            for pid in (1, 2):
                p = state["players"][pid]
                if rects_collide(
                    p["x"], p["y"], PLAYER_W, PLAYER_H,
                    c["x"] - COIN_R, c["y"] - COIN_R, COIN_R * 2, COIN_R * 2
                ):
                    state["players"][pid]["score"] += 1
                    picked = True
                    print(f"   Coin #{c['id']} ramasse par Joueur {pid} (score: {state['players'][pid]['score']})")
                    break
            if not picked:
                remaining.append(c)
        state["coins"] = remaining

        # Condition de victoire
        if state["winner"] is None and len(state["coins"]) == 0:
            s1 = state["players"][1]["score"]
            s2 = state["players"][2]["score"]
            n1 = state["players"][1]["name"] or "Joueur 1"
            n2 = state["players"][2]["name"] or "Joueur 2"
            if s1 > s2:
                state["winner"] = 1
                print(f"\n[SERVEUR] {n1} GAGNE ! ({s1} vs {s2})")
            elif s2 > s1:
                state["winner"] = 2
                print(f"\n[SERVEUR] {n2} GAGNE ! ({s2} vs {s1})")
            else:
                state["winner"] = 0
                print(f"\n[SERVEUR] EGALITE ! ({s1} vs {s2})")

        snapshot = {"type": "state", "state": state}

    broadcast(snapshot)
    time.sleep(TICK)
