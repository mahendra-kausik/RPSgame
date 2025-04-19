import socket
from _thread import start_new_thread
import signal
import sys
import logging
import time
import ssl

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

HOST = "0.0.0.0"
DATA_PORT = 5555
CTRL_PORT = 5556

# SSL Context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

pending_clients = {}
waiting_clients = []
games = {}
game_counter = 0

# Create regular sockets (do not wrap here)
server_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ctrl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_ctrl_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_data_socket.bind((HOST, DATA_PORT))
server_ctrl_socket.bind((HOST, CTRL_PORT))

server_data_socket.listen(5)
server_ctrl_socket.listen(5)

def graceful_exit(sig, frame):
    logging.info("Shutting down server gracefully...")
    server_data_socket.close()
    server_ctrl_socket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)

def accept_connections(sock, label):
    while True:
        conn, addr = sock.accept()
        try:
            ssl_conn = context.wrap_socket(conn, server_side=True)
            start_new_thread(handle_channel, (ssl_conn, addr, label))
        except Exception as e:
            logging.error(f"[{label}] SSL wrap failed for {addr}: {e}")
            conn.close()

def handle_channel(connection, address, channel_type):
    try:
        data = connection.recv(1024).decode().strip()
        if data == "PING":
            connection.close()
            return
        parts = data.split(";")
        if len(parts) != 3 or parts[0] != "CHANNEL" or parts[1] != channel_type:
            connection.close()
            return
        username = parts[2].strip()
        logging.info(f"{channel_type} channel received from {username}")
        if username not in pending_clients:
            pending_clients[username] = {"DATA": None, "CTRL": None}
        pending_clients[username][channel_type] = connection

        if pending_clients[username]["DATA"] and pending_clients[username]["CTRL"]:
            waiting_clients.append(username)
            logging.info(f"{username} is ready and added to queue")
            try_pair_clients()
    except Exception as e:
        logging.error(f"Error in {channel_type} channel handler: {e}")
        connection.close()

def try_pair_clients():
    global game_counter
    while len(waiting_clients) >= 2:
        u1 = waiting_clients.pop(0)
        u2 = waiting_clients.pop(0)
        g_id = game_counter
        game_counter += 1

        games[g_id] = {
            0: {"username": u1, "data_conn": pending_clients[u1]["DATA"], "ctrl_conn": pending_clients[u1]["CTRL"]},
            1: {"username": u2, "data_conn": pending_clients[u2]["DATA"], "ctrl_conn": pending_clients[u2]["CTRL"]}
        }

        del pending_clients[u1]
        del pending_clients[u2]

        logging.info(f"Paired players: {u1} and {u2} into game {g_id}")
        start_new_thread(game_data_handler, (g_id,))
        start_new_thread(game_ctrl_handler, (g_id,))

def game_data_handler(game_id):
    try:
        g = games[game_id]
        moves = {0: None, 1: None}
        while True:
            if moves[0] is None:
                try:
                    data0 = g[0]["data_conn"].recv(2048).decode()
                    if data0.startswith("MOVE"):
                        moves[0] = data0.split(";")[1]
                        logging.info(f"Game {game_id}: Player 1 move received")
                except:
                    break

            if moves[1] is None:
                try:
                    data1 = g[1]["data_conn"].recv(2048).decode()
                    if data1.startswith("MOVE"):
                        moves[1] = data1.split(";")[1]
                        logging.info(f"Game {game_id}: Player 2 move received")
                except:
                    break

            # When both moves are in, send them out
            if moves[0] is not None and moves[1] is not None:
                g[0]["data_conn"].send(f"UPDATE;{moves[1]}".encode())
                g[1]["data_conn"].send(f"UPDATE;{moves[0]}".encode())
                logging.info(f"Game {game_id}: Both moves sent, resetting")

                moves[0] = None
                moves[1] = None
    except Exception as e:
        logging.warning(f"Game {game_id} error: {e}")
        try: g[0]["ctrl_conn"].send("FORFEIT;".encode())
        except: pass
        try: g[1]["ctrl_conn"].send("FORFEIT;".encode())
        except: pass
        cleanup_game(game_id)


def game_ctrl_handler(game_id):
    try:
        g = games[game_id]
        g[0]["ctrl_conn"].send(f"FIRST;1;{g[1]['username']}".encode())
        g[1]["ctrl_conn"].send(f"FIRST;2;{g[0]['username']}".encode())

        while True:
            ctrl0 = g[0]["ctrl_conn"].recv(2048).decode()
            if ctrl0.startswith("END"):
                g[1]["ctrl_conn"].send("FORFEIT;".encode())
                break

            ctrl1 = g[1]["ctrl_conn"].recv(2048).decode()
            if ctrl1.startswith("END"):
                g[0]["ctrl_conn"].send("FORFEIT;".encode())
                break
    except:
        pass
    finally:
        cleanup_game(game_id)

def cleanup_game(game_id):
    g = games.get(game_id, {})
    for p in g.values():
        try: p["data_conn"].close()
        except: pass
        try: p["ctrl_conn"].close()
        except: pass
    if game_id in games:
        del games[game_id]

# Start accepting connections
start_new_thread(lambda: accept_connections(server_data_socket, "DATA"), ())
start_new_thread(lambda: accept_connections(server_ctrl_socket, "CTRL"), ())

logging.info(f"SSL server started on ports {DATA_PORT} (data), {CTRL_PORT} (control)")

while True:
    time.sleep(1)