using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Hot.Client
{
    /// <summary>U0 test hook: 5 cycles combat weapon profiles so attack rate is visibly equipment-bound.</summary>
    public class CombatLoadoutTester : MonoBehaviour
    {
        public PlayerMotor motor;
        public List<WeaponProfile> profiles = new List<WeaponProfile>();
        private int index;
        private string status = "";

        private void Update()
        {
            var kb = Keyboard.current;
            if (kb == null || motor == null || profiles.Count == 0) return;
            if (kb.digit5Key.wasPressedThisFrame)
            {
                index = (index + 1) % profiles.Count;
                motor.weaponProfile = profiles[index];
                status = "combat weapon: " + profiles[index].displayName;
            }
        }

        private void OnGUI()
        {
            if (motor == null) return;
            var style = new GUIStyle(GUI.skin.label) { fontSize = 12 };
            GUILayout.BeginArea(new Rect(18, 340, 760, 64), GUI.skin.box);
            GUILayout.Label("COMBAT LOADOUT: " + motor.WeaponName + " · light " +
                            motor.LightCooldown.ToString("0.00") + "s / heavy " +
                            motor.HeavyCooldown.ToString("0.00") + "s", style);
            GUILayout.Label("5 cycle combat weapon (visual slots are separate)", style);
            if (!string.IsNullOrEmpty(status)) GUILayout.Label(status, style);
            GUILayout.EndArea();
        }
    }
}
