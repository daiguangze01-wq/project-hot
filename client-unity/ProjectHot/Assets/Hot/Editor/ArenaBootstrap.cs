using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Hot.Client;

namespace Hot.Editor
{
    /// <summary>
    /// Creates the U0 arena scene from code so the project is reproducible.
    /// Run: Unity.exe -batchmode -quit -executeMethod Hot.Editor.ArenaBootstrap.CreateArena
    /// </summary>
    public static class ArenaBootstrap
    {
        private const string ScenePath = "Assets/Scenes/Arena.unity";

        [MenuItem("Hot/Bootstrap Arena (U0)")]
        public static void CreateArena()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var lit = Shader.Find("Universal Render Pipeline/Lit");
            if (lit == null) lit = Shader.Find("Standard");
            var floorMat = new Material(lit) { name = "FloorMat" };
            floorMat.SetColor("_BaseColor", new Color(0.11f, 0.14f, 0.21f));
            floorMat.color = new Color(0.11f, 0.14f, 0.21f);

            var gridMat = new Material(lit) { name = "GridMat" };
            gridMat.SetColor("_BaseColor", new Color(0.22f, 0.32f, 0.46f));
            gridMat.color = new Color(0.22f, 0.32f, 0.46f);

            // Floor.
            var floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            floor.name = "Floor";
            floor.transform.position = new Vector3(0f, -0.15f, 0f);
            floor.transform.localScale = new Vector3(16f, 0.3f, 16f);
            floor.GetComponent<Renderer>().sharedMaterial = floorMat;

            // Grid lines (thin cubes, no colliders).
            for (int i = -8; i <= 8; i++)
            {
                AddGridLine(new Vector3(i, 0f, 0f), new Vector3(0.035f, 0.012f, 16f), gridMat);
                AddGridLine(new Vector3(0f, 0f, i), new Vector3(16f, 0.012f, 0.035f), gridMat);
            }

            // Low boundary walls.
            AddWall(new Vector3(0f, 0.5f, 8.15f), new Vector3(16.6f, 1f, 0.3f), floorMat);
            AddWall(new Vector3(0f, 0.5f, -8.15f), new Vector3(16.6f, 1f, 0.3f), floorMat);
            AddWall(new Vector3(8.15f, 0.5f, 0f), new Vector3(0.3f, 1f, 16.6f), floorMat);
            AddWall(new Vector3(-8.15f, 0.5f, 0f), new Vector3(0.3f, 1f, 16.6f), floorMat);

            // Player.
            var player = new GameObject("Player");
            player.transform.position = new Vector3(0f, 0f, -3f);
            player.transform.rotation = Quaternion.Euler(0f, 0f, 0f);

            var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = "Body";
            body.transform.SetParent(player.transform, false);
            body.transform.localPosition = new Vector3(0f, 0.9f, 0f);
            body.transform.localScale = new Vector3(0.8f, 0.9f, 0.8f);
            var bodyMat = new Material(lit) { name = "PlayerBodyMat" };
            bodyMat.SetColor("_BaseColor", new Color(0.28f, 0.78f, 1f));
            bodyMat.color = new Color(0.28f, 0.78f, 1f);
            body.GetComponent<Renderer>().sharedMaterial = bodyMat;

            var head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            head.name = "Head";
            head.transform.SetParent(player.transform, false);
            head.transform.localPosition = new Vector3(0f, 1.95f, 0f);
            head.transform.localScale = Vector3.one * 0.55f;
            var headMat = new Material(lit) { name = "PlayerHeadMat" };
            headMat.SetColor("_BaseColor", new Color(1f, 0.84f, 0.66f));
            headMat.color = new Color(1f, 0.84f, 0.66f);
            head.GetComponent<Renderer>().sharedMaterial = headMat;

            var weapon = GameObject.CreatePrimitive(PrimitiveType.Cube);
            weapon.name = "Sword";
            weapon.transform.SetParent(player.transform, false);
            weapon.transform.localPosition = new Vector3(0.55f, 1.1f, 0.35f);
            weapon.transform.localScale = new Vector3(0.09f, 0.09f, 1.0f);
            weapon.transform.localRotation = Quaternion.Euler(0f, 0f, -25f);
            var weaponMat = new Material(lit) { name = "WeaponMat" };
            weaponMat.SetColor("_BaseColor", new Color(0.9f, 0.95f, 1f));
            weaponMat.color = new Color(0.9f, 0.95f, 1f);
            weapon.GetComponent<Renderer>().sharedMaterial = weaponMat;

            var motor = player.AddComponent<PlayerMotor>();

            // Training dummy.
            var dummyRoot = new GameObject("TrainingDummy");
            dummyRoot.transform.position = new Vector3(0f, 0f, 2.8f);
            var dummyBody = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            dummyBody.name = "DummyBody";
            dummyBody.transform.SetParent(dummyRoot.transform, false);
            dummyBody.transform.localPosition = new Vector3(0f, 1.1f, 0f);
            dummyBody.transform.localScale = new Vector3(1.0f, 1.0f, 1.0f);
            var dummyMat = new Material(lit) { name = "DummyMat" };
            dummyMat.SetColor("_BaseColor", new Color(0.86f, 0.68f, 0.42f));
            dummyMat.color = new Color(0.86f, 0.68f, 0.42f);
            dummyBody.GetComponent<Renderer>().sharedMaterial = dummyMat;

            var dummyHead = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            dummyHead.name = "DummyHead";
            dummyHead.transform.SetParent(dummyRoot.transform, false);
            dummyHead.transform.localPosition = new Vector3(0f, 2.35f, 0f);
            dummyHead.transform.localScale = Vector3.one * 0.7f;
            dummyHead.GetComponent<Renderer>().sharedMaterial = dummyMat;

            var dummy = dummyRoot.AddComponent<TargetDummy>();
            dummy.bodyRenderer = dummyBody.GetComponent<Renderer>();
            dummy.hp = dummy.maxHp;

            // Camera: fixed 2.5D ortho.
            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 8f;
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 100f;
            camGo.AddComponent<AudioListener>();
            var rig = camGo.AddComponent<OrthoCameraRig>();
            rig.target = player.transform;
            camGo.transform.position = new Vector3(0f, 20f, -20f);

            // Light.
            var lightGo = new GameObject("Directional Light");
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.1f;
            light.color = new Color(1f, 0.96f, 0.9f);
            lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            // HUD.
            var hud = player.AddComponent<HotHud>();
            hud.player = motor;
            hud.dummy = dummy;

            // A few pillars for scale/readability.
            for (int i = 0; i < 4; i++)
            {
                var pillar = GameObject.CreatePrimitive(PrimitiveType.Cube);
                pillar.name = "Pillar" + i;
                float x = (i % 2 == 0) ? -6.5f : 6.5f;
                float z = (i < 2) ? -6.5f : 6.5f;
                pillar.transform.position = new Vector3(x, 1.5f, z);
                pillar.transform.localScale = new Vector3(0.7f, 3f, 0.7f);
                pillar.GetComponent<Renderer>().sharedMaterial = floorMat;
            }

            System.IO.Directory.CreateDirectory("Assets/Scenes");
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("U0 Arena created: " + ScenePath);
        }

        private static void AddGridLine(Vector3 position, Vector3 scale, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = "GridLine";
            go.transform.position = new Vector3(position.x, 0.005f, position.z);
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            Object.DestroyImmediate(go.GetComponent<Collider>());
        }

        private static void AddWall(Vector3 position, Vector3 scale, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = "Wall";
            go.transform.position = position;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }
    }
}
