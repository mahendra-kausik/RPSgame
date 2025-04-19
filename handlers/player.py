import socket
import ssl
import time
import tkinter as tk
import threading
from tkinter import ttk
import screens.endScreen as EndScreen

PORT_DATA = 5555
PORT_CTRL = 5556
p_moves = {"r": 0, "p": 1, "s": 2}
points = [0, 0]

class PlayerHandler:
    def __init__(self, master, frame):
        self.master = master
        self.frame = frame
        self.labels = frame.labels
        self.buttons = frame.buttons
        self.notif_label = ttk.Label(self.frame, text="Pairing", font=("Helvetica", 20, "bold"), foreground="red")
        self.notif_label.grid(row=1, column=2)
        self.player_move = None
        self.opponent_move = None
        self.running = True  # New flag to gracefully stop threads

        self.toggle_buttons(tk.DISABLED)
        self.connect()

    def connect(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        self.data_client = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=self.master.HOST)
        self.ctrl_client = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=self.master.HOST)

        self.data_client.connect((self.master.HOST, PORT_DATA))
        self.ctrl_client.connect((self.master.HOST, PORT_CTRL))

        self.data_client.send(f"CHANNEL;DATA;{self.master.username}".encode())
        self.ctrl_client.send(f"CHANNEL;CTRL;{self.master.username}".encode())

        threading.Thread(target=self.receive_data, daemon=True).start()
        threading.Thread(target=self.receive_ctrl, daemon=True).start()

    def receive_data(self):
        while self.running:
            try:
                data = self.data_client.recv(2048).decode().strip()
                if not data:
                    break
                if data.startswith("UPDATE;"):
                    move = data.split(";")[1]
                    self.master.after(0, self.update, move, True)
            except:
                break

    def receive_ctrl(self):
        while self.running:
            try:
                data = self.ctrl_client.recv(2048).decode().strip()
                if not data:
                    break
                if data.startswith("FIRST"):
                    _, pid, opp = data.split(";")
                    self.player_id = pid
                    self.master.oppName = opp
                    self.frame.oppLabel.config(text=opp)
                    self.master.after(0, self.toggle_buttons, tk.NORMAL)
                    self.master.after(0, self.show_notif, "Start!")
                elif data.startswith("FORFEIT"):
                    self.running = False
                    self.master.endMessage = "Opponent disconnected!"
                    self.master.switch_frame(EndScreen.EndScreen)
                    break
            except:
                break

    def send(self, msg):
        try:
            self.data_client.send(msg.encode())
        except:
            pass

    def handle_click(self, choice):
        self.master.after(0, self.update, choice, False)
        self.send(f"MOVE;{choice}")

    def update(self, move, opp):
        if not opp:
            self.player_move = p_moves[move]
            self.toggle_buttons(tk.DISABLED)
            self.labels[0].config(image=self.frame.imgs[self.player_move])
        else:
            self.opponent_move = p_moves[move]
            self.labels[1].config(image=self.frame.oppImgs[self.opponent_move])

        # Only determine winner when both moves are available
        if self.player_move is not None and self.opponent_move is not None:
            self.master.after(500, self.determine_winner)

    def determine_winner(self):
        if self.player_move == self.opponent_move:
            result = "Tie"
        elif (self.player_move - self.opponent_move) % 3 == 1:
            result = "Player"
        else:
            result = "Opponent"

        self.master.after(0, self.show_notif,
            "Yay!" if result == "Player" else
            "Whoops!" if result == "Opponent" else "Tie!"
        )
        self.master.after(0, self.update_stats, result)

    def update_stats(self, result):
        if result == "Player":
            points[0] += 1
        elif result == "Opponent":
            points[1] += 1
        self.labels[2].config(text=points[0])
        self.labels[3].config(text=points[1])
        self.master.after(500, self.reset)

    def toggle_buttons(self, state):
        for b in self.buttons:
            b["state"] = state

    def show_notif(self, msg):
        self.notif_label.config(text=msg)
        self.notif_label.grid(row=1, column=2)
        self.master.after(500, self.hide_notif)

    def hide_notif(self):
        try:
            self.notif_label.grid_remove()
        except:
            pass

    def reset(self):
        self.player_move = None
        self.opponent_move = None
        self.labels[0].config(image=self.frame.blankImg)
        self.labels[1].config(image=self.frame.blankImg)
        self.toggle_buttons(tk.NORMAL)
        self.master.after(0, self.show_notif, "Play!")
        self.master.after(200, self.check_end)

    def check_end(self):
        if points[0] == 5:
            self.running = False
            self.master.endTitle = "You Won!"
            self.master.endMessage = f"You won {points[0]} - {points[1]}!"
            self.master.switch_frame(EndScreen.EndScreen)
            if self.player_id == "1":
                self.ctrl_client.send("END;".encode())
        elif points[1] == 5:
            self.running = False
            self.master.endTitle = "You Lost!"
            self.master.endMessage = f"You lost {points[0]} - {points[1]}!"
            self.master.switch_frame(EndScreen.EndScreen)