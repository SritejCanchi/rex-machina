using System;
using System.Collections.Generic;
using UnityEngine;

namespace RexMachina
{
    /// <summary>
    /// Scene component bridging NemesisTurnLogic to scene actors.
    /// Attached to Rex (boss agent) in BossArena.
    /// </summary>
    public class RexBossAgent : MonoBehaviour
    {
        [Header("Actor References")]
        [SerializeField] private Transform dogTransform;
        [SerializeField] private Transform predictedTileTransform;
        [SerializeField] private NemesisReadTable readTable;

        [Header("Arena Configuration")]
        [SerializeField] private Vector2Int gridSpan = new Vector2Int(10, 10);
        [SerializeField] private List<Vector2Int> coverTiles = new List<Vector2Int> { new Vector2Int(3, 5), new Vector2Int(6, 2) };
        [SerializeField] private List<Vector2Int> exitTiles = new List<Vector2Int> { new Vector2Int(0, 4), new Vector2Int(9, 7) };

        [Header("Configuration")]
        [SerializeField] private NemesisConfig config = new NemesisConfig();

        [Header("Runtime State")]
        [SerializeField] private NemesisTurnState state = new NemesisTurnState();

        private NemesisArenaData arenaData = new NemesisArenaData();

        public Transform DogTransform { get => dogTransform; set => dogTransform = value; }
        public Transform PredictedTileTransform { get => predictedTileTransform; set => predictedTileTransform = value; }
        public NemesisReadTable ReadTable { get => readTable; set => readTable = value; }
        public Vector2Int GridSpan { get => gridSpan; set => gridSpan = value; }
        public List<Vector2Int> CoverTiles { get => coverTiles; set => coverTiles = value; }
        public List<Vector2Int> ExitTiles { get => exitTiles; set => exitTiles = value; }
        public NemesisTurnState State => state;
        public NemesisConfig Config => config;
        public NemesisArenaData ArenaData => arenaData;

        private void Awake()
        {
            SyncArenaData();
            ResetState();
        }

        public void SyncArenaData()
        {
            if (arenaData == null) arenaData = new NemesisArenaData();
            arenaData.gridSpan = gridSpan;
            arenaData.coverTiles = coverTiles != null ? new List<Vector2Int>(coverTiles) : new List<Vector2Int>();
            arenaData.exitTiles = exitTiles != null ? new List<Vector2Int>(exitTiles) : new List<Vector2Int>();
        }

        public void ResetState(Vector2Int? rexStart = null, Vector2Int? dogStart = null)
        {
            SyncArenaData();

            Vector2Int rPos = rexStart.HasValue
                ? rexStart.Value
                : new Vector2Int(Mathf.RoundToInt(transform.position.x), Mathf.RoundToInt(transform.position.y));

            Vector2Int dPos = dogStart.HasValue
                ? dogStart.Value
                : (dogTransform != null
                    ? new Vector2Int(Mathf.RoundToInt(dogTransform.position.x), Mathf.RoundToInt(dogTransform.position.y))
                    : new Vector2Int(4, 6));

            state = new NemesisTurnState
            {
                rexPos = rPos,
                dogPos = dPos,
                charge = config != null ? config.startCharge : 100f,
                stamina = 17,
                round = 0,
                isLimping = false,
                lastCategory = null,
                spokenLines = new List<string>(),
                moveHistory = new List<string>()
            };

            transform.position = new Vector3(state.rexPos.x, state.rexPos.y, transform.position.z);
            if (dogTransform != null)
            {
                dogTransform.position = new Vector3(state.dogPos.x, state.dogPos.y, dogTransform.position.z);
            }
        }

        /// <summary>
        /// Executes a single turn: commits player move, calculates boss intercept & dialogue,
        /// updates actor positions in the scene, and logs structured debug output.
        /// </summary>
        public NemesisTurnResult ExecuteTurn(string playerMove)
        {
            SyncArenaData();
            var result = NemesisTurnLogic.ExecuteTurn(state, arenaData, readTable, config, playerMove);

            if (result.moveRefused)
            {
                return result;
            }

            // Update scene actor positions
            transform.position = new Vector3(state.rexPos.x, state.rexPos.y, transform.position.z);
            if (dogTransform != null)
            {
                dogTransform.position = new Vector3(state.dogPos.x, state.dogPos.y, dogTransform.position.z);
            }
            if (predictedTileTransform != null)
            {
                predictedTileTransform.position = new Vector3(result.predictedTile.x, result.predictedTile.y, predictedTileTransform.position.z);
            }

            // Structured debug log
            if (!string.IsNullOrEmpty(result.spokenLine))
            {
                Debug.Log($"REX: \"{result.spokenLine}\" [Category: {result.spokenCategory}, Band: {result.chargeBand}, Charge: {Mathf.RoundToInt(result.newCharge)}%]");
            }

            return result;
        }
    }
}
