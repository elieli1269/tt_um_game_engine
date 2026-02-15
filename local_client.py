import json
import time
from pathlib import Path

import requests

from crypto_utils import decrypt_text, encrypt_text

SERVER_URL = "http://127.0.0.1:8000/api.php"
USER = "luc"
USER_KEY = "luc_demo_key_2026"
LOCAL_STORE = Path("local_messages_luc.json")


def load_local_messages():
    if not LOCAL_STORE.exists():
        return []
    return json.loads(LOCAL_STORE.read_text(encoding="utf-8"))


def save_local_messages(messages):
    LOCAL_STORE.write_text(json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8")


def persist_encrypted_local(msg):
    local_messages = load_local_messages()
    local_messages.append(
        {
            "id": msg["id"],
            "sender": msg["sender"],
            "kind": msg["kind"],
            "target": msg["target"],
            "external": msg["external"],
            "ciphertext": encrypt_text(msg["message"], USER_KEY),
            "created_at": msg["created_at"],
        }
    )
    save_local_messages(local_messages)


def notify_console(msg):
    print("\a", end="")
    print(f"[NOTIF] #{msg['id']} {msg['sender']} -> {msg['kind']}:{msg['target']} | {msg['message']}")


def send_message(sender, kind, target, text, external=False):
    payload = {
        "sender": sender,
        "kind": kind,
        "target": target,
        "message": text,
        "external": external,
    }
    res = requests.post(f"{SERVER_URL}?action=send", json=payload, timeout=5)
    res.raise_for_status()
    return res.json()


def poll_forever():
    print(f"Client local pour {USER}, polling chaque seconde...")
    after_id = 0
    while True:
        try:
            res = requests.get(
                f"{SERVER_URL}?action=inbox&user={USER}&mode=encrypted&after_id={after_id}",
                timeout=5,
            )
            res.raise_for_status()
            batch = res.json().get("messages", [])

            for encrypted_msg in batch:
                clear = decrypt_text(encrypted_msg["ciphertext"], USER_KEY)
                msg = {
                    "id": encrypted_msg["id"],
                    "sender": encrypted_msg["sender"],
                    "kind": encrypted_msg["kind"],
                    "target": encrypted_msg["target"],
                    "external": encrypted_msg.get("external", False),
                    "message": clear,
                    "created_at": encrypted_msg["created_at"],
                }
                notify_console(msg)
                persist_encrypted_local(msg)
                after_id = max(after_id, int(encrypted_msg["id"]))
        except Exception as exc:
            print(f"Erreur sync: {exc}")

        time.sleep(1)


if __name__ == "__main__":
    # exemple d'envoi depuis python:
    # send_message("alice", "group", "famille", "hello groupe", external=True)
    poll_forever()
