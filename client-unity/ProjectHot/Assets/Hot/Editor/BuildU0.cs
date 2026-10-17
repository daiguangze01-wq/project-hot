using System;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Hot.Editor
{
    public static class BuildU0
    {
        public const string ScenePath = "Assets/Scenes/Arena.unity";
        public const string OutputPath = "Builds/U0/ProjectHot.exe";

        [MenuItem("Hot/Build U0 Windows Player")]
        public static void Build()
        {
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, ScriptingImplementation.Mono2x);
            PlayerSettings.productName = "Project Hot — U0";
            PlayerSettings.companyName = "Project Hot";
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.runInBackground = true;

            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            };

            BuildReport report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded)
            {
                Debug.LogError("U0 build failed: " + report.summary.result);
                EditorApplication.Exit(1);
            }

            Debug.Log("U0 build succeeded: " + OutputPath + " size=" + report.summary.totalSize);
            EditorApplication.Exit(0);
        }
    }
}
