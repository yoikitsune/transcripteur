# Vue d’ensemble de l’architecture

## Contexte système
Le CLI opère sur des fichiers médias locaux et orchestre le prétraitement, l’inférence du modèle et les pipelines d’export. Les dépendances externes se limitent aux runtimes installés localement (PyTorch, Whisper, FFmpeg).

## Composants principaux
- **Interface CLI** : gère l’analyse des arguments, le chargement de la configuration, l’affichage de la progression et l’orchestration des étapes du pipeline.
- **Préprocesseur média** : invoque FFmpeg pour extraire l’audio, normaliser la fréquence d’échantillonnage et gérer le découpage des fichiers volumineux.
- **Moteur de transcription** : encapsule le chargement du modèle Whisper, l’inférence, le batching et l’accélération GPU optionnelle.
- **Post-traitement** : applique les nettoyages spécifiques à la langue, normalise la ponctuation et propose des hooks de diarisation.
- **Exporteur** : sérialise les données de segments en formats texte, JSON et SRT en conservant la timeline.
- **Couche de persistance** : gère le cache des artefacts intermédiaires et des fichiers modèles.

## Flux de données
1. Le CLI valide la configuration d’entrée/sortie et charge les valeurs par défaut du projet.
2. Le préprocesseur média extrait la forme d’onde audio et les métadonnées éventuelles.
3. Le moteur de transcription exécute l’inférence du modèle et produit les segments avec horodatage.
4. Le post-traitement améliore la lisibilité et fusionne les segments si nécessaire.
5. L’exporteur écrit les transcriptions et métadonnées dans les formats sélectionnés.

## Choix technologiques
- **Python** pour l’implémentation.
- **Typer** (candidat) pour une ergonomie CLI moderne.
- **Rich** pour l’affichage console enrichi et les barres de progression.
- **PyTorch** et **Whisper** pour l’inférence.
- **FFmpeg** accessible via `ffmpeg-python` ou `subprocess`.
- **pytest** + **coverage** pour les tests.

## Qualité et observabilité
- Journalisation structurée vers la console et, en option, vers des fichiers.
- Hooks de collecte de métriques pour mesurer les performances (temps d’exécution, débit).
- Niveaux de verbosité configurables pour le débogage.

## Extensibilité
- Architecture modulaire pour ajouter de nouveaux formats d’export et fournisseurs de diarisation.
- Interfaces abstraites pour les moteurs de transcription afin de supporter d’autres modèles.
- Fichiers de configuration permettant des surcharges par projet ou profil utilisateur.
