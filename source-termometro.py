import sys
import serial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QComboBox, QFileDialog, QLabel, QFrame)
from PySide6.QtCore import QThread, Signal, QStandardPaths
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt
from serial.tools import list_ports

"""
Classe para comunicação serial com a placa Arduino UNO. Aqui acontece a leitura dos dados crus e o processamento para unidades que façam sentido para leitura. Alterar o código dessa parte tem ALTO risco de quebrar o script inteiro
"""

class SerialWorker(QThread):
    dados_recebidos_crus = Signal(float, float)  # Sinal: tempo, temperatura
    erro_conexao = Signal(str)              # Sinal para erros

    def __init__(self):
        super().__init__()
        self.porta = None
        self.executando = False
        self.registrando = False
        self.dados_registro = []
        self.caminho_arquivo = None

    def configurar_porta(self, porta):
        """Define qual porta serial será utilizada"""
        self.porta = porta

    def configurar_arquivo(self, caminho):
        """Configura o caminho do arquivo para registro"""
        self.caminho_arquivo = caminho

    def run(self):
        """Método principal de execução da thread"""
        if not self.porta:
            self.erro_conexao.emit("Nenhuma porta selecionada!")
            return

        try:
            self.serial = serial.Serial(self.porta, 9600, timeout=0.1)
            self.executando = True
        except Exception as e:
            self.erro_conexao.emit(str(e))
            return

        while self.executando:
            try:
                linha = self.serial.readline().decode().strip()
                if linha:
                    print(f"Dado recedido: {linha}")
                    partes_da_linha = linha.split(',')
                    if len(partes_da_linha) != 2:
                        self.erro_conexao.emit("Dado inválido!")
                    print(f"Processando linha: {linha}")

                    tempo_str, temp_str = partes_da_linha
                    tempo = int(tempo_str)
                    temperatura = float(temp_str)

                    # Calcula tempo relativo em segundos
                    # Convertendo µs para segundos
                    tempo_decorrido = round((tempo / 1e6), 2)

                    # Emite dados para a interface
                    self.dados_recebidos_crus.emit(tempo_decorrido, temperatura)

                    # Armazena dados em memória se estiver registrando
                    if self.registrando:
                        self.dados_registro.append(
                            (tempo_decorrido, temperatura))

            except Exception as e:
                print(f"Erro na leitura: {str(e)}")
                self.erro_conexao.emit(f"Erro na leitura: {str(e)}")

        self.serial.close()

    def iniciar_registro(self):
        """Inicia o registro dos dados em memória"""
        self.dados_registro = []
        self.registrando = True

    def parar_registro(self):
        """Para o registro e salva em arquivo"""
        self.registrando = False
        if self.caminho_arquivo and self.dados_registro:
            try:
                with open(self.caminho_arquivo, 'w') as f:
                    f.write("Tempo(s)\tTemperatura(°C)\n")
                    tempo_primeiro = self.dados_registro[0][0]
                    for tempo_decorrido, temp in self.dados_registro:
                        f.write(
                            f"{(tempo_decorrido-tempo_primeiro):.2f}\t{temp:.2f}\n")
            except Exception as e:
                self.erro_conexao.emit(f"Erro ao salvar arquivo: {str(e)}")

    def parar(self):
        """Encerra a execução da thread"""
        self.executando = False

"""
Classe principal da interface gráfica. Aqui são construídos a parte de controle e visualização dos dados, desde botões pressionáveis até o gráfico em tempo real.Alterar essa parte tem baixo risco de quebrar o script inteiro, mas pode afetar a usabilidade do sistema, como a visualização em tempo real do gráfico ou a aparência geral do programa. Alguns botões como o de conectar ou de salvar arquivo são essenciais para o funcionamento do sistema, cuidado ao alterar esses botões
"""


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tempo_primordial = None
        self.configurar_interface()
        self.trabalhador_serial = SerialWorker()
        self.configurar_conexoes()

    def configurar_interface(self):
        """Configuração completa da interface"""
        self.setWindowTitle("Sistema de Monitoramento Térmico")
        self.resize(1200, 800)

        # Painel esquerdo com controles
        painel_controles = QFrame()
        painel_controles.setFixedWidth(320)
        layout_controles = QVBoxLayout(painel_controles)
        layout_controles.setContentsMargins(20, 20, 20, 20)
        layout_controles.setSpacing(15)

        # Componentes de controle
        self.combo_portas = QComboBox()
        self.btn_atualizar = QPushButton("Atualizar Portas")
        self.btn_conectar = QPushButton("Conectar")
        self.btn_desconectar = QPushButton("Desconectar")

        # Controles de registro
        self.btn_selecionar_arquivo = QPushButton("Selecionar Arquivo")
        self.label_caminho = QLabel("Arquivo não selecionado")
        self.label_caminho.setWordWrap(True)
        self.btn_registro = QPushButton("Iniciar Registro")
        self.btn_registro.setEnabled(False)

        self.status_label = QLabel("Status: Desconectado")

        # Display de temperatura
        self.label_temperatura = QLabel("-- °C")
        self.label_temperatura.setAlignment(Qt.AlignCenter)
        self.label_temperatura.setStyleSheet("""
            QLabel {
                font: bold 56px;
            }
        """)

        # Adicionar componentes ao layout
        layout_controles.addWidget(QLabel("Porta COM:"))
        layout_controles.addWidget(self.combo_portas)
        layout_controles.addWidget(self.btn_atualizar)
        layout_controles.addWidget(self.btn_conectar)
        layout_controles.addWidget(self.btn_desconectar)
        layout_controles.addWidget(QLabel(" "))
        layout_controles.addWidget(self.btn_selecionar_arquivo)
        layout_controles.addWidget(self.label_caminho)
        layout_controles.addWidget(self.btn_registro)
        layout_controles.addWidget(self.status_label)
        layout_controles.addStretch()
        layout_controles.addWidget(self.label_temperatura)
        layout_controles.addStretch()

        # Configuração do gráfico
        self.grafico = QChart()
        self.serie = QLineSeries()
        self.grafico.addSeries(self.serie)
        self.configurar_eixos()

        visualizacao_grafico = QChartView(self.grafico)
        visualizacao_grafico.setRenderHint(QPainter.Antialiasing)

        # Layout principal
        layout_principal = QHBoxLayout()
        layout_principal.addWidget(painel_controles)
        layout_principal.addWidget(visualizacao_grafico)

        widget_central = QWidget()
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)

        self.atualizar_portas()
        self.atualizar_estado_botoes(False)

    def configurar_estilo_grafico(self):
        caneta = self.serie.pen()
        caneta.setStyle(Qt.DashLine)
        caneta.setWidth(2)
        self.serie.setPen(caneta)
        self.serie.setColor(Qt.red)
        self.serie.setPointsVisible(True)

    def configurar_conexoes(self):
        """Conecta sinais e slots entre componentes"""
        self.btn_atualizar.clicked.connect(self.atualizar_portas)
        self.btn_conectar.clicked.connect(self.iniciar_conexao)
        self.btn_desconectar.clicked.connect(self.parar_conexao)
        self.btn_selecionar_arquivo.clicked.connect(self.selecionar_arquivo)
        self.btn_registro.clicked.connect(self.gerenciar_registro)
        self.trabalhador_serial.dados_recebidos_crus.connect(self.atualizar_display)
        self.trabalhador_serial.dados_recebidos_crus.connect(self.atualizar_grafico)
        self.trabalhador_serial.erro_conexao.connect(self.mostrar_erro)

    def configurar_eixos(self):
        """Configura os eixos do gráfico"""

        self.grafico.legend().hide()

        self.eixo_x = QValueAxis()
        self.eixo_x.setTitleText("Tempo Decorrido (s)")
        self.eixo_x.setLabelFormat("%.1f")

        self.eixo_y = QValueAxis()
        self.eixo_y.setTitleText("Temperatura (°C)")
        self.eixo_y.setLabelFormat("%.1f")

        self.grafico.addAxis(self.eixo_x, Qt.AlignBottom)
        self.grafico.addAxis(self.eixo_y, Qt.AlignLeft)
        self.serie.attachAxis(self.eixo_x)
        self.serie.attachAxis(self.eixo_y)

        self.configurar_estilo_grafico()

    def atualizar_portas(self):
        """Atualiza lista de portas seriais disponíveis"""
        self.combo_portas.clear()
        portas = [p.device for p in list_ports.comports()]
        self.combo_portas.addItems(portas)

    def selecionar_arquivo(self):
        """Abre diálogo para seleção do arquivo de saída"""
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar Dados",
            QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
            "Arquivos Texto (*.txt)")

        if caminho:
            self.trabalhador_serial.configurar_arquivo(caminho)
            self.label_caminho.setText(caminho)
            self.btn_registro.setEnabled(True)

    def gerenciar_registro(self):
        """Controla início/parada do registro"""
        if not self.trabalhador_serial.registrando:
            self.serie.clear()
            self.tempo_primordial = None
            self.trabalhador_serial.iniciar_registro()
            self.btn_registro.setText("Parar Registro")
            self.btn_selecionar_arquivo.setEnabled(False)
        else:
            self.trabalhador_serial.parar_registro()
            self.btn_registro.setText("Iniciar Registro")
            self.btn_selecionar_arquivo.setEnabled(True)
            self.label_caminho.setText(
                "Arquivo salvo: " + self.label_caminho.tex())

    def atualizar_display(self, tempo_decorrido, temperatura):
        """Atualiza o display de temperatura"""
        self.label_temperatura.setText(f"{temperatura:.2f} °C")

    def iniciar_conexao(self):
        """Inicia conexão com a porta selecionada"""
        porta = self.combo_portas.currentText()
        if not porta:
            self.mostrar_erro("Selecione uma porta COM!")
            return

        self.trabalhador_serial = SerialWorker()

        self.trabalhador_serial.dados_recebidos_crus.connect(self.atualizar_display)
        self.trabalhador_serial.dados_recebidos_crus.connect(self.atualizar_grafico)
        self.trabalhador_serial.erro_conexao.connect(self.mostrar_erro)

        self.trabalhador_serial.configurar_porta(porta)
        self.trabalhador_serial.start()
        self.status_label.setText("Status: Conectado")
        self.atualizar_estado_botoes(True)

    def parar_conexao(self):
        """Encerra conexão serial"""
        self.trabalhador_serial.parar()
        self.trabalhador_serial.wait()
        self.status_label.setText("Status: Desconectado")
        self.atualizar_estado_botoes(False)

    def atualizar_grafico(self, tempo_decorrido, temperatura):
        """Atualiza o gráfico com novos dados recebidos"""
        if not self.trabalhador_serial.registrando:
            return

        if self.tempo_primordial is None:
            self.tempo_primordial = tempo_decorrido

        tempo_relativo_ao_registro = tempo_decorrido - self.tempo_primordial

        self.serie.append(tempo_relativo_ao_registro, temperatura)  # type: ignore

        # Ajusta faixa dos eixos
        ultimo_tempo = self.serie.at(self.serie.count()-1).x()
        self.eixo_x.setRange(0, ultimo_tempo)

        temperaturas = [p.y() for p in self.serie.pointsVector()]
        if temperaturas:
            self.eixo_y.setRange(min(temperaturas)-1, max(temperaturas)+1)

    def atualizar_estado_botoes(self, conectado):
        """Atualiza estado dos botões conforme conexão"""
        self.btn_conectar.setEnabled(not conectado)
        self.btn_desconectar.setEnabled(conectado)
        self.btn_registro.setEnabled(
            conectado and self.label_caminho.text() != "Arquivo não selecionado")

    def mostrar_erro(self, mensagem):
        """Exibe mensagens de erro na interface"""
        self.status_label.setText(f"ERRO: {mensagem}")
        self.parar_conexao()

    def closeEvent(self, evento):
        """Garante encerramento correto ao fechar janela"""
        self.trabalhador_serial.parar()
        self.trabalhador_serial.wait()
        evento.accept()


"""
Boilerplate para execução da aplicação
"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
