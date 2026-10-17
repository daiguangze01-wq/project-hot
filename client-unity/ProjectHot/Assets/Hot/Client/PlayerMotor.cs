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
        public float walkSpeed = 2.7f;
        public float jumpVelocity = 5.0f;
        public float gravity = 16f;
        public float attackRange = 2.4f;
        public float attackRadius = 1.2f;
        public float lightDamage = 30f;
        public float heavyDamage = 80f;
        public float lightAttackLock = 0.45f;
        public float heavyAttackLock = 0.7f;

        [Header("Camera-relative input")]
        [Tooltip("Fixed 2.5D camera. WASD maps to screen right/up, not world X/Z.")]
        public Transform cameraTransform;

        private float verticalVelocity;
        private float height;
        private bool guarding;
        private bool moving;
        private bool running;
        private bool attacking;
        private bool attackStartedRunning;
        private int attackKind;
        private float attackUntil;

        private void Update()
        {
            var kb = Keyboard.current;
            if (kb == null) return;

            Vector2 input = Vector2.zero;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) input.x -= 1f;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) input.x += 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) input.y -= 1f;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) input.y += 1f;

            moving = input.sqrMagnitude > 0.001f;
            running = moving && (kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed);

            Vector3 dir = CameraRelativeDirection(input, cameraTransform);
            if (moving)
            {
                dir.Normalize();
                float moveSpeed = running ? speed : walkSpeed;
                if (guarding) moveSpeed *= 0.3f;
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

            if (attacking && Time.time >= attackUntil) attacking = false;
            if (kb.cKey.wasPressedThisFrame) StartAttack(false);
            if (kb.xKey.wasPressedThisFrame) StartAttack(true);
        }

        private void StartAttack(bool heavy)
        {
            attackKind = heavy ? 1 : 0;
            attackStartedRunning = running;
            attacking = true;
            attackUntil = Time.time + (heavy ? heavyAttackLock : lightAttackLock);
            Attack(heavy ? heavyDamage : lightDamage);
        }

        /// <summary>
        /// Converts screen-space input (x=right, y=up) into a ground direction using
        /// the camera's projected right/forward axes. For a yaw-45 isometric camera
        /// this makes D move screen-right and W move screen-up, not world +X/+Z.
        /// </summary>
        public static Vector3 CameraRelativeDirection(Vector2 input, Transform cameraTransform)
        {
            if (cameraTransform == null)
                return new Vector3(input.x, 0f, input.y);

            Vector3 right = Vector3.ProjectOnPlane(cameraTransform.right, Vector3.up);
            Vector3 forward = Vector3.ProjectOnPlane(cameraTransform.forward, Vector3.up);
            if (right.sqrMagnitude < 1e-4f) right = Vector3.right;
            if (forward.sqrMagnitude < 1e-4f) forward = Vector3.forward;
            right.Normalize();
            forward.Normalize();

            Vector3 dir = right * input.x + forward * input.y;
            return dir.sqrMagnitude > 1f ? dir.normalized : dir;
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
        public bool IsMoving => moving;
        public bool IsRunning => running;
        public bool IsAttacking => attacking;
        public bool IsGrounded => height <= 0.001f;
        public int AttackKind => attackKind;
        public bool AttackStartedRunning => attackStartedRunning;
        public float Height => height;
    }
}
