using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace NemoWorld.Harr
{
    // M1 migration preview: authored city geometry only. No mission or economy authority lives here.
    public sealed class HarrPreviewGame : MonoBehaviour
    {
        private readonly Dictionary<int, Material> _materials = new Dictionary<int, Material>();
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
        private float _pitch = 17f;

        private void Awake()
        {
            Application.targetFrameRate = 60;
            RenderSettings.ambientLight = new Color(0.52f, 0.6f, 0.78f);
            var sun = new GameObject("Harr night lighting").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1.35f;
            sun.color = new Color(0.65f, 0.8f, 1f);
            sun.transform.rotation = Quaternion.Euler(55f, -28f, 0f);

            var cameraObject = new GameObject("Harr preview camera");
            _camera = cameraObject.AddComponent<Camera>();
            _camera.clearFlags = CameraClearFlags.SolidColor;
            _camera.backgroundColor = new Color(0.035f, 0.05f, 0.12f);
            _camera.fieldOfView = 72f;
            cameraObject.AddComponent<AudioListener>();
            cameraObject.transform.position = new Vector3(0f, 17f, -35f);
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
            ground.GetComponent<Renderer>().sharedMaterial = MaterialFor(new[] { 38, 48, 71 });
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
                                Extent(op.@from[1], op.to[1]), op.rgb);
                            _blocks++;
                            break;
                        case "foundation":
                            if (!ValidRange(op, 2) || op.depth < 1 || op.depth > 64)
                                throw new InvalidDataException("Malformed foundation in " + group.id);
                            AddBox(root, "Foundation", baseX + Mid(op.@from[0], op.to[0]),
                                baseY - op.depth / 2f, baseZ + Mid(op.@from[1], op.to[1]),
                                Extent(op.@from[0], op.to[0]), op.depth,
                                Extent(op.@from[1], op.to[1]), op.rgb);
                            _blocks++;
                            break;
                        case "sprite":
                            if (op.at == null || op.at.Length != 3) throw new InvalidDataException("Malformed sprite in " + group.id);
                            AddBox(root, "Sprite placeholder: " + op.sprite,
                                baseX + op.at[0], baseY + op.at[2] + 0.4f, baseZ + op.at[1],
                                0.65f, 0.8f, 0.65f, new[] { 35, 207, 225 });
                            _sprites++;
                            break;
                        case "clear":
                            _clears++;
                            break;
                        default:
                            throw new InvalidDataException("Unsupported op in " + group.id);
                    }
                }
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

        private void AddBox(Transform parent, string name, float x, float y, float z,
            float sx, float sy, float sz, int[] rgb)
        {
            var block = GameObject.CreatePrimitive(PrimitiveType.Cube);
            block.name = name;
            block.transform.SetParent(parent, false);
            block.transform.position = new Vector3(x, y, z);
            block.transform.localScale = new Vector3(sx, sy, sz);
            block.GetComponent<Renderer>().sharedMaterial = MaterialFor(rgb);
            Destroy(block.GetComponent<Collider>());
        }

        private Material MaterialFor(int[] rgb)
        {
            if (rgb == null || rgb.Length != 3) rgb = new[] { 90, 100, 120 };
            var key = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2];
            if (_materials.TryGetValue(key, out var cached)) return cached;
            var template = Resources.Load<Material>("PreviewStandard");
            if (template == null) throw new InvalidOperationException("PreviewStandard material unavailable");
            var material = new Material(template);
            material.color = new Color(rgb[0] / 255f, rgb[1] / 255f, rgb[2] / 255f);
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
            foreach (var material in _materials.Values) Destroy(material);
        }
    }
}
