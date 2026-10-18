using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace NemoWorld.Harr
{
    [Serializable] public sealed class WorldAtlasPackage
    {
        public string format;
        public int[] bounds;
        public string source_sha256;
        public WorldAtlasRegion[] regions;
    }

    [Serializable] public sealed class WorldAtlasRegion
    {
        public string world;
        public int x;
        public int y;
        public int width;
        public int height;
    }

    // Read-only landscape preview of the source global map. It never grants land or saves movement.
    public sealed class WorldAtlasPreview : MonoBehaviour
    {
        private const int Columns = 288;
        private const int Rows = 208;
        private readonly Dictionary<int, Material> materials = new Dictionary<int, Material>();
        private readonly List<WorldAtlasRegion> regions = new List<WorldAtlasRegion>();
        private Camera view;
        private string error;
        private float yaw;
        private float pitch = 72f;
        private bool overview = true;

        private void Awake()
        {
            Application.targetFrameRate = 60;
            RenderSettings.skybox = null;
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.72f, 0.75f, 0.82f);
            RenderSettings.fog = false;
            var light = new GameObject("Atlas sunlight").AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.25f;
            light.transform.rotation = Quaternion.Euler(48f, -35f, 0f);
            var cameraObject = new GameObject("Atlas camera");
            view = cameraObject.AddComponent<Camera>();
            view.clearFlags = CameraClearFlags.SolidColor;
            view.backgroundColor = new Color(0.06f, 0.12f, 0.19f);
            view.fieldOfView = 64f;
            view.farClipPlane = 1000f;
            cameraObject.AddComponent<AudioListener>();
            SetOverview();
            try
            {
                var path = Path.Combine(Application.streamingAssetsPath, "NemoWorld", "world-atlas-v1.json");
                var package = JsonUtility.FromJson<WorldAtlasPackage>(File.ReadAllText(path));
                Validate(package);
                Build(package);
            }
            catch (Exception exception)
            {
                error = exception.Message;
                Debug.LogError("World atlas preview could not load: " + exception);
            }
        }

        private static void Validate(WorldAtlasPackage package)
        {
            if (package == null || package.format != "nemoworld-unity-atlas-v1" ||
                package.bounds == null || package.bounds.Length != 2 ||
                package.bounds[0] != Columns || package.bounds[1] != Rows ||
                package.regions == null || package.regions.Length != 23)
                throw new InvalidDataException("Unsupported atlas package");
            var names = new HashSet<string>();
            foreach (var region in package.regions)
            {
                if (region == null || string.IsNullOrEmpty(region.world) || !names.Add(region.world) ||
                    region.x < 0 || region.y < 0 || region.width < 1 || region.height < 1 ||
                    region.x + region.width > Columns || region.y + region.height > Rows)
                    throw new InvalidDataException("Invalid atlas region");
            }
            for (var i = 0; i < package.regions.Length; i++)
                for (var j = i + 1; j < package.regions.Length; j++)
                    if (Overlaps(package.regions[i], package.regions[j]))
                        throw new InvalidDataException("Overlapping atlas regions");
        }

        private static bool Overlaps(WorldAtlasRegion a, WorldAtlasRegion b) =>
            a.x < b.x + b.width && b.x < a.x + a.width &&
            a.y < b.y + b.height && b.y < a.y + a.height;

        private void Build(WorldAtlasPackage package)
        {
            AddBox(transform, "Sea / unallocated map area", new Vector3(0f, -1.8f, 0f),
                new Vector3(Columns + 12f, 2f, Rows + 12f), new Color(0.035f, 0.23f, 0.32f));
            foreach (var region in package.regions)
            {
                regions.Add(region);
                var root = new GameObject(region.world).transform;
                root.SetParent(transform, false);
                var center = new Vector3(region.x + region.width / 2f - Columns / 2f, 0f,
                    region.y + region.height / 2f - Rows / 2f);
                var tone = Tone(region.world);
                AddTerrain(root, region, tone);
                Decorate(root, region, tone);
            }
        }

        private void AddTerrain(Transform root, WorldAtlasRegion region, Color tone)
        {
            var nx = Mathf.Max(1, Mathf.CeilToInt(region.width / 2f));
            var nz = Mathf.Max(1, Mathf.CeilToInt(region.height / 2f));
            var vertices = new Vector3[(nx + 1) * (nz + 1)];
            var uv = new Vector2[vertices.Length];
            var triangles = new int[nx * nz * 6];
            for (var z = 0; z <= nz; z++)
                for (var x = 0; x <= nx; x++)
                {
                    var localX = x * region.width / (float)nx;
                    var localZ = z * region.height / (float)nz;
                    var worldX = region.x + localX - Columns / 2f;
                    var worldZ = region.y + localZ - Rows / 2f;
                    var edge = Mathf.Min(localX, region.width - localX, localZ, region.height - localZ);
                    var relief = Relief(region.world) * Mathf.SmoothStep(0f, 1f, edge / 5f);
                    var height = 0.55f + Mathf.PerlinNoise(worldX * 0.034f + 8f, worldZ * 0.034f + 7f) * 2.15f
                        + Mathf.PerlinNoise(worldX * 0.11f + 19f, worldZ * 0.11f + 23f) * 0.38f + relief;
                    var index = z * (nx + 1) + x;
                    vertices[index] = new Vector3(worldX, height, worldZ);
                    uv[index] = new Vector2(worldX / 6f, worldZ / 6f);
                }
            var t = 0;
            for (var z = 0; z < nz; z++)
                for (var x = 0; x < nx; x++)
                {
                    var a = z * (nx + 1) + x;
                    var b = a + nx + 1;
                    triangles[t++] = a; triangles[t++] = b; triangles[t++] = a + 1;
                    triangles[t++] = a + 1; triangles[t++] = b; triangles[t++] = b + 1;
                }
            var mesh = new Mesh { name = "Generated atlas terrain: " + region.world };
            mesh.vertices = vertices;
            mesh.uv = uv;
            mesh.triangles = triangles;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            var terrain = new GameObject("generated terrain preview");
            terrain.transform.SetParent(root, false);
            terrain.AddComponent<MeshFilter>().sharedMesh = mesh;
            terrain.AddComponent<MeshRenderer>().sharedMaterial = TerrainMaterial(region.world, tone);
        }

        private static float Relief(string name)
        {
            if (name.Contains("highland") || name.Contains("snow")) return 5.5f;
            if (name.Contains("foothill") || name.Contains("forest")) return 2.5f;
            if (name.Contains("desert") || name.Contains("dry")) return 1.2f;
            return 0.4f;
        }

        private Material TerrainMaterial(string biome, Color tone)
        {
            var key = StableHash("terrain:" + biome);
            if (materials.TryGetValue(key, out var cached)) return cached;
            var template = Resources.Load<Material>("PreviewStandard");
            if (template == null) throw new InvalidOperationException("PreviewStandard material unavailable");
            var material = new Material(template);
            var asset = biome.Contains("desert") || biome.Contains("dry") ? "forrest_sand_01" :
                biome.Contains("city") || biome.Contains("workshop") ? "worn_asphalt" :
                biome.Contains("snow") || biome.Contains("highland") ? "concrete_wall_004" : "leafy_grass";
            material.mainTexture = Resources.Load<Texture2D>("Visual/" + asset + "_Diffuse");
            material.SetTexture("_BumpMap", Resources.Load<Texture2D>("Visual/" + asset + "_nor_gl"));
            material.EnableKeyword("_NORMALMAP");
            material.color = Color.Lerp(tone, Color.white, 0.72f);
            material.SetFloat("_Glossiness", 0.18f);
            materials.Add(key, material);
            return material;
        }

        private void Decorate(Transform root, WorldAtlasRegion region, Color tone)
        {
            // Small bounded visual cues only. They are not imported saved buildings or geography.
            var seed = StableHash(region.world);
            var count = region.world == "commons" ? 14 : 8;
            for (var i = 0; i < count; i++)
            {
                var u = ((seed + i * 37) % 997) / 997f;
                var v = ((seed / 7 + i * 71) % 991) / 991f;
                var x = region.x + 3f + u * Mathf.Max(1f, region.width - 6f) - Columns / 2f;
                var z = region.y + 3f + v * Mathf.Max(1f, region.height - 6f) - Rows / 2f;
                var height = 1.5f + ((seed + i * 13) % 4);
                var baseHeight = 0.55f + Mathf.PerlinNoise(x * 0.034f + 8f, z * 0.034f + 7f) * 2.15f
                    + Mathf.PerlinNoise(x * 0.11f + 19f, z * 0.11f + 23f) * 0.38f;
                var ground = baseHeight + Relief(region.world) * 0.7f;
                if (region.world.Contains("city") || region.world.Contains("workshop"))
                    AddBox(root, "generated skyline cue", new Vector3(x, ground + height / 2f, z),
                        new Vector3(1.5f, height, 1.5f), Color.Lerp(tone, Color.white, 0.27f));
                else if (region.world.Contains("highland") || region.world.Contains("snow") || region.world.Contains("desert"))
                    AddShape(root, PrimitiveType.Sphere, "generated rock cue", new Vector3(x, ground + 0.7f, z),
                        new Vector3(2f, 1.4f, 1.5f), Color.Lerp(tone, Color.white, 0.18f));
                else
                {
                    AddShape(root, PrimitiveType.Cylinder, "generated tree trunk", new Vector3(x, ground + height / 2f, z),
                        new Vector3(0.35f, height / 2f, 0.35f), new Color(0.29f, 0.23f, 0.18f));
                    AddShape(root, PrimitiveType.Sphere, "generated tree canopy", new Vector3(x, ground + height + 0.9f, z),
                        new Vector3(2.2f, 2.3f, 2.2f), new Color(0.25f, 0.42f, 0.25f));
                }
            }
        }

        private static int StableHash(string value)
        {
            unchecked
            {
                var hash = 17;
                foreach (var character in value) hash = (hash * 31 + character) & 0x7fffffff;
                return hash;
            }
        }

        private static Color Tone(string name)
        {
            if (name.Contains("snow")) return new Color(0.78f, 0.87f, 0.92f);
            if (name.Contains("desert") || name.Contains("dry")) return new Color(0.78f, 0.60f, 0.38f);
            if (name.Contains("coast") || name.Contains("island") || name.Contains("harbor")) return new Color(0.33f, 0.66f, 0.67f);
            if (name.Contains("highland") || name.Contains("foothill")) return new Color(0.47f, 0.53f, 0.55f);
            if (name.Contains("forest") || name.Contains("woodland")) return new Color(0.24f, 0.48f, 0.34f);
            if (name.Contains("city") || name.Contains("workshop")) return new Color(0.53f, 0.59f, 0.68f);
            return new Color(0.40f, 0.64f, 0.42f);
        }

        private void AddBox(Transform parent, string name, Vector3 position, Vector3 size, Color color)
        {
            AddShape(parent, PrimitiveType.Cube, name, position, size, color);
        }

        private void AddShape(Transform parent, PrimitiveType shape, string name, Vector3 position, Vector3 size, Color color)
        {
            var box = GameObject.CreatePrimitive(shape);
            box.name = name;
            box.transform.SetParent(parent, false);
            box.transform.position = position;
            box.transform.localScale = size;
            box.GetComponent<Renderer>().sharedMaterial = MaterialFor(color);
            Destroy(box.GetComponent<Collider>());
        }

        private Material MaterialFor(Color color)
        {
            var key = ColorUtility.ToHtmlStringRGB(color).GetHashCode();
            if (materials.TryGetValue(key, out var material)) return material;
            var template = Resources.Load<Material>("PreviewStandard");
            if (template == null) throw new InvalidOperationException("PreviewStandard material unavailable");
            material = new Material(template) { color = color };
            materials.Add(key, material);
            return material;
        }

        private void SetOverview()
        {
            overview = true;
            view.transform.position = new Vector3(0f, 200f, -55f);
            view.transform.LookAt(Vector3.zero);
            yaw = view.transform.eulerAngles.y;
            pitch = view.transform.eulerAngles.x;
        }

        private void Update()
        {
            if (view == null) return;
            if (Input.GetKeyDown(KeyCode.Alpha1)) SetOverview();
            if (Input.GetKeyDown(KeyCode.Alpha2))
            {
                overview = false;
                view.transform.position = new Vector3(0f, 8f, -20f);
                pitch = 18f;
                yaw = 0f;
                view.transform.rotation = Quaternion.Euler(pitch, yaw, 0f);
            }
            if (Input.GetKeyDown(KeyCode.H)) SceneManager.LoadScene("HarrPreview");
            var forward = view.transform.forward; forward.y = 0f; forward.Normalize();
            var right = view.transform.right; right.y = 0f; right.Normalize();
            var motion = Vector3.zero;
            if (Input.GetKey(KeyCode.W)) motion += forward;
            if (Input.GetKey(KeyCode.S)) motion -= forward;
            if (Input.GetKey(KeyCode.D)) motion += right;
            if (Input.GetKey(KeyCode.A)) motion -= right;
            if (Input.GetKey(KeyCode.E)) motion += Vector3.up;
            if (Input.GetKey(KeyCode.Q)) motion -= Vector3.up;
            view.transform.position += motion.normalized * (Input.GetKey(KeyCode.LeftShift) ? 90f : 35f) * Time.deltaTime;
            if (Input.GetMouseButton(1))
            {
                yaw += Input.GetAxis("Mouse X") * 2f;
                pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * 2f, -80f, 89f);
                view.transform.rotation = Quaternion.Euler(pitch, yaw, 0f);
            }
        }

        private void OnGUI()
        {
            var width = Mathf.Min(520f, Screen.width - 24f);
            if (width < 240f) return;
            GUI.Box(new Rect(12, 12, width, 112), "");
            var style = new GUIStyle(GUI.skin.label) { fontSize = Mathf.Clamp(Screen.height / 50, 12, 20) };
            style.normal.textColor = Color.white;
            GUI.Label(new Rect(24, 20, width - 28, 27), "NEMOWORLD  /  WORLD ATLAS", style);
            style.fontSize = Mathf.Max(11, style.fontSize - 3);
            GUI.Label(new Rect(24, 49, width - 28, 24),
                error ?? $"{regions.Count} source regions  •  {Columns} × {Rows} finite tiles", style);
            GUI.Label(new Rect(24, 73, width - 28, 24),
                "Generated terrain preview — no saved construction or land grants", style);
            GUI.Label(new Rect(24, 96, width - 28, 22),
                "1 overview  •  2 ground  •  WASD/QE fly  •  H Harr", style);
            if (!overview || view == null) return;
            foreach (var region in regions)
            {
                var center = new Vector3(region.x + region.width / 2f - Columns / 2f, 2f,
                    region.y + region.height / 2f - Rows / 2f);
                var screen = view.WorldToScreenPoint(center);
                if (screen.z < 0 || screen.x < 0 || screen.x > Screen.width ||
                    screen.y < 0 || screen.y > Screen.height) continue;
                GUI.Label(new Rect(screen.x - 55f, Screen.height - screen.y - 8f, 110f, 24f),
                    region.world.Replace("district:", ""), style);
            }
        }

        private void OnDestroy()
        {
            foreach (var material in materials.Values) Destroy(material);
            foreach (var filter in GetComponentsInChildren<MeshFilter>())
                if (filter.sharedMesh != null && filter.sharedMesh.name.StartsWith("Generated atlas terrain:")) Destroy(filter.sharedMesh);
        }
    }
}
