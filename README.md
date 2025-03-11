# Rock-Paper-Scissors Game

A networked Rock-Paper-Scissors game built in Python with a graphical user interface (GUI) using Tkinter. The project supports both single-player (vs. a bot) and multiplayer (vs. another player) modes, complete with user authentication and real-time gameplay. All network communication is handled via TCP sockets.

---

## Features

- **User Authentication:**  
  Log in or sign up using stored credentials (via pickle) to access the game.
  
- **Single-Player Mode:**  
  Play against a computer-controlled opponent with a responsive GUI.

- **Multiplayer Mode:**  
  Challenge another player over the network in real time.

- **Reliable Networking:**  
  Uses TCP sockets to ensure reliable, ordered, and error-checked data transmission.

- **Automatic Server Detection:**  
  The client scans the local network to detect an active server automatically.

- **Multi-threaded Server:**  
  The server handles multiple client connections concurrently using threading.

---

## Requirements

- Python 3.x
- Tkinter (bundled with Python)
- [Pillow](https://pillow.readthedocs.io/) for image handling  
  _Install via:_ `pip install Pillow`

Other standard libraries used include: `socket`, `_thread`, `pickle`, and `os`.

---

## Installation

Clone the repository and install any necessary dependencies:

```bash
git clone https://github.com/mahendra-kausik/RPSgame.git
cd RPSgame
pip install -r requirements.txt
