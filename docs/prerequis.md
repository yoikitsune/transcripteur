# Prérequis matériel et logiciel

## Matériel recommandé
- **GPU** : NVIDIA avec support CUDA (>= compute capability 6.1) et au moins 6 Go de VRAM pour les modèles moyens/grands.
- **CPU** : 4 cœurs physiques minimum ; 8 cœurs recommandés.
- **Mémoire** : 16 Go de RAM recommandés pour traiter des vidéos d’une heure.
- **Stockage** : SSD avec au moins 10 Go libres pour les modèles et les fichiers temporaires.

## Logiciels requis
- **Système d’exploitation** : Linux ou macOS (support Windows en meilleur effort).
- **Python** : version 3.11 ou supérieure.
- **FFmpeg** : installé et accessible dans le PATH système.
- **Poetry** (ou gestionnaire équivalent) pour gérer les dépendances.
- **CUDA/cuDNN** (optionnel) pour l’accélération GPU avec PyTorch.

## Dépendances Python principales
- `torch` / `torchaudio`
- `whisper`
- `ffmpeg-python`
- `typer`
- `rich`

## Installation de l’environnement Python
1. Créer un environnement virtuel local :
   ```bash
   python3 -m venv .venv
   ```
2. Mettre à jour `pip` dans l’environnement :
   ```bash
   .venv/bin/pip install -U pip
   ```
3. Installer les dépendances principales :
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```
4. Installer les utilitaires CLI complémentaires :
   ```bash
   .venv/bin/pip install typer rich
   ```
5. Vérifier les imports Python et la disponibilité CUDA :
   ```bash
   .venv/bin/python -c "import torch, whisper, ffmpeg, typer, rich; print('Imports OK'); print('CUDA disponible :', torch.cuda.is_available())"
   ```
6. Confirmer la version de FFmpeg :
   ```bash
   ffmpeg -version
   ```

## Vérifications recommandées
- **GPU** : `nvidia-smi` pour confirmer la disponibilité et la version des drivers.
- **FFmpeg** : `ffmpeg -version` pour vérifier l’installation.
- **Python** : `python --version` pour confirmer la version 3.11.
- **CUDA** : `nvcc --version` (si pertinent) pour valider le toolkit.

## Notes sur l’accélération matérielle
- **CPU AMD Ryzen 7000/8000** : profiter des instructions AVX2/AVX-512 pour accélérer Whisper ou les LLM (utiliser `whisper.cpp` ou `llama.cpp` compilés avec AVX512).
- **GPU AMD RDNA3** : support ROCm en cours de déploiement. Tester la compatibilité avec `rocminfo` après installation du runtime ROCm 6.x.
- **Ryzen AI (NPU XDNA)** : support principalement disponible via les SDK AMD dédiés (Ryzen AI Software Platform). Sur Linux, suivre l’évolution des pilotes/EP ONNX Runtime pour l’exploitation de l’NPU.
