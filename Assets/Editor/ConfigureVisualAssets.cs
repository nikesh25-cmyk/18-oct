using UnityEditor;
using UnityEngine;

public static class ConfigureVisualAssets
{
    private const string Root = "Assets/Resources/Visual/";

    public static void Prepare()
    {
        foreach (var name in new[] { "worn_asphalt", "concrete_wall_004", "blue_metal_plate", "leafy_grass", "forrest_sand_01" })
        {
            ConfigureTexture(Root + name + "_Diffuse.jpg", false);
            ConfigureTexture(Root + name + "_nor_gl.jpg", true);
        }
        ConfigureTexture(Root + "rooftop_night_hdri.hdr", false);
        ConfigureTexture(Root + "Models/textures/street_lamp_01_diff_1k.jpg", false);
        ConfigureTexture(Root + "Models/textures/street_lamp_01_nor_gl_1k.exr", true);
        foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Root + "Models/textures" }))
        {
            var path = AssetDatabase.GUIDToAssetPath(guid);
            if (path.Contains("_nor_gl_1k.")) ConfigureTexture(path, true);
        }
        var skyPath = Root + "NightSky.mat";
        var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
        if (sky == null)
        {
            sky = new Material(Shader.Find("Skybox/Panoramic"));
            AssetDatabase.CreateAsset(sky, skyPath);
        }
        sky.SetTexture("_MainTex", AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "rooftop_night_hdri.hdr"));
        sky.SetFloat("_Exposure", 0.85f);
        sky.SetFloat("_Rotation", 115f);
        EditorUtility.SetDirty(sky);
        AssetDatabase.SaveAssets();
    }

    private static void ConfigureTexture(string path, bool normal)
    {
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null) throw new System.InvalidOperationException("Missing visual asset: " + path);
        var wanted = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
        if (importer.textureType == wanted && importer.wrapMode == TextureWrapMode.Repeat) return;
        importer.textureType = wanted;
        importer.wrapMode = TextureWrapMode.Repeat;
        importer.SaveAndReimport();
    }
}
