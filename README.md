# Scripts utilizados para a implementação de um sistema de monitoramento térmico com Arduino.

### Repositório destinado ao armazenamento e disponibilização de scripts desenvolvidos para um sistema de monitoramento térmico com sensor MLX90614 conectado a uma placa Arduino UNO.

O script `termometro-iv-com-arduino.ino` é responsável por fazer as leituras instantâneas periodicamente, determinado por constante de tempo, e enviar os dados via serial ao programa GUI feito em `.py`. Além das leituras de temperaturas, ele também envia o tempo decorrido cru, em microssegundos, desde que a placa foi ligada, obtido via através da função `micros()`.

O programa em Python, o `source.termometro.py`, recebe essa output crua obtida via serial e faz a correção para obter o tempo real desde que a medida foi iniciada.

Optou-se por fazer dessa forma para obter medidas com menor margem de erro possível em relação ao tempo.

No momento da escrita deste `README.md`, não foi implementado overflow failsafe para a função `micros()` no código `.ino`. Antes que se complete 4295 segundos (71 minutos) contínuos de operação, a placa deve ser reiniciada para garantir o funcionamento correto. Basta desconectar e conectar novamente o cabo ao computador em seguida, sem que seja necessário esperar algum tempo entre essas operações.