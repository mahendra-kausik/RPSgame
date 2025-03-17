import socket
from _thread import start_new_thread
import signal
import sys
import logging
import time

# Setup Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

HOST = "0.0.0.0"
PORT = 5555

# Global structures for managing game sessions and waiting players
games = {}         # game_id: {0: {...}, 1: {...}}
waiting_clients = []  # list of tuples: (connection, address, username)
game_counter = 0

server_socket = None  # Global server socket for graceful shutdown


def graceful_exit(signal_num, frame):
    global server_socket
    logging.info("Shutting down server gracefully...")
    if server_socket:
        server_socket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)


def client_thread(connection, p_id, game_id):
    opp_id = 0 if p_id == 1 else 1

    try:
        # Wait until both players are paired
        while game_id not in games or not games[game_id].get(p_id, {}).get("paired", False):
            time.sleep(0.05)  # avoid busy waiting

        # Send the pairing information
        opponent_username = games[game_id][opp_id]['username']
        connection.send(f"FIRST;{p_id+1};{opponent_username}".encode())
        logging.info(f"Sent pairing info to Player {p_id+1} in game {game_id}")

        while True:
            data = connection.recv(2048).decode()
            if not data:
                break

            if game_id in games:
                game = games[game_id]
                parts = data.split(";")
                msg_type = parts[0]

                if msg_type == "MOVE":
                    move = parts[1]
                    game[p_id]["move"] = move
                    logging.info(f"Game {game_id}: Player {p_id+1} move: {move}")

                    if game[opp_id]["move"] is not None:
                        # Both players have made their moves.
                        game[opp_id]["conn"].send(f"UPDATE;{game[p_id]['move']}".encode())
                        game[p_id]["conn"].send(f"UPDATE;{game[opp_id]['move']}".encode())
                        logging.info(f"Game {game_id}: Moves exchanged between players.")

                        # Reset moves
                        game[p_id]["move"] = None
                        game[opp_id]["move"] = None

                elif msg_type == "END":
                    logging.info(f"Game {game_id}: Player {p_id+1} ended the game.")
                    connection.close()
                    game[opp_id]["conn"].close()
                    break

            else:
                break

    except Exception as e:
        logging.error(f"Exception in client thread for game {game_id}: {e}")

    finally:
        logging.info(f"Player {p_id+1} in game {game_id} has disconnected!")
        try:
            # Inform opponent of disconnection if possible
            if game_id in games and games[game_id].get(opp_id):
                games[game_id][opp_id]["conn"].send("FORFEIT;".encode())
            if game_id in games:
                del games[game_id]
        except Exception as e:
            logging.warning(f"Cleanup error in game {game_id}: {e}")
        connection.close()


def handle_new_connection(connection, address):
    global game_counter

    try:
        first_msg = connection.recv(2048).decode()
    except Exception as e:
        logging.error(f"Error receiving initial message from {address}: {e}")
        connection.close()
        return

    # Ignore PING messages used for server detection
    if first_msg == "PING":
        connection.close()
        return

    username = first_msg.strip()
    logging.info(f"New connection from {address} with username: {username}")

    # If there is a waiting client, pair them
    if waiting_clients:
        waiting_conn, waiting_addr, waiting_username = waiting_clients.pop(0)
        game_id = game_counter
        game_counter += 1

        games[game_id] = {
            0: {"conn": waiting_conn, "username": waiting_username, "move": None, "paired": True},
            1: {"conn": connection, "username": username, "move": None, "paired": True}
        }
        logging.info(f"Paired players: {waiting_username} and {username} into game {game_id}")

        # Start threads for both players
        start_new_thread(client_thread, (waiting_conn, 0, game_id))
        start_new_thread(client_thread, (connection, 1, game_id))
    else:
        # No waiting player: add this client to the waiting queue
        waiting_clients.append((connection, address, username))
        logging.info(f"Added {username} to waiting queue.")


# Server Initialization
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server_socket.bind((HOST, PORT))
except socket.error as e:
    logging.error(f"Bind failed: {e}")
    sys.exit()

server_socket.listen(5)
logging.info(f"Server started on {HOST}:{PORT}")

while True:
    try:
        connection, address = server_socket.accept()
        handle_new_connection(connection, address)
    except Exception as e:
        logging.error(f"Server exception: {e}")