# Scripts utilizados para a implementação de um sistema de monitoramento térmico com Arduino.

### Repositório destinado ao armazenamento e disponibilização de scripts desenvolvidos para um sistema de monitoramento térmico com sensor MLX90614 conectado a uma placa Arduino UNO.

O script `termometro-iv-com-arduino.ino` é responsável por fazer as leituras instantâneas periodicamente, determinado por constante de tempo, e enviar os dados via serial ao programa GUI feito em `.py`. Além das leituras de temperaturas, ele também envia o tempo de execução decorrido cru, em milissegundos, desde que a placa foi ligada, obtido via através da função `millis()`.

O programa em Python, o `source.termometro.py`, recebe essa output crua obtida via serial e faz a correção para obter o tempo real desde que a medida foi iniciada.

Optou-se por fazer dessa forma para obter medidas com menor margem de erro possível em relação ao tempo.