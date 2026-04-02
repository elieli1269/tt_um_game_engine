# tt_um_game_engine
TinyTapeout project: a mini hardware game engine with score and collision logic.

## Chat IA local (sans API) avec entraînement continu
Le script `chat_local_model.py` fonctionne sans API externe et entraîne un modèle local léger en continu.

### Fonctionnalités
- Pré-entraînement sur dump Wikipedia local (`.txt` ou `.jsonl`).
- Recherche web à la demande (`/web ...`) + résumé local + ré-entraînement.
- Apprentissage continu sur chaque message utilisateur et chaque réponse assistant.
- `turboquant` intégré (quantization dynamique) pour réduire le poids mémoire.
- Sauvegarde/chargement du modèle (`--model-out`, `--model-in`).

### Lancement local
```bash
python3 chat_local_model.py --model-out ./models/turbo_local_model.json
```

### Entraînement batch puis sauvegarde
```bash
python3 chat_local_model.py \
  --train-only \
  --wikipedia-dump ./wikipedia.jsonl \
  --max-wiki-docs 5000 \
  --model-out ./models/turbo_local_model.json
```

### Commandes chat
- `/web votre requête` : recherche web + résumé + entraînement.
- `/quit` : quitter.

## GitHub Actions: entraîner et compiler un exécutable
Un workflow est disponible: `.github/workflows/build.yml`.

### Ce que fait le workflow
1. Télécharge le corpus Wikipedia (si `wikipedia_url` est fourni via `workflow_dispatch`).
2. Entraîne le modèle en mode batch (`--train-only`).
3. Compile un exécutable avec `pyinstaller`.
4. Publie les artifacts:
   - `dist/local_turbo_chat`
   - `models/turbo_local_model.json`

### Déclenchement
- Automatique sur push `main`/`master`.
- Manuel via **Actions > train-and-build-local-ai > Run workflow** (avec URL du corpus si besoin).
