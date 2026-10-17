using System;
using System.Collections;
using System.IO;
using UnityEngine;

namespace Hot.Client
{
    /// <summary>
    /// Optional visual-QA helper. Only runs when the player is launched with "-capture";
    /// writes a PNG and quits so automated agents can inspect the U0 scene.
    /// </summary>
    public class U0Capture : MonoBehaviour
    {
        private IEnumerator Start()
        {
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "-capture") < 0) yield break;
            yield return new WaitForSeconds(2.5f);
            string path = Path.Combine(Application.persistentDataPath, "u0-capture.png");
            ScreenCapture.CaptureScreenshot(path);
            yield return new WaitForSeconds(0.8f);
            Debug.Log("U0_CAPTURE:" + path);
            Application.Quit();
        }
    }
}
