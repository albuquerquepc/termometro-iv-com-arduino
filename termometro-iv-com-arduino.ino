#include <LiquidCrystal.h> // Inclui a biblioteca LiquidCrystal para controlar o display LCD
#include <Adafruit_MLX90614.h> // Inclui a biblioteca Adafruit_MLX90614 para controlar o sensor MLX90614-CL

/* Abaixo, variáveis e constantes fundamentais do sistema */

// Objeto MLX90614 para referenciar o sensor de temperatura infravermelho
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

// Objeto LiquidCrystal que define os pinos (RS, Enable, D4, D5, D6, D7) utilizados no LCD
LiquidCrystal lcd(7, 6, 5, 4, 3, 2);

// Array de 8 bytes que desenha o símbolo de grau para o display LCD
byte grau[8] = { B00110, B01001, B01001, B00110, B00000, B00000, B00000, B00000 };

// Variável para armazenar o tempo da última atualização
unsigned long ultimoTempo = 0;

// Constante que representa o intervalo de 100 ms
const unsigned long INTERVALO = 100;

// Tamanho do array que armazenará as medições; modificar esse valor altera o número de medidas para o cálculo da média
const int ARRAY_TAMANHO = 10;

// Array de floats para armazenar as medições de temperatura
float arrDeMedidas[ARRAY_TAMANHO];

// Variável que atua como ponteiro para indicar a posição atual do array para a próxima medida
int pointerDoArr = 0;

// Função que calcula a média de um array de medidas de temperatura
float tempMedia(float dummyArr[], int dummyArrTam) {
    float soma = 0; // Inicializa a soma das medições com zero

    // Percorre o array para calcular a soma dos valores, exibindo o acumulado a cada iteração para debug
    for (int i = 0; i < dummyArrTam; i++) {
        soma += dummyArr[i]; // Acumula o valor atual na soma total
    } 
    
    float media = (soma / dummyArrTam);// Calcula a média das medições
    return media; // Retorna a média calculada
}

/* Setup do sistema */

// Função setup: executada uma vez na inicialização do sistema
void setup() {
  Serial.begin(9600); // Inicializa a comunicação serial com baud rate de 9600
  lcd.begin(16, 2); // Configura o LCD para 16 colunas e 2 linhas
  lcd.clear(); // Limpa qualquer informação prévia no display LCD

  // Inicializa o sensor MLX90614-CL; caso a inicialização falhe, exibe mensagem de erro e entra em loop solicitando reinicialização
  if (!mlx.begin()) {
    Serial.println("Falha de conexao com o sensor, reiniciar!"); // Informa o erro via serial
    lcd.clear(); // Limpa o display LCD
    lcd.setCursor(0, 0); // Define o cursor na coluna 0, linha 0
    lcd.print("  Erro conexao  "); // Exibe mensagem de erro no LCD
    lcd.setCursor(0, 1); // Define o cursor na coluna 0, linha 1
    lcd.print("   Reiniciar!   "); // Exibe instrução para reiniciar o sistema
    while (1); // Entra em loop infinito para travar o programa
  }

  lcd.createChar(1, grau); // Cria um caractere customizado (índice 1) com o símbolo de grau
  lcd.setCursor(0, 0); //Posiciona o cursor na coluna 0, linha 0 do LCD
  lcd.print("UFRN  DFTE  GNMS"); // Exibe "DFTE" centralizada
  lcd.setCursor(0, 1); // Posiciona o cursor na coluna 0, linha 1 do LCD
  lcd.print("  MLX90614-CL  "); // Exibe a identificação do sensor utilizado
  delay(2000); // Aguarda 2000 ms para que a mensagem seja visualizada
  lcd.clear(); // Limpa o display LCD
  lcd.setCursor(0, 0); // Posiciona o cursor novamente na coluna 0, linha 0
  lcd.print("Temperatura do"); // Exibe "Temperatura do" na primeira linha
  lcd.setCursor(0, 1); // Posiciona o cursor na coluna 0, linha 1
  lcd.print("alvo:  "); // Exibe "Objeto:" na segunda linha
  
  // Configura a emissividade do sensor para 0.95 (valor aproximado para água); a mudança desse valor pode afetar a precisão da medição; ao iniciar o sensor, a emissividade padrão é 1, como alteramos aqui, dependnedo da superfície que ele esteja apontando inicialmente, os valores da temperatura mensurada podem ser absurdamente discrepantes com a realidade, ou seja, cuidado na superfície que o sensor está apontando quando ligar o sistema
  mlx.writeEmissivity(0.95);
}

/* Loop de execução do programa */

// Função loop: executada continuamente após o setup
void loop() {
  // Verifica se o intervalo de tempo definido já passou desde a última leitura
  if ((millis() - ultimoTempo) >= INTERVALO) {
    // Lê a temperatura do objeto (em graus Celsius) através do sensor MLX90614
    float tempObjeto = mlx.readObjectTempC();
    // Armazena a medida lida no array de medições na posição indicada por pointerDoArr
    arrDeMedidas[pointerDoArr] = tempObjeto;
    // Incrementa o ponteiro para apontar para a próxima posição do array
    pointerDoArr += 1; 
    // Atualiza o tempo da última leitura para o tempo atual
    ultimoTempo = millis();

    // Quando o array de medições estiver preenchido (10 medidas)
    if (pointerDoArr >= 10) {
      // Calcula a média das 10 medições e armazena o resultado em storeTempMedia
      float storeTempMedia = tempMedia(arrDeMedidas, ARRAY_TAMANHO);
      
      // Imprime o tempo de execução e a média calculada via comunicação serial
      Serial.print(ultimoTempo);
      Serial.print(",");
      Serial.println(storeTempMedia);

      // Exibe a média de temperatura no display LCD
      lcd.setCursor(8, 1); // Posiciona o cursor na coluna 8, linha 1 para exibir a média
      lcd.print(storeTempMedia); // Exibe o valor da média
      lcd.setCursor(14, 1); // Posiciona o cursor na coluna 14, linha 1 para exibir o símbolo de grau
      lcd.write(1); // Exibe o caractere customizado (símbolo de grau)
      lcd.setCursor(15, 1); // Posiciona o cursor na coluna 15, linha 1 para exibir a unidade
      lcd.print("C"); // Exibe a letra "C" de graus Celsius

      pointerDoArr = 0; // Reseta o ponteiro do array para iniciar uma nova coleta de medições
    }
  }
}