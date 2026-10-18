using UnityEngine;
using UnityEngine.SceneManagement;

namespace NemoWorld.Harr
{
    // Handles both editor entry and travel between the two read-only preview scenes.
    public static class PreviewSceneRouter
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Register()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void AfterFirstScene() => Ensure(SceneManager.GetActiveScene().name);

        private static void OnSceneLoaded(Scene scene, LoadSceneMode mode) => Ensure(scene.name);

        private static void Ensure(string sceneName)
        {
            if (sceneName == "HarrPreview" && Object.FindFirstObjectByType<HarrPreviewGame>() == null)
                new GameObject("Harr Unity Migration Preview").AddComponent<HarrPreviewGame>();
            if (sceneName == "WorldAtlas" && Object.FindFirstObjectByType<WorldAtlasPreview>() == null)
                new GameObject("NemoWorld Atlas Preview").AddComponent<WorldAtlasPreview>();
        }
    }
}
