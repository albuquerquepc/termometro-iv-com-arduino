import os
import sys
import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

class TemperatureMonitorApp:
    def __init__(self, root):   
        self.root = root
        self.root.title("Monitor de Temperatura")

        # Variáveis de controle
        self.interval = tk.DoubleVar(value=0.5)
        self.serial_port = None
        self.arduino_connected = False
        self.is_measuring = False
        self.temperatures = []  # Stores object and ambient temperatures as tuples (time, object_temp, ambient_temp)
        self.start_time = None  # Start time for measurements
        self.file_path = None  # File path to save the data

        # Criando layout
        self.create_widgets()

        # Lidando com o fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Função chamada quando a janela é fechada"""
        if self.is_measuring:
            self.is_measuring = False  # Parar medições
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()  # Fechar conexão serial
        self.root.quit()  # Fechar janela Tkinter
        self.root.destroy()  # Garantir que todos os recursos sejam liberados
        print("Programa encerrado.")

    def create_widgets(self):
        # Coluna esquerda (Configurações e Botões)
        control_frame = tk.Frame(self.root)
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Botão Iniciar/Stop
        self.start_button = tk.Button(control_frame, text="INICIAR", command=self.toggle_measurement)
        self.start_button.grid(row=0, column=0, columnspan=2, pady=10)

        # Seção de configuração de medição
        config_frame = tk.LabelFrame(control_frame, text="Conf. de Medição")
        config_frame.grid(row=2, column=0, columnspan=2, pady=10)

        tk.Label(config_frame, text="Intervalo de Medição (s):").grid(row=0, column=0, sticky="w")
        tk.Entry(config_frame, textvariable=self.interval).grid(row=0, column=1, sticky="w")

        # Seção de conexão
        connect_frame = tk.LabelFrame(control_frame, text="Conexão")
        connect_frame.grid(row=3, column=0, columnspan=2, pady=10)

        tk.Label(connect_frame, text="Portas:").grid(row=0, column=0, sticky="w")
        self.port_combobox = ttk.Combobox(connect_frame, values=self.get_serial_ports())
        self.port_combobox.grid(row=0, column=1, sticky="w")

        self.connect_button = tk.Button(connect_frame, text="CONECTAR", command=self.connect_arduino)
        self.connect_button.grid(row=1, column=0, pady=5, padx=5)

        self.refresh_button = tk.Button(connect_frame, text="ATUALIZAR", command=self.refresh_serial_ports)
        self.refresh_button.grid(row=1, column=1, pady=5, padx=5)

        # Coluna direita (Gráfico)
        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(row=1, column=1)

        self.line_obj, = self.ax.plot([], [], 'r-', label="Temperatura Objeto")
        self.line_amb, = self.ax.plot([], [], 'b-', label="Temperatura Ambiente")
        self.ax.set_ylim(20, 50)  # Limites iniciais
        self.ax.set_xlim(0, 10)
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Temperatura (°C)")
        self.ax.legend()

        self.anim = animation.FuncAnimation(self.figure, self.update_graph, interval=1000, save_count=100)

    def refresh_serial_ports(self):
        """Atualizando as opções de Porta serial"""
        self.port_combobox['values'] = self.get_serial_ports()
        self.port_combobox.set("")  # Limpa a seleção atual, se necessário

    def get_serial_ports(self):
        """Retorna uma lista de portas seriais disponíveis."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_arduino(self):
        """Conecta ou desconecta do Arduino."""
        if self.arduino_connected:
            self.disconnect_arduino()
        else:
            selected_port = self.port_combobox.get()
            if selected_port:
                try:
                    self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
                    self.arduino_connected = True
                    self.connect_button.config(text="DESCONECTAR")
                except serial.SerialException:
                    tk.messagebox.showerror("Erro", "Não foi possível conectar ao Arduino.")
            else:
                tk.messagebox.showerror("Erro", "Selecione uma porta serial.")

    def disconnect_arduino(self):
        """Desconecta do Arduino."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.arduino_connected = False
        self.connect_button.config(text="CONECTAR")

    def toggle_measurement(self):
        """Inicia ou para a medição."""
        if not self.arduino_connected:
            tk.messagebox.showerror("Erro", "Conecte ao Arduino primeiro.")
            return

        if self.is_measuring:
            self.is_measuring = False
            self.start_button.config(text="INICIAR")
        else:
            # Pedir o caminho para salvar os dados antes de iniciar a medição
            self.file_path = tk.filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if not self.file_path:
                tk.messagebox.showwarning("Aviso", "Você precisa selecionar um local para salvar os dados.")
                return
            # Limpa os dados das medidas anteriores do gráfico
            self.clear_graph()

            self.is_measuring = True
            self.start_button.config(text="STOP")
            self.start_time = None  # Reseta o tempo inicial
            threading.Thread(target=self.measure_temperatures_loop, daemon=True).start()

    def measure_temperatures_loop(self):
        """Loop contínuo de leitura de temperaturas em uma thread separada."""
        while self.is_measuring:
            sensor_values = self.measure_temperature_from_serial()

            if sensor_values is not None:
                obj_temp, amb_temp = sensor_values
                # Define o tempo inicial na primeira leitura
                if self.start_time is None:
                    self.start_time = time.time()
                current_time = time.time() - self.start_time  # Calcula o tempo transcorrido
                print(f"[{current_time:.2f}, Obj: {obj_temp:.2f}°C, Amb: {amb_temp:.2f}°C]")

                # Salva os dados continuamente no arquivo
                self.save_data_to_file(current_time, obj_temp, amb_temp)

                # Armazena os dados localmente para o gráfico
                self.temperatures.append([current_time, obj_temp, amb_temp])

            time.sleep(self.interval.get())

    def measure_temperature_from_serial(self):
        try:
            # Lê a resposta do Arduino, que envia ambas as temperaturas no formato: "Temp Objeto C Temp Ambiente"
            response = self.serial_port.readline().decode('utf-8').strip()
            try:
                values = response.split()  # Split the two temperature values
                obj_temp = float(values[0])  # First value is object temperature
                amb_temp = float(values[1])  # Second value is ambient temperature
                return obj_temp, amb_temp
            except (ValueError, IndexError):
                return None
        except Exception as e:
            print(f"Erro na leitura dos sensores: {e}")
            return None

    def update_graph(self, frame):
        """Atualiza o gráfico com os dados mais recentes."""
        if not self.is_measuring:  # Verifica se a medição está parada
            return

        if self.temperatures:
            times = [t[0] for t in self.temperatures]
            obj_temps = [t[1] for t in self.temperatures]
            amb_temps = [t[2] for t in self.temperatures]

            if times and obj_temps and amb_temps:
                self.line_obj.set_data(times, obj_temps)
                self.line_amb.set_data(times, amb_temps)

                if max(times):
                    self.ax.set_xlim(0, max(times))  # Atualiza o limite do eixo x
                else:
                    self.ax.set_xlim(0, 1)  # Atualiza o limite do eixo x

                # Ajuste automático do eixo Y
                min_temp = min(min(obj_temps), min(amb_temps))
                max_temp = max(max(obj_temps), max(amb_temps))

                self.ax.set_ylim(min_temp - 5, max_temp + 5)  # Adiciona uma margem de 5°C

                self.canvas.draw()
            else:
                print("Nenhum dado válido para atualizar o gráfico.")

    def save_data_to_file(self, time, obj_temp, amb_temp):
        """Salva os dados continuamente no arquivo selecionado."""
        with open(self.file_path, 'a') as f:
            f.write(f"{time:.2f}\t{obj_temp:.2f}\t{amb_temp:.2f}\n")

    def clear_graph(self):
        """Limpa os dados do gráfico e reinicia o tempo."""
        self.temperatures.clear()
        self.line_obj.set_data([], [])
        self.line_amb.set_data([], [])
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(20, 50)  # Limites iniciais
        self.canvas.draw()
        self.start_time = None  # Reseta o tempo inicial

# Execução do programa
if __name__ == "__main__":
    root = tk.Tk()
    app = TemperatureMonitorApp(root)
    root.mainloop()
