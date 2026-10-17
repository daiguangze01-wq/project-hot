using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Hot.Client
{
    /// <summary>Debug hooks for U0 modular avatar: 1 head, 2 cape, 3 weapon, 4 offhand, U UGC texture.</summary>
    public class AvatarDebugInput : MonoBehaviour
    {
        public AvatarEquipmentController equipment;
        public string ugcFileName = "ugc/test_pattern.png";

        private string status = "";

        private void Update()
        {
            var kb = Keyboard.current;
            if (kb == null || equipment == null) return;

            if (kb.digit1Key.wasPressedThisFrame) { equipment.Toggle(AvatarSlot.HeadAccessory); status = "head toggled"; }
            if (kb.digit2Key.wasPressedThisFrame) { equipment.Toggle(AvatarSlot.Cape); status = "cape toggled"; }
            if (kb.digit3Key.wasPressedThisFrame) { equipment.Cycle(AvatarSlot.WeaponMain); status = "weapon cycled"; }
            if (kb.digit4Key.wasPressedThisFrame) { equipment.Cycle(AvatarSlot.WeaponOffhand); status = "offhand cycled"; }

            if (kb.uKey.wasPressedThisFrame)
            {
                string path = Path.Combine(Application.streamingAssetsPath, ugcFileName);
                if (UgcTextureLoader.TryLoad(path, out var tex, out var error))
                {
                    equipment.ApplyUgcTexture(tex);
                    status = "UGC texture applied";
                }
                else status = "UGC failed: " + error;
            }
        }

        private void OnGUI()
        {
            if (equipment == null) return;
            var style = new GUIStyle(GUI.skin.label) { fontSize = 12 };
            GUILayout.BeginArea(new Rect(18, 250, 760, 90), GUI.skin.box);
            GUILayout.Label("AVATAR SLOTS: " + equipment.Describe(), style);
            GUILayout.Label("1 head / 2 cape / 3 weapon / 4 offhand / U UGC texture", style);
            if (!string.IsNullOrEmpty(status)) GUILayout.Label(status, style);
            GUILayout.EndArea();
        }
    }
}
