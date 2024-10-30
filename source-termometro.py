import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TemperatureMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Temperatura")
        self.serial_port = None
        self.arduino_connected = False
        self.is_measuring = False
        self.temperatures = []
        self.start_time = None
        self.file_path = None
        self.latest_temp = None  # Store the latest temperature value

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if self.is_measuring:
            self.is_measuring = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.quit()
        self.root.destroy()
        print("Programa encerrado.")

    def create_widgets(self):
        control_frame = tk.Frame(self.root)
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.start_button = tk.Button(
            control_frame, text="INICIAR", command=self.toggle_measurement)
        self.start_button.grid(row=0, column=0, columnspan=2, pady=10)

        config_frame = tk.LabelFrame(control_frame, text="Parâmetros de medição")
        config_frame.grid(row=2, column=0, columnspan=2, pady=10)

        connect_frame = tk.LabelFrame(control_frame, text="Conexão")
        connect_frame.grid(row=3, column=0, columnspan=2, pady=10)

        tk.Label(connect_frame, text="Portas:").grid(row=0, column=0, sticky="w")
        self.port_combobox = ttk.Combobox(
            connect_frame, values=self.get_serial_ports())
        self.port_combobox.grid(row=0, column=1, sticky="w")

        self.connect_button = tk.Button(
            connect_frame, text="CONECTAR", command=self.connect_arduino)
        self.connect_button.grid(row=1, column=0, pady=5, padx=5)

        self.refresh_button = tk.Button(
            connect_frame, text="ATUALIZAR", command=self.refresh_serial_ports)
        self.refresh_button.grid(row=1, column=1, pady=5, padx=5)

        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=1)

        self.line_obj, = self.ax.plot([], [], '--r', label="Temperatura do objeto")
        self.ax.set_ylim(0, 20)
        self.ax.set_xlim(0, 10)
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Temperatura (°C)")
        self.ax.legend()

    def refresh_serial_ports(self):
        self.port_combobox['values'] = self.get_serial_ports()
        self.port_combobox.set("")

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_arduino(self):
        if self.arduino_connected:
            self.disconnect_arduino()
        else:
            selected_port = self.port_combobox.get()
            if selected_port:
                try:
                    self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
                    self.arduino_connected = True
                    self.connect_button.config(text="DESCONECTAR")
                    time.sleep(2)  # Give time for the connection
                except serial.SerialException:
                    messagebox.showerror("Erro", "Não foi possível conectar ao Arduino.")
            else:
                messagebox.showerror("Erro", "Selecione uma porta serial.")

    def disconnect_arduino(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.arduino_connected = False
        self.connect_button.config(text="CONECTAR")

    def toggle_measurement(self):
        if not self.arduino_connected:
            messagebox.showerror("Erro", "Conecte ao Arduino primeiro.")
            return

        if self.is_measuring:
            self.is_measuring = False
            self.start_button.config(text="INICIAR")
        else:
            self.file_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if not self.file_path:
                messagebox.showwarning("Aviso", "Você precisa selecionar um local para salvar os dados.")
                return
            self.clear_graph()
            self.is_measuring = True
            self.start_button.config(text="STOP")
            threading.Thread(target=self.listen_to_serial, daemon=True).start()
            self.start_timer()  # Start the timer for 1000ms updates

    def listen_to_serial(self):
        while self.is_measuring:
            if self.serial_port.in_waiting > 0:  # Check if data is available
                data = self.serial_port.readline().decode('utf-8').strip()
                print(f"Recebido: {data}")  # Debugging the received data
                try:
                    self.latest_temp = float(data)  # Store latest temperature value
                except ValueError:
                    print(f"Erro de conversão: {data}")

    def start_timer(self):
        self.update_graph_and_save()  # First immediate update
        self.root.after(1000, self.start_timer)  # Schedule the next update for 1000ms later

    def update_graph_and_save(self):
        if self.latest_temp is not None:  # Only update if valid temperature exists
            current_time = round(float(time.time() - self.start_time), 2)
            self.save_data_to_file(current_time, self.latest_temp)
            self.temperatures.append([current_time, self.latest_temp])

            # Update the graph with new data
            times = [t[0] for t in self.temperatures]
            obj_temps = [t[1] for t in self.temperatures]
            self.line_obj.set_data(times, obj_temps)
            self.ax.set_xlim(0, max(times) if times else 10)
            self.ax.set_ylim((min(obj_temps) - 5), (max(obj_temps) + 5))
            self.canvas.draw()

    def save_data_to_file(self, current_time, obj_temp):
        with open(self.file_path, 'a') as f:
            f.write(f"{current_time} {obj_temp}\n")

    def clear_graph(self):
        self.temperatures.clear()
        self.line_obj.set_data([], [])
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(20, 50)
        self.canvas.draw()
        self.start_time = time.time()


if __name__ == "__main__":
    root = tk.Tk()
    app = TemperatureMonitorApp(root)
    root.mainloop()
