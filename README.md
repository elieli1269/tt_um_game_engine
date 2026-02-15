# Messagerie chiffrée web (PHP) + client Python

Application demandée en **HTML + PHP + Python** avec:

- version web (envoi/lecture, notifications navigateur),
- version Python (polling toutes les secondes + notification console),
- messages utilisateur ou groupe,
- marquage des messages externes,
- liens d'appel audio / vision (room Jitsi),
- stockage des messages chiffrés sur serveur + copie par utilisateur.

## Fichiers principaux

- `index.php`: interface web.
- `api.php`: API JSON (`users`, `send`, `inbox`, `call_link`).
- `mirror.php`: endpoint de miroir distant.
- `storage.php`: stockage local JSON + copie utilisateur + tentative de miroir distant.
- `crypto_lib.php`: chiffrement/déchiffrement côté PHP.
- `local_client.py`: client Python qui poll chaque seconde.

## Lancer en local

### 1) Serveur PHP

```bash
php -S 0.0.0.0:8000
```

Puis ouvrir: `http://127.0.0.1:8000/index.php`

### 2) Client Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python local_client.py
```

## Miroir distant (alwaysdata)

Dans `config.php`, régler:

- `REMOTE_MIRROR_URL` (ex: `https://eliphotos.alwaysdata.net/messaging/mirror.php`)
- `API_MIRROR_TOKEN`

Le serveur enverra chaque nouveau message au miroir (best effort, non bloquant).

## API rapide

- `GET api.php?action=users`
- `POST api.php?action=send`
- `GET api.php?action=inbox&user=luc&after_id=0&mode=decrypted`
- `GET api.php?action=inbox&user=luc&after_id=0&mode=encrypted`
- `GET api.php?action=call_link&room=test&video=1`
