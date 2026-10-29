<div align="center">

# 😴 Detector de Sonolência

**Detecta sinais de sono em tempo real pela webcam e dispara um alarme sonoro.**

![Python](https://img.shields.io/badge/Python-3.10%20a%203.12-3776AB?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-visão%20computacional-5C3EE8?logo=opencv&logoColor=white)
![dlib](https://img.shields.io/badge/dlib-68%20landmarks-008000)
![Plataformas](https://img.shields.io/badge/macOS%20%7C%20Windows%20%7C%20Linux-suportado-lightgrey)

</div>

---

## 📌 Sobre o projeto

O **Detector de Sonolência** usa visão computacional para observar o rosto do usuário pela webcam e identificar dois sinais clássicos de cansaço:

| Sinal | Técnica | Quando dispara |
|-------|---------|----------------|
| 👁️ **Olhos fechados** | **EAR** — *Eye Aspect Ratio* | olhos fechados por **1,0 s** ou mais |
| 🥱 **Bocejo** | **MAR** — *Mouth Aspect Ratio* | boca muito aberta por **1,2 s** ou mais |

Quando um desses sinais é detectado, aparece o aviso **SONOLÊNCIA** na tela e um alarme sonoro é tocado.

## ⚙️ Como funciona

1. **Detecção do rosto:** o `dlib` localiza o rosto em cada quadro da câmera. Para ganhar desempenho, a busca é feita primeiro na região onde o rosto estava no quadro anterior.
2. **Pontos faciais:** o modelo `shape_predictor_68_face_landmarks.dat` marca 68 pontos no rosto, entre eles os contornos dos olhos e da boca.
3. **Cálculo das proporções:**
   - **EAR** compara a altura com a largura do olho. Quando o olho fecha, o valor cai.
   - **MAR** compara a abertura vertical com a largura da boca. Num bocejo, o valor sobe.
4. **Calibração automática:** nos primeiros 30 quadros, o sistema mede o seu EAR e MAR "normais" e calcula limites personalizados para o seu rosto:
   - limite do EAR = 80% do seu valor normal;
   - limite do MAR = 2,4× o seu valor normal.
5. **Suavização:** os valores passam por uma média móvel de 5 quadros, o que evita alarmes falsos causados por piscadas ou ruído.
6. **Alarme:** se o valor passar do limite pelo tempo definido, o alerta aparece e o som toca.

```
Webcam ─► Detecta rosto ─► 68 pontos faciais ─► EAR / MAR ─► Suavização ─► Limite + tempo ─► 🔔 Alarme
```

## 🛠️ Tecnologias

- [Python 3](https://www.python.org/)
- [OpenCV](https://opencv.org/): captura e exibição do vídeo
- [dlib](http://dlib.net/): detecção do rosto e dos pontos faciais
- [imutils](https://github.com/PyImageSearch/imutils): utilitários de visão computacional
- [SciPy](https://scipy.org/) e [NumPy](https://numpy.org/): cálculos de distância

## 📦 Instalação

### 1. Pré-requisitos

- **Python 3.10 a 3.12** ([download](https://www.python.org/downloads/))
- **Uma webcam**
- **Um compilador C++**, exigido pela biblioteca `dlib`:

| Sistema | Como instalar |
|---------|---------------|
| 🍎 macOS | `xcode-select --install` |
| 🪟 Windows | [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), marcando a opção **"Desenvolvimento para desktop com C++"** |
| 🐧 Linux | `sudo apt install build-essential cmake` |

### 2. Clone o repositório

```bash
git clone https://github.com/Zaion07/detector-sonolencia.git
```

```bash
cd detector-sonolencia
```

### 3. Crie o ambiente virtual e instale as dependências

**🍎 macOS / 🐧 Linux**

```bash
python3 -m venv venv
venv/bin/pip install cmake
venv/bin/pip install -r requirements.txt
```

**🪟 Windows**

```bash
python -m venv venv
venv\Scripts\pip install cmake
venv\Scripts\pip install -r requirements.txt
```

> ⏳ A instalação do `dlib` compila código C++ e pode levar alguns minutos.

### 4. Confira o modelo de pontos faciais

O arquivo `shape_predictor_68_face_landmarks.dat` precisa estar na mesma pasta do `todas.py`. Ele já vem no repositório. Se estiver faltando, baixe em [dlib.net](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2) e descompacte na pasta do projeto.

## ▶️ Como usar

**🍎 macOS / 🐧 Linux**

```bash
venv/bin/python todas.py
```

**🪟 Windows**

```bash
venv\Scripts\python todas.py
```

### Passo a passo

1. Quando a janela abrir, **olhe para a câmera com os olhos abertos e a boca fechada** até terminar a calibração (`Calibrando... 30/30`).
2. A partir daí, o detector está ativo. Na tela você vê:
   - 🟥 o retângulo em volta do rosto;
   - 🟩 o contorno dos olhos e 🟦 o da boca;
   - os valores atuais de **EAR** e **MAR**;
   - um cronômetro sempre que um sinal de sono começa a ser contado.
3. Para **sair**, aperte **`q`**.

### Usando outra câmera

O programa procura uma câmera disponível sozinho. Para escolher uma específica, passe o número dela:

```bash
venv/bin/python todas.py 1
```

## 🎛️ Ajustes

Os principais parâmetros ficam no começo do arquivo [`todas.py`](todas.py):

| Parâmetro | Padrão | O que faz |
|-----------|--------|-----------|
| `RATIO_EAR` | `0.80` | Quanto o olho precisa fechar, em relação ao normal, para contar como fechado |
| `RATIO_MAR` | `2.4` | Quanto a boca precisa abrir, em relação ao normal, para contar como bocejo |
| `CONFIG_TECNICAS["ear"]["tempo"]` | `1.0` | Segundos de olho fechado até o alarme |
| `CONFIG_TECNICAS["mar"]["tempo"]` | `1.2` | Segundos de bocejo até o alarme |
| `FRAMES_CALIBRACAO` | `30` | Quantidade de quadros usados na calibração |
| `JANELA_SUAVIZACAO` | `5` | Quadros usados na média móvel |

## 🔊 Alarme por sistema

| Sistema | Som |
|---------|-----|
| 🍎 macOS | Som do sistema `Sosumi` |
| 🪟 Windows | Bipe de 1000 Hz |
| 🐧 Linux | Bipe do terminal |

## 🧩 Problemas comuns

- **`erro nenhuma camera encontrada.`**: verifique se a webcam está conectada e se o terminal tem permissão para usar a câmera. No macOS, veja em *Ajustes do Sistema → Privacidade e Segurança → Câmera*.
- **`erro arquivo shape_predictor_68_face_landmarks.dat não encontrado.`**: coloque o arquivo na mesma pasta do `todas.py` (veja o passo 4 da instalação).
- **Erro ao instalar o `dlib`**: confirme que o compilador C++ e o `cmake` estão instalados e que a versão do Python está entre 3.10 e 3.12.
- **Alarmes demais ou de menos**: reinicie o programa para recalibrar com boa iluminação, ou ajuste `RATIO_EAR` e `RATIO_MAR`.

## 📁 Estrutura

```
detector-sonolencia/
├── todas.py                                # Código principal do detector
├── shape_predictor_68_face_landmarks.dat   # Modelo de 68 pontos faciais do dlib
├── requirements.txt                        # Dependências Python
└── README.md
```

---

<div align="center">

Feito por **Gabriel Zaion**

</div>
