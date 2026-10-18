# Detector de Sonolência

Detecta sinais de sono pela webcam e toca um alarme quando:

- os olhos ficam fechados por mais de 0,7 segundo (**EAR**);
- a boca fica muito aberta, como num bocejo, por mais de 0,7 segundo (**MAR**).

## Como rodar

1. Instale o [Python 3](https://www.python.org/downloads/) (de preferência de 3.10 a 3.12).

2. Instale o compilador usado pela biblioteca `dlib`:
   - **macOS:** `xcode-select --install`
   - **Windows:** [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), com a opção "Desenvolvimento para desktop com C++"
   - **Linux:** `sudo apt install build-essential cmake`

3. Na pasta do projeto, crie o ambiente virtual e instale as bibliotecas:

   **macOS / Linux**
   ```bash
   python3 -m venv venv
   venv/bin/pip install cmake
   venv/bin/pip install -r requirements.txt
   ```

   **Windows**
   ```bash
   python -m venv venv
   venv\Scripts\pip install cmake
   venv\Scripts\pip install -r requirements.txt
   ```

4. Rode o detector:

   **macOS / Linux**
   ```bash
   venv/bin/python todas.py
   ```

   **Windows**
   ```bash
   venv\Scripts\python todas.py
   ```

## Como usar

- No começo, olhe para a câmera com os olhos abertos e a boca fechada até terminar a calibração.
- Para sair, aperte **q**.
- Para usar outra câmera, passe o número dela: `python todas.py 1`.

O arquivo `shape_predictor_68_face_landmarks.dat` precisa estar na mesma pasta do `todas.py`.
