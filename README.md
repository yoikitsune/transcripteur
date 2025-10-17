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

## Prise en main
1. Créer l’environnement virtuel : `python3 -m venv .venv`
2. Mettre à jour les dépendances : `.venv/bin/pip install -r requirements.txt`
3. Installer les utilitaires CLI : `.venv/bin/pip install typer rich` *(si non inclus)*
4. Vérifier l’installation : `PYTHONPATH=src .venv/bin/python -m transcripteur doctor`

La commande `doctor` contrôle la présence de FFmpeg, Torch et Whisper en réalisant une transcription factice. Consultez `docs/` pour les exigences détaillées, l’architecture et la feuille de route.

## Utilisation
### Transcrire un média
```bash
PYTHONPATH=src .venv/bin/python -m transcripteur transcribe chemin/vers/media.mp4 \
    --output-dir sorties \
    --model base \
    --device cpu
```

### Exports générés
- **Texte (`.txt`)** : transcription continue.
- **JSON (`.json`)** : segments avec horodatages et métadonnées brutes.
- **SRT (`.srt`)** : sous-titres synchronisés.

Options disponibles via `--help` (chemin config, langue, fréquence d’échantillonnage, etc.).

## Contribution
Le processus de développement et les règles de contribution seront définis en parallèle des premiers jalons d’implémentation.
