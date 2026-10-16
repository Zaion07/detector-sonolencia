# SleepGuard

Detector de sonolência em tempo real usando a webcam. O programa identifica o rosto, acompanha os olhos e a boca e toca um alarme quando detecta sinais de sono:

- **EAR (Eye Aspect Ratio):** olhos fechados por mais de 0,7 segundo.
- **MAR (Mouth Aspect Ratio):** boca muito aberta (bocejo) por mais de 0,7 segundo.

## Arquivos necessários

- `todas.py`: o código do detector
- `requirements.txt`: lista de bibliotecas
- `shape_predictor_68_face_landmarks.dat`: modelo de pontos do rosto (obrigatório)

> Não copie a pasta `venv` de um computador para outro. Crie uma nova em cada máquina.

## Passo a passo

### 1. Instalar o Python

Instale o Python 3 (recomendado de 3.10 a 3.12) pelo site [python.org](https://www.python.org/downloads/).

No Windows, marque a opção **"Add Python to PATH"** durante a instalação.

### 2. Instalar as ferramentas para compilar o dlib

A biblioteca `dlib` normalmente é compilada durante a instalação, e para isso precisa de um compilador C++ e do CMake.

**macOS**
```bash
xcode-select --install
```

**Windows**

Instale o [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) e marque a opção **"Desenvolvimento para desktop com C++"**.

**Linux (Ubuntu/Debian)**
```bash
sudo apt install build-essential cmake
```

### 3. Abrir o terminal na pasta do projeto

```bash
cd caminho/para/a/pasta/do/projeto
```

### 4. Criar o ambiente virtual

**macOS / Linux**
```bash
python3 -m venv venv
```

**Windows**
```bash
python -m venv venv
```

### 5. Instalar as bibliotecas

**macOS / Linux**
```bash
venv/bin/pip install cmake
venv/bin/pip install -r requirements.txt
```

**Windows**
```bash
venv\Scripts\pip install cmake
venv\Scripts\pip install -r requirements.txt
```

A instalação do `dlib` pode demorar alguns minutos.

### 6. Rodar o detector

**macOS / Linux**
```bash
venv/bin/python todas.py
```

**Windows**
```bash
venv\Scripts\python todas.py
```

O programa usa automaticamente a primeira câmera encontrada no computador. Para escolher outra câmera, passe o número dela:

```bash
venv/bin/python todas.py 1
```

## Como usar

1. Ao abrir, olhe para a câmera com os olhos abertos e a boca fechada por alguns segundos. O programa faz uma **calibração** (aparece "Calibrando... x/30").
2. Depois da calibração, o rosto aparece marcado com um quadrado vermelho, os olhos em verde e a boca em azul-claro.
3. Se os olhos ficarem fechados ou a boca muito aberta por mais de 0,7 segundo, aparece **"SONOLENCIA!"** na tela e o alarme toca.
4. Para sair, aperte **q** com a janela do vídeo selecionada.

## Problemas comuns

- **A câmera não abre no macOS:** libere o acesso em **Ajustes do Sistema → Privacidade e Segurança → Câmera** para o Terminal (ou o editor que você está usando).
- **"erro nenhuma camera encontrada":** confira se a webcam está conectada e se nenhum outro programa (Zoom, Teams etc.) está usando a câmera.
- **Erro ao instalar o dlib:** confira se o passo 2 foi feito. No Windows, uma alternativa é instalar uma versão do `dlib` já compilada (arquivo `.whl`) para a sua versão do Python.
- **Erro com o OpenCV:** o `requirements.txt` tem o `opencv-python` e o `opencv-contrib-python`. Se der conflito, remova a linha `opencv-contrib-python` e instale de novo.
