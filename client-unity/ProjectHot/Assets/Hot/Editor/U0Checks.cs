using UnityEditor;
using UnityEngine;
using Hot.Client;

namespace Hot.Editor
{
    public static class U0Checks
    {
        [MenuItem("Hot/Run U0 Camera-Relative Checks")]
        public static void Run()
        {
            var cam = new GameObject("U0CheckCamera");
            cam.transform.rotation = Quaternion.Euler(50f, 45f, 0f);

            Vector3 screenRight = PlayerMotor.CameraRelativeDirection(Vector2.right, cam.transform);
            Vector3 screenUp = PlayerMotor.CameraRelativeDirection(Vector2.up, cam.transform);
            Vector3 screenDown = PlayerMotor.CameraRelativeDirection(Vector2.down, cam.transform);

            bool pass = true;
            pass &= Check("D -> screen-right (world +X,-Z)", screenRight.x > 0.5f && screenRight.z < -0.5f, screenRight);
            pass &= Check("W -> screen-up (world +X,+Z)", screenUp.x > 0.5f && screenUp.z > 0.5f, screenUp);
            pass &= Check("S -> opposite of W", Vector3.Dot(screenUp, screenDown) < -0.9f, screenDown);
            pass &= Check("D/W perpendicular", Mathf.Abs(Vector3.Dot(screenRight, screenUp)) < 0.1f, screenRight);

            Object.DestroyImmediate(cam);
            Debug.Log(pass ? "U0 CAMERA-RELATIVE CHECK PASS" : "U0 CAMERA-RELATIVE CHECK FAIL");
            EditorApplication.Exit(pass ? 0 : 1);
        }

        private static bool Check(string label, bool condition, Vector3 value)
        {
            Debug.Log((condition ? "PASS " : "FAIL ") + label + " -> " + value.ToString("F3"));
            return condition;
        }
    }
}
