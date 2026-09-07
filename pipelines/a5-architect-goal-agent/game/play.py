#!/usr/bin/env python3
"""Rex Machina, Act 3 vertical slice. Run: python play.py

Controls: w a s d to move, e to wait, q to quit.
Standard library only. No install, no key, no network.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rex.loop import Game, MAX_ROUNDS          # noqa: E402
from rex import arena                          # noqa: E402

KEYS = {"a": "left", "d": "right", "w": "up", "s": "down", "e": "wait"}

# The grid uses words rather than initials so a first-time player does not have
# to decode a legend before moving. DOG is the player, REX is the REX-line
# robot of the GDD, KID is the objective tile.
CELL = 5


def draw(g):
    p, dog, nem = g.phase, g.dog.tile, g.nemesis.tile
    print()
    print("  phase %d/3  %-11s round %2d/%d  stamina %2d  approach %.2f"
          % (p.index, p.name, g.round, MAX_ROUNDS, g.dog.stamina, g.dog.approach))
    # The robot's register is a player-facing tell (GDD 3), so it belongs on
    # the HUD rather than only inside a read line that suppression may eat.
    print("  robot charge %3d%%  register %s"
          % (g.nemesis.self_charge_pct, g.nemesis.charge_band()))
    for y in range(p.height):
        row = []
        for x in range(p.width):
            t = (x, y)
            if t == dog:
                row.append("DOG")
            elif t == nem:
                row.append("REX")
            elif t == g.kid_tile:
                row.append("KID")
            elif t in p.exits:
                row.append("exit")
            elif t in p.cover:
                row.append("cover")
            else:
                row.append(".")
        print("  " + " ".join(c.center(CELL) for c in row))
    print("  DOG is you, the player. REX is the robot. KID is your goal tile.")
    print("  cover and exit are dressing from the Assignment 4 arena table.")


def intro(g):
    print("=" * 62)
    print("REX MACHINA, Act 3. Reach the kid before the clock runs out.")
    print("=" * 62)
    print("You play DOG. A REX-line robot, REX, is hunting you across a")
    print("%dx%d yard. KID is the child you are running to."
          % (g.phase.width, g.phase.height))
    print("Stand on the KID tile before round %d and before stamina" % MAX_ROUNDS)
    print("empties. Stamina costs 1 a round, 2 if REX ends the round beside")
    print("you. Watch its charge fall: a tired robot talks differently.")
    print()
    print("One key per round, then Enter:")
    print("  w up    a left    s down    d right    e wait    q quit")
    print()
    print(g.phase.light)


def main():
    g = Game()
    intro(g)
    while not g.over:
        draw(g)
        raw = input("  move [wasd/e/q] > ").strip().lower()
        if raw == "q":
            print("  left the yard.")
            return
        if raw not in KEYS:
            print("  not a direction.")
            continue
        e = g.play_round(KEYS[raw])
        if e["read"]:
            print('\n  REX: "%s"' % e["read"])
        if e["gate"]:
            nxt = g.phase
            print("\n  >>> the arena opens. %s" % nxt.gate.split(";")[0])
            print("  %s" % nxt.light)
    draw(g)
    if g.outcome == "win":
        print("\n  She sees you. The robot goes still.\n")
    else:
        print("\n  The porch light is still on. You cannot reach it.\n")


if __name__ == "__main__":
    main()
