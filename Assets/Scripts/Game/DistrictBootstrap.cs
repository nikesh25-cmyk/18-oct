using UnityEngine;
using UnityEngine.SceneManagement;

namespace AgentDistrict.Game
{
    public static class DistrictBootstrap
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void CreateGame()
        {
            if (SceneManager.GetActiveScene().name != "Main") return;
            if (Object.FindFirstObjectByType<DistrictGame>() != null) return;
            var root = new GameObject("Agent District Runtime");
            root.AddComponent<DistrictGame>();
        }
    }
}
