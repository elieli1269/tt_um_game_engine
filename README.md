# tt_um_game_engine
TinyTapeout project: a mini hardware game engine with score and collision logic.

## Chat IA avec votre propre modèle
Un script Python est fourni pour lancer un chat CLI avec votre modèle local ou un modèle Hugging Face.

### Prérequis
```bash
pip install torch transformers
```

### Lancement
```bash
python3 chat_local_model.py --model /chemin/vers/votre_modele
```

Options utiles :
- `--device cpu|cuda`
- `--max-new-tokens 256`
- `--temperature 0.7`

Commandes pendant le chat :
- `/reset` : efface l'historique
- `/quit` : quitte le chat
