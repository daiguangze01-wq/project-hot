using UnityEditor;
using UnityEngine;
using Hot.Client;

namespace Hot.Editor
{
    public static class AvatarChecks
    {
        public static void Run()
        {
            bool ok = true;
            if (UgcTextureLoader.TryLoad("Assets/StreamingAssets/ugc/test_pattern.png", out var tex, out var err))
            {
                Debug.Log("AVATAR_CHECK UGC ok size=" + tex.width + "x" + tex.height);
                Object.DestroyImmediate(tex);
            }
            else
            {
                Debug.LogError("AVATAR_CHECK UGC failed: " + err);
                ok = false;
            }

            var scene = UnityEditor.SceneManagement.EditorSceneManager.OpenScene("Assets/Scenes/Arena.unity");
            var controller = Object.FindFirstObjectByType<AvatarEquipmentController>();
            if (controller == null)
            {
                Debug.LogError("AVATAR_CHECK missing AvatarEquipmentController");
                ok = false;
            }
            else
            {
                Debug.Log("AVATAR_CHECK slots=" + controller.slots.Count + " " + controller.Describe());
                controller.Toggle(AvatarSlot.HeadAccessory);
                controller.Cycle(AvatarSlot.WeaponMain);
                controller.Cycle(AvatarSlot.WeaponOffhand);
                Debug.Log("AVATAR_CHECK after cycle " + controller.Describe());
            }

            Debug.Log(ok ? "AVATAR_CHECK PASS" : "AVATAR_CHECK FAIL");
            EditorApplication.Exit(ok ? 0 : 1);
        }
    }
}
