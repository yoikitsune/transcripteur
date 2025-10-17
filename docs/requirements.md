# Cahier des charges

## Exigences fonctionnelles
- Transcrire les pistes audio des fichiers vidéo en texte français à l’aide de modèles Whisper locaux.
- Générer des horodatages par segment alignés sur la sortie Whisper.
- Exporter les transcriptions vers plusieurs formats : texte brut, JSON avec métadonnées et SRT.
- Fournir des options CLI pour sélectionner la taille du modèle, les chemins d’entrée/sortie et les formats d’export.
- Autoriser le traitement par lot de plusieurs médias.
- Afficher dans le CLI le suivi de progression, le temps restant estimé et les erreurs.
- Gérer une détection de langue de secours lorsque l’entrée n’est pas strictement en français.
- Permettre la persistance de la configuration via un fichier de config au niveau du projet.

## Exigences non fonctionnelles
- Fonctionner entièrement hors ligne une fois les dépendances et modèles installés.
- Traiter une vidéo HD de 60 minutes en moins de 120 minutes sur le matériel GPU cible ; moins de 240 minutes en mode CPU.
- Atteindre une précision de transcription adaptée au sous-titrage (>90 % sur le jeu de référence).
- Fournir une journalisation riche pour le débogage et l’analyse d’usage (locale uniquement).
- Maintenir la compatibilité avec Linux et macOS, avec un support Windows en meilleur effort.
- Garantir >85 % de couverture de tests unitaires/intégration sur les modules cœur.

## Personae et récits utilisateurs
- **Créateur de contenu** : « En tant que créateur de contenu, je veux transcrire mes vidéos en fichiers SRT pour publier des sous-titres rapidement. »
- **Monteur vidéo** : « En tant que monteur, j’ai besoin de transcriptions horodatées pour accélérer mon workflow d’édition. »
- **Spécialiste de la localisation** : « En tant que spécialiste de la localisation, j’ai besoin de transcriptions françaises précises pour alimenter mes pipelines de traduction. »

## Contraintes
- Doit fonctionner sur du matériel standard avec VRAM GPU limitée ; les grands modèles peuvent nécessiter une optimisation ou un découpage.
- FFmpeg doit être présent sur la machine hôte pour l’extraction audio.

## Dépendances et intégrations
- Package Python `whisper` (ou équivalent) pour l’inférence du modèle.
- PyTorch avec support CUDA/cuDNN lorsque disponible.
- FFmpeg pour l’extraction audio et le prétraitement.
- Rich/Typer/Click (à confirmer) pour améliorer l’UX du CLI.

## Critères d’acceptation
- La commande CLI `transcripteur` traite correctement un média d’exemple et produit les fichiers texte, JSON et SRT.
- Les tests automatisés couvrent les chemins critiques : ingestion média, pipeline de transcription, exports.
- La documentation inclut l’installation, des exemples d’usage et le dépannage.
