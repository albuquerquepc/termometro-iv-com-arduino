import os #funcionalidade de sistema operacional
import sys #funcionalidade de sistema
import tkinter as tk #interface gráfica
from tkinter import ttk #widgets
import serial #comunicação serial
import serial.tools.list_ports #listagem de portas seriais
import time #funções de tempo   
import threading #multi-threading
import matplotlib.pyplot as plt #plotagem de gráficos
import matplotlib.animation as animation #animação de gráficos
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

"""
Este script é o código fonté um monitor de temperatura que se comunica com um Arduino serialmente para obter leituras de temperatura de dois sensores infravermelhos.
Os dados são exibidos em um gráfico em tempo real e salvos em um arquivo de texto.
Notavelmente, o script é executado em uma interface gráfica Tkinter e usa a biblioteca Matplotlib para plotar o gráfico.
Este script foi desenvolvido principalmente por Abner Carlos Melo, com algumas adaptações e documentação feitas por Paulo Albquerque e Pedro Cruz, na Universidade Federal do Rio Grande do Norte
"""

class TemperatureMonitorApp:
    def __init__(self, root):   
        self.root = root
        self.root.title("Monitor de Temperatura")

        # Adicionando imagens ao cabeçalho
        self.add_header_images()

        # Variáveis de controle
        self.interval = tk.DoubleVar(value=0.5)
        self.serial_port = None
        self.arduino_connected = False
        self.is_measuring = False
        self.temperatures = []
        self.start_time = None  # Inicia o tempo
        self.file_path = None  # Caminho para salvar o arquivo

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

    def resource_path(self, relative_path):
        """ Retorna o caminho absoluto, considerando se está executando como script ou como executável """
        try:
            # Quando empacotado com PyInstaller, __MEIPASS é o diretório temporário onde os arquivos estão
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def add_header_images(self):
        # Carregar e exibir as imagens usando o caminho correto
        #logo1_path = self.resource_path("logo_simbolo.png")
        #logo2_path = self.resource_path("logo_nome.png")

        #logo1 = Image.open(logo1_path)
        #logo2 = Image.open(logo2_path)

        #logo1 = logo1.resize((232, 100))  # Ajuste o tamanho conforme necessário
        #logo2 = logo2.resize((670, 100))

        #self.logo1_photo = ImageTk.PhotoImage(logo1)
        #self.logo2_photo = ImageTk.PhotoImage(logo2)

        header_frame = tk.Frame(self.root)
        header_frame.grid(row=0, column=0, columnspan=2)

        #tk.Label(header_frame, image=self.logo1_photo).pack(side="left")
        #tk.Label(header_frame, image=self.logo2_photo).pack(side="left")

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

        self.line2, = self.ax.plot([], [], 'g-', label="Sensor 2")
        self.ax.set_ylim(30, 75)  # Limites iniciais
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
            self.file_path = tk.tk.filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
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
            sensor_value = self.measure_temperature_sensor2()

            if sensor_value is not None:
                # Define o tempo inicial na primeira leitura
                if self.start_time is None:
                    self.start_time = time.time()
                current_time = time.time() - self.start_time  # Calcula o tempo transcorrido
                print(f"[{current_time:.2f}, {sensor_value:.2f}]")

                # Salva os dados continuamente no arquivo
                self.save_data_to_file(current_time, sensor_value)

                # Armazena os dados localmente para o gráfico
                self.temperatures.append([current_time, sensor_value])

            time.sleep(self.interval.get())

    def measure_temperature_sensor2(self):
        try:
            # Envia comando para o sensor 2
            self.serial_port.write(b'T2\n')
            # Aguarda o retorno do sensor 2
            response = self.serial_port.readline().decode('utf-8').strip()
            try:
                return float(response)
            except ValueError:
                return None
        except Exception as e:
            print(f"Erro na leitura do sensor 2: {e}")
            return None

    def update_graph(self, frame):
        """Atualiza o gráfico com os dados mais recentes."""
        if not self.is_measuring:  # Verifica se a medição está parada
            return

        if self.temperatures:
            times = [t[0] for t in self.temperatures]
            temps2 = [t[1] for t in self.temperatures]

            if times and temps2:
                self.line2.set_data(times, temps2)
                if max(times):
                    self.ax.set_xlim(0, max(times))  # Atualiza o limite do eixo x
                else:
                    self.ax.set_xlim(0, 1)  # Atualiza o limite do eixo x

                # Ajuste automático do eixo Y
                min_temp = min(temps2)
                max_temp = max(temps2)

                self.ax.set_ylim(min_temp - 5, max_temp + 5)  # Adiciona uma margem de 5°C

                self.canvas.draw()
            else:
                print("Nenhum dado válido para atualizar o gráfico.")

    def save_data_manually(self):
        """Salva os dados do gráfico manualmente em um arquivo .txt."""
        file_path = tk.filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                for t in self.temperatures:
                    f.write(f"{t[0]}\t{t[1]}\n")

    def save_data_to_file(self, time, temp):
        """Salva os dados continuamente no arquivo selecionado."""
        with open(self.file_path, 'a') as f:
            f.write(f"{time:.2f}\t{temp:.2f}\n")

    def clear_graph(self):
        """Limpa os dados do gráfico e reinicia o tempo."""
        self.temperatures.clear()
        self.line2.set_data([], [])
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(30, 75)  # Limites iniciais
        self.canvas.draw()
        self.start_time = None  # Reseta o tempo inicial

# Execução do programa
if __name__ == "__main__":
    root = tk.Tk()
    app = TemperatureMonitorApp(root)
    root.mainloop()
