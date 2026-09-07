"""Gap detection: what the GDD requires against what the codebase contains.

Four evidence levels, strongest first:

  implemented  a real symbol carries the behaviour
  stubbed      the name exists but the body returns a literal
  mentioned    it appears only in a comment or docstring
  absent       nothing in the codebase refers to it

"stubbed" and "mentioned" both count as gaps. A comment describing a system is
evidence that it was considered and not built, which is exactly the state this
assignment asks the agent to notice.
"""


class Gap:
    def __init__(self, feature, status, evidence):
        self.feature = feature
        self.status = status
        self.evidence = evidence
        self.score = None
        self.breakdown = {}

    @property
    def key(self):
        return self.feature["key"]

    def as_dict(self):
        return {"key": self.key, "name": self.feature.get("name", self.key),
                "status": self.status, "evidence": self.evidence,
                "score": self.score, "breakdown": self.breakdown,
                "gdd_section": self.feature.get("gdd_section"),
                "blocks": self.feature.get("blocks", []),
                "requires": self.feature.get("requires", [])}


def classify(feature, code):
    """Return a Gap for one feature, using the strongest evidence found."""
    tokens = feature.get("detect", [feature["key"]])
    stub_hits, sym_hits, comment_hits = [], [], []
    for tok in tokens:
        stub_hits += code.find_stub(tok)
        sym_hits += [s for s in code.find(tok) if s.kind in ("class", "def")]
        # An attribute counts only on an exact name match. Substring matching
        # attributes would let any incidental name imply a system exists.
        sym_hits += [s for s in code.find(tok)
                     if s.kind == "attr" and s.name.lower() == tok.lower()]
        comment_hits += code.in_comments(tok)

    if stub_hits:
        s = stub_hits[0]
        return Gap(feature, "stubbed",
                   "%s:%d %s() returns a literal" % (s.module, s.lineno, s.name))
    if sym_hits:
        # An exact name match is the strongest evidence, not the weakest.
        # An earlier version excluded exact matches and reported five working
        # systems as absent, which would have sent the agent to rebuild them.
        # Prefer a definition over an attribute when reporting evidence, so
        # the trace names where the behaviour lives rather than where it is used.
        defs = [s for s in sym_hits if s.kind in ("class", "def")]
        exact = [s for s in (defs or sym_hits)
                 if s.name.lower() in {t.lower() for t in tokens}]
        s = (exact or defs or sym_hits)[0]
        return Gap(feature, "implemented",
                   "%s:%d %s %s" % (s.module, s.lineno, s.kind, s.name))
    if comment_hits:
        m, ln, t = comment_hits[0]
        return Gap(feature, "mentioned", "%s:%d comment only: %s" % (m, ln, t[:60]))
    return Gap(feature, "absent", "no reference anywhere in %d modules"
               % len(code.modules))


def detect(features, code):
    return [classify(f, code) for f in features]


def open_gaps(gaps):
    return [g for g in gaps if g.status != "implemented"]
