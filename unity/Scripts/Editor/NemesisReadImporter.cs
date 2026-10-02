using System.IO;
using UnityEditor;
using UnityEngine;

namespace RexMachina.EditorTools
{
    // Converts the pipeline's JSON into a ScriptableObject. No hand edits: re-run after a pipeline run.
    public static class NemesisReadImporter
    {
        const string Src = "Assets/RexMachina/Data/DT_NemesisReads.json";
        const string Dst = "Assets/RexMachina/Data/NemesisReads.asset";

        [System.Serializable] class Wrap { public NemesisRead[] rows; }

        [MenuItem("Rex Machina/Import Nemesis Reads")]
        public static void Import()
        {
            var json = File.ReadAllText(Src);
            var wrap = JsonUtility.FromJson<Wrap>("{\"rows\":" + json + "}");
            var table = AssetDatabase.LoadAssetAtPath<NemesisReadTable>(Dst);
            if (table == null)
            {
                table = ScriptableObject.CreateInstance<NemesisReadTable>();
                AssetDatabase.CreateAsset(table, Dst);
            }
            table.rows.Clear();
            table.rows.AddRange(wrap.rows);
            EditorUtility.SetDirty(table);
            AssetDatabase.SaveAssets();
            Debug.Log($"RM | imported {table.rows.Count} nemesis reads into {Dst}");
        }
    }
}
