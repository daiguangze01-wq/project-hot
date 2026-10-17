using UnityEditor;
using UnityEngine;

namespace Hot.Editor
{
    public static class InspectKayKit
    {
        public static void Run()
        {
            const string path = "Assets/Hot/Art/KayKit/Knight.fbx";
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go == null) { Debug.LogError("missing"); EditorApplication.Exit(1); return; }

            foreach (var smr in go.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                Debug.Log("KAYKIT_SMR " + smr.name + " root=" + smr.rootBone?.name);
                foreach (var bone in smr.bones)
                {
                    if (bone != null && (bone.name.Contains("Head") || bone.name.Contains("Spine") ||
                        bone.name.Contains("Neck") || bone.name.Contains("Hips") ||
                        bone.name.Contains("Shoulder") || bone.name.Contains("Hand")))
                        Debug.Log("KAYKIT_BONE " + bone.name);
                }
            }
            EditorApplication.Exit(0);
        }
    }
}
