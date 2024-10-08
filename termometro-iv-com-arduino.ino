#include <LiquidCrystal.h>  // Biblioteca para controlar o display LCD
#include <Adafruit_MLX90614.h> //biblioteca para controlar o sensor MX90614

//inicia o objeto MLX90614
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

//---------------------------------------------------------------
//DEFINIÇÕES DO HARDWARE DE DESENVOLVIMENTO

  
// Define os pinos usados para o display LCD (RS, Enable, D4, D5, D6, D7)
LiquidCrystal lcd(7, 6, 5, 4, 3, 2);

/*
   Respectivamente:
   - LCD RS pin to digital pin 7
   - LCD Enable pin to digital pin 6
   - LCD R/W pin to ground (não usado)
   - LCD D4 pin to digital pin 5
   - LCD D5 pin to digital pin 4
   - LCD D6 pin to digital pin 3
   - LCD D7 pin to digital pin 2
*/

// Definindo variáveis
bool continuo = 0;         // Variável para controlar se os dados serão enviados continuamente
double emissivity = 0.95;  //parametro de emissividade do sensor. emissividade é a capacidade de um corpo de emitir radiação térmica. o intervalo vai de 0 a 1 - 0 é um corpo perfeitamente refletor e 1 é um corpo perfeitamente emissor.
String dados;              // String para armazenar dados da comunicação serial
char subcomando = 'c';     // Variável para armazenar subcomandos
// Array que desenha o símbolo de grau no display LCD
byte grau[8] = {B00110, B01001, B01001, B00110,
                B00000, B00000, B00000, B00000,};

//---------------------------------------------------------------

void setup()
{
  // Inicia comunicação serial a 9600 baud
  Serial.begin(9600);

  // Inicializa o display LCD com 16 colunas e 2 linhas
  lcd.begin(16, 2);
  lcd.clear();  // Limpa o display LCD

  // Inicializa o sensor MLX90614
  if (!mlx.begin()) {
    // Caso haja falha na comunicação com o sensor, exibe mensagem de erro
    Serial.println("Falha de Conexao com o Sensor, Reiniciar!");
    lcd.clear(); 
    lcd.setCursor(0, 0);
    lcd.print("  Erro Conexao  ");
    lcd.setCursor(0, 1);
    lcd.print("   Reiniciar!   ");
    while (1);  // Entra em loop infinito até que o sistema seja reiniciado
  }

  // Lê a emissividade do sensor
  emissivity = mlx.readEmissivity();

  // Atribui o símbolo de grau ao índice 1 do display
  lcd.createChar(1, grau);

  // Mostra informações iniciais no display
  lcd.setCursor(0, 0); //setamos o cursor para escrever a partir da coluna 0 e linha 0 (primeiro caractere, primeira linha)
  lcd.print("      DFTE      "); //note que o display tem 16 colunas, então o texto deve ter no máximo 16 caracteres, incluindo espaços. aqui temos 6 espaços antes e 6 espaços depois do texto para centralizar o texto no display
  lcd.setCursor(0, 1); //setamos o cursor para escrever a partir da coluna 0 e linha 1 (primeiro caractere, segunda linha)
  lcd.print("    MLX90614    "); // o mesmo aqui, 4 espaços antes e 4 depois para centralizar o texto no display
  delay(4000);  // Aguarda 4 segundos (4000 milisegundos) antes rodar o linha abaixo abaixo para limpar a tela
  lcd.clear();    
}

//---------------------------------------------------------------

void loop()
{
  // Verifica se há comunicação serial disponível
  if (Serial) {
    if (Serial.available()) {
      // Lê o comando da interface serial
      switch (Serial.read()) {
        case '?':  // Comando para mostrar a emissividade de cada sensor
          Serial.println("DFTE - Sensor Temperatura MLX90614"); 
          Serial.print("Emissivity Sensor 1: ");
          Serial.println(mlx.readEmissivity());
          Serial.print("Emissivity Sensor 2: ");
    mlx.writeEmissivity(emissivity);
    Serial.println(mlx.readEmissivity());
    digitalWrite(A5, HIGH);
    digitalWrite(A4, LOW);
    delay(50);
  } else {
    // Exibe 
        case 'C':  // Comando para alternar o envio contínuo de valores de temperatura
          continuo = !continuo;          
          break;

        case 'E':  // Comando para ajustar a emissividade dos sensores
          subcomando = Serial.read();  // Lê o próximo caractere para determinar o subcomando
          if (subcomando == '1') {  // Ajusta a emissividade do sensor 1
            dados = Serial.readString();
            emissivity = dados.toDouble();
            if (emissivity <= 1.0 && emissivity >= 0.0) {  // Verifica se o valor é válido
              mlx.writeEmissivity(emissivity);
              Serial.println(mlx.readEmissivity());
              digitalWrite(A5, HIGH);
              digitalWrite(A4, LOW);
              delay(50);
            } else {
              // Exibe erro se a emissividade estiver fora dos limites
              Serial.println("Erro, valor deve estar entre 0.0 a 1.0!");
              emissivity = mlx.readEmissivity();            
            }
          }  
          if (subcomando == '2') {  // Ajusta a emissividade do sensor 2
            dados = Serial.readString();
            emissivity = dados.toDouble();
            if (emissivity <= 1.0 && emissivity >= 0.0) {  // Verifica se o valor é válido
              mlx.writeEmissivity2(emissivity);
              Serial.println(mlx.readEmissivity2());
              digitalWrite(A5a, HIGH);
              digitalWrite(A4, LOW);
              delay(50);
            } else {
              // Exibe erro se a emissividade estiver fora dos limites
              Serial.println("Erro, valor deve estar entre 0.0 a 1.0!");
              emissivity = mlx.readEmissivity2();            
            }
          }        
          break;                  
      }
      Serial.readString();  // Limpa o buffer serial
    }

    // Envia os valores de temperatura continuamente se o modo contínuo estiver ativado
    if (continuo) {
      Serial.print(mlx.readObjectTempC());
      Serial.print("  ");
      Serial.println(mlx.readObject2TempC());
    }
  }

  // Exibe a temperatura dos sensores no display LCD
  lcd.setCursor(0, 0);
  lcd.print("Temp-S1: ");
  lcd.setCursor(9, 0);
  lcd.print(mlx.readObjectTempC());
  lcd.setCursor(14, 0);
  lcd.write(1);  // Exibe o símbolo de grau
  lcd.setCursor(15, 0);
  lcd.print("C");

  lcd.setCursor(0, 1);
  lcd.print("Temp-S2: ");
  lcd.setCursor(9, 1);
  lcd.print(mlx.readObject2TempC());
  lcd.setCursor(14, 1);
  lcd.write(1);  // Exibe o símbolo de grau
  lcd.setCursor(15, 1);
  lcd.print("C");

  delay(500);  // Atualiza o display a cada 500 ms
}

//---------------------------------------------------------------

// Função para mudar a emissividade de um sensor
bool mudar_emisi(String dadoss, int sensor = 1) {
  dadoss = Serial.readString();
  emissivity = dadoss.toDouble();
  if (emissivity <= 1.0 && emissivity >= 0.0) {  // Verifica se o valor de emissividade é válido
    mlx.writeEmissivity(emissivity);
    Serial.println(mlx.readEmissivity());
    digitalWrite(A5, HIGH);
    digitalWrite(A4, LOW);
    delay(50);
  } else {
    // Exibe erro se o valor estiver fora dos limites
    Serial.println("Erro, valor deve estar entre 0.0 a 1.0!");
    emissivity = mlx.readEmissivity();            
  }     
}
