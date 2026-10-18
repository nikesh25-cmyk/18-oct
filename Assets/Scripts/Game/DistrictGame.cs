using System;
using AgentDistrict.Core;
using UnityEngine;

namespace AgentDistrict.Game
{
    // Temporary all-in-one scene builder. The scene and mock job are playable without assets or keys.
    public sealed class DistrictGame : MonoBehaviour
    {
        private readonly ResearchJob _job = new ResearchJob();
        private readonly Transform[] _agents = new Transform[3];
        private readonly Vector3[] _agentHomes =
        {
            new Vector3(-8f, 1f, 3f), new Vector3(8f, 1f, 3f), new Vector3(5f, 1f, 4f)
        };

        private CharacterController _person;
        private CharacterController _car;
        private Camera _camera;
        private LiveResearchClient _live;
        private Transform _library;
        private Transform _office;
        private bool _driving;
        private bool _showEvidence;
        private bool _usingLive;
        private float _yaw = 180f;
        private float _carSpeed;
        private float _verticalSpeed;
        private Vector2 _touchMove;
        private int _moveFinger = -1;
        private Vector2 _moveOrigin;
        private int _lookFinger = -1;
        private Vector2 _lookPrevious;
        private GUIStyle _heading;
        private GUIStyle _body;

        private void Awake()
        {
            Application.targetFrameRate = 60;
            Screen.orientation = ScreenOrientation.LandscapeLeft;
            _live = gameObject.AddComponent<LiveResearchClient>();
            BuildDistrict();
            BuildActors();
            var cameraObject = new GameObject("Follow Camera");
            _camera = cameraObject.AddComponent<Camera>();
            _camera.fieldOfView = 65f;
            cameraObject.AddComponent<AudioListener>();
            RenderSettings.ambientLight = new Color(0.65f, 0.7f, 0.8f);
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1.3f;
            sun.transform.rotation = Quaternion.Euler(45f, -35f, 0f);
        }

        private void BuildDistrict()
        {
            Block("Ground", new Vector3(0f, -0.55f, 0f), new Vector3(90f, 1f, 90f),
                new Color(0.32f, 0.5f, 0.38f));
            Block("Main Road", new Vector3(0f, -0.03f, 0f), new Vector3(11f, 0.08f, 80f),
                new Color(0.15f, 0.18f, 0.23f));
            Block("Cross Road", new Vector3(0f, -0.02f, 0f), new Vector3(80f, 0.08f, 10f),
                new Color(0.15f, 0.18f, 0.23f));
            for (var i = -3; i <= 3; i++)
            {
                Block("Lane mark", new Vector3(0f, 0.03f, i * 10f),
                    new Vector3(0.2f, 0.02f, 4f), Color.yellow);
                Block("Lane mark", new Vector3(i * 10f, 0.04f, 0f),
                    new Vector3(4f, 0.02f, 0.2f), Color.yellow);
            }
            var palette = new[]
            {
                new Color(0.58f, 0.7f, 0.75f), new Color(0.77f, 0.66f, 0.55f),
                new Color(0.62f, 0.6f, 0.72f)
            };
            for (var x = -3; x <= 3; x++)
            for (var z = -3; z <= 3; z++)
            {
                if (x == 0 || z == 0) continue;
                if (z == 1 && Math.Abs(x) == 1) continue; // Reserve the two workspaces.
                var height = 5f + ((Math.Abs(x * 7 + z * 11) % 4) * 2f);
                Block("City building", new Vector3(x * 11f, height / 2f, z * 11f),
                    new Vector3(7f, height, 7f), palette[Math.Abs(x + z * 2) % palette.Length]);
            }
            _library = BuildWorkspace("Library", -11f, new Color(0.2f, 0.65f, 0.8f));
            _office = BuildWorkspace("Office", 11f, new Color(0.95f, 0.62f, 0.25f));
            Block("Task board", new Vector3(2.8f, 1.3f, 5.5f), new Vector3(2.2f, 2f, 0.3f),
                new Color(0.25f, 0.3f, 0.45f));
        }

        private Transform BuildWorkspace(string title, float x, Color color)
        {
            var root = new GameObject(title + " workspace").transform;
            root.position = new Vector3(x, 0f, 8f);
            Block(title + " floor", new Vector3(x, 0.05f, 8f),
                new Vector3(7f, 0.1f, 7f), new Color(0.72f, 0.72f, 0.68f));
            Block(title + " back wall", new Vector3(x, 1.6f, 11.5f),
                new Vector3(7f, 3.2f, 0.3f), color);
            Block(title + " left wall", new Vector3(x - 3.5f, 1.6f, 8f),
                new Vector3(0.3f, 3.2f, 7f), color);
            Block(title + " right wall", new Vector3(x + 3.5f, 1.6f, 8f),
                new Vector3(0.3f, 3.2f, 7f), color);
            Block(title + " front wall left", new Vector3(x - 2.35f, 1.6f, 4.5f),
                new Vector3(2.3f, 3.2f, 0.3f), color);
            Block(title + " front wall right", new Vector3(x + 2.35f, 1.6f, 4.5f),
                new Vector3(2.3f, 3.2f, 0.3f), color);
            Block(title + " desk", new Vector3(x, 0.8f, 9.5f),
                new Vector3(2.5f, 0.3f, 0.9f), new Color(0.4f, 0.3f, 0.25f));
            return root;
        }

        private void BuildActors()
        {
            var personObject = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            personObject.name = "Player";
            personObject.transform.position = new Vector3(0f, 1.1f, 7f);
            personObject.GetComponent<Renderer>().material.color = new Color(0.25f, 0.45f, 0.95f);
            Destroy(personObject.GetComponent<CapsuleCollider>());
            _person = personObject.AddComponent<CharacterController>();
            _person.height = 2f;
            _person.radius = 0.42f;

            var carObject = new GameObject("Player vehicle");
            carObject.transform.position = new Vector3(2.5f, 0.9f, -3f);
            var carBody = Block("Car body", Vector3.zero,
                new Vector3(1.8f, 1.1f, 3.5f), new Color(0.95f, 0.25f, 0.2f));
            carBody.transform.SetParent(carObject.transform, false);
            Destroy(carBody.GetComponent<BoxCollider>());
            _car = carObject.AddComponent<CharacterController>();
            _car.height = 1.6f;
            _car.radius = 0.9f;
            _car.center = new Vector3(0f, -0.1f, 0f);
            for (var i = 0; i < 3; i++)
            {
                var actor = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                actor.name = ((AgentRole)i).ToString();
                actor.transform.position = _agentHomes[i];
                actor.GetComponent<Renderer>().material.color = i == 0
                    ? new Color(0.35f, 0.9f, 0.65f)
                    : i == 1 ? new Color(0.95f, 0.75f, 0.2f) : new Color(0.8f, 0.5f, 0.95f);
                _agents[i] = actor.transform;
            }
        }

        private GameObject Block(string title, Vector3 position, Vector3 scale, Color color)
        {
            var block = GameObject.CreatePrimitive(PrimitiveType.Cube);
            block.name = title;
            block.transform.position = position;
            block.transform.localScale = scale;
            block.GetComponent<Renderer>().material.color = color;
            return block;
        }

        private void Update()
        {
            ReadTouchInput();
            var move = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
            if (move.sqrMagnitude < 0.01f) move = _touchMove;
            move = Vector2.ClampMagnitude(move, 1f);

            if (_driving) MoveCar(move);
            else MovePerson(move);
            if (Input.GetKeyDown(KeyCode.E)) ToggleVehicle();
            _job.Tick(Time.deltaTime);
            MoveAgents();
            FollowCamera();
        }

        private void MovePerson(Vector2 input)
        {
            var yawRotation = Quaternion.Euler(0f, _yaw, 0f);
            var direction = yawRotation * new Vector3(input.x, 0f, input.y);
            var speed = Input.GetKey(KeyCode.LeftShift) ? 7f : 4.5f;
            if (_person.isGrounded)
            {
                _verticalSpeed = -0.5f;
                if (Input.GetKeyDown(KeyCode.Space)) _verticalSpeed = 6f;
            }
            else _verticalSpeed += Physics.gravity.y * Time.deltaTime;
            _person.Move((direction * speed + Vector3.up * _verticalSpeed) * Time.deltaTime);
            if (direction.sqrMagnitude > 0.02f)
                _person.transform.rotation = Quaternion.Slerp(_person.transform.rotation,
                    Quaternion.LookRotation(direction), Time.deltaTime * 10f);
        }

        private void MoveCar(Vector2 input)
        {
            var acceleration = input.y * 12f;
            _carSpeed = Mathf.Clamp(_carSpeed + acceleration * Time.deltaTime, -8f, 24f);
            _carSpeed = Mathf.MoveTowards(_carSpeed, 0f, 3f * Time.deltaTime);
            var turn = input.x * Mathf.Clamp01(Mathf.Abs(_carSpeed) / 3f) * 90f;
            _car.transform.Rotate(0f, turn * Time.deltaTime, 0f);
            _car.Move(_car.transform.forward * (_carSpeed * Time.deltaTime));
        }

        private void ToggleVehicle()
        {
            if (_driving)
            {
                _driving = false;
                _carSpeed = 0f;
                _person.gameObject.SetActive(true);
                _person.enabled = false;
                _person.transform.position = _car.transform.position - _car.transform.right * 2f
                    + Vector3.up * 0.4f;
                _person.enabled = true;
                return;
            }
            if (Vector3.Distance(_person.transform.position, _car.transform.position) > 4f) return;
            _driving = true;
            _person.gameObject.SetActive(false);
        }

        private void MoveAgents()
        {
            if (_usingLive)
            {
                if (!_live.Active) return;
                _agents[(int)AgentRole.Scout].position = Vector3.MoveTowards(
                    _agents[(int)AgentRole.Scout].position,
                    _library.position + new Vector3(0f, 1f, -1f), 4f * Time.deltaTime);
                return;
            }
            if (_job.Status == JobStatus.Idle) return;
            var active = (int)_job.ActiveAgent;
            for (var i = 0; i < _agents.Length; i++)
            {
                if (i != active || _job.Status == JobStatus.Cancelled) continue;
                var site = i == 0 ? _library : _office;
                var target = site.position + new Vector3(0f, 1f, -1f);
                _agents[i].position = Vector3.MoveTowards(_agents[i].position, target,
                    4f * Time.deltaTime);
            }
        }

        private void FollowCamera()
        {
            if (_camera == null) return;
            var target = _driving ? _car.transform : _person.transform;
            _yaw += Input.GetAxis("Mouse X") * 2f;
            var rotation = Quaternion.Euler(20f, _yaw, 0f);
            var desired = target.position + rotation * new Vector3(0f, 2f, -9f);
            _camera.transform.position = Vector3.Lerp(_camera.transform.position, desired,
                Mathf.Clamp01(Time.deltaTime * 7f));
            _camera.transform.LookAt(target.position + Vector3.up * 1.3f);
        }

        private void ReadTouchInput()
        {
            if (Input.touchCount == 0)
            {
                _touchMove = Vector2.zero;
                _moveFinger = -1;
                _lookFinger = -1;
                return;
            }
            foreach (var touch in Input.touches)
            {
                if (touch.phase == TouchPhase.Began)
                {
                    if (touch.position.x < Screen.width * 0.5f && _moveFinger < 0)
                    {
                        _moveFinger = touch.fingerId;
                        _moveOrigin = touch.position;
                    }
                    else if (_lookFinger < 0)
                    {
                        _lookFinger = touch.fingerId;
                        _lookPrevious = touch.position;
                    }
                }
                if (touch.fingerId == _moveFinger)
                {
                    if (touch.phase == TouchPhase.Ended || touch.phase == TouchPhase.Canceled)
                    {
                        _touchMove = Vector2.zero;
                        _moveFinger = -1;
                    }
                    else _touchMove = Vector2.ClampMagnitude((touch.position - _moveOrigin) / 85f, 1f);
                }
                if (touch.fingerId == _lookFinger)
                {
                    if (touch.phase == TouchPhase.Ended || touch.phase == TouchPhase.Canceled)
                        _lookFinger = -1;
                    else
                    {
                        _yaw += (touch.position.x - _lookPrevious.x) * 0.18f;
                        _lookPrevious = touch.position;
                    }
                }
            }
        }

        private void OnGUI()
        {
            if (_heading == null)
            {
                _heading = new GUIStyle(GUI.skin.label) { fontSize = 22, fontStyle = FontStyle.Bold };
                _body = new GUIStyle(GUI.skin.label) { fontSize = 15, wordWrap = true };
                _heading.normal.textColor = Color.white;
                _body.normal.textColor = Color.white;
            }
            var scale = Mathf.Max(1f, Screen.width / 1100f);
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, Vector3.one * scale);
            var width = Screen.width / scale;
            var height = Screen.height / scale;
            GUI.Box(new Rect(12f, 12f, 330f, 125f), "");
            GUI.Label(new Rect(25f, 19f, 310f, 30f), "AGENT DISTRICT  ·  prototype", _heading);
            GUI.Label(new Rect(25f, 53f, 310f, 80f),
                _driving ? "Driving — E or button to exit" : "Walking — E near red car to drive", _body);
            GUI.Label(new Rect(25f, 84f, 310f, 40f),
                "WASD move  ·  Mouse look  ·  Shift run", _body);

            GUI.Box(new Rect(width - 370f, 12f, 358f, 295f), "");
            GUI.Label(new Rect(width - 355f, 18f, 335f, 30f), "WORK BOARD", _heading);
            GUI.Label(new Rect(width - 355f, 51f, 330f, 50f),
                _usingLive ? "Compare documented city and vehicle assets (live)"
                : _job.Status == JobStatus.Idle ? "Assign a sample research task." : _job.Goal, _body);
            GUI.Label(new Rect(width - 355f, 104f, 330f, 48f),
                _usingLive ? "Status: " + _live.Status + "  ·  Agent: Scout"
                : "Status: " + _job.Status + "  ·  Agent: " + _job.ActiveAgent, _body);
            if (_usingLive)
            {
                if (_live.Active)
                {
                    if (GUI.Button(new Rect(width - 355f, 154f, 330f, 55f), "CANCEL LIVE TASK"))
                        _live.CancelResearch();
                }
                else if (GUI.Button(new Rect(width - 355f, 154f, 330f, 55f), "BACK TO TASK MENU"))
                    _usingLive = false;
            }
            else if (_job.Status == JobStatus.Idle)
            {
                if (GUI.Button(new Rect(width - 355f, 154f, 330f, 48f), "ASSIGN DEMO RESEARCH"))
                    _job.AssignDemoTask();
                if (GUI.Button(new Rect(width - 355f, 205f, 330f, 48f), "TRY LIVE DEEPSEEK TASK"))
                {
                    _usingLive = true;
                    _live.StartResearch();
                }
            }
            else if (_job.Status == JobStatus.Completed || _job.Status == JobStatus.Cancelled)
            {
                if (GUI.Button(new Rect(width - 355f, 154f, 330f, 55f), "RESET TASK"))
                    _job.Reset();
            }
            else if (GUI.Button(new Rect(width - 355f, 154f, 330f, 55f), "CANCEL TASK"))
                _job.Cancel();

            if (GUI.Button(new Rect(width - 355f, 261f, 330f, 38f),
                _showEvidence ? "HIDE TASK DETAILS" : "SHOW TASK DETAILS"))
                _showEvidence = !_showEvidence;
            if (_showEvidence) DrawTaskDetails(width, height);
            if (GUI.Button(new Rect(365f, height - 82f, 140f, 68f),
                _driving ? "EXIT CAR" : "ENTER CAR")) ToggleVehicle();
            if (Input.touchSupported)
                GUI.Label(new Rect(20f, height - 55f, 450f, 40f),
                    "Left drag: move  ·  Right drag: look", _body);
            DrawWorldLabel(_library.position + Vector3.up * 3.8f, "LIBRARY · SOURCES", scale);
            DrawWorldLabel(_office.position + Vector3.up * 3.8f, "OFFICE · ANALYSIS", scale);
            for (var i = 0; i < _agents.Length; i++)
                DrawWorldLabel(_agents[i].position + Vector3.up * 1.5f,
                    ((AgentRole)i).ToString(), scale);
        }

        private void DrawWorldLabel(Vector3 position, string label, float scale)
        {
            var point = _camera.WorldToScreenPoint(position);
            if (point.z <= 0f) return;
            GUI.Label(new Rect(point.x / scale - 90f,
                (Screen.height - point.y) / scale - 12f, 180f, 26f), label, _body);
        }

        private Vector2 _detailsScroll;

        private void DrawTaskDetails(float width, float height)
        {
            var panelHeight = Mathf.Min(370f, height - 320f);
            if (panelHeight < 100f) return;
            var panel = new Rect(width - 370f, 315f, 358f, panelHeight);
            GUI.Box(panel, "");
            if (_usingLive)
            {
                DrawLiveDetails(panel);
                return;
            }
            var contentHeight = _job.Events.Count * 42f
                + (_job.Status == JobStatus.Completed ? 145f + _job.Evidence.Count * 42f : 0f);
            _detailsScroll = GUI.BeginScrollView(new Rect(panel.x + 8f, panel.y + 8f,
                    panel.width - 16f, panel.height - 16f), _detailsScroll,
                new Rect(0f, 0f, 320f, Mathf.Max(contentHeight, panel.height - 20f)));
            var y = 0f;
            foreach (var item in _job.Events)
            {
                GUI.Label(new Rect(4f, y, 300f, 40f), "• " + item, _body);
                y += 42f;
            }
            if (_job.Status == JobStatus.Completed)
            {
                GUI.Label(new Rect(4f, y, 300f, 135f), _job.Report, _body);
                y += 145f;
                foreach (var evidence in _job.Evidence)
                {
                    if (GUI.Button(new Rect(4f, y, 300f, 36f), evidence.Title))
                        Application.OpenURL(evidence.Url);
                    y += 42f;
                }
            }
            GUI.EndScrollView();
        }

        private void DrawLiveDetails(Rect panel)
        {
            var reportHeight = Mathf.Max(65f, Mathf.CeilToInt(_live.Report.Length / 45f) * 24f);
            var contentHeight = 110f + reportHeight + _live.Evidence.Length * 42f;
            _detailsScroll = GUI.BeginScrollView(new Rect(panel.x + 8f, panel.y + 8f,
                    panel.width - 16f, panel.height - 16f), _detailsScroll,
                new Rect(0f, 0f, 320f, Mathf.Max(contentHeight, panel.height - 20f)));
            GUI.Label(new Rect(4f, 0f, 300f, 50f),
                "Live mode: one backend research worker. Multi-agent handoffs are in demo mode.", _body);
            GUI.Label(new Rect(4f, 54f, 300f, 45f), _live.Error, _body);
            GUI.Label(new Rect(4f, 100f, 300f, reportHeight), _live.Report, _body);
            var y = 105f + reportHeight;
            foreach (var evidence in _live.Evidence)
            {
                if (GUI.Button(new Rect(4f, y, 300f, 36f), evidence.title))
                    Application.OpenURL(evidence.url);
                y += 42f;
            }
            GUI.EndScrollView();
        }
    }
}
