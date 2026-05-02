import time
from config.display_manager import display
from screens.menu import MenuScreen
from screens.library import LibraryScreen

class EReader:
    def __init__(self):
        self.current_screen = None
        self.running = True
        
    def switch_to(self, screen_class, **kwargs):
        # Deep clear before new screen
        display.deep_clear()
        self.current_screen = screen_class(self,**kwargs)
        self.current_screen.draw()
    
    def run(self):
        display.init_display()
        self.switch_to(MenuScreen)
        
        # Button mapping (replace with GPIO later)
        # For testing: simulate buttons via keyboard input
        # We'll use a simple input() loop (no sshkeyboard conflicts)
        while self.running:
            key = input("Press key (w=up, s=down, p=select, q=go-back, z=quit): ").strip()
            if key == 'z':
                self.running = False
            else:
                self.current_screen.handle_key(key)

if __name__ == "__main__":
    ereader = EReader()
    ereader.run()
