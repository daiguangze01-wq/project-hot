using UnityEngine;

namespace Hot.Client
{
    /// <summary>
    /// Fixed 2.5D orthographic camera: pitch 50, yaw 45, size 8.
    /// No mouse, no rotation input; follows a target on the X/Z plane.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class OrthoCameraRig : MonoBehaviour
    {
        public Transform target;
        public float pitch = 50f;
        public float yaw = 45f;
        public float orthoSize = 8f;
        public float distance = 24f;
        public float followLerp = 12f;

        private Camera cam;

        private void Awake()
        {
            cam = GetComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = orthoSize;
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 100f;
            ApplyRotation();
        }

        private void LateUpdate()
        {
            if (target == null) return;

            Vector3 focus = target.position;
            focus.y = 0f;
            transform.position = Vector3.Lerp(transform.position, focus - transform.forward * distance, 1f - Mathf.Exp(-followLerp * Time.deltaTime));
            ApplyRotation();
        }

        private void ApplyRotation()
        {
            transform.rotation = Quaternion.Euler(pitch, yaw, 0f);
            if (cam != null) cam.orthographicSize = orthoSize;
        }
    }
}
