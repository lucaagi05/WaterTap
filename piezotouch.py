import serial
import tkinter as tk
import threading

# --- CONFIGURATION ---
SERIAL_PORT = 'COM8'  # Update to your active Arduino port
BAUD_RATE = 115200
GRID_SIZE = 450       # Window dimension in pixels

# Adjust this filter weight if needed (0.10 = ultra smooth/dampened, 1.0 = raw/instant)
FILTER_SMOOTHING = 0.50  

class Advanced9PointSmoothApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Piezo Matrix: 9-Point Calibrated & Stabilized Grid")
        
        self.canvas = tk.Canvas(root, width=GRID_SIZE, height=GRID_SIZE, bg="#111111")
        self.canvas.pack()
        
        # Draw target guide lines
        for i in range(1, 3):
            self.canvas.create_line(GRID_SIZE * i / 3, 0, GRID_SIZE * i / 3, GRID_SIZE, fill="#222222", dash=(2, 2))
            self.canvas.create_line(0, GRID_SIZE * i / 3, GRID_SIZE, GRID_SIZE * i / 3, fill="#222222", dash=(2, 2))
            
        self.status_text = self.canvas.create_text(
            GRID_SIZE/2, GRID_SIZE - 25, 
            text="Q = Calibrate 9 Points | C = Reset to Default", 
            fill="#00FF00", font=("Arial", 11, "bold")
        )
        
        self.marker = None
        self.calib_markers = []
        
        # Historical tracking positions for the filter buffer
        self.display_x = GRID_SIZE / 2
        self.display_y = GRID_SIZE / 2
        
        # Calibration State Parameters
        self.is_calibrating = False
        self.calib_step = 0
        self.calib_labels = [
            "STEP 1/9: Tap TOP-LEFT Corner",
            "STEP 2/9: Tap TOP-MIDDLE (On Piezo)",
            "STEP 3/9: Tap TOP-RIGHT Corner",
            "STEP 4/9: Tap MIDDLE-LEFT Edge",
            "STEP 5/9: Tap absolute CENTER of board",
            "STEP 6/9: Tap MIDDLE-RIGHT Edge",
            "STEP 7/9: Tap BOTTOM-LEFT (On Piezo)",
            "STEP 8/9: Tap BOTTOM-MIDDLE Edge",
            "STEP 9/9: Tap BOTTOM-RIGHT (On Piezo)"
        ]
        
        self.target_pixels = [
            (50, 50), (GRID_SIZE/2, 50), (GRID_SIZE-50, 50),
            (50, GRID_SIZE/2), (GRID_SIZE/2, GRID_SIZE/2), (GRID_SIZE-50, GRID_SIZE/2),
            (50, GRID_SIZE-50), (GRID_SIZE/2, GRID_SIZE-50), (GRID_SIZE-50, GRID_SIZE-50)
        ]
        
        self.calib_data = {}
        self.set_default_boundaries()
        
        # Keyboard Bindings
        self.root.bind("<q>", self.start_calibration)
        self.root.bind("<Q>", self.start_calibration)
        self.root.bind("<c>", self.reset_calibration)
        self.root.bind("<C>", self.reset_calibration)
        
        self.running = True
        self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.serial_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_default_boundaries(self):
        self.min_raw_x, self.max_raw_x = -350, 350
        self.min_raw_y, self.max_raw_y = -450, 350
        self.calib_data = {}
        for m in self.calib_markers:
            self.canvas.delete(m)
        self.calib_markers = []

    def start_calibration(self, event):
        if not self.is_calibrating:
            self.set_default_boundaries()
            self.is_calibrating = True
            self.calib_step = 0
            self.show_next_target()

    def reset_calibration(self, event):
        self.is_calibrating = False
        self.calib_step = 0
        self.set_default_boundaries()
        self.update_status("Calibration cleared. Defaults loaded.", color="#00FFFF")

    def update_status(self, text, color="#00FF00"):
        self.canvas.itemconfig(self.status_text, text=text, fill=color)

    def show_next_target(self):
        self.update_status(self.calib_labels[self.calib_step], color="#FFCC00")
        tx, ty = self.target_pixels[self.calib_step]
        t_marker = self.canvas.create_oval(tx-8, ty-8, tx+8, ty+8, outline="#FFCC00", width=3, fill="#443300")
        self.calib_markers.append(t_marker)

    def process_calibration_point(self, raw_x, raw_y):
        self.calib_data[self.calib_step] = (raw_x, raw_y)
        self.canvas.itemconfig(self.calib_markers[self.calib_step], fill="#004400", outline="#00FF00")
        
        self.calib_step += 1
        if self.calib_step < 9:
            self.show_next_target()
        else:
            self.is_calibrating = False
            
            # Map coordinates based on dynamic bounding rows calculated from your true structural hits
            self.min_raw_x = (self.calib_data[0][0] + self.calib_data[3][0] + self.calib_data[6][0]) / 3
            self.max_raw_x = (self.calib_data[2][0] + self.calib_data[5][0] + self.calib_data[8][0]) / 3
            self.min_raw_y = (self.calib_data[6][1] + self.calib_data[7][1] + self.calib_data[8][1]) / 3
            self.max_raw_y = (self.calib_data[0][1] + self.calib_data[1][1] + self.calib_data[2][1]) / 3
            
            self.update_status("9-Point Boundaries Active!", color="#00FF00")

    def read_serial(self):
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        except Exception:
            self.update_status(f"Port Error on {SERIAL_PORT}", color="#FF3333")
            return

        while self.running:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "," in line:
                    try:
                        parts = line.split(",")
                        raw_x = int(parts[0])
                        raw_y = int(parts[1])
                        
                        if self.is_calibrating:
                            self.root.after(0, self.process_calibration_point, raw_x, raw_y)
                        else:
                            # Map raw points onto our calibrated limits
                            norm_x = (raw_x - self.min_raw_x) / max(1, (self.max_raw_x - self.min_raw_x))
                            norm_y = (raw_y - self.min_raw_y) / max(1, (self.max_raw_y - self.min_raw_y))
                            
                            norm_x = max(0.0, min(1.0, norm_x))
                            norm_y = max(0.0, min(1.0, norm_y))
                            
                            target_x = norm_x * GRID_SIZE
                            target_y = (1.0 - norm_y) * GRID_SIZE
                            
                            # Smooth data jumps with the Low-Pass filter math
                            self.display_x = (target_x * FILTER_SMOOTHING) + (self.display_x * (1.0 - FILTER_SMOOTHING))
                            self.display_y = (target_y * FILTER_SMOOTHING) + (self.display_y * (1.0 - FILTER_SMOOTHING))
                            
                            self.root.after(0, self.draw_impact, self.display_x, self.display_y)
                    except (ValueError, IndexError):
                        pass
        ser.close()

    def draw_impact(self, x, y):
        if self.marker: self.canvas.delete(self.marker)
        r = 12
        self.marker = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#FF3333", outline="#FFFFFF", width=2)

    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = Advanced9PointSmoothApp(root)
    root.mainloop()