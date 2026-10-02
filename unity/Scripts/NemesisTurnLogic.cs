using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;

namespace RexMachina
{
    [Serializable]
    public class NemesisConfig
    {
        public int window = 4;
        public int maxRounds = 15;
        public float pursuit = 8f;
        public float hold = 1f;
        public float solar = 2f;
        public float startCharge = 100f;
        public float bandClin = 60f;
        public float bandConf = 30f;
        public int freq = 20;
    }

    [Serializable]
    public class NemesisTurnState
    {
        public Vector2Int rexPos = new Vector2Int(4, 3);
        public Vector2Int dogPos = new Vector2Int(4, 6);
        public float charge = 100f;
        public int stamina = 17;
        public int round = 0;
        public bool isLimping = false;
        public string lastCategory = null;
        public List<string> spokenLines = new List<string>();
        public List<string> moveHistory = new List<string>();
    }

    [Serializable]
    public class NemesisArenaData
    {
        public Vector2Int gridSpan = new Vector2Int(10, 10);
        public List<Vector2Int> coverTiles = new List<Vector2Int>();
        public List<Vector2Int> exitTiles = new List<Vector2Int>();
    }

    public class NemesisTurnResult
    {
        public bool moveRefused;
        public bool isRefused => moveRefused;
        public bool refused => moveRefused;
        public string refusalReason;
        public Vector2Int predictedTile;
        public Vector2Int interceptMove;
        public bool moved;
        public float newCharge;
        public string chargeBand;
        public string spokenLine;
        public string spokenCategory;
        public List<string> firingCategories = new List<string>();
        public string dominantDirection;
        public int staminaDrain;
        public int newStamina;
    }

    /// <summary>
    /// Pure logic port of Rex's turn-based Nemesis brain from game.js.txt and GDD v3.
    /// Manages perception, prediction, intercept moves, charge dynamics,
    /// dialogue triggers, and rule RM-001 direction filtering.
    /// </summary>
    public static class NemesisTurnLogic
    {
        public static readonly string[] COMPASS = { "left", "right", "up", "down" };

        public static Vector2Int GetStep(string move)
        {
            switch (move)
            {
                case "left": return new Vector2Int(-1, 0);
                case "right": return new Vector2Int(1, 0);
                case "up": return new Vector2Int(0, 1);
                case "down": return new Vector2Int(0, -1);
                default: return Vector2Int.zero;
            }
        }

        public static bool IsDirectional(string move)
        {
            return move == "left" || move == "right" || move == "up" || move == "down";
        }

        public static int Manhattan(Vector2Int a, Vector2Int b)
        {
            return Mathf.Abs(a.x - b.x) + Mathf.Abs(a.y - b.y);
        }

        public static bool InBounds(Vector2Int t, Vector2Int span)
        {
            return t.x >= 0 && t.x < span.x && t.y >= 0 && t.y < span.y;
        }

        public static string GetChargeBand(float charge, NemesisConfig cfg)
        {
            if (charge > cfg.bandClin) return "clinical";
            if (charge >= cfg.bandConf) return "confident";
            return "strained";
        }

        public static Dictionary<string, float> CalculateDirFreq(List<string> moves, int freqLimit = 20)
        {
            var outDict = new Dictionary<string, float>
            {
                { "left", 0f }, { "right", 0f }, { "up", 0f }, { "down", 0f }
            };
            if (moves == null || moves.Count == 0) return outDict;

            int startIndex = Mathf.Max(0, moves.Count - freqLimit);
            var span = new List<string>();
            for (int i = startIndex; i < moves.Count; i++)
            {
                if (IsDirectional(moves[i]))
                    span.Add(moves[i]);
            }
            if (span.Count == 0) return outDict;

            for (int i = 0; i < span.Count; i++)
            {
                outDict[span[i]]++;
            }
            var keys = new List<string>(outDict.Keys);
            foreach (var k in keys)
            {
                outDict[k] = outDict[k] / span.Count;
            }
            return outDict;
        }

        public static float CalculatePeriodicity(List<string> moves, int freqLimit = 20)
        {
            if (moves == null) return 0f;
            int startIndex = Mathf.Max(0, moves.Count - freqLimit);
            int spanLength = moves.Count - startIndex;
            if (spanLength < 4) return 0f;

            var span = new List<string>(spanLength);
            for (int i = startIndex; i < moves.Count; i++)
            {
                span.Add(moves[i]);
            }

            float best = 0f;
            for (int lag = 2; lag < 6; lag++)
            {
                int hits = 0;
                int n = 0;
                for (int i = lag; i < span.Count; i++)
                {
                    n++;
                    if (span[i] == span[i - lag])
                        hits++;
                }
                if (n > 0)
                {
                    float ratio = (float)hits / n;
                    if (ratio > best) best = ratio;
                }
            }
            return best;
        }

        public static string GetDominantDirection(Dictionary<string, float> f)
        {
            string best = null;
            float bv = -1f;
            foreach (var d in COMPASS)
            {
                if (f.TryGetValue(d, out float val) && val > bv)
                {
                    bv = val;
                    best = d;
                }
            }
            return bv > 0f ? best : null;
        }

        public static Vector2Int Predict(Vector2Int dogPos, List<string> moves, int window = 4)
        {
            if (moves == null || moves.Count == 0) return dogPos;

            int startIndex = Mathf.Max(0, moves.Count - window);
            var w = new List<string>();
            for (int i = startIndex; i < moves.Count; i++)
            {
                if (IsDirectional(moves[i]))
                    w.Add(moves[i]);
            }
            if (w.Count == 0) return dogPos;

            var counts = new Dictionary<string, int>();
            foreach (var m in w)
            {
                if (!counts.ContainsKey(m)) counts[m] = 0;
                counts[m]++;
            }

            string best = null;
            int maxCount = -1;
            foreach (var m in w)
            {
                if (counts[m] > maxCount)
                {
                    maxCount = counts[m];
                    best = m;
                }
            }

            return dogPos + GetStep(best);
        }

        public static Vector2Int StepToward(Vector2Int from, Vector2Int target, Vector2Int dogPos, Vector2Int gridSpan)
        {
            Vector2Int best = from;
            int bd = Manhattan(from, target);
            foreach (var d in COMPASS)
            {
                Vector2Int c = from + GetStep(d);
                if (!InBounds(c, gridSpan) || c == dogPos) continue;
                int dTarget = Manhattan(c, target);
                if (dTarget < bd)
                {
                    best = c;
                    bd = dTarget;
                }
            }
            return best;
        }

        public static (Vector2Int predicted, Vector2Int move, bool moved, float newCharge) RexAct(
            Vector2Int rexPos,
            Vector2Int dogPos,
            List<string> moves,
            Vector2Int gridSpan,
            float currentCharge,
            NemesisConfig cfg)
        {
            Vector2Int predicted = Predict(dogPos, moves, cfg.window);
            int before = Manhattan(rexPos, dogPos);
            Vector2Int move = StepToward(rexPos, predicted, dogPos, gridSpan);

            // GDD Exploit #2 Leash Veto: reject any intercept that increases true distance to dog
            if (Manhattan(move, dogPos) > before)
            {
                move = StepToward(rexPos, dogPos, dogPos, gridSpan);
            }

            bool moved = (move != rexPos);
            float cost = moved ? cfg.pursuit : cfg.hold;
            float newCharge = Mathf.Clamp(currentCharge - cost + cfg.solar, 0f, cfg.startCharge);

            return (predicted, move, moved, newCharge);
        }

        public static List<string> FiringCategories(
            NemesisTurnState state,
            NemesisArenaData arena,
            NemesisConfig cfg)
        {
            var outList = new List<string>();
            var f = CalculateDirFreq(state.moveHistory, cfg.freq);

            // 1. Periodicity
            if (CalculatePeriodicity(state.moveHistory, cfg.freq) >= 0.6f)
                outList.Add("periodicity_called");

            // 2. Sealing direction (dominant frequency >= 0.45)
            float maxF = Mathf.Max(f["left"], f["right"], f["up"], f["down"]);
            if (maxF >= 0.45f)
                outList.Add("sealing_direction");

            // 3. Stall detected (>= 2 "wait" in last 4 moves)
            int waitCount = 0;
            int startWait = Mathf.Max(0, state.moveHistory.Count - 4);
            for (int i = startWait; i < state.moveHistory.Count; i++)
            {
                if (state.moveHistory[i] == "wait") waitCount++;
            }
            if (waitCount >= 2)
                outList.Add("stall_detected");

            // 4. Cover habit (dog is on a cover tile)
            if (arena.coverTiles != null && arena.coverTiles.Contains(state.dogPos))
                outList.Add("cover_habit");

            // 5. Exit fixation (dog within Manhattan distance <= 2 of any exit)
            if (arena.exitTiles != null)
            {
                bool nearExit = false;
                foreach (var exit in arena.exitTiles)
                {
                    if (Manhattan(state.dogPos, exit) <= 2)
                    {
                        nearExit = true;
                        break;
                    }
                }
                if (nearExit) outList.Add("exit_fixation");
            }

            // 6. Charge strain (charge < 30)
            if (state.charge < cfg.bandConf)
                outList.Add("charge_strain");

            // 7. Gait read (limping)
            if (state.isLimping)
                outList.Add("gait_read");

            return outList;
        }

        public static List<string> NamesDirection(string line)
        {
            var matched = new List<string>();
            if (string.IsNullOrEmpty(line)) return matched;

            foreach (var d in COMPASS)
            {
                if (Regex.IsMatch(line, @"\b" + d + @"\b", RegexOptions.IgnoreCase))
                {
                    matched.Add(d);
                }
            }
            return matched;
        }

        public static (string line, string category) SpeakRead(
            NemesisTurnState state,
            NemesisArenaData arena,
            NemesisReadTable readTable,
            NemesisConfig cfg,
            out List<string> firingCats,
            out string dominantDir)
        {
            firingCats = FiringCategories(state, arena, cfg);
            var f = CalculateDirFreq(state.moveHistory, cfg.freq);
            dominantDir = GetDominantDirection(f);
            string currentBand = GetChargeBand(state.charge, cfg);

            foreach (var cat in firingCats)
            {
                // GDD 4 suppression: never the same category twice running
                if (cat == state.lastCategory) continue;

                NemesisRead row = readTable != null ? readTable.Pick(cat, currentBand) : null;
                if (row == null || string.IsNullOrEmpty(row.Line)) continue;
                if (state.spokenLines.Contains(row.Line)) continue; // never twice in one run

                // RM-001: a line that names a compass direction is held back unless
                // that direction is the player's dominant one.
                var named = NamesDirection(row.Line);
                if (named.Count > 0)
                {
                    if (dominantDir == null || !named.Contains(dominantDir))
                    {
                        // Held back! Fall through to next live trigger
                        continue;
                    }
                }

                return (row.Line, cat);
            }

            return (null, null);
        }

        public static NemesisTurnResult ExecuteTurn(
            NemesisTurnState state,
            NemesisArenaData arena,
            NemesisReadTable readTable,
            NemesisConfig cfg)
        {
            if (state == null) throw new ArgumentNullException(nameof(state));
            arena = arena ?? new NemesisArenaData();
            cfg = cfg ?? new NemesisConfig();
            if (state.spokenLines == null) state.spokenLines = new List<string>();
            if (state.moveHistory == null) state.moveHistory = new List<string>();

            state.round++;

            // 1. Rex Act (intercept & battery)
            var (predicted, move, moved, newCharge) = RexAct(
                state.rexPos,
                state.dogPos,
                state.moveHistory,
                arena.gridSpan,
                state.charge,
                cfg);

            state.rexPos = move;
            state.charge = newCharge;

            // 2. Speak Read (tactical readout with suppression and RM-001)
            var (spokenLine, spokenCat) = SpeakRead(
                state,
                arena,
                readTable,
                cfg,
                out var firingCats,
                out var dominantDir);

            if (!string.IsNullOrEmpty(spokenLine))
            {
                state.lastCategory = spokenCat;
                state.spokenLines.Add(spokenLine);
            }

            // 3. RM-002 Stamina Drain (1 unconditional + 1 if adjacent)
            int adjacencyDrain = (Manhattan(state.rexPos, state.dogPos) <= 1) ? 1 : 0;
            int totalDrain = 1 + adjacencyDrain;
            state.stamina = Mathf.Max(0, state.stamina - totalDrain);

            return new NemesisTurnResult
            {
                predictedTile = predicted,
                interceptMove = move,
                moved = moved,
                newCharge = state.charge,
                chargeBand = GetChargeBand(state.charge, cfg),
                spokenLine = spokenLine,
                spokenCategory = spokenCat,
                firingCategories = firingCats,
                dominantDirection = dominantDir,
                staminaDrain = totalDrain,
                newStamina = state.stamina
            };
        }

        public static NemesisTurnResult ExecuteTurn(
            NemesisTurnState state,
            NemesisArenaData arena,
            NemesisReadTable readTable,
            NemesisConfig cfg,
            string playerMove)
        {
            if (state == null) throw new ArgumentNullException(nameof(state));
            arena = arena ?? new NemesisArenaData();
            cfg = cfg ?? new NemesisConfig();

            if (string.IsNullOrEmpty(playerMove))
            {
                return new NemesisTurnResult
                {
                    moveRefused = true,
                    refusalReason = "Invalid move: null or empty.",
                    predictedTile = state.dogPos,
                    interceptMove = state.rexPos,
                    moved = false,
                    newCharge = state.charge,
                    chargeBand = GetChargeBand(state.charge, cfg),
                    spokenLine = null,
                    spokenCategory = null,
                    firingCategories = new List<string>(),
                    dominantDirection = GetDominantDirection(CalculateDirFreq(state.moveHistory, cfg.freq)),
                    staminaDrain = 0,
                    newStamina = state.stamina
                };
            }

            if (playerMove != "wait")
            {
                Vector2Int step = GetStep(playerMove);
                Vector2Int target = state.dogPos + step;

                // RM-003: Step out of bounds is refused (e.g. into the fence)
                if (!InBounds(target, arena.gridSpan))
                {
                    return new NemesisTurnResult
                    {
                        moveRefused = true,
                        refusalReason = "The fence is there. Nothing on that side.",
                        predictedTile = state.dogPos,
                        interceptMove = state.rexPos,
                        moved = false,
                        newCharge = state.charge,
                        chargeBand = GetChargeBand(state.charge, cfg),
                        spokenLine = null,
                        spokenCategory = null,
                        firingCategories = new List<string>(),
                        dominantDirection = GetDominantDirection(CalculateDirFreq(state.moveHistory, cfg.freq)),
                        staminaDrain = 0,
                        newStamina = state.stamina
                    };
                }

                // Solid pieces: Step onto Rex's tile is refused
                if (target == state.rexPos)
                {
                    return new NemesisTurnResult
                    {
                        moveRefused = true,
                        refusalReason = "REX is on that tile. Go round it.",
                        predictedTile = state.dogPos,
                        interceptMove = state.rexPos,
                        moved = false,
                        newCharge = state.charge,
                        chargeBand = GetChargeBand(state.charge, cfg),
                        spokenLine = null,
                        spokenCategory = null,
                        firingCategories = new List<string>(),
                        dominantDirection = GetDominantDirection(CalculateDirFreq(state.moveHistory, cfg.freq)),
                        staminaDrain = 0,
                        newStamina = state.stamina
                    };
                }

                state.dogPos = target;
            }

            if (state.moveHistory == null) state.moveHistory = new List<string>();
            state.moveHistory.Add(playerMove);

            return ExecuteTurn(state, arena, readTable, cfg);
        }
    }
}
