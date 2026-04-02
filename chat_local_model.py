#!/usr/bin/env python3
"""CLI minimal pour discuter avec votre propre modèle local."""

from __future__ import annotations

import argparse
import sys
from typing import List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


SYSTEM_PROMPT = (
    "Tu es un assistant utile, clair et concis. "
    "Réponds en français sauf si on te demande autre chose."
)


def load_model(model_path: str, device: str):
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if device == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    )

    if device == "cuda" and torch.cuda.is_available():
        model = model.to("cuda")
    else:
        model = model.to("cpu")

    model.eval()
    return tokenizer, model


def format_history(history: List[tuple[str, str]]) -> str:
    blocks = [f"System: {SYSTEM_PROMPT}"]
    for role, content in history:
        prefix = "User" if role == "user" else "Assistant"
        blocks.append(f"{prefix}: {content}")
    blocks.append("Assistant:")
    return "\n".join(blocks)


def generate_reply(tokenizer, model, prompt: str, max_new_tokens: int, temperature: float) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            do_sample=temperature > 0,
            temperature=max(temperature, 1e-5),
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True)
    return text.strip()


def chat_loop(tokenizer, model, max_new_tokens: int, temperature: float):
    print("Chat prêt. Tapez /quit pour sortir, /reset pour effacer l'historique.\n")
    history: List[tuple[str, str]] = []

    while True:
        try:
            user_input = input("Vous: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            return

        if not user_input:
            continue
        if user_input.lower() in {"/quit", "quit", "exit"}:
            print("Au revoir !")
            return
        if user_input.lower() == "/reset":
            history.clear()
            print("Historique effacé.\n")
            continue

        history.append(("user", user_input))
        prompt = format_history(history)
        reply = generate_reply(tokenizer, model, prompt, max_new_tokens, temperature)
        history.append(("assistant", reply))
        print(f"Assistant: {reply}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chat local avec votre propre modèle.")
    parser.add_argument("--model", required=True, help="Chemin local ou nom HF du modèle")
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Périphérique de calcul",
    )
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.7)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        tokenizer, model = load_model(args.model, args.device)
    except Exception as exc:  # surface loading error to CLI user
        print(f"Erreur de chargement du modèle: {exc}", file=sys.stderr)
        return 1

    chat_loop(tokenizer, model, args.max_new_tokens, args.temperature)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
