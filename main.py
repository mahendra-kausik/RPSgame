import tkinter as tk
import random
import screens.authScreen as authScreen
import utils.ip_util as ip_util

class RPSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x600")
        self.resizable(False, False)
        self.title("RPS Game")
        servers = ip_util.detect_servers()
        if servers:
            self.HOST = random.choice(servers)
        else:
            self.HOST = None  
        self.current_frame = None
        self.endMessage = None
        self.endTitle = None
        self.username = None
        self.oppName = None
        self.switch_frame(authScreen.AuthScreen)

    def switch_frame(self, n_frame):
        new_frame = n_frame(self)
        if self.current_frame is not None:
            self.current_frame.destroy()  
        self.current_frame = new_frame
        self.current_frame.pack()    

app = RPSApp()
app.mainloop()