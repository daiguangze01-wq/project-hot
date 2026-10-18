using System.Reflection;
using UnityEditor;
using UnityEngine;
using Hot.Client;

namespace Hot.Editor
{
    public static class CombatChecks
    {
        public static void Run()
        {
            UnityEditor.SceneManagement.EditorSceneManager.OpenScene("Assets/Scenes/Arena.unity");
            var motor = Object.FindFirstObjectByType<PlayerMotor>();
            if (motor == null || motor.weaponProfile == null)
            {
                Debug.LogError("COMBAT_CHECK missing motor/profile");
                EditorApplication.Exit(1);
                return;
            }

            var unarmed = motor.weaponProfile;
            var sword1h = AssetDatabase.LoadAssetAtPath<WeaponProfile>("Assets/Hot/Data/WeaponProfiles/Sword1H.asset");
            var sword2h = AssetDatabase.LoadAssetAtPath<WeaponProfile>("Assets/Hot/Data/WeaponProfiles/Sword2H.asset");
            bool passive =
                unarmed != null && sword1h != null && sword2h != null &&
                unarmed.lightCooldown < sword1h.lightCooldown &&
                sword1h.lightCooldown < sword2h.lightCooldown &&
                unarmed.displayName == "空手";

            var startAttack = typeof(PlayerMotor).GetMethod("StartAttack", BindingFlags.Instance | BindingFlags.NonPublic);
            int before = motor.AttackCount;
            startAttack.Invoke(motor, new object[] { false });
            startAttack.Invoke(motor, new object[] { false });
            int after = motor.AttackCount;
            bool gated = after == before + 1;

            Debug.Log("COMBAT_CHECK unarmed=" + unarmed.lightCooldown + "s 1H=" + sword1h.lightCooldown +
                      "s 2H=" + sword2h.lightCooldown + "s gated=" + gated + " attacks=" + after);

            Debug.Log(passive && gated ? "COMBAT_CHECK PASS" : "COMBAT_CHECK FAIL");
            EditorApplication.Exit(passive && gated ? 0 : 1);
        }
    }
}
