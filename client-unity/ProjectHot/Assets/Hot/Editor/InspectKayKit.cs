using UnityEditor;
using UnityEngine;

namespace Hot.Editor
{
    public static class InspectKayKit
    {
        public static void Run()
        {
            const string path = "Assets/Hot/Art/KayKit/Knight.fbx";
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);
            var assets = AssetDatabase.LoadAllAssetsAtPath(path);
            int clipCount = 0;
            foreach (var a in assets)
            {
                if (a is AnimationClip clip) clipCount++;
            }
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go != null)
            {
                var renderers = go.GetComponentsInChildren<Renderer>();
                var bounds = new Bounds(go.transform.position, Vector3.zero);
                foreach (var r in renderers) bounds.Encapsulate(r.bounds);
                Debug.Log("KAYKIT_MODEL prefab=" + go.name + " renderers=" + renderers.Length + " bounds=" + bounds.size.ToString("F2"));
                foreach (var r in renderers) Debug.Log("KAYKIT_RENDERER " + r.name + " mats=" + r.sharedMaterials.Length);
            }
            Debug.Log("KAYKIT_CLIPS=" + clipCount);
            EditorApplication.Exit(0);
        }
    }
}
