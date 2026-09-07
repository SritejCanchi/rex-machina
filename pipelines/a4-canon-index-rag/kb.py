"""
kb.py — the knowledge base for REX MACHINA's content pipeline.

Chunks the GDD, builds a TF-IDF vector index over the chunks, and retrieves by
cosine similarity. Pure standard library: no numpy, no network, no model
download. The whole index is rebuilt from source in well under a second, so
retrieval is reproducible on any machine with Python 3.9+.

Why lexical vectors and not neural embeddings: see README, "What the retriever
actually is". Short version — the corpus is one 12 KB document whose whole
vocabulary is proper nouns and identifiers (`dir_freq_20`, `read_category`,
`fence_gap`, `boxcar`). Exact term overlap is the signal. An embedding model
would cost a 90 MB download and a dependency, and it would blur precisely the
identifiers the queries key on. The retriever is swappable at one interface
(`Index.embed`) if that judgement turns out to be wrong.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable

# --------------------------------------------------------------------------
# tokenisation
# --------------------------------------------------------------------------

# Keep underscores and digits: `dir_freq_20` and `read_category` are single
# meaningful tokens in this corpus, and splitting them destroys the signal.
_TOKEN_RE = re.compile(r"[a-z0-9_]+")

_STOP = frozenset("""
a an the and or but if then than that this these those of to in on at by for
with from as is are was were be been being it its it's do does did doing have
has had having i you he she they we not no so such own same too very can will
just don should now
""".split())


def tokenize(text: str) -> list[str]:
    """Lowercase, split to [a-z0-9_]+, drop stopwords and 1-char tokens."""
    out = []
    for tok in _TOKEN_RE.findall(text.lower()):
        if len(tok) < 2 or tok in _STOP:
            continue
        out.append(tok)
    return out


def bigrams(tokens: list[str]) -> list[str]:
    return [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]


def featurize(text: str) -> list[str]:
    """Unigrams plus adjacent bigrams. Bigrams carry phrases like
    'fence gap', 'train yard', 'read category' that unigrams alone lose."""
    toks = tokenize(text)
    return toks + bigrams(toks)


# --------------------------------------------------------------------------
# chunking
# --------------------------------------------------------------------------

@dataclass
class Chunk:
    id: str
    source: str
    heading: str          # breadcrumb, e.g. "3. BOSS MECHANICS > phases"
    kind: str             # prose | code | table_row | list
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


_HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
_FENCE_RE = re.compile(r"^\s*```")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:\-|]+\|\s*$")

MAX_CHARS = 900       # soft ceiling for a merged prose chunk
MIN_CHARS = 60        # below this, merge forward rather than emit


def _breadcrumb(stack: list[tuple[int, str]]) -> str:
    return " > ".join(title for _, title in stack)


def chunk_markdown(text: str, source: str) -> list[Chunk]:
    """Structure-aware markdown chunker.

    Three chunk kinds are emitted, because the GDD carries three kinds of
    payload and they retrieve very differently:

      * ``code``      — a fenced block, kept whole. The JSON agent contracts
                        are the highest-value chunks in the corpus and must
                        never be split across a boundary.
      * ``table_row`` — one row of a markdown table, with the header row
                        prepended so the row is self-describing. The Chronicler
                        beat table is eight independent facts wearing a table
                        costume; chunking it as one blob makes every beat query
                        return all eight.
      * ``prose``     — everything else, merged to ~900 chars on paragraph
                        boundaries and never across a heading.
    """
    lines = text.splitlines()
    chunks: list[Chunk] = []
    stack: list[tuple[int, str]] = []
    buf: list[str] = []
    i = 0
    n = 0  # chunk counter

    def flush_prose():
        nonlocal buf, n
        body = "\n".join(buf).strip()
        buf = []
        if not body:
            return
        # split into paragraphs, then greedily merge to MAX_CHARS
        paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        acc: list[str] = []
        acc_len = 0
        for p in paras:
            if acc and acc_len + len(p) > MAX_CHARS:
                n += 1
                chunks.append(Chunk(f"{source}#{n:03d}", source,
                                    _breadcrumb(stack), "prose",
                                    "\n\n".join(acc)))
                acc, acc_len = [], 0
            acc.append(p)
            acc_len += len(p)
        if acc:
            n += 1
            chunks.append(Chunk(f"{source}#{n:03d}", source,
                                _breadcrumb(stack), "prose",
                                "\n\n".join(acc)))

    while i < len(lines):
        line = lines[i]

        m = _HEADING_RE.match(line)
        if m:
            flush_prose()
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            i += 1
            continue

        if _FENCE_RE.match(line):
            flush_prose()
            block = [line]
            i += 1
            while i < len(lines) and not _FENCE_RE.match(lines[i]):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i])
                i += 1
            n += 1
            chunks.append(Chunk(f"{source}#{n:03d}", source,
                                _breadcrumb(stack), "code",
                                "\n".join(block)))
            continue

        if _TABLE_ROW_RE.match(line):
            flush_prose()
            header = line
            i += 1
            # optional separator row
            if i < len(lines) and _TABLE_SEP_RE.match(lines[i]):
                i += 1
            while i < len(lines) and _TABLE_ROW_RE.match(lines[i]):
                row = lines[i]
                n += 1
                chunks.append(Chunk(f"{source}#{n:03d}", source,
                                    _breadcrumb(stack), "table_row",
                                    header.strip() + "\n" + row.strip()))
                i += 1
            continue

        buf.append(line)
        i += 1

    flush_prose()
    return [c for c in chunks if len(c.text.strip()) >= MIN_CHARS or c.kind != "prose"]


def load_kb(kb_dir: str | Path) -> list[Chunk]:
    kb_dir = Path(kb_dir)
    out: list[Chunk] = []
    for path in sorted(kb_dir.glob("*.md")):
        out.extend(chunk_markdown(path.read_text(encoding="utf-8"), path.stem))
    if not out:
        raise FileNotFoundError(f"no .md knowledge base files under {kb_dir}")
    return out


# --------------------------------------------------------------------------
# vector index
# --------------------------------------------------------------------------

@dataclass
class Hit:
    chunk: Chunk
    score: float
    overlap: list[str] = field(default_factory=list)   # top shared terms, for the trace


class Index:
    """TF-IDF vector store with cosine similarity.

    Vectors are sparse dicts term -> weight, L2-normalised at build time so
    similarity is a plain dot product. Weighting is sublinear tf (1+log tf)
    times smoothed idf, the standard `ltc` scheme.
    """

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.df: Counter[str] = Counter()
        docs_terms: list[Counter[str]] = []
        for c in chunks:
            tf = Counter(featurize(self._indexed_text(c)))
            docs_terms.append(tf)
            for term in tf:
                self.df[term] += 1
        self.N = len(chunks)
        self.vectors = [self._weight(tf) for tf in docs_terms]

    @staticmethod
    def _indexed_text(c: Chunk) -> str:
        # The heading breadcrumb is indexed with the body. A chunk under
        # "BOSS MECHANICS" should match a boss query even when the body
        # never repeats the word.
        return f"{c.heading}\n{c.text}"

    def _idf(self, term: str) -> float:
        return math.log((self.N + 1) / (self.df.get(term, 0) + 1)) + 1.0

    def _weight(self, tf: Counter[str]) -> dict[str, float]:
        vec = {t: (1.0 + math.log(f)) * self._idf(t) for t, f in tf.items()}
        norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
        return {t: w / norm for t, w in vec.items()}

    def embed(self, text: str) -> dict[str, float]:
        """Public seam. Swap this (and _weight) for a neural encoder and the
        rest of the pipeline is unchanged."""
        return self._weight(Counter(featurize(text)))

    def search(self, query: str, k: int = 5) -> list[Hit]:
        q = self.embed(query)
        scored: list[Hit] = []
        for chunk, vec in zip(self.chunks, self.vectors):
            # iterate the shorter dict
            small, large = (q, vec) if len(q) < len(vec) else (vec, q)
            score = 0.0
            contrib: list[tuple[float, str]] = []
            for term, w in small.items():
                other = large.get(term)
                if other:
                    p = w * other
                    score += p
                    contrib.append((p, term))
            if score > 0:
                contrib.sort(reverse=True)
                scored.append(Hit(chunk, score,
                                  [t for _, t in contrib[:6]]))
        scored.sort(key=lambda h: (-h.score, h.chunk.id))
        return scored[:k]

    def stats(self) -> dict:
        return {
            "chunks": self.N,
            "vocabulary": len(self.df),
            "by_kind": dict(Counter(c.kind for c in self.chunks)),
            "sources": sorted({c.source for c in self.chunks}),
            "mean_chunk_chars": round(
                sum(len(c.text) for c in self.chunks) / self.N, 1),
        }


def build_index(kb_dir: str | Path = "data/kb") -> Index:
    return Index(load_kb(kb_dir))


if __name__ == "__main__":
    idx = build_index()
    print(json.dumps(idx.stats(), indent=2))
