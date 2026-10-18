using System;

namespace NemoWorld.Harr
{
    [Serializable]
    public sealed class HarrCityPackage
    {
        public string format;
        public string site;
        public int ground_reference;
        public HarrGroup[] groups;
    }

    [Serializable]
    public sealed class HarrGroup
    {
        public string id;
        public string provenance;
        public int[] anchor;
        public int ground;
        public HarrOp[] ops;
    }

    [Serializable]
    public sealed class HarrOp
    {
        public string op;
        public int[] @from;
        public int[] to;
        public int[] at;
        public int[] rgb;
        public int depth;
        public string sprite;
    }
}
