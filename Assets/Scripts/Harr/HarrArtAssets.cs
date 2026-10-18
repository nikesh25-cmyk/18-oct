using System;
using System.Collections.Generic;
using UnityEngine;

namespace NemoWorld.Harr
{
    // Visual interpretation of saved Harr positions. These models never write world state.
    public sealed class HarrArtAssets : IDisposable
    {
        private readonly Dictionary<string, GameObject> _sources = new Dictionary<string, GameObject>();
        private readonly Dictionary<string, Material> _materials = new Dictionary<string, Material>();

        public bool PlaceProp(Transform parent, string asset, float width)
        {
            var source = Source(asset);
            if (source == null) return false;
            var model = UnityEngine.Object.Instantiate(source, parent);
            model.name = "CC0 Poly Haven: " + asset;
            model.transform.localPosition = Vector3.zero;
            foreach (var renderer in model.GetComponentsInChildren<Renderer>())
                renderer.sharedMaterial = MaterialFor(asset);
            var bounds = BoundsOf(model);
            if (bounds.size.x < 0.001f) { UnityEngine.Object.Destroy(model); return false; }
            model.transform.localScale *= width / bounds.size.x;
            bounds = BoundsOf(model);
            model.transform.position += new Vector3(parent.position.x - bounds.center.x,
                parent.position.y - bounds.min.y, parent.position.z - bounds.center.z);
            return true;
        }

        public void DressSavedBuilding(Transform parent, string id, float x, float groundY, float z)
        {
            string pack;
            int width;
            if (id == "workshop-hall-3") { pack = "modular_factory_facade"; width = 11; }
            else if (id == "market-hall-3") { pack = "modular_urban_apartments_facade"; width = 11; }
            else if (id == "library-annex-3") { pack = "modular_urban_apartments_facade"; width = 8; }
            else if (id == "data-archive-3") { pack = "modular_urban_apartments_facade"; width = 13; }
            else if (id == "schoolhouse-3" || id == "guesthouse-3")
            { pack = "modular_urban_apartments_facade"; width = 9; }
            else if (id.StartsWith("city-home-") && id.EndsWith("-shell"))
            { pack = "modular_urban_apartments_facade"; width = 11; }
            else return;

            var source = Source(pack);
            if (source == null) return;
            var panels = Mathf.Clamp(Mathf.RoundToInt(width / 3f), 2, 4);
            var spacing = width / (float)panels;
            for (var index = 0; index < panels; index++)
            {
                var door = index == panels / 2;
                var wall = door ? "wall_door_centered_large_01" : "wall_window_centered_large_01";
                var inset = door ? "door_centered_large_01" : "window_centered_large_01";
                var center = new Vector3(x + (index + 0.5f) * spacing - 0.5f,
                    groundY + 2.5f, z - 0.58f);
                PlaceModulePair(parent, source, wall, inset, center, spacing / 3f);
            }
        }

        private void PlaceModulePair(Transform parent, GameObject source, string wallName,
            string detailName, Vector3 center, float widthScale)
        {
            var wall = Find(source, wallName);
            var detail = Find(source, detailName);
            if (wall == null || detail == null) return;
            var root = new GameObject("CC0 modular facade: " + wallName).transform;
            root.SetParent(parent, false);
            root.position = center;
            AddPart(root, wall, widthScale);
            AddPart(root, detail, widthScale);
            var bounds = BoundsOf(root.gameObject);
            root.position += center - bounds.center;
        }

        private void AddPart(Transform parent, MeshFilter source, float widthScale)
        {
            var item = new GameObject(source.name);
            item.transform.SetParent(parent, false);
            item.transform.localRotation = source.transform.localRotation;
            var scale = source.transform.localScale;
            scale.x *= widthScale;
            item.transform.localScale = scale;
            item.AddComponent<MeshFilter>().sharedMesh = source.sharedMesh;
            var renderer = item.AddComponent<MeshRenderer>();
            var sourceRenderer = source.GetComponent<MeshRenderer>();
            var sourceMaterials = sourceRenderer.sharedMaterials;
            var targetMaterials = new Material[sourceMaterials.Length];
            for (var i = 0; i < sourceMaterials.Length; i++)
                targetMaterials[i] = MaterialFor(sourceMaterials[i].name);
            renderer.sharedMaterials = targetMaterials;
        }

        private static MeshFilter Find(GameObject source, string name)
        {
            foreach (var filter in source.GetComponentsInChildren<MeshFilter>(true))
                if (filter.name == name) return filter;
            return null;
        }

        private GameObject Source(string name)
        {
            if (_sources.TryGetValue(name, out var cached)) return cached;
            var source = Resources.Load<GameObject>("Visual/Models/" + name + "_1k");
            _sources[name] = source;
            return source;
        }

        private Material MaterialFor(string sourceName)
        {
            if (_materials.TryGetValue(sourceName, out var cached)) return cached;
            var template = Resources.Load<Material>("PreviewStandard");
            if (template == null) throw new InvalidOperationException("PreviewStandard material unavailable");
            var material = new Material(template);
            var textureName = sourceName.Replace("_brick_doors", "_doors")
                .Replace("_windows_glass", "_windows");
            material.mainTexture = Resources.Load<Texture2D>("Visual/Models/textures/" + textureName + "_diff_1k");
            var normal = Resources.Load<Texture2D>("Visual/Models/textures/" + textureName + "_nor_gl_1k");
            if (normal != null)
            {
                material.SetTexture("_BumpMap", normal);
                material.EnableKeyword("_NORMALMAP");
            }
            material.enableInstancing = true;
            _materials[sourceName] = material;
            return material;
        }

        private static Bounds BoundsOf(GameObject root)
        {
            var renderers = root.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return new Bounds(root.transform.position, Vector3.zero);
            var bounds = renderers[0].bounds;
            for (var i = 1; i < renderers.Length; i++) bounds.Encapsulate(renderers[i].bounds);
            return bounds;
        }

        public void Dispose()
        {
            foreach (var material in _materials.Values) UnityEngine.Object.Destroy(material);
            _materials.Clear();
        }
    }
}
