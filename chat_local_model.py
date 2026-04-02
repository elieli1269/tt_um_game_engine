#!/usr/bin/env python3
"""Chat IA local sans API avec entraînement continu et turbo-quantization."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import random
import re
import threading
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

TOKEN_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ']+|[^\w\s]", re.UNICODE)


@dataclass
class SearchResult:
    title: str
    snippet: str
    url: str


class TurboQuantNgramModel:
    """
    Modèle n-gram léger avec:
    - apprentissage incrémental
    - génération simple
    - quantization dynamique des poids (turboquant)
    """

    def __init__(self, order: int = 3, turboquant: bool = True, seed: int = 7):
        self.order = max(2, order)
        self.rng = random.Random(seed)
        self.turboquant = turboquant
        self._lock = threading.Lock()
        self.counts: Dict[Tuple[str, ...], Counter] = defaultdict(Counter)
        self.quantized: Dict[Tuple[str, ...], Dict[str, int]] = {}
        self.scales: Dict[Tuple[str, ...], float] = {}

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return TOKEN_RE.findall(text.lower())

    @staticmethod
    def detokenize(tokens: Iterable[str]) -> str:
        out: List[str] = []
        for tok in tokens:
            if not out:
                out.append(tok)
            elif re.match(r"[^\wÀ-ÖØ-öø-ÿ']", tok):
                out[-1] += tok
            else:
                out.append(" " + tok)
        return "".join(out)

    def train_text(self, text: str) -> int:
        tokens = self.tokenize(text)
        if len(tokens) < self.order:
            return 0

        updates = 0
        with self._lock:
            for i in range(len(tokens) - self.order + 1):
                context = tuple(tokens[i : i + self.order - 1])
                nxt = tokens[i + self.order - 1]
                self.counts[context][nxt] += 1
                updates += 1

            if self.turboquant:
                self._quantize_recent(tokens)

        return updates

    def _quantize_recent(self, tokens: List[str]) -> None:
        contexts = set()
        for i in range(len(tokens) - self.order + 1):
            contexts.add(tuple(tokens[i : i + self.order - 1]))

        for context in contexts:
            cnt = self.counts.get(context)
            if not cnt:
                continue
            max_val = max(cnt.values())
            if max_val <= 0:
                continue
            scale = max_val / 255.0
            q = {tok: min(255, int(round(v / scale))) for tok, v in cnt.items()}
            self.quantized[context] = q
            self.scales[context] = scale

    def _distribution(self, context: Tuple[str, ...]) -> Dict[str, float]:
        if self.turboquant and context in self.quantized:
            scale = self.scales[context]
            return {tok: qv * scale for tok, qv in self.quantized[context].items()}
        cnt = self.counts.get(context, Counter())
        return dict(cnt)

    def generate(self, prompt: str, max_new_tokens: int = 60, temperature: float = 0.9) -> str:
        base = self.tokenize(prompt)
        if not base:
            base = ["bonjour"]

        generated: List[str] = []
        for _ in range(max_new_tokens):
            context_source = (base + generated)[-(self.order - 1) :]
            if len(context_source) < self.order - 1:
                break
            context = tuple(context_source)
            dist = self._distribution(context)
            if not dist:
                break

            nxt = self._sample(dist, max(0.05, temperature))
            generated.append(nxt)
            if nxt in {".", "!", "?"} and len(generated) > 12:
                break

        if not generated:
            return "Je n'ai pas encore assez de données, mais je continue à apprendre."
        return self.detokenize(generated)

    def _sample(self, dist: Dict[str, float], temperature: float) -> str:
        toks = list(dist.keys())
        weights = [max(v, 1e-6) for v in dist.values()]
        if temperature != 1.0:
            weights = [w ** (1.0 / temperature) for w in weights]
        total = sum(weights)
        pick = self.rng.random() * total
        run = 0.0
        for tok, w in zip(toks, weights):
            run += w
            if run >= pick:
                return tok
        return toks[-1]


def load_wikipedia_corpus(path: Path, limit_docs: int | None = None) -> List[str]:
    texts: List[str] = []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if limit_docs and i >= limit_docs:
                    break
                if not line.strip():
                    continue
                row = json.loads(line)
                text = row.get("text") or row.get("content") or ""
                if text:
                    texts.append(text)
    else:
        full_text = path.read_text(encoding="utf-8", errors="ignore")
        docs = [d.strip() for d in full_text.split("\n\n") if d.strip()]
        texts = docs[:limit_docs] if limit_docs else docs
    return texts


def train_on_wikipedia(model: TurboQuantNgramModel, wiki_path: Path, limit_docs: int | None) -> int:
    docs = load_wikipedia_corpus(wiki_path, limit_docs)
    updates = 0
    for doc in docs:
        updates += model.train_text(doc)
    return updates


def web_search(query: str, max_results: int = 5, timeout: float = 10.0) -> List[SearchResult]:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LocalTurboChat/1.0)"},
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    results: List[SearchResult] = []
    blocks = re.findall(r'<a rel="nofollow" class="result__a".*?</a>.*?<a class="result__snippet".*?</a>', html, flags=re.S)
    for block in blocks[: max_results * 2]:
        t = re.search(r'class="result__a" href="(.*?)".*?>(.*?)</a>', block, flags=re.S)
        s = re.search(r'class="result__snippet".*?>(.*?)</a>', block, flags=re.S)
        if not t or not s:
            continue
        raw_url, raw_title = t.group(1), t.group(2)
        raw_snip = s.group(1)
        clean = lambda x: re.sub(r"<.*?>", "", x).replace("\n", " ").strip()
        result = SearchResult(title=clean(raw_title), snippet=clean(raw_snip), url=raw_url)
        if result.title and result.snippet:
            results.append(result)
        if len(results) >= max_results:
            break

    return results


def summarize_results(query: str, results: List[SearchResult], max_sentences: int = 4) -> str:
    if not results:
        return "Aucun résultat web exploitable."

    query_terms = set(TurboQuantNgramModel.tokenize(query))
    scored: List[Tuple[float, str]] = []
    for r in results:
        sentence = f"{r.title}. {r.snippet}"
        toks = set(TurboQuantNgramModel.tokenize(sentence))
        overlap = len(toks.intersection(query_terms))
        density = overlap / max(1, math.sqrt(len(toks)))
        scored.append((density, sentence))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:max_sentences]]
    return " ".join(top)


def build_reply(user_msg: str, local_generation: str, web_summary: str | None) -> str:
    if web_summary:
        return (
            "Voici un résumé web rapide: "
            f"{web_summary}\n\n"
            "Complément généré par le modèle local: "
            f"{local_generation}"
        )
    return local_generation


def chat(args: argparse.Namespace) -> None:
    model = TurboQuantNgramModel(order=args.order, turboquant=not args.disable_turboquant, seed=args.seed)

    if args.wikipedia_dump:
        wiki_path = Path(args.wikipedia_dump)
        if not wiki_path.exists():
            raise FileNotFoundError(f"Fichier Wikipedia introuvable: {wiki_path}")
        t0 = time.time()
        updates = train_on_wikipedia(model, wiki_path, args.max_wiki_docs)
        print(f"[init] Entraînement Wikipedia terminé: {updates} mises à jour en {time.time() - t0:.1f}s")

    print("Chat local prêt. /quit pour quitter, /web <requête> pour recherche web + résumé.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        while True:
            try:
                user_msg = input("Vous: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAu revoir.")
                return

            if not user_msg:
                continue
            if user_msg.lower() in {"/quit", "quit", "exit"}:
                print("Au revoir.")
                return

            web_query = None
            if user_msg.startswith("/web "):
                web_query = user_msg[5:].strip()

            train_future = pool.submit(model.train_text, user_msg)
            web_future = pool.submit(web_search, web_query, args.web_results) if web_query else None

            local_generation = model.generate(user_msg, max_new_tokens=args.max_new_tokens, temperature=args.temperature)

            web_summary = None
            if web_future is not None:
                try:
                    web_results = web_future.result(timeout=args.web_timeout)
                    web_summary = summarize_results(web_query, web_results)
                    model.train_text(web_summary)
                except Exception as exc:
                    web_summary = f"Recherche web indisponible ({exc})."

            assistant_msg = build_reply(user_msg, local_generation, web_summary)
            model.train_text(assistant_msg)

            updates = train_future.result(timeout=2)
            print(f"Assistant: {assistant_msg}\n")
            print(f"[learn] +{updates} updates user msg | turboquant={'on' if model.turboquant else 'off'}\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="IA chat locale sans API avec apprentissage continu.")
    p.add_argument("--wikipedia-dump", help="Chemin vers dump texte/.jsonl Wikipedia (optionnel)")
    p.add_argument("--max-wiki-docs", type=int, default=2000, help="Nombre max de docs wiki à ingérer")
    p.add_argument("--order", type=int, default=3, help="Ordre du modèle n-gram")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--max-new-tokens", type=int, default=60)
    p.add_argument("--temperature", type=float, default=0.9)
    p.add_argument("--web-results", type=int, default=5)
    p.add_argument("--web-timeout", type=float, default=10.0)
    p.add_argument("--disable-turboquant", action="store_true", help="Désactive la quantization dynamique")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    chat(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
