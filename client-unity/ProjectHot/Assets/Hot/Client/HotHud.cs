using UnityEngine;

namespace Hot.Client
{
    public class HotHud : MonoBehaviour
    {
        public PlayerMotor player;
        public TargetDummy dummy;
        public CombatSimBridge simBridge;

        private void OnGUI()
        {
            if (player == null)
                player = FindFirstObjectByType<PlayerMotor>();
            if (dummy == null)
                dummy = FindFirstObjectByType<TargetDummy>();
            if (simBridge == null)
                simBridge = FindFirstObjectByType<CombatSimBridge>();

            var style = new GUIStyle(GUI.skin.label) { fontSize = 14 };
            GUILayout.BeginArea(new Rect(18, 18, 330, 210), GUI.skin.box);
            GUILayout.Label("PROJECT HOT — U0 ENGINE CLIENT", style);
            GUILayout.Label("2.5D ortho · pitch 50 / yaw 45 · size 8", style);
            GUILayout.Space(6);
            if (player != null)
            {
                if (simBridge != null)
                {
                    GUILayout.Label("HP " + simBridge.Hp.ToString("0") + " / MP " + simBridge.Mp.ToString("0") +
                                    " / GUARD " + simBridge.Guard.ToString("0") + " / ULT " + simBridge.Ult.ToString("0"), style);
                    GUILayout.Label("Core: " + simBridge.CoreName + " (Hot.Sim)", style);
                }
                else
                {
                    GUILayout.Label("HP 500 / MP 100 / GUARD 300 / ULT 0", style);
                    GUILayout.Label("Weapon: " + player.WeaponName + " · light " +
                                    player.LightCooldown.ToString("0.00") + "s / heavy " +
                                    player.HeavyCooldown.ToString("0.00") + "s", style);
                }
                GUILayout.Label("Player height: " + player.Height.ToString("0.00") + "m", style);
                GUILayout.Label("Guard: " + (player.IsGuarding ? "ON" : "off"), style);
            }
            GUILayout.Space(6);
            if (dummy != null)
                GUILayout.Label("Dummy HP: " + dummy.hp.ToString("0") + " / " + dummy.maxHp.ToString("0"), style);
            GUILayout.Space(6);
            GUILayout.Label("WASD/方向（屏幕方向） · 双击方向/Shift 跑 · V jump · C light · X heavy · Space/C+X guard", style);
            GUILayout.Label("Mouse not used. U0 local only; Fusion comes in U2.", style);
            GUILayout.EndArea();
        }
    }
}
