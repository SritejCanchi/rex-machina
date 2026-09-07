"""Raw orchestration. No framework.

Class 7 slide 21: "FOR THIS ASSIGNMENT: RAW. You're writing code in your own
codebase. You need to see every decision the agent makes about your game before
it writes a file."

So this is a direct HTTPS call to the Anthropic messages endpoint using only
urllib. Three providers share one interface:

  live    real API call, needs ANTHROPIC_API_KEY, records what it receives
  replay  plays back a recorded turn by prompt hash, no network, deterministic
  refuse  raises, used by tests that must never reach a model

Every turn is keyed by sha256 of the exact prompt, so a replay cannot silently
drift from the prompt that produced it.
"""
import hashlib
import json
import os
import urllib.error
import urllib.request

MODEL = "claude-haiku-4-5-20251001"
TRANSCRIPT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "transcript")


def key_for(role, prompt):
    return "%s.%s" % (role, hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16])


class ReplayProvider:
    name = "replay"

    def complete(self, role, prompt, max_tokens=4000):
        path = os.path.join(TRANSCRIPT, key_for(role, prompt) + ".json")
        if not os.path.exists(path):
            raise RuntimeError(
                "no recorded turn for %s.\nExpected %s\n"
                "Run with --live and a key to record it."
                % (role, os.path.basename(path)))
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)["response"]


class LiveProvider:
    name = "live"

    def __init__(self, api_key):
        self.api_key = api_key

    def complete(self, role, prompt, max_tokens=4000):
        body = json.dumps({
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"content-type": "application/json",
                     "x-api-key": self.api_key,
                     "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            raise SystemExit(_explain(err))
        except urllib.error.URLError as err:
            raise SystemExit(
                "Could not reach api.anthropic.com: %s\n"
                "Check the network, then try again. Nothing was written."
                % err.reason)
        text = "".join(b.get("text", "") for b in payload.get("content", []))
        os.makedirs(TRANSCRIPT, exist_ok=True)
        path = os.path.join(TRANSCRIPT, key_for(role, prompt) + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"role": role, "model": MODEL, "prompt": prompt,
                       "response": text,
                       "usage": payload.get("usage", {})}, fh, indent=1)
        return text


def _explain(err):
    """Turn an API error into something a person can act on."""
    try:
        detail = json.loads(err.read().decode("utf-8"))
        message = detail.get("error", {}).get("message", "")
    except Exception:
        message = ""
    if err.code == 401:
        hint = ("The key was rejected. Check it was pasted whole and has not "
                "been revoked.")
    elif err.code == 400 and "credit balance" in message.lower():
        hint = ("The API account has no credits. A Max plan covers Claude.ai "
                "and Claude Code, not the API. Add credits in the Console "
                "under Billing.")
    elif err.code == 429:
        hint = "Rate limited. Wait a minute and run it again."
    else:
        hint = "Nothing was written to the game."
    return "Live call failed, HTTP %s.\n%s\n%s" % (err.code, message, hint)


def provider(mode="auto"):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if mode == "live" or (mode == "auto" and key):
        if not key:
            raise SystemExit("--live needs ANTHROPIC_API_KEY in the environment")
        return LiveProvider(key)
    return ReplayProvider()


def parse_json(text):
    """Pull the first JSON object or array out of a model reply."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start = min([i for i in (text.find("{"), text.find("[")) if i >= 0] or [0])
    depth, instr, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            continue
        if c == '"':
            instr = True
        elif c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    return json.loads(text[start:])
