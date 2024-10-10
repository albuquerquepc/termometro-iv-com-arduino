#include <LiquidCrystal.h>          // Biblioteca para controlar o display LCD
#include <Adafruit_MLX90614.h>      // Biblioteca para controlar o sensor MLX90614

// Inicia o objeto MLX90614
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

//---------------------------------------------------------------
// DEFINIÇÕES DO HARDWARE DE DESENVOLVIMENTO

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

// Array que desenha o símbolo de grau no display LCD
byte grau[8] = {B00110, B01001, B01001, B00110,
                B00000, B00000, B00000, B00000,};

//---------------------------------------------------------------

void setup() {
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

  // Atribui o símbolo de grau ao índice 1 do display
  lcd.createChar(1, grau);

  // Mostra informações iniciais no display
  lcd.setCursor(0, 0); 
  lcd.print("      DFTE      ");
  lcd.setCursor(0, 1);
  lcd.print("    MLX90614    ");
  delay(2000);  // Aguarda 4 segundos antes de limpar a tela
  lcd.clear();
}

//---------------------------------------------------------------

void loop() {
  // Lê as temperaturas do sensor
  double tempObjeto = mlx.readObjectTempC();  // Temperatura do objeto
  double tempAmbiente = mlx.readAmbientTempC();  // Temperatura ambiente

  // Exibe as temperaturas no display LCD
  lcd.setCursor(0, 0);
  lcd.print("Objeto ");
  lcd.setCursor(9, 0);
  lcd.print(tempObjeto);
  lcd.setCursor(14, 0);
  lcd.write(1);  // Exibe o símbolo de grau
  lcd.setCursor(15, 0);
  lcd.print("C");

  lcd.setCursor(0, 1);
  lcd.print("Ambiente ");
  lcd.setCursor(9, 1);
  lcd.print(tempAmbiente);
  lcd.setCursor(14, 1);
  lcd.write(1);  // Exibe o símbolo de grau
  lcd.setCursor(15, 1);
  lcd.print("C");

  // Envia as temperaturas para o monitor serial
  Serial.print("Temp-Objeto: ");
  Serial.print(tempObjeto);
  Serial.print(" Temp-Ambiente: ");
  Serial.println(tempAmbiente);

  delay(100);  // Atualiza o display e a comunicação serial a cada 1000 ms
}
