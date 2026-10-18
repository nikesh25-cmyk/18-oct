using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace NemoWorld.Harr
{
    // M1 migration preview: authored city geometry only. No mission or economy authority lives here.
    public sealed class HarrPreviewGame : MonoBehaviour
    {
        private readonly Dictionary<string, Material> _materials = new Dictionary<string, Material>();
        private readonly HarrArtAssets _artAssets = new HarrArtAssets();
        private Camera _camera;
        private string _error;
        private int _groups;
        private int _blocks;
        private int _sprites;
        private int _clears;
        private int _legacyGroups;
        private HarrContentPackage _content;
        private bool _guideOpen;
        private int _guideTab;
        private int _guideIndex;
        private Vector2 _guideScroll;
        private float _yaw;
        private float _pitch = 13f;

        private void Awake()
        {
            Application.targetFrameRate = 60;
            QualitySettings.antiAliasing = 4;
            QualitySettings.anisotropicFiltering = AnisotropicFiltering.ForceEnable;
            QualitySettings.shadowDistance = 160f;
            RenderSettings.skybox = Resources.Load<Material>("Visual/NightSky");
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.72f, 0.75f, 0.82f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.18f, 0.26f, 0.34f);
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = 0.0025f;
            var sun = new GameObject("Harr night lighting").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1.2f;
            sun.color = new Color(0.83f, 0.88f, 1f);
            sun.shadows = LightShadows.Soft;
            sun.shadowStrength = 0.48f;
            sun.transform.rotation = Quaternion.Euler(55f, -28f, 0f);

            var cameraObject = new GameObject("Harr preview camera");
            _camera = cameraObject.AddComponent<Camera>();
            _camera.clearFlags = CameraClearFlags.Skybox;
            _camera.backgroundColor = new Color(0.035f, 0.05f, 0.12f);
            _camera.fieldOfView = 72f;
            cameraObject.AddComponent<AudioListener>();
            cameraObject.transform.position = new Vector3(0f, 78f, -125f);
            cameraObject.transform.rotation = Quaternion.Euler(_pitch, _yaw, 0f);

            try
            {
                var path = Path.Combine(Application.streamingAssetsPath, "NemoWorld", "harr-city-v1.json");
                var package = JsonUtility.FromJson<HarrCityPackage>(File.ReadAllText(path));
                if (package == null || package.format != "harr-unity-city-v1" || package.groups == null)
                    throw new InvalidDataException("Unsupported or empty Harr city package");
                BuildCity(package);
                var contentPath = Path.Combine(Application.streamingAssetsPath, "NemoWorld", "harr-authored-content-v1.json");
                _content = JsonUtility.FromJson<HarrContentPackage>(File.ReadAllText(contentPath));
                _content.Validate();
            }
            catch (Exception error)
            {
                _error = error.Message;
                Debug.LogError("Harr preview could not load: " + error);
            }
        }

        private void BuildCity(HarrCityPackage package)
        {
            if (package.groups.Length > 600) throw new InvalidDataException("Too many Harr groups");
            var ground = GameObject.CreatePrimitive(PrimitiveType.Cube);
            ground.name = "Harr terrain preview";
            ground.transform.position = new Vector3(0f, -0.6f, 0f);
            ground.transform.localScale = new Vector3(900f, 1f, 900f);
            ground.GetComponent<Renderer>().sharedMaterial = MaterialFor(new[] { 210, 215, 218 }, "asphalt", 110f);
            Destroy(ground.GetComponent<Collider>());

            foreach (var group in package.groups)
            {
                if (string.IsNullOrEmpty(group.id) || group.anchor == null || group.anchor.Length != 2 || group.ops == null)
                    throw new InvalidDataException("Malformed Harr group");
                var root = new GameObject(group.id).transform;
                if (group.provenance == "legacy-saved") _legacyGroups++;
                root.SetParent(transform, false);
                var baseX = group.anchor[0];
                var baseZ = group.anchor[1];
                var baseY = group.ground - package.ground_reference;
                foreach (var op in group.ops)
                {
                    switch (op.op)
                    {
                        case "fill":
                            if (!ValidRange(op, 3)) throw new InvalidDataException("Malformed fill in " + group.id);
                            AddBox(root, "Block", baseX + Mid(op.@from[0], op.to[0]),
                                baseY + Mid(op.@from[2], op.to[2]), baseZ + Mid(op.@from[1], op.to[1]),
                                Extent(op.@from[0], op.to[0]), Extent(op.@from[2], op.to[2]),
                                Extent(op.@from[1], op.to[1]), op.rgb, SurfaceFor(group.id));
                            _blocks++;
                            break;
                        case "foundation":
                            if (!ValidRange(op, 2) || op.depth < 1 || op.depth > 64)
                                throw new InvalidDataException("Malformed foundation in " + group.id);
                            AddBox(root, "Foundation", baseX + Mid(op.@from[0], op.to[0]),
                                baseY - op.depth / 2f, baseZ + Mid(op.@from[1], op.to[1]),
                                Extent(op.@from[0], op.to[0]), op.depth,
                                Extent(op.@from[1], op.to[1]), op.rgb, SurfaceFor(group.id));
                            _blocks++;
                            break;
                        case "sprite":
                            if (op.at == null || op.at.Length != 3) throw new InvalidDataException("Malformed sprite in " + group.id);
                            AddProp(root, op.sprite, baseX + op.at[0], baseY + op.at[2], baseZ + op.at[1]);
                            _sprites++;
                            break;
                        case "clear":
                            _clears++;
                            break;
                        default:
                            throw new InvalidDataException("Unsupported op in " + group.id);
                    }
                }
                _artAssets.DressSavedBuilding(root, group.id, baseX, baseY, baseZ);
                _groups++;
            }
        }

        private static bool ValidRange(HarrOp op, int dimensions)
        {
            if (op.@from == null || op.to == null || op.@from.Length != dimensions || op.to.Length != dimensions)
                return false;
            for (var i = 0; i < dimensions; i++) if (op.to[i] < op.@from[i]) return false;
            return true;
        }

        private static float Mid(int a, int b) { return (a + b) / 2f; }
        private static float Extent(int a, int b) { return b - a + 1f; }

        private static string SurfaceFor(string id)
        {
            if (id.Contains("path") || id.Contains("road") || id.Contains("plaza") || id.Contains("transit")) return "asphalt";
            if (id.Contains("solar") || id.Contains("archive") || id.Contains("tower")) return "metal";
            return "concrete";
        }

        private void AddBox(Transform parent, string name, float x, float y, float z,
            float sx, float sy, float sz, int[] rgb, string surface)
        {
            var block = GameObject.CreatePrimitive(PrimitiveType.Cube);
            block.name = name;
            block.transform.SetParent(parent, false);
            block.transform.position = new Vector3(x, y, z);
            block.transform.localScale = new Vector3(sx, sy, sz);
            block.GetComponent<Renderer>().sharedMaterial = MaterialFor(rgb, surface, Mathf.Clamp(Mathf.Max(sx, sz) / 5f, 1f, 8f));
            Destroy(block.GetComponent<Collider>());
        }

        private Material MaterialFor(int[] rgb, string surface, float tiling = 2f)
        {
            if (rgb == null || rgb.Length != 3) rgb = new[] { 90, 100, 120 };
            tiling = Mathf.Round(tiling);
            var key = surface + ":" + rgb[0] + ":" + rgb[1] + ":" + rgb[2] + ":" + tiling;
            if (_materials.TryGetValue(key, out var cached)) return cached;
            var template = Resources.Load<Material>("PreviewStandard");
            if (template == null) throw new InvalidOperationException("PreviewStandard material unavailable");
            var material = new Material(template);
            var source = new Color(rgb[0] / 255f, rgb[1] / 255f, rgb[2] / 255f);
            material.color = Color.Lerp(source, Color.white, surface == "concrete" ? 0.56f : 0.38f);
            var asset = surface == "asphalt" ? "worn_asphalt" : surface == "metal" ? "blue_metal_plate" : "concrete_wall_004";
            material.mainTexture = Resources.Load<Texture2D>("Visual/" + asset + "_Diffuse");
            material.SetTexture("_BumpMap", Resources.Load<Texture2D>("Visual/" + asset + "_nor_gl"));
            material.EnableKeyword("_NORMALMAP");
            material.mainTextureScale = new Vector2(tiling, tiling);
            material.SetTextureScale("_BumpMap", new Vector2(tiling, tiling));
            material.SetFloat("_Metallic", surface == "metal" ? 0.65f : 0.03f);
            material.SetFloat("_Glossiness", surface == "metal" ? 0.68f : 0.30f);
            material.enableInstancing = true;
            _materials.Add(key, material);
            return material;
        }

        private void AddProp(Transform parent, string sprite, float x, float y, float z)
        {
            // Source sprites have only a name and saved position. These are visual interpretations.
            var root = new GameObject("Visual proxy: " + sprite).transform;
            root.SetParent(parent, false);
            root.position = new Vector3(x, y, z);
            if (sprite == "StreetLamp" && AddStreetLampModel(root, y)) return;
            if (sprite == "BenchWoodWoodland" && _artAssets.PlaceProp(root, "painted_wooden_bench", 1.7f)) return;
            if ((sprite == "CrateBlock" || sprite.StartsWith("CarpenterCrate")) &&
                _artAssets.PlaceProp(root, "wooden_crate_01", 0.85f)) return;
            if ((sprite == "Planter" || sprite.StartsWith("Flowerpot")) &&
                _artAssets.PlaceProp(root, "planter_pot_clay", 0.72f))
            {
                AddProxy(root, PrimitiveType.Sphere, "foliage preview", new Vector3(0f, 0.85f, 0f),
                    new Vector3(0.85f, 0.9f, 0.85f), new[] { 50, 128, 75 }, "concrete");
                return;
            }
            if (sprite.Contains("Lamp") || sprite.Contains("Lantern") || sprite == "Candle")
            {
                var height = sprite == "Candle" ? 0.55f : 2.6f;
                AddProxy(root, PrimitiveType.Cylinder, "fixture", new Vector3(0f, height / 2f, 0f),
                    new Vector3(0.09f, height / 2f, 0.09f), new[] { 165, 154, 128 }, "metal");
                var bulb = AddProxy(root, PrimitiveType.Sphere, "warm glass", new Vector3(0f, height, 0f),
                    Vector3.one * (sprite == "Candle" ? 0.18f : 0.38f), new[] { 255, 207, 112 }, "metal");
                bulb.GetComponent<Renderer>().sharedMaterial = GlowMaterial();
            }
            else if (sprite.Contains("Planter") || sprite.Contains("Flowerpot"))
            {
                AddProxy(root, PrimitiveType.Cylinder, "planter", new Vector3(0f, 0.28f, 0f),
                    new Vector3(0.38f, 0.28f, 0.38f), new[] { 164, 122, 91 }, "concrete");
                AddProxy(root, PrimitiveType.Sphere, "foliage", new Vector3(0f, 0.85f, 0f),
                    new Vector3(0.85f, 0.9f, 0.85f), new[] { 50, 128, 75 }, "concrete");
            }
            else
            {
                AddProxy(root, PrimitiveType.Cube, "unmapped source prop", new Vector3(0f, 0.38f, 0f),
                    new Vector3(0.65f, 0.75f, 0.65f), new[] { 124, 161, 176 }, "metal");
            }
        }

        private bool AddStreetLampModel(Transform root, float groundY)
        {
            var source = Resources.Load<GameObject>("Visual/Models/street_lamp_01_1k");
            if (source == null) return false;
            var model = Instantiate(source, root);
            model.name = "Poly Haven CC0 street lamp";
            var renderers = model.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return false;
            var bounds = renderers[0].bounds;
            foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
            var scale = 3.1f / Mathf.Max(0.1f, bounds.size.y);
            model.transform.localScale *= scale;
            foreach (var renderer in renderers) renderer.sharedMaterial = StreetLampMaterial();
            bounds = renderers[0].bounds;
            foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
            model.transform.position += Vector3.up * (groundY - bounds.min.y);
            if (_sprites % 16 == 0)
            {
                var glow = new GameObject("Lamp light").AddComponent<Light>();
                glow.transform.SetParent(root, false);
                glow.transform.localPosition = new Vector3(0f, 2.6f, 0f);
                glow.type = LightType.Point;
                glow.color = new Color(1f, 0.73f, 0.40f);
                glow.range = 7f;
                glow.intensity = 1.6f;
            }
            return true;
        }

        private Material StreetLampMaterial()
        {
            const string key = "polyhaven-street-lamp";
            if (_materials.TryGetValue(key, out var cached)) return cached;
            var material = new Material(Resources.Load<Material>("PreviewStandard"));
            material.mainTexture = Resources.Load<Texture2D>("Visual/Models/textures/street_lamp_01_diff_1k");
            material.SetTexture("_BumpMap", Resources.Load<Texture2D>("Visual/Models/textures/street_lamp_01_nor_gl_1k"));
            material.EnableKeyword("_NORMALMAP");
            material.SetFloat("_Metallic", 0.72f);
            material.SetFloat("_Glossiness", 0.38f);
            material.enableInstancing = true;
            _materials.Add(key, material);
            return material;
        }

        private GameObject AddProxy(Transform parent, PrimitiveType shape, string name, Vector3 offset,
            Vector3 size, int[] rgb, string surface)
        {
            var obj = GameObject.CreatePrimitive(shape);
            obj.name = name;
            obj.transform.SetParent(parent, false);
            obj.transform.localPosition = offset;
            obj.transform.localScale = size;
            obj.GetComponent<Renderer>().sharedMaterial = MaterialFor(rgb, surface);
            Destroy(obj.GetComponent<Collider>());
            return obj;
        }

        private Material GlowMaterial()
        {
            const string key = "glow";
            if (_materials.TryGetValue(key, out var cached)) return cached;
            var material = new Material(Resources.Load<Material>("PreviewStandard"));
            material.color = new Color(1f, 0.74f, 0.37f);
            material.EnableKeyword("_EMISSION");
            material.SetColor("_EmissionColor", new Color(1.8f, 1.05f, 0.35f));
            _materials.Add(key, material);
            return material;
        }

        private void Update()
        {
            if (_camera == null) return;
            if (Input.GetKeyDown(KeyCode.M)) SceneManager.LoadScene("WorldAtlas");
            if (Input.GetKeyDown(KeyCode.Tab)) _guideOpen = !_guideOpen;
            if (Input.GetKeyDown(KeyCode.Escape)) _guideOpen = false;
            var forward = _camera.transform.forward;
            forward.y = 0f;
            forward.Normalize();
            var right = _camera.transform.right;
            right.y = 0f;
            right.Normalize();
            var motion = Vector3.zero;
            if (Input.GetKey(KeyCode.W)) motion += forward;
            if (Input.GetKey(KeyCode.S)) motion -= forward;
            if (Input.GetKey(KeyCode.D)) motion += right;
            if (Input.GetKey(KeyCode.A)) motion -= right;
            if (Input.GetKey(KeyCode.E)) motion += Vector3.up;
            if (Input.GetKey(KeyCode.Q)) motion -= Vector3.up;
            _camera.transform.position += motion.normalized * (Input.GetKey(KeyCode.LeftShift) ? 35f : 14f) * Time.deltaTime;
            if (Input.GetMouseButton(1))
            {
                _yaw += Input.GetAxis("Mouse X") * 3f;
                _pitch = Mathf.Clamp(_pitch - Input.GetAxis("Mouse Y") * 3f, -80f, 80f);
                _camera.transform.rotation = Quaternion.Euler(_pitch, _yaw, 0f);
            }
        }

        private void OnGUI()
        {
            var width = Mathf.Min(450f, Screen.width - 24f);
            if (width < 200f) return;
            var panel = new Rect(12f, 12f, width, 126f);
            GUI.Box(panel, "");
            var style = new GUIStyle(GUI.skin.label);
            style.fontSize = Mathf.Clamp(Mathf.RoundToInt(Screen.height / 45f), 12, 20);
            style.normal.textColor = Color.white;
            GUI.Label(new Rect(24f, 20f, width - 24f, 30f), "HARR — UNITY MIGRATION PREVIEW", style);
            style.fontSize = Mathf.Clamp(style.fontSize - 3, 11, 17);
            GUI.Label(new Rect(24f, 52f, width - 24f, 25f),
                _error == null ? $"{_groups} authored groups  •  {_blocks} structures  •  {_sprites} prop placeholders" : _error, style);
            GUI.Label(new Rect(24f, 78f, width - 24f, 25f),
                $"{_legacyGroups} saved groups recovered from earlier Harr manifest", style);
            GUI.Label(new Rect(24f, 101f, width - 24f, 22f),
                "WASD/QE fly  •  right mouse look  •  Tab guide  •  M atlas", style);
            if (_guideOpen && _content != null) DrawGuide();
        }

        private void DrawGuide()
        {
            var width = Mathf.Min(560f, Screen.width - 24f);
            var height = Mathf.Min(720f, Screen.height - 160f);
            if (width < 280f || height < 250f) return;
            var panel = new Rect(Screen.width - width - 12f, 12f, width, height);
            GUI.Box(panel, "");
            var title = new GUIStyle(GUI.skin.label) { fontSize = 20, fontStyle = FontStyle.Bold };
            title.normal.textColor = Color.white;
            GUI.Label(new Rect(panel.x + 16f, panel.y + 12f, width - 72f, 28f), "HARR  /  SOURCE GUIDE", title);
            if (GUI.Button(new Rect(panel.x + width - 43f, panel.y + 10f, 30f, 28f), "×")) _guideOpen = false;

            var tabs = new[] { "Residents (52)", "Missions (28)", "Research (30)" };
            for (var i = 0; i < tabs.Length; i++)
                if (GUI.Button(new Rect(panel.x + 12f + i * (width - 24f) / 3f,
                    panel.y + 51f, (width - 24f) / 3f, 31f), tabs[i]))
                {
                    _guideTab = i;
                    _guideIndex = 0;
                    _guideScroll = Vector2.zero;
                }

            var listY = panel.y + 95f;
            var listHeight = Mathf.Min(220f, height * 0.32f);
            var total = _guideTab == 0 ? _content.residents.Length :
                _guideTab == 1 ? _content.missions.Length : _content.techs.Length;
            var view = new Rect(panel.x + 12f, listY, width - 24f, listHeight);
            _guideScroll = GUI.BeginScrollView(view, _guideScroll,
                new Rect(0f, 0f, width - 46f, total * 30f));
            for (var i = 0; i < total; i++)
            {
                var label = _guideTab == 0 ? _content.residents[i].name :
                    _guideTab == 1 ? _content.missions[i].content.title : _content.techs[i].name;
                if (GUI.Button(new Rect(0f, i * 30f, width - 50f, 27f),
                    (i == _guideIndex ? "●  " : "   ") + label)) _guideIndex = i;
            }
            GUI.EndScrollView();

            var detail = new GUIStyle(GUI.skin.label) { fontSize = 14, wordWrap = true };
            detail.normal.textColor = Color.white;
            var detailY = listY + listHeight + 12f;
            var text = GuideDetail();
            GUI.Label(new Rect(panel.x + 16f, detailY, width - 32f, height - (detailY - panel.y) - 47f),
                text, detail);
            var foot = new GUIStyle(GUI.skin.label) { fontSize = 12, wordWrap = true };
            foot.normal.textColor = new Color(0.75f, 0.87f, 0.95f);
            GUI.Label(new Rect(panel.x + 16f, panel.y + height - 39f, width - 32f, 33f),
                "Authored definitions only. No simulated presence, mission progress or research unlocks.", foot);
        }

        private string GuideDetail()
        {
            if (_guideTab == 0)
            {
                var resident = _content.residents[_guideIndex];
                return resident.name + "  /  " + resident.role + "  /  " + resident.id +
                    "\n\n" + resident.capabilities + "\n\nLimitations: " + resident.limitations;
            }
            if (_guideTab == 1)
            {
                var mission = _content.missions[_guideIndex];
                var item = mission.content;
                var text = item.title + "  /  " + mission.source + "  /  " + item.id +
                    "\nPrinciple: " + item.principle + "\n\n" +
                    (!string.IsNullOrEmpty(item.purpose) ? item.purpose : item.blurb);
                if (!string.IsNullOrEmpty(item.how)) text += "\n\n" + item.how;
                if (item.steps != null)
                    foreach (var step in item.steps)
                        text += "\n• " + (string.IsNullOrEmpty(step.label) ? step.kind : step.label) +
                            " (" + step.count + ")";
                return text;
            }
            var tech = _content.techs[_guideIndex];
            return tech.name + "  /  " + tech.id + "\nInsight cost: " + tech.cost +
                "\nPrerequisites: " + (tech.needs == null || tech.needs.Length == 0 ? "none" : string.Join(", ", tech.needs)) +
                "\n\n" + tech.text;
        }

        private void OnDestroy()
        {
            _artAssets.Dispose();
            foreach (var material in _materials.Values) Destroy(material);
        }
    }
}
