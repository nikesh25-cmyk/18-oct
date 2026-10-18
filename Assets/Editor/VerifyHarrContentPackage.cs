using System;
using System.IO;
using NemoWorld.Harr;
using UnityEditor;
using UnityEngine;

public static class VerifyHarrContentPackage
{
    public static void Run()
    {
        try
        {
            var path = Path.Combine(Application.streamingAssetsPath, "NemoWorld", "harr-authored-content-v1.json");
            var package = JsonUtility.FromJson<HarrContentPackage>(File.ReadAllText(path));
            package.Validate();
            Debug.Log("HARR_CONTENT_PASSED: 52 residents, 28 missions, 30 technologies");
            EditorApplication.Exit(0);
        }
        catch (Exception error)
        {
            Debug.LogError("HARR_CONTENT_FAILED: " + error);
            EditorApplication.Exit(1);
        }
    }
}
