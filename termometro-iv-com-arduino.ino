#include <LiquidCrystal.h>          // Biblioteca para controlar o display LCD
#include <Adafruit_MLX90614.h>      // Biblioteca para controlar o sensor MLX90614

// Inicia o objeto MLX90614
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

// Define os pinos usados para o display LCD (RS, Enable, D4, D5, D6, D7)
LiquidCrystal lcd(7, 6, 5, 4, 3, 2);

// Array que desenha o símbolo de grau no display LCD
byte grau[8] = {B00110, B01001, B01001, B00110,
                B00000, B00000, B00000, B00000};

// Variável para armazenar o tempo do último update
unsigned long ultimoTempo = 0;
const unsigned long intervalo = 100000; // 100 ms em microssegundos

//---------------------------------------------------------------

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  lcd.clear();

  // Inicializa o sensor MLX90614
  if (!mlx.begin()) {
    Serial.println("Falha de conexao com o sensor, reiniciar!");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("  Erro Conexao  ");
    lcd.setCursor(0, 1);
    lcd.print("   Reiniciar!   ");
    while (1);
  }

  lcd.createChar(1, grau);
  lcd.setCursor(0, 0); 
  lcd.print("      DFTE      ");
  lcd.setCursor(0, 1);
  lcd.print("    MLX90614    ");
  delay(2000);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Objeto ");
}

//---------------------------------------------------------------

void loop() {
  // Verifica se já passou o intervalo de 100 ms
  if (micros() - ultimoTempo >= intervalo) {
    ultimoTempo = micros();  // Atualiza o tempo do último update
    
    // Lê a temperatura do sensor
    double tempObjeto = mlx.readObjectTempC();

    // Exibe a temperatura no display LCD
    lcd.setCursor(8, 0);
    lcd.print(tempObjeto);
    lcd.setCursor(14, 0);
    lcd.write(1);  // Exibe o símbolo de grau
    lcd.setCursor(15, 0);
    lcd.print("C");

    // Envia a temperatura para o monitor serial
    Serial.println(tempObjeto);
  }
}