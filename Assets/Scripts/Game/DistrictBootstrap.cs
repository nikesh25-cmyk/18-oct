using UnityEngine;

namespace AgentDistrict.Game
{
    public static class DistrictBootstrap
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void CreateGame()
        {
            if (Object.FindFirstObjectByType<DistrictGame>() != null) return;
            var root = new GameObject("Agent District Runtime");
            root.AddComponent<DistrictGame>();
        }
    }
}
