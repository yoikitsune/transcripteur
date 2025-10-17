# Charte du projet

## Objectif
Fournir un CLI fiable capable de transcrire localement des contenus vidéo et audio en français avec Whisper d’OpenAI tout en générant des timelines précises pour les workflows de montage et de sous-titrage.

## Objectifs
- Produire des transcriptions françaises précises incluant les métadonnées temporelles.
- Fonctionner entièrement hors ligne avec des modèles et dépendances installés en local.
- Proposer des formats d’export extensibles pour les sous-titres et données structurées.
- Offrir une expérience développeur fluide grâce à une documentation claire et à l’automatisation.

## Périmètre
- Inclus : conception et implémentation du CLI, intégration du modèle Whisper, ingestion des médias via FFmpeg, génération des timelines (JSON/SRT), tests, packaging et automatisation des releases.
- Exclus : API cloud pour l’inférence, interface web, diarisation avancée dépassant les outils locaux disponibles.

## Indicateurs de réussite
- >90 % de précision au niveau des mots sur un jeu de référence sélectionné.
- Temps de traitement de bout en bout <2× la durée du média sur la cible matérielle.
- Aucune anomalie bloquante dans la release candidate pendant deux sprints consécutifs.
- Onboarding développeur <1 jour grâce à la documentation et aux scripts fournis.

## Parties prenantes
- Product Owner : supervise la feuille de route et les priorités.
- Tech Lead : définit l’architecture et contrôle la qualité de l’implémentation.
- Développeurs : réalisent les fonctionnalités, maintiennent les tests, assurent le support.
- QA/Relecteurs : valident le fonctionnement et les performances.

## Contraintes et hypothèses
- Les systèmes cibles disposent d’une accélération GPU mais doivent dégrader correctement sur CPU.
- Les modèles s’exécutent localement sans appels réseau externes.
- Les médias sont fournis via le système de fichiers local.

## Dépendances
- Modèles Whisper d’OpenAI (via le package Python `whisper` ou équivalent).
- FFmpeg pour le décodage des médias.
- Optionnel : PyTorch, CUDA/cuDNN pour l’accélération GPU.
