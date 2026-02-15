"""
=== SERVEUR MULTIJOUEUR - SUPER MARIO AVENTURE ETOILEE ===
Serveur leger qui synchronise les positions et l'etat du jeu
entre 2 joueurs sur le meme parcours 3D en reseau local (LAN).

Le serveur :
  - Accepte 2 connexions de joueurs
  - Verifie le code de la salle
  - Lance un compte a rebours de 5 secondes
  - Diffuse l'etat du jeu 30 fois par seconde

Usage : python serveur_multijoueur.py
"""

import socket
import threading
import json
import time

HOST = "0.0.0.0"
PORT = 5556
ROOM_CODE = "AYOUB-YASSMINE"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Tenter de libérer le port si déjà utilisé
def kill_port(port):
    """Tue le processus qui utilise le port donné (Windows)."""
    try:
        import subprocess as _sp
        result = _sp.run(f'netstat -ano | findstr :{port} | findstr LISTENING', 
                        shell=True, capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 0:
                    _sp.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    print(f"[SERVEUR 3D] Ancien processus (PID {pid}) tue sur le port {port}")
                    time.sleep(1)
    except:
        pass

try:
    server.bind((HOST, PORT))
except OSError as e:
    print(f"[SERVEUR 3D] Port {PORT} deja utilise, tentative de liberation...")
    kill_port(PORT)
    time.sleep(1)
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        print(f"[SERVEUR 3D] Port {PORT} libere avec succes !")
    except OSError as e2:
        print(f"[SERVEUR 3D] ERREUR: Impossible de liberer le port {PORT} ({e2})")
        print(f"[SERVEUR 3D] Ferme l'ancien serveur manuellement.")
        time.sleep(5)
        exit(1)
server.listen(2)

# Afficher l'IP locale
try:
    import subprocess as sp
    result = sp.run(["ipconfig"], capture_output=True, text=True, encoding="cp850")
    for line in result.stdout.split("\n"):
        if "IPv4" in line:
            print(f"   -> {line.strip()}")
except:
    pass

print(f"\n[SERVEUR 3D] Code de salle: {ROOM_CODE}")
print(f"[SERVEUR 3D] Port: {PORT}")
print(f"[SERVEUR 3D] En attente de 2 joueurs...\n")

clients = {}
lock = threading.Lock()

game_state = {
    "players": {
        1: {"x": 0, "y": 1, "z": 350, "ry": 180, "coins": 0, "score": 0, "name": "Joueur 1", "finished": False, "dead": False},
        2: {"x": 0, "y": 1, "z": 345, "ry": 180, "coins": 0, "score": 0, "name": "Joueur 2", "finished": False, "dead": False},
    },
    "collected_coins": [],
    "winner": None,
    "game_started": False,
}


def send_json(conn, obj):
    try:
        conn.sendall((json.dumps(obj) + "\n").encode("utf-8"))
    except:
        pass


def broadcast(obj):
    with lock:
        for pid, conn in list(clients.items()):
            send_json(conn, obj)


def handle_client(pid, conn):
    conn.settimeout(5.0)

    # Vérification du code
    try:
        data = conn.recv(4096).decode("utf-8")
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
        print(f"[SERVEUR] Erreur code Joueur {pid}: {e}")
        with lock:
            clients.pop(pid, None)
        return

    # Traiter les messages restants (set_name, etc.)
    for line in lines[1:]:
        if line.strip():
            try:
                msg = json.loads(line)
                if msg.get("type") == "set_name":
                    with lock:
                        game_state["players"][pid]["name"] = msg.get("name", f"Joueur {pid}")
                        print(f"   Joueur {pid} = '{game_state['players'][pid]['name']}'")
            except:
                pass

    send_json(conn, {"type": "welcome", "player_id": pid})
    print(f"[SERVEUR] Welcome envoye a Joueur {pid}")

    buffer = ""
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

                if msg.get("type") == "position":
                    with lock:
                        p = game_state["players"][pid]
                        p["x"] = msg["x"]
                        p["y"] = msg["y"]
                        p["z"] = msg["z"]
                        p["ry"] = msg.get("ry", 180)
                        p["coins"] = msg.get("coins", 0)
                        p["score"] = msg.get("score", 0)

                elif msg.get("type") == "collect_coin":
                    idx = msg["index"]
                    with lock:
                        if idx not in game_state["collected_coins"]:
                            game_state["collected_coins"].append(idx)

                elif msg.get("type") == "finished":
                    with lock:
                        game_state["players"][pid]["finished"] = True
                        if game_state["winner"] is None:
                            game_state["winner"] = pid
                            print(f"[SERVEUR] Joueur {pid} a GAGNE !")

                elif msg.get("type") == "dead":
                    with lock:
                        game_state["players"][pid]["dead"] = True
                        print(f"[SERVEUR] Joueur {pid} est mort (bombe)")

                elif msg.get("type") == "set_name":
                    with lock:
                        game_state["players"][pid]["name"] = msg.get("name", f"Joueur {pid}")

        except socket.timeout:
            continue
        except Exception:
            break

    with lock:
        clients.pop(pid, None)
    conn.close()
    print(f"[SERVEUR] Joueur {pid} deconnecte")


def broadcast_loop():
    """Envoie l'état du jeu à tous les clients 30 fois par seconde."""
    while True:
        with lock:
            msg = {
                "type": "state",
                "players": game_state["players"],
                "collected_coins": game_state["collected_coins"],
                "winner": game_state["winner"],
            }
        broadcast(msg)
        time.sleep(1 / 30)


# ============== ACCEPTER 2 JOUEURS ==============
next_id = 1
while next_id <= 2:
    conn, addr = server.accept()
    print(f"[SERVEUR] Connexion depuis {addr}...")
    with lock:
        clients[next_id] = conn
    t = threading.Thread(target=handle_client, args=(next_id, conn), daemon=True)
    t.start()
    time.sleep(1.5)
    with lock:
        if next_id in clients:
            print(f"[SERVEUR] Joueur {next_id} accepte !")
            next_id += 1
        else:
            print(f"[SERVEUR] Connexion refusee, en attente...")

print("\n[SERVEUR] 2 joueurs connectes ! Compte a rebours...\n")

# ============== COMPTE A REBOURS 5 SECONDES ==============
for sec in range(5, 0, -1):
    print(f"[SERVEUR] Depart dans {sec}...")
    broadcast({"type": "countdown", "seconds": sec})
    time.sleep(1)

print("[SERVEUR] GO ! GO ! GO !\n")
broadcast({"type": "countdown", "seconds": 0})
time.sleep(0.3)

with lock:
    game_state["game_started"] = True
broadcast({"type": "start"})

# Lancer la diffusion d'état
threading.Thread(target=broadcast_loop, daemon=True).start()

# Garder le serveur en vie
try:
    while True:
        time.sleep(1)
        with lock:
            if game_state["winner"] is not None:
                w = game_state["winner"]
                wn = game_state["players"][w]["name"]
                print(f"\r[SERVEUR] Gagnant: {wn} (Joueur {w})", end="")
except KeyboardInterrupt:
    print("\n[SERVEUR] Arret.")
    server.close()
