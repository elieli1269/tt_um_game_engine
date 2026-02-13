# tt_um_game_engine

Prototype de jeu FPS HTML5/WebGL côté client (JS + Three.js) orienté démonstration Poki.

## Lancer en local

```bash
python3 -m http.server 8080
```

Puis ouvrir `http://localhost:8080`.

## Contrôles

- `WASD` : déplacement
- Souris : visée (arrivée directe sur la scène, pointer lock tenté automatiquement; si refus navigateur, un clic active la visée)
- Clic gauche maintenu : **tir automatique** avec cooldown

## Fonctionnalités implémentées

- Scène 3D avec décor urbain simple, fog et lumières.
- Ennemis bots avec corps 3D stylisés et fusils visibles.
- Système de tir côté client (hitscan), HP + score + respawn.
- Si la room contient peu de joueurs, ajout automatique de bots pour maintenir l'action.
- Hook WebSocket optionnel via `?ws=wss://...`.

### Présence WebSocket (optionnel)

Le client écoute des messages JSON de forme:

```json
{ "type": "presence", "players": 3 }
```

`players` représente le nombre de joueurs humains connectés. Si `players` vaut `0`, la partie est automatiquement remplie par des bots pour garder de l'action. Le client ajuste ensuite dynamiquement le nombre de bots pour conserver un minimum de combattants.
