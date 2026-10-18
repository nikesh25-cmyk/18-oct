using System;
using System.Collections.Generic;
using System.IO;

namespace NemoWorld.Harr
{
    [Serializable] public sealed class HarrContentPackage
    {
        public string format;
        public HarrContentCounts counts;
        public HarrResident[] residents;
        public HarrMission[] missions;
        public HarrTechnology[] techs;

        public void Validate()
        {
            if (format != "harr-authored-content-v1" || counts == null ||
                residents == null || missions == null || techs == null ||
                counts.residents != 52 || counts.core_missions != 16 ||
                counts.story_missions != 12 || counts.techs != 30 ||
                residents.Length != counts.residents ||
                missions.Length != counts.core_missions + counts.story_missions ||
                techs.Length != counts.techs)
                throw new InvalidDataException("Unsupported or incomplete Harr content package");

            var residentIds = new HashSet<string>();
            foreach (var resident in residents)
                if (resident == null || string.IsNullOrWhiteSpace(resident.id) ||
                    string.IsNullOrWhiteSpace(resident.name) || !residentIds.Add(resident.id))
                    throw new InvalidDataException("Duplicate or malformed Harr resident");

            var missionIds = new HashSet<string>();
            var core = 0;
            var story = 0;
            foreach (var mission in missions)
            {
                if (mission == null || mission.content == null ||
                    string.IsNullOrWhiteSpace(mission.content.id) ||
                    string.IsNullOrWhiteSpace(mission.content.title) ||
                    !missionIds.Add(mission.content.id))
                    throw new InvalidDataException("Duplicate or malformed Harr mission");
                if (mission.source == "core") core++;
                else if (mission.source == "story") story++;
                else throw new InvalidDataException("Unknown Harr mission source");
            }
            if (core != counts.core_missions || story != counts.story_missions)
                throw new InvalidDataException("Harr mission source counts differ");

            var techIds = new HashSet<string>();
            foreach (var tech in techs)
                if (tech == null || string.IsNullOrWhiteSpace(tech.id) ||
                    string.IsNullOrWhiteSpace(tech.name) || !techIds.Add(tech.id))
                    throw new InvalidDataException("Duplicate or malformed Harr technology");
            foreach (var tech in techs)
                if (tech.needs != null)
                    foreach (var need in tech.needs)
                        if (!techIds.Contains(need))
                            throw new InvalidDataException("Unknown Harr research prerequisite");
        }
    }

    [Serializable] public sealed class HarrContentCounts
    {
        public int residents;
        public int core_missions;
        public int story_missions;
        public int techs;
    }

    [Serializable] public sealed class HarrResident
    {
        public string id;
        public string name;
        public string role;
        public string calling;
        public string capabilities;
        public string limitations;
        public string[] barks;
    }

    [Serializable] public sealed class HarrMission
    {
        public string source;
        public HarrMissionContent content;
    }

    [Serializable] public sealed class HarrMissionContent
    {
        public string id;
        public string title;
        public string principle;
        public string purpose;
        public string how;
        public string shortText;
        public string blurb;
        public HarrMissionStep[] steps;
    }

    [Serializable] public sealed class HarrMissionStep
    {
        public string kind;
        public int count;
        public string label;
        public string distinct;
    }

    [Serializable] public sealed class HarrTechnology
    {
        public string id;
        public string name;
        public int cost;
        public string text;
        public string[] needs;
    }
}
