# Transcripteur CLI

Outil CLI pour transcrire en local des vidéos en français avec les modèles Whisper d’OpenAI tout en produisant des timelines détaillées.

## Vision
Ce projet vise à proposer un flux de transcription « offline-first » optimisé pour les contenus audiovisuels français. Les transcriptions doivent préserver la précision temporelle, distinguer les locuteurs et être faciles à exporter pour les besoins de sous-titrage.

## Fonctionnalités clés (planifiées)
- Inférence Whisper locale avec choix de la taille du modèle.
- Prise en charge des formats vidéo/audio courants via FFmpeg.
- Export des timelines au niveau des segments (SRT, JSON, etc.).
- Diarisation et nettoyage de la ponctuation configurables.
- Traitement par lot et reprise de tâches interrompues.
- CLI légère avec retour d’information exploitable sur la progression.
 - Mode dictée temps réel depuis le microphone (`mic`), avec sélection du modèle adaptée à l’environnement (via une batterie de tests).

## Prise en main
1. Créer l’environnement virtuel : `python3 -m venv .venv`
2. Installer les dépendances : `.venv/bin/pip install -r requirements.txt` *(inclut Whisper, Torch, Typer, Rich, etc.)*
3. Vérifier l’installation : `PYTHONPATH=src .venv/bin/python -m transcripteur doctor`

La commande `doctor` contrôle la présence de FFmpeg, Torch et Whisper en réalisant une transcription factice. Consultez `docs/` pour les exigences détaillées, l’architecture et la feuille de route.

## Utilisation
### Transcrire un média
```bash
PYTHONPATH=src .venv/bin/python -m transcripteur transcribe chemin/vers/media.mp4 \
    --output-dir sorties \
    --model base \
    --device cpu
```

Pour un premier test sur une machine CPU-only, il est recommandé d’utiliser un extrait audio court (≈30 s) et/ou un modèle plus petit (`--model tiny`) afin de réduire le temps de transcription.

### Transcrire depuis le microphone (`mic`, planifié)
Un mode `mic` permettra de capturer le microphone en continu et de produire du texte en temps (quasi) réel.

Avant d’implémenter ce mode, une batterie de tests d’environnement sera utilisée pour profiler la machine (CPU/GPU, mémoire, latence) et recommander automatiquement le modèle Whisper le plus adapté. Voir `docs/roadmap.md` pour le détail des étapes.

Exemple d’appel cible (non encore implémenté) :

```bash
PYTHONPATH=src .venv/bin/python -m transcripteur mic \
    --model auto \
    --device auto
```

Une commande `benchmark` (planifiée) permettra de mesurer les performances des différents modèles Whisper sur votre machine, afin de guider automatiquement ou manuellement le choix du modèle à utiliser, en particulier pour le mode `mic`.

### Exports générés
- **Texte (`.txt`)** : transcription continue.
- **JSON (`.json`)** : segments avec horodatages et métadonnées brutes.
- **SRT (`.srt`)** : sous-titres synchronisés.

Options disponibles via `--help` (chemin config, langue, fréquence d’échantillonnage, etc.).

## Contribution
Le processus de développement et les règles de contribution seront définis en parallèle des premiers jalons d’implémentation.
