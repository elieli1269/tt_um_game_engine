# tt_um_game_engine
TinyTapeout project: a mini hardware game engine with score and collision logic.

## Chat IA local (sans API) avec entraînement continu
Le script `chat_local_model.py` fonctionne **sans API externe** et entraîne un modèle local léger en continu.

### Fonctionnalités
- Entraînement initial sur un dump Wikipedia local (`.txt` ou `.jsonl`).
- Recherche web à la demande (`/web ...`), résumé local, puis ré-entraînement sur ce résumé.
- Apprentissage continu : chaque message utilisateur **et** chaque réponse assistant sont réinjectés en entraînement.
- `turboquant` intégré : quantization dynamique des poids pour garder un modèle léger.

### Lancement simple
```bash
python3 chat_local_model.py
```

### Lancement avec pré-entraînement Wikipedia
```bash
python3 chat_local_model.py --wikipedia-dump ./wikipedia.jsonl --max-wiki-docs 5000
```

### Commandes pendant le chat
- `/web votre requête` : fait une recherche web + résumé + entraînement.
- `/quit` : quitte.

### Paramètres utiles
- `--order 3` : ordre du modèle n-gram.
- `--temperature 0.9` : diversité de génération.
- `--max-new-tokens 60` : longueur max de réponse.
- `--disable-turboquant` : désactive la quantization dynamique.
