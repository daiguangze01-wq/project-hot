using UnityEngine;
using UnityEngine.InputSystem;

namespace Hot.Client
{
    /// <summary>
    /// U0 keyboard-only movement/attack prototype. Server authority/Fusion comes in U2;
    /// this local component exists to verify the camera/input/arena feel in the engine.
    /// </summary>
    public class PlayerMotor : MonoBehaviour
    {
        public float speed = 5.2f;
        public float jumpVelocity = 5.0f;
        public float gravity = 16f;
        public float attackRange = 2.4f;
        public float attackRadius = 1.2f;
        public float lightDamage = 30f;
        public float heavyDamage = 80f;

        private float verticalVelocity;
        private float height;
        private bool guarding;

        private void Update()
        {
            var kb = Keyboard.current;
            if (kb == null) return;

            Vector3 dir = Vector3.zero;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) dir.x -= 1f;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) dir.x += 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) dir.z -= 1f;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) dir.z += 1f;

            if (dir.sqrMagnitude > 0.001f)
            {
                dir.Normalize();
                float moveSpeed = guarding ? speed * 0.3f : speed;
                transform.position += dir * (moveSpeed * Time.deltaTime);
                transform.rotation = Quaternion.LookRotation(dir, Vector3.up);
            }

            // Arena bounds (16 x 16m).
            var p = transform.position;
            p.x = Mathf.Clamp(p.x, -7.5f, 7.5f);
            p.z = Mathf.Clamp(p.z, -7.5f, 7.5f);
            transform.position = p;

            // Jump: V. Z is visual-only for U0; hit z is not checked yet.
            if (kb.vKey.wasPressedThisFrame && height <= 0.001f && verticalVelocity <= 0f)
                verticalVelocity = jumpVelocity;
            verticalVelocity -= gravity * Time.deltaTime;
            height += verticalVelocity * Time.deltaTime;
            if (height < 0f) { height = 0f; verticalVelocity = 0f; }
            transform.position = new Vector3(p.x, height, p.z);

            // Guard: Space or C+X. Damage reduction is local-only in U0.
            guarding = kb.spaceKey.isPressed || (kb.cKey.isPressed && kb.xKey.isPressed);

            if (kb.cKey.wasPressedThisFrame) Attack(lightDamage);
            if (kb.xKey.wasPressedThisFrame) Attack(heavyDamage);
        }

        private void Attack(float damage)
        {
            Vector3 center = transform.position + transform.forward * attackRange + Vector3.up * 0.9f;
            var hits = Physics.OverlapSphere(center, attackRadius);
            foreach (var hit in hits)
            {
                var dummy = hit.GetComponentInParent<TargetDummy>();
                if (dummy != null)
                {
                    dummy.TakeDamage(damage);
                    return;
                }
            }
        }

        public bool IsGuarding => guarding;
        public float Height => height;
    }
}
