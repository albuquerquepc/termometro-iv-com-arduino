import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial
import serial.tools.list_ports
import threading
import time
from time import perf_counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import csv

class TempMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Temperatura com Arduino")
        
        # Variáveis de estado
        self.arduino = None
        self.port = tk.StringVar()
        self.update_rate = tk.DoubleVar(value=1.0)
        self.connected = False
        self.collecting_data = False
        self.start_time = None
        self.data = []
        self.filepath = tk.StringVar(value="Nenhum local escolhido")
        self.latest_temp = tk.StringVar(value="---")

        # Elementos de interface
        self.setup_ui()

    def setup_ui(self):
        # Frame para a seção de parâmetros
        param_frame = ttk.Frame(self.root)
        param_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
        
        ttk.Label(param_frame, text="Parâmetros").pack(anchor="w")

        # Seletor de porta serial
        ttk.Label(param_frame, text="Porta Serial:").pack(anchor="w", pady=5)
        self.port_combobox = ttk.Combobox(param_frame, textvariable=self.port, state="readonly", width=15)
        self.port_combobox.pack(anchor="w", pady=5)
        self.update_ports()
        
        self.update_button = ttk.Button(param_frame, text="Atualizar", command=self.update_ports)
        self.update_button.pack(anchor="w", pady=5)

        self.connect_button = ttk.Button(param_frame, text="Conectar", command=self.toggle_connection)
        self.connect_button.pack(anchor="w", pady=5)

        # Taxa de atualização
        ttk.Label(param_frame, text="Taxa de atualização (s):").pack(anchor="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.update_rate, width=10).pack(anchor="w", pady=5)

        # Exibição da última temperatura
        ttk.Label(param_frame, text="Última Temperatura (°C):").pack(anchor="w", pady=5)
        self.temp_label = ttk.Label(param_frame, textvariable=self.latest_temp)
        self.temp_label.pack(anchor="w", pady=5)

        # Escolher local para salvar e exibição do caminho
        self.file_button = ttk.Button(param_frame, text="Escolher Local para Salvar", command=self.choose_file_location)
        self.file_button.pack(anchor="w", pady=5)

        ttk.Label(param_frame, text="Local do Arquivo:").pack(anchor="w", pady=5)
        self.filepath_label = ttk.Label(param_frame, textvariable=self.filepath, wraplength=150)
        self.filepath_label.pack(anchor="w", pady=5)

        # Botão para iniciar e parar a coleta de dados
        self.start_button = ttk.Button(param_frame, text="Começar", command=self.start_acquisition, state="disabled")
        self.start_button.pack(anchor="w", pady=10)

        # Configuração do gráfico
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], lw=2)
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Temperatura (°C)")
        self.ax.set_title("Temperatura em tempo real")

        # Canvas para exibir o gráfico na interface Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Animação do gráfico
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=100)

    def update_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combobox['values'] = [port.device for port in ports]
    
    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        port = self.port.get()
        if port:
            try:
                self.arduino = serial.Serial(port, 9600, timeout=1)
                time.sleep(2)  # Pequeno atraso para estabilizar a conexão
                self.connected = True
                self.connect_button.config(text="Desconectar")
                self.file_button.config(state="normal")
                self.start_button.config(state="normal")
                messagebox.showinfo("Conexão", "Conectado ao Arduino com sucesso!")
                
                # Iniciar thread para atualizar a última temperatura
                self.temp_thread = threading.Thread(target=self.update_latest_temp)
                self.temp_thread.start()

            except serial.SerialException as e:
                messagebox.showerror("Erro de Conexão", f"Não foi possível conectar: {e}")
        else:
            messagebox.showwarning("Aviso", "Selecione uma porta serial.")
    
    def disconnect(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self.connected = False
        self.connect_button.config(text="Conectar")
        self.file_button.config(state="disabled")
        self.start_button.config(state="disabled")
        self.collecting_data = False

    def choose_file_location(self):
        self.filepath.set(filedialog.asksaveasfilename(defaultextension=".txt",
                                                       filetypes=[("Text files", "*.txt")]))
        if self.filepath.get():
            self.start_button.config(state="normal")
        else:
            self.filepath.set("Nenhum local escolhido")

    def start_acquisition(self):
        if not self.collecting_data:
            if not self.filepath.get():
                messagebox.showwarning("Aviso", "Escolha o local para salvar os dados antes de iniciar.")
                return
            
            self.collecting_data = True
            self.start_button.config(text="Parar")
            self.start_time = perf_counter()
            self.data = []
            
            # Inicia thread para aquisição de dados
            self.thread = threading.Thread(target=self.acquire_data)
            self.thread.start()
        else:
            self.collecting_data = False
            self.start_button.config(text="Começar")
            self.save_data_to_file()
            # Esvazia o caminho do arquivo para uma nova medida
            self.filepath.set("Nenhum local escolhido")

    def acquire_data(self):
        while self.collecting_data and self.arduino and self.arduino.is_open:
            try:
                line = self.arduino.readline().decode().strip()
                if line:
                    temp = float(line)
                    elapsed_time = perf_counter() - self.start_time
                    self.data.append((elapsed_time, temp))
                    print(f"{elapsed_time:.1f}s: {temp:.2f}°C")
                time.sleep(self.update_rate.get())
            except (ValueError, serial.SerialException):
                continue

    def update_latest_temp(self):
        while self.connected and self.arduino and self.arduino.is_open:
            try:
                line = self.arduino.readline().decode().strip()
                if line:
                    temp = float(line)
                    self.latest_temp.set(f"{temp:.2f} °C")
            except (ValueError, serial.SerialException):
                continue

    def update_plot(self, frame):
        if self.data:
            times, temps = zip(*self.data)
            self.line.set_data(times, temps)
            self.ax.relim()
            self.ax.autoscale_view()
        self.canvas.draw()

    def save_data_to_file(self):
        if self.data and self.filepath.get():
            with open(self.filepath.get(), "w") as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(["Tempo (s)", "Temperatura (°C)"])
                for time, temp in self.data:
                    writer.writerow([f"{time:.1f}", f"{temp:.2f}"])
            messagebox.showinfo("Dados Salvos", f"Dados salvos em '{self.filepath.get()}'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TempMonitorApp(root)
    root.mainloop()
