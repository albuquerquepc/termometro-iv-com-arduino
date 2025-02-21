#!/bin/sh

# Checa se tem um argumento passado para o script
if [ -z "$1" ]; then
    echo "Usage: $0 <script.py>"
    exit 1
fi

# Roda o PyInstaller para criar o executável e remove os arquivos remanentes
# O argumento --icon só funciona no Windows e MacOS. No Linux é necessário adicionar uma entrada para o programa e criar uma entrada no menu de aplicativos em /usr/share/applications/ utilizando o comando: sudo nano /usr/share/applications/termometro.desktop
pyinstaller --onefile --noconsole --clean --noconfirm --icon="/termometro-iv-com-arduino/images/icotermia.ico" --name="Termômetro" "$1" && rm -rf build *.spec

echo "Executável criado. Arquivos remanentes removidos."
