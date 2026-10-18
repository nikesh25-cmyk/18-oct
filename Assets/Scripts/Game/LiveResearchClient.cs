using System;
using System.Collections;
using System.Text;
using AgentDistrict.Core;
using UnityEngine;
using UnityEngine.Networking;

namespace AgentDistrict.Game
{
    // Local Mac Editor prototype transport. Never embeds the AI provider key in Unity.
    public sealed class LiveResearchClient : MonoBehaviour
    {
        private const string ApiRoot = "http://127.0.0.1:8765";
        private const string DemoGoal = "Compare open-license starter assets for a mobile city game";
        private string _jobId = string.Empty;

        public string Status { get; private set; } = "idle";
        public string Error { get; private set; } = string.Empty;
        public string Report { get; private set; } = string.Empty;
        public EvidenceDto[] Evidence { get; private set; } = Array.Empty<EvidenceDto>();
        public bool Active => Status == "connecting" || Status == "queued" || Status == "researching";

        [Serializable]
        private sealed class JobRequest { public string goal = DemoGoal; }

        [Serializable]
        private sealed class IdResponse { public string id = string.Empty; }

        [Serializable]
        private sealed class JobResponse
        {
            public string status = string.Empty;
            public string report = string.Empty;
            public string error = string.Empty;
            public EvidenceDto[] evidence = Array.Empty<EvidenceDto>();
        }

        [Serializable]
        public sealed class EvidenceDto
        {
            public string title = string.Empty;
            public string url = string.Empty;
        }

        public void StartResearch()
        {
            if (Active) return;
            _jobId = string.Empty;
            Status = "connecting";
            Error = string.Empty;
            Report = string.Empty;
            Evidence = Array.Empty<EvidenceDto>();
            StartCoroutine(RunResearch());
        }

        private IEnumerator RunResearch()
        {
            var data = Encoding.UTF8.GetBytes(JsonUtility.ToJson(new JobRequest()));
            using (var request = new UnityWebRequest(ApiRoot + "/jobs", "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(data);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.timeout = 10;
                yield return request.SendWebRequest();
                if (request.result != UnityWebRequest.Result.Success)
                {
                    Fail("Local research backend is unavailable. Start it on this Mac first.");
                    yield break;
                }
                _jobId = JsonUtility.FromJson<IdResponse>(request.downloadHandler.text).id;
                if (string.IsNullOrWhiteSpace(_jobId))
                {
                    Fail("The research backend did not return a job ID.");
                    yield break;
                }
            }
            Status = "queued";
            while (Active)
            {
                using (var request = UnityWebRequest.Get(ApiRoot + "/jobs/" + _jobId))
                {
                    request.timeout = 10;
                    yield return request.SendWebRequest();
                    if (request.result != UnityWebRequest.Result.Success)
                    {
                        Fail("Lost connection to the research backend.");
                        yield break;
                    }
                    var job = JsonUtility.FromJson<JobResponse>(request.downloadHandler.text);
                    Status = job.status;
                    Error = job.error;
                    Report = job.report;
                    Evidence = job.evidence ?? Array.Empty<EvidenceDto>();
                }
                if (Active) yield return new WaitForSeconds(0.8f);
            }
        }

        public void CancelResearch()
        {
            if (!Active || string.IsNullOrWhiteSpace(_jobId)) return;
            StartCoroutine(SendCancel());
        }

        private IEnumerator SendCancel()
        {
            using (var request = new UnityWebRequest(ApiRoot + "/jobs/" + _jobId + "/cancel", "POST"))
            {
                request.downloadHandler = new DownloadHandlerBuffer();
                request.timeout = 10;
                yield return request.SendWebRequest();
                if (request.result == UnityWebRequest.Result.Success) Status = "cancelled";
                else Error = "Cancellation could not reach the backend.";
            }
        }

        private void Fail(string message)
        {
            Status = "failed";
            Error = message;
        }
    }
}
