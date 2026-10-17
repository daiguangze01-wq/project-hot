using System;
using System.Collections.Generic;
using UnityEngine;

namespace Hot.Client
{
    /// <summary>
    /// U0/U1 placeholder modular avatar: shared base body + toggleable equipment parts.
    /// Formal items will be AvatarItemDefinition/ScriptableObjects per ADR-013.
    /// </summary>
    public class AvatarEquipmentController : MonoBehaviour
    {
        [Serializable]
        public class Slot
        {
            public AvatarSlot slot;
            public List<GameObject> options = new List<GameObject>();
            public int index;
            public bool visible = true;

            public GameObject Current =>
                options.Count == 0 ? null : options[Mathf.Clamp(index, 0, options.Count - 1)];
        }

        public List<Slot> slots = new List<Slot>();
        public Renderer ugcTarget;

        private readonly Dictionary<AvatarSlot, Slot> lookup = new Dictionary<AvatarSlot, Slot>();

        private void Awake()
        {
            EnsureLookup();
            ApplyAll();
        }

        private void EnsureLookup()
        {
            if (lookup.Count == slots.Count) return;
            lookup.Clear();
            foreach (var s in slots) lookup[s.slot] = s;
        }

        public void Cycle(AvatarSlot slot)
        {
            EnsureLookup();
            if (!lookup.TryGetValue(slot, out var s) || s.options.Count <= 1) return;
            s.index = (s.index + 1) % s.options.Count;
            Apply(s);
        }

        public void Toggle(AvatarSlot slot)
        {
            EnsureLookup();
            if (!lookup.TryGetValue(slot, out var s)) return;
            s.visible = !s.visible;
            Apply(s);
        }

        public void ApplyUgcTexture(Texture2D texture)
        {
            if (ugcTarget == null || texture == null) return;
            var mat = new Material(ugcTarget.sharedMaterial);
            if (mat.HasProperty("_BaseMap")) mat.SetTexture("_BaseMap", texture);
            if (mat.HasProperty("_MainTex")) mat.SetTexture("_MainTex", texture);
            ugcTarget.material = mat;
        }

        public string Describe()
        {
            var parts = new List<string>();
            foreach (var s in slots)
            {
                var cur = s.Current;
                parts.Add(s.slot + ":" + (s.visible && cur != null ? cur.name : "off"));
            }
            return string.Join("  ", parts);
        }

        private void ApplyAll()
        {
            foreach (var s in slots) Apply(s);
        }

        private void Apply(Slot s)
        {
            for (int i = 0; i < s.options.Count; i++)
            {
                if (s.options[i] != null) s.options[i].SetActive(s.visible && i == s.index);
            }
        }
    }
}
