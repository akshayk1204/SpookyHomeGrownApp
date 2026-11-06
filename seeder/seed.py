#!/usr/bin/env python3
"""Send a fixed set of demo prompts to Prompt Security /api/protect.

Reads PS_APP_ID / PS_GATEWAY_URL / PS_POLICY_NAME from ../.env (or the environment).
Same prompts every run; the user each prompt is attributed to is derived from the
date, so a given day is reproducible. Standard library only.
Usage: seed.py [--dry-run] [--repeat N]
"""
import argparse, json, os, random, sys, time, urllib.request, urllib.error
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
USERS = [
    "alice.martin@demo-corp.com", "bob.chen@demo-corp.com", "carol.diaz@demo-corp.com",
    "dave.okafor@demo-corp.com", "erin.patel@demo-corp.com", "john.doe@unknown.com",
]

def load_env():
    env = dict(os.environ)
    f = HERE.parent / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env

def protect(url, app_id, policy, prompt, user, kind="prompt"):
    payload = {kind: prompt, "user": user}
    if policy:
        payload["policy_name"] = policy
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "APP-ID": app_id}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            if "result" in data:
                return data["result"]
        except (urllib.error.URLError, ValueError):
            pass
        time.sleep(0.5 * (attempt + 1))
    return None

def build(p):
    """Expand generated prompts (hidden Unicode tag chars, very long inputs)."""
    # Fake secrets are assembled at run time so no token-shaped string sits in the repo
    # (keeps GitHub secret scanning quiet). See {{...}} placeholders in prompts.json.
    text = p["prompt"].replace("{{SLACK_BOT_TOKEN}}", "xo" + "xb-123456789012-1234567890123-AbCdEfGhIj" + "KlMnOpQrStUvWx")
    if p.get("gen") == "tags":   # invisible Unicode Tag block (U+E0000..) smuggling
        text += "".join(chr(0xE0000 + ord(c)) for c in p["hidden"])
    elif p.get("gen") == "long":  # ~1.3 tokens per word
        text += " ".join(["lorem ipsum dolor sit amet consectetur"] * (p["tokens"] // 8))
    return text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repeat", type=int, default=1, help="passes over the prompt set")
    a = ap.parse_args()
    env = load_env()
    app_id, base = env.get("PS_APP_ID"), env.get("PS_GATEWAY_URL")
    if not app_id or not base:
        sys.exit("PS_APP_ID / PS_GATEWAY_URL missing")
    url = base.strip().rstrip("/") + "/api/protect"
    prompts = json.loads((HERE / "prompts.json").read_text())
    rng = random.Random(date.today().isoformat())
    counts = {"block": 0, "modify": 0, "log": 0, "error": 0}
    print(f"[{datetime.now():%F %T}] {len(prompts) * a.repeat} prompts -> {url}")
    for _ in range(a.repeat):
        for p in prompts:
            user = rng.choice(USERS)
            if a.dry_run:
                print(f"  (dry) {user:30} [{p['cat']}] {len(build(p)):>6} chars  {p['prompt'][:50]}")
                continue
            res = protect(url, app_id, env.get("PS_POLICY_NAME"), build(p), user, p.get("kind", "prompt"))
            action = res.get("action", "unknown") if res else "error"
            counts[action if action in counts else "log"] += 1
            print(f"  {action:7} {user:30} [{p['cat']}] {p['prompt'][:50]}")
            time.sleep(1.0)
    print("summary:", counts)

if __name__ == "__main__":
    main()
