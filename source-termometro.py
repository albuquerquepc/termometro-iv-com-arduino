from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                               QLabel, QPushButton, QLineEdit, QComboBox, QFileDialog, QMessageBox)  # type: ignore
from PySide6.QtCharts import QChart, QChartView, QLineSeries  # type: ignore
from PySide6.QtCore import QTimer, QPointF  # type: ignore
from PySide6.QtGui import QDoubleValidator  # type: ignore
import serial
import serial.tools.list_ports
import threading
import csv
from time import perf_counter


class MonitorTemperaturaApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurações iniciais da janela principal
        self.setWindowTitle("Monitor de Temperatura com Qt")
        self.resize(1024, 768)

        # Estado da aplicação
        self.conexao_arduino = None
        self.porta_serial_selecionada = ""
        self.taxa_atualizacao = 1.0
        self.conectado = False
        self.coletando_dados = False
        self.tempo_inicio = None
        self.dados = []
        self.serie_dados = QLineSeries()

        # Configuração da interface
        self.configurar_interface()

        # Timer para atualizar o gráfico
        self.timer_atualizacao = QTimer()
        self.timer_atualizacao.timeout.connect(self.atualizar_grafico)

    def configurar_interface(self):
        # Cria a interface gráfica com Qt.#
        # Widget principal
        widget_principal = QWidget()
        self.setCentralWidget(widget_principal)

        # Layout principal
        layout_principal = QHBoxLayout(widget_principal)

        # Seção de controles (lado esquerdo)
        layout_controles = QVBoxLayout()
        layout_principal.addLayout(layout_controles)

        # Rótulo e combobox para seleção de porta serial
        layout_controles.addWidget(QLabel("Porta Serial:"))
        self.caixa_portas = QComboBox()
        self.atualizar_portas()
        layout_controles.addWidget(self.caixa_portas)

        # Botão para atualizar portas disponíveis
        self.botao_atualizar_portas = QPushButton("Atualizar Portas")
        self.botao_atualizar_portas.clicked.connect(self.atualizar_portas)
        layout_controles.addWidget(self.botao_atualizar_portas)

        # Botão de conexão/desconexão
        self.botao_conectar = QPushButton("Conectar")
        self.botao_conectar.clicked.connect(self.alternar_conexao)
        layout_controles.addWidget(self.botao_conectar)

        # Campo para taxa de atualização
        layout_controles.addWidget(QLabel("Taxa de Atualização (s):"))
        self.campo_taxa_atualizacao = QLineEdit("1.0")
        self.campo_taxa_atualizacao.setValidator(
            QDoubleValidator(0.1, 10.0, 1))  # Aceita apenas floats entre 0.1 e 10.0
        self.campo_taxa_atualizacao.textChanged.connect(self.atualizar_portas)
        layout_controles.addWidget(self.campo_taxa_atualizacao)

        # Rótulo para exibir a última temperatura
        layout_controles.addWidget(QLabel("Última Temperatura (°C):"))
        self.rotulo_temperatura = QLabel("---")
        layout_controles.addWidget(self.rotulo_temperatura)

        # Botão para escolher o local de salvamento do arquivo
        self.botao_escolher_local = QPushButton("Escolher Local para Salvar")
        self.botao_escolher_local.clicked.connect(self.escolher_local_arquivo)
        layout_controles.addWidget(self.botao_escolher_local)

        # Botão para iniciar/parar coleta de dados
        self.botao_iniciar_coleta = QPushButton("Iniciar Coleta")
        self.botao_iniciar_coleta.setEnabled(False)
        self.botao_iniciar_coleta.clicked.connect(self.alternar_coleta)
        layout_controles.addWidget(self.botao_iniciar_coleta)

        # Seção do gráfico (lado direito)
        self.chart = QChart()
        self.chart.addSeries(self.serie_dados)
        self.chart.setTitle("Temperatura")
        self.chart.createDefaultAxes()

        self.chart_view = QChartView(self.chart)
        layout_principal.addWidget(self.chart_view)

    def atualizar_portas(self):
        # Atualiza a lista de portas seriais disponíveis.#
        portas = serial.tools.list_ports.comports()
        self.caixa_portas.clear()
        self.caixa_portas.addItems([porta.device for porta in portas])

    def alternar_conexao(self):
        # Conecta ou desconecta do Arduino.#
        if self.conectado:
            self.desconectar()
        else:
            self.conectar()

    def conectar(self):
        # Tenta estabelecer conexão com a porta serial selecionada.#
        porta = self.caixa_portas.currentText()
        if porta:
            try:
                self.conexao_arduino = serial.Serial(porta, 9600, timeout=1)
                self.conectado = True
                self.botao_conectar.setText("Desconectar")
                self.botao_iniciar_coleta.setEnabled(True)
                QMessageBox.information(
                    self, "Conexão", "Conectado com sucesso!")
            except serial.SerialException as e:
                QMessageBox.critical(self, "Erro de Conexão", str(e))
        else:
            QMessageBox.warning(self, "Aviso", "Selecione uma porta serial!")

    def desconectar(self):
        # Desconecta do Arduino.#
        if self.conexao_arduino and self.conexao_arduino.is_open:
            self.conexao_arduino.close()
        self.conectado = False
        self.botao_conectar.setText("Conectar")
        self.botao_iniciar_coleta.setEnabled(False)

    def escolher_local_arquivo(self):
        # Abre um diálogo para escolher onde salvar os dados.#
        caminho = QFileDialog.getSaveFileName(
            self, "Salvar Dados", "", "TXT Files (*.txt)")
        self.caminho_arquivo = caminho[0]

    def alternar_coleta(self):
        # Inicia ou para a coleta de dados.#
        if not self.coletando_dados:
            self.coletando_dados = True
            self.botao_iniciar_coleta.setText("Parar Coleta")
            self.dados.clear()
            self.tempo_inicio = perf_counter()
            self.timer_atualizacao.start(float(self.taxa_atualizacao))
            threading.Thread(target=self.coletar_dados, daemon=True).start()
        else:
            self.coletando_dados = False
            self.botao_iniciar_coleta.setText("Iniciar Coleta")
            self.timer_atualizacao.stop()
            self.salvar_dados()

    def coletar_dados(self):
        # Coleta dados da porta serial.#
        while self.coletando_dados:
            try:
                linha = self.conexao_arduino.readline().decode('utf-8').strip()
                if linha:
                    tempo = perf_counter() - self.tempo_inicio
                    self.dados.append((tempo, float(linha)))
                    self.rotulo_temperatura.setText(f"{linha} °C")
            except Exception as e:
                QMessageBox.critical(self, "Erro de Coleta", str(e))
                break

    def atualizar_grafico(self):
        # Atualiza o gráfico em tempo real.#
        self.serie_dados.clear()
        for tempo, temperatura in self.dados:
            self.serie_dados.append(QPointF(tempo, temperatura))

    def salvar_dados(self):
        # salva os dados coletados em um arquivo CSV
        if hasattr(self, "caminho_arquivo") and self.caminho_arquivo:
            try:
                with open(self.caminho_arquivo, 'w', newline='') as arquivo:
                    escritor = csv.writer(arquivo)
                    escritor.writerows(self.dados)
                QMessageBox.information(
                    self, "Sucesso", "Dados salvos com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", str(e))


if __name__ == "__main__":
    app = QApplication([])
    janela = MonitorTemperaturaApp()
    janela.show()
    app.exec()
