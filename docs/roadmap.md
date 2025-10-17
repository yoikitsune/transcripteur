# Feuille de route

## Phase 0 – Mise en place du projet (Semaine 1)
- ✅ Définir le périmètre, les indicateurs de réussite et la documentation.
- ✅ Établir la structure du dépôt, les standards de code et la base outillage.
- ✅ Vérifier les prérequis matériels/logiciels (GPU disponible, installation de FFmpeg, commande `doctor`).

## Phase 1 – Pipeline de transcription cœur (Semaines 2-4)
- ✅ Structurer la CLI (`transcripteur.cli`) : commandes `transcribe`, `doctor`, gestion des logs (`Rich`) et options communes.
- ✅ Implémenter le chargement de configuration (`AppConfig`) et les defaults.
- ✅ Intégrer un module de prétraitement (extraction audio via FFmpeg) et un transcripteur Whisper fonctionnel.
- ✅ Créer les exports basiques (texte/JSON/SRT) avec timeline.
- ✅ Écrire des tests unitaires d’amorçage (CLI, configuration) et valider le pipeline.

## Phase 2 – Export et UX (Semaines 5-6)
- Ajouter l’export SRT et améliorer le formatage des segments.
- Mettre en place indicateurs de progression, journalisation et gestion d’erreurs dans le CLI.
- Introduire la persistance de configuration et la gestion de presets.
- Étendre les tests d’intégration avec des médias représentatifs.

## Phase 3 – Performance et fiabilité (Semaines 7-8)
- Optimiser le découpage, le batching et l’utilisation GPU.
- Implémenter la reprise de jobs et le traitement par lot.
- Ajouter des hooks de télémétrie (métriques locales) et des benchmarks de performance.
- Réaliser des tests d’acceptation utilisateur avec un panel pilote.

## Phase 4 – Préparation à la release (Semaines 9-10)
- Packager le CLI pour distribution (PyPI, Homebrew tap en option).
- Finaliser la documentation : guide utilisateur, dépannage, référence API.
- Mettre en place la CI/CD avec linting, tests et automatisation des releases.
- Tenir une revue de préparation au lancement et finaliser le plan de release.

## En continu
- Collecter les retours, trier les issues et planifier des améliorations itératives.
- Explorer des fonctionnalités avancées (diarisation, traduction) après le lancement.
