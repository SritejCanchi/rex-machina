// Run inside the Unity Editor (Unity MCP RunCommand, or any editor script runner).
// Replays unity/parity/sequences.json through the C# port and writes cs_trace.json
// in game.js coordinates. Then: python unity/parity/compare.py
using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.IO;
using System.Text;
using RexMachina;

internal class CommandScript : IRunCommand
{
    // game.js uses screen coordinates (up = y-1); the C# port uses Unity's (up = y+1).
    static Vector2Int M(int x, int y) { return new Vector2Int(x, 9 - y); }
    static string P(Vector2Int v) { return "[" + v.x + "," + (9 - v.y) + "]"; }
    static string Q(string s) { return s == null ? "null" : "\"" + s.Replace("\"", "\\\"") + "\""; }

    public void Execute(ExecutionResult result)
    {
        const string dir = "D:/Side Projects/AI Game Dev Course/rex-machina/unity/parity/";
        var seqJson = File.ReadAllText(dir + "sequences.json");
        var table = AssetDatabase.LoadAssetAtPath<NemesisReadTable>("Assets/RexMachina/Data/NemesisReads.asset");
        var sb = new StringBuilder("{");
        bool firstSeq = true;
        foreach (var name in new[] { "run_right_then_down", "zigzag_cycle", "fence_bumps", "seeded_random" })
        {
            int a = seqJson.IndexOf("\"" + name + "\""); int b = seqJson.IndexOf('[', a); int c = seqJson.IndexOf(']', b);
            var moves = new List<string>();
            foreach (var part in seqJson.Substring(b + 1, c - b - 1).Split(','))
            { var t = part.Trim().Trim('"'); if (t.Length > 0) moves.Add(t); }
            // the canonical opening game.js uses headless: dog [0,0], Rex [5,5], yard phase
            var st = new NemesisTurnState { dogPos = M(0, 0), rexPos = M(5, 5), charge = 100f, stamina = 17 };
            var arena = new NemesisArenaData
            {
                gridSpan = new Vector2Int(10, 10),
                exitTiles = new List<Vector2Int> { M(0, 4), M(9, 7) },
                coverTiles = new List<Vector2Int> { M(3, 5), M(6, 2) }
            };
            var cfg = new NemesisConfig();
            if (!firstSeq) sb.Append(","); firstSeq = false;
            sb.Append("\"" + name + "\":[");
            Vector2Int? lastPred = null;
            for (int i = 0; i < moves.Count; i++)
            {
                var r = NemesisTurnLogic.ExecuteTurn(st, arena, table, cfg, moves[i]);
                bool refused = r.moveRefused;
                string pred = refused ? (lastPred.HasValue ? P(lastPred.Value) : "null") : P(r.predictedTile);
                if (!refused) lastPred = r.predictedTile;
                if (i > 0) sb.Append(",");
                sb.Append("{\"move\":" + Q(moves[i]) + ",\"dog\":" + P(st.dogPos) + ",\"rex\":" + P(st.rexPos) +
                          ",\"predicted\":" + pred + ",\"charge\":" + st.charge +
                          ",\"stamina\":" + st.stamina + ",\"line\":" + Q(refused ? null : r.spokenLine) + "}");
            }
            sb.Append("]");
        }
        sb.Append("}");
        File.WriteAllText(dir + "cs_trace.json", sb.ToString());
        result.Log("wrote cs_trace.json");
    }
}
