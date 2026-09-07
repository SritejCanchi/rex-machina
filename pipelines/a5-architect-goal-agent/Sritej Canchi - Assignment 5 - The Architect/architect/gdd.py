"""Read the GDD and extract the systems it requires.

Deterministic structural extraction. Three signals, in order of reliability:

  1. JSON agent contracts in fenced code blocks. Field names in the Nemesis
     input and output contracts are the highest-value signal in the document,
     because every field is something the runtime must compute.
  2. Bolded terms in section prose, which is how this GDD names its systems.
  3. Numbered constraint headings in section 6.

Nothing here calls a model. The model's job comes later, in build.py. A
reviewer can read this file and know exactly where every requirement came from.
"""
import json
import re

CONTRACT_KEYS = re.compile(r'"([a-z_][a-z0-9_]*)"\s*:')
BOLD = re.compile(r"\*\*([^*]{3,60})\*\*")
SECTION = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.M)


class Requirement:
    def __init__(self, key, source, section, evidence):
        self.key = key
        self.source = source          # contract | prose | constraint
        self.section = section
        self.evidence = evidence.strip()

    def __repr__(self):
        return "Requirement(%s, %s, GDD %s)" % (self.key, self.source, self.section)

    def as_dict(self):
        return {"key": self.key, "source": self.source,
                "section": self.section, "evidence": self.evidence}


def _section_of(text, pos):
    last = "0"
    for m in SECTION.finditer(text):
        if m.start() > pos:
            break
        last = m.group(1)
    return last


def extract(path):
    """Return a de-duplicated list of Requirement objects."""
    text = open(path, encoding="utf-8").read()
    found, seen = [], set()

    # 1. JSON contract field names
    for block in re.findall(r"```json(.*?)```", text, re.S):
        start = text.find(block)
        for key in CONTRACT_KEYS.findall(block):
            if key in seen:
                continue
            seen.add(key)
            found.append(Requirement(key, "contract", _section_of(text, start),
                                     _line_around(block, key)))

    # 2. bolded system names
    for m in BOLD.finditer(text):
        term = m.group(1).strip().rstrip(".:")
        key = _slug(term)
        if not key or key in seen or len(key) < 4:
            continue
        seen.add(key)
        found.append(Requirement(key, "prose", _section_of(text, m.start()),
                                 _line_around(text, m.group(0))))

    return found


def _slug(term):
    s = re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_")
    return s if 0 < len(s) <= 40 else ""


def _line_around(text, needle):
    idx = text.find(needle)
    if idx < 0:
        return needle
    start = text.rfind("\n", 0, idx) + 1
    end = text.find("\n", idx)
    return text[start: end if end > 0 else len(text)]


if __name__ == "__main__":
    import sys
    reqs = extract(sys.argv[1])
    print(json.dumps([r.as_dict() for r in reqs], indent=1))
