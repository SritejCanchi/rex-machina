using System;
using System.Collections.Generic;
using UnityEngine;

namespace RexMachina
{
    // One row of DT_NemesisReads.json, the same contract the browser and Unreal builds read.
    [Serializable]
    public class NemesisRead
    {
        public string ReadID;
        public string ReadCategory;
        public string ChargeBand;
        public string Line;
        public int WordCount;
        public string ObservableCited;
        public string TriggerCondition;
        public string Provenance;
    }

    [CreateAssetMenu(menuName = "Rex Machina/Nemesis Read Table")]
    public class NemesisReadTable : ScriptableObject
    {
        public List<NemesisRead> rows = new List<NemesisRead>();

        public NemesisRead Pick(string category, string band)
        {
            return rows.Find(r => r.ReadCategory == category && r.ChargeBand == band);
        }
    }
}
