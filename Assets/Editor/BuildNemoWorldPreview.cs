using System;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class BuildNemoWorldPreview
{
    public static void Run()
    {
        var output = Environment.GetEnvironmentVariable("NEMOWORLD_PREVIEW_OUTPUT");
        if (string.IsNullOrWhiteSpace(output)) output = "Builds/NemoWorld Preview.app";
        PlayerSettings.companyName = "NemoWorld";
        PlayerSettings.productName = "NemoWorld Preview";
        PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Standalone, "org.nemoworld.preview");
        ConfigureVisualAssets.Prepare();
        var scenes = new[] { "Assets/Scenes/HarrPreview.unity", "Assets/Scenes/WorldAtlas.unity" };
        var report = BuildPipeline.BuildPlayer(scenes, output, BuildTarget.StandaloneOSX,
            BuildOptions.Development);
        if (report.summary.result != BuildResult.Succeeded)
        {
            Debug.LogError("NEMOWORLD_PREVIEW_BUILD_FAILED: " + report.summary.result);
            EditorApplication.Exit(1);
            return;
        }
        Debug.Log("NEMOWORLD_PREVIEW_BUILD_PASSED: " + output);
        EditorApplication.Exit(0);
    }
}
