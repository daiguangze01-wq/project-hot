using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Hot.Editor
{
    /// <summary>
    /// One-time setup: build the Knight material + AnimatorController from the
    /// CC0 KayKit FBX. Run before ArenaBootstrap after the FBX is imported.
    /// </summary>
    public static class KayKitAnimationBuilder
    {
        public const string FbxPath = "Assets/Hot/Art/KayKit/Knight.fbx";
        public const string TexturePath = "Assets/Hot/Art/KayKit/knight_texture.png";
        public const string MaterialPath = "Assets/Hot/Art/KayKit/KnightMat.mat";
        public const string ControllerPath = "Assets/Hot/Art/KayKit/KnightAnimator.controller";

        private static readonly Dictionary<string, string> StateToClip = new Dictionary<string, string>
        {
            { "Idle", "Idle" },
            { "Walk", "Walking_A" },
            { "Run", "Running_A" },
            { "LightAttack", "1H_Melee_Attack_Slice_Diagonal" },
            { "HeavyAttack", "1H_Melee_Attack_Chop" },
            { "RunLightAttack", "1H_Melee_Attack_Slice_Horizontal" },
            { "RunHeavyAttack", "1H_Melee_Attack_Chop" },
            { "Jump", "Jump_Full_Short" },
            { "JumpAttack", "1H_Melee_Attack_Stab" },
            { "Guard", "Blocking" },
        };

        [MenuItem("Hot/Build KayKit Animation Assets")]
        public static void Run()
        {
            BuildMaterial();
            BuildController();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("KayKit animation assets built");
            EditorApplication.Exit(0);
        }

        private static void BuildMaterial()
        {
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(TexturePath);
            if (tex == null)
            {
                Debug.LogError("Missing texture: " + TexturePath);
                EditorApplication.Exit(1);
                return;
            }

            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            var mat = new Material(shader) { name = "KnightMat" };
            if (mat.HasProperty("_BaseMap")) mat.SetTexture("_BaseMap", tex);
            if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", Color.white);
            mat.color = Color.white;

            AssetDatabase.DeleteAsset(MaterialPath);
            AssetDatabase.CreateAsset(mat, MaterialPath);
        }

        private static void BuildController()
        {
            var assets = AssetDatabase.LoadAllAssetsAtPath(FbxPath);
            var clips = new Dictionary<string, AnimationClip>();
            foreach (var a in assets)
            {
                if (a is AnimationClip clip && !clip.name.StartsWith("__preview__") && !clips.ContainsKey(clip.name))
                    clips[clip.name] = clip;
            }

            var missing = new List<string>();
            foreach (var clipName in StateToClip.Values)
            {
                if (!clips.ContainsKey(clipName)) missing.Add(clipName);
            }
            if (missing.Count > 0)
            {
                Debug.LogError("Missing KayKit clips: " + string.Join(", ", missing));
                EditorApplication.Exit(1);
                return;
            }

            AssetDatabase.DeleteAsset(ControllerPath);
            var controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            var sm = controller.layers[0].stateMachine;

            AnimatorState idle = null;
            foreach (var pair in StateToClip)
            {
                var state = sm.AddState(pair.Key);
                state.motion = clips[pair.Value];
                if (pair.Key == "Idle") idle = state;
            }
            if (idle != null) sm.defaultState = idle;
            Debug.Log("KayKit states=" + StateToClip.Count + " clips=" + clips.Count);
        }
    }
}
