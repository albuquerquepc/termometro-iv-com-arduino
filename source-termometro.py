import os
import sys
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

        self.interval = tk.DoubleVar(value=0.1)
        self.serial_port = None
        self.arduino_connected = False
        self.is_measuring = False
        self.temperatures = []
        self.start_time = None
        self.file_path = None

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

        self.start_button = tk.Button(control_frame, text="INICIAR", command=self.toggle_measurement)
        self.start_button.grid(row=0, column=0, columnspan=2, pady=10)

        config_frame = tk.LabelFrame(control_frame, text="Conf. de Medição")
        config_frame.grid(row=2, column=0, columnspan=2, pady=10)

        tk.Label(config_frame, text="Intervalo de Medição (s):").grid(row=0, column=0, sticky="w")
        tk.Entry(config_frame, textvariable=self.interval).grid(row=0, column=1, sticky="w")

        connect_frame = tk.LabelFrame(control_frame, text="Conexão")
        connect_frame.grid(row=3, column=0, columnspan=2, pady=10)

        tk.Label(connect_frame, text="Portas:").grid(row=0, column=0, sticky="w")
        self.port_combobox = ttk.Combobox(connect_frame, values=self.get_serial_ports())
        self.port_combobox.grid(row=0, column=1, sticky="w")

        self.connect_button = tk.Button(connect_frame, text="CONECTAR", command=self.connect_arduino)
        self.connect_button.grid(row=1, column=0, pady=5, padx=5)

        self.refresh_button = tk.Button(connect_frame, text="ATUALIZAR", command=self.refresh_serial_ports)
        self.refresh_button.grid(row=1, column=1, pady=5, padx=5)

        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=1)

        self.line_obj, = self.ax.plot([], [], 'r-', label="Temperatura Objeto")
        self.line_amb, = self.ax.plot([], [], 'b-', label="Temperatura Ambiente")
        self.ax.set_ylim(20, 50)
        self.ax.set_xlim(0, 10)
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Temperatura (°C)")
        self.ax.legend()

        self.anim = animation.FuncAnimation(self.figure, self.update_graph, interval=1000, cache_frame_data=False)

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
            self.file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if not self.file_path:
                messagebox.showwarning("Aviso", "Você precisa selecionar um local para salvar os dados.")
                return
            self.clear_graph()
            self.is_measuring = True
            self.start_button.config(text="STOP")
            threading.Thread(target=self.measure_temperatures_loop, daemon=True).start()

    def measure_temperatures_loop(self):
        while self.is_measuring:
            sensor_values = self.measure_temperature_from_serial()
            if sensor_values is not None:
                obj_temp, amb_temp = sensor_values
                if self.start_time is None:
                    self.start_time = time.time()
                current_time = time.time() - self.start_time
                print(f"[{current_time:.2f}, Obj: {obj_temp:.2f}°C, Amb: {amb_temp:.2f}°C]")
                self.save_data_to_file(current_time, obj_temp, amb_temp)
                self.temperatures.append([current_time, obj_temp, amb_temp])
            time.sleep(self.interval.get())

    def measure_temperature_from_serial(self):
        try:
            response = self.serial_port.readline().decode('utf-8').strip()
            print(f"Received: {response}")  # Print the raw response for debugging
            values = response.split()
            if len(values) == 2:  # Ensure we have both temperatures
                obj_temp = float(values[0])  # Expecting first value to be object temperature
                amb_temp = float(values[1])   # Expecting second value to be ambient temperature
                return obj_temp, amb_temp
            else:
                print("Invalid data format, expected two temperatures.")
                return None
        except ValueError as e:
            print(f"Erro na leitura dos sensores: {e}")
            return None
        except UnicodeDecodeError as e:
            print(f"Erro de decodificação: {e}")
            return None

    def update_graph(self, frame):
        if not self.is_measuring:
            return

        if self.temperatures:
            times = [t[0] for t in self.temperatures]
            obj_temps = [t[1] for t in self.temperatures]
            amb_temps = [t[2] for t in self.temperatures]

            self.line_obj.set_data(times, obj_temps)
            self.line_amb.set_data(times, amb_temps)

            if times:
                self.ax.set_xlim(0, max(times))
            else:
                self.ax.set_xlim(0, 10)

            min_temp = min(min(obj_temps), min(amb_temps))
            max_temp = max(max(obj_temps), max(amb_temps))

            self.ax.set_ylim(min_temp - 5, max_temp + 5)

            self.canvas.draw()
        else:
            print("Nenhum dado válido para atualizar o gráfico.")

    def save_data_to_file(self, time, obj_temp, amb_temp):
        with open(self.file_path, 'a') as f:
            f.write(f"{time:.2f}\t{obj_temp:.2f}\t{amb_temp:.2f}\n")

    def clear_graph(self):
        self.temperatures.clear()
        self.line_obj.set_data([], [])
        self.line_amb.set_data([], [])
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(20, 50)
        self.canvas.draw()
        self.start_time = None

if __name__ == "__main__":
    root = tk.Tk()
    app = TemperatureMonitorApp(root)
    root.mainloop()
