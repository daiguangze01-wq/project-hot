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
        public float doubleTapWindow = 0.28f;

        [Header("Equipment-bound combat")]
        [Tooltip("Attack rate/damage come from the equipped weapon profile. Null = unarmed fallback.")]
        public WeaponProfile weaponProfile;
        public bool externalCombat;
        private bool externalGuard;

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
        private bool runLatched;
        private int lastTapDirection = -1;
        private float lastTapTime = -10f;

        private void Update()
        {
            var kb = Keyboard.current;
            if (kb == null) return;

            bool leftHeld = kb.aKey.isPressed || kb.leftArrowKey.isPressed;
            bool rightHeld = kb.dKey.isPressed || kb.rightArrowKey.isPressed;
            bool downHeld = kb.sKey.isPressed || kb.downArrowKey.isPressed;
            bool upHeld = kb.wKey.isPressed || kb.upArrowKey.isPressed;

            Vector2 input = Vector2.zero;
            if (leftHeld) input.x -= 1f;
            if (rightHeld) input.x += 1f;
            if (downHeld) input.y -= 1f;
            if (upHeld) input.y += 1f;

            // Run latch: double-tap one direction, then keep running while any
            // direction key remains held (including switching to another direction).
            if (!(leftHeld || rightHeld || upHeld || downHeld))
            {
                runLatched = false;
            }
            else
            {
                int pressedDirection = -1;
                if (kb.aKey.wasPressedThisFrame || kb.leftArrowKey.wasPressedThisFrame) pressedDirection = 0;
                else if (kb.dKey.wasPressedThisFrame || kb.rightArrowKey.wasPressedThisFrame) pressedDirection = 1;
                else if (kb.sKey.wasPressedThisFrame || kb.downArrowKey.wasPressedThisFrame) pressedDirection = 2;
                else if (kb.wKey.wasPressedThisFrame || kb.upArrowKey.wasPressedThisFrame) pressedDirection = 3;

                if (pressedDirection >= 0)
                {
                    if (pressedDirection == lastTapDirection &&
                        Time.unscaledTime - lastTapTime <= doubleTapWindow)
                    {
                        runLatched = true;
                    }
                    lastTapDirection = pressedDirection;
                    lastTapTime = Time.unscaledTime;
                }
            }

            moving = input.sqrMagnitude > 0.001f;
            running = moving && (runLatched || kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed);

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

            // Guard: Space or C+X. When the sim bridge owns combat, it supplies guard.
            guarding = externalCombat
                ? externalGuard
                : (kb.spaceKey.isPressed || (kb.cKey.isPressed && kb.xKey.isPressed));

            if (attacking && Time.time >= attackUntil) attacking = false;
            if (!externalCombat)
            {
                if (kb.cKey.wasPressedThisFrame) StartAttack(false);
                if (kb.xKey.wasPressedThisFrame) StartAttack(true);
            }
        }

        public void SetExternalGuard(bool value) => externalGuard = value;

        /// <summary>Sim-driven attack presentation; damage/cooldown are owned by Hot.Sim.</summary>
        public void PlayExternalAttack(bool heavy, float duration)
        {
            attackKind = heavy ? 1 : 0;
            attackStartedRunning = running;
            attacking = true;
            attackUntil = Time.time + Mathf.Max(0.05f, duration);
        }

        private void StartAttack(bool heavy)
        {
            // Critical: a rapid tap during the active/recovery window must not
            // deal damage again while the same attack animation is still playing.
            if (attacking) return;

            attackKind = heavy ? 1 : 0;
            attackStartedRunning = running;
            attacking = true;
            AttackCount++;
            attackUntil = Time.time + (heavy ? HeavyCooldown : LightCooldown);
            Attack(heavy ? HeavyDamage : LightDamage, heavy ? HeavyRange : LightRange, heavy ? HeavyRadius : LightRadius);
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

        private void Attack(float damage, float range, float radius)
        {
            Vector3 center = transform.position + transform.forward * range + Vector3.up * 0.9f;
            var hits = Physics.OverlapSphere(center, radius);
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

        public int AttackCount { get; private set; }
        public string WeaponName => weaponProfile != null ? weaponProfile.displayName : "空手";
        public float LightCooldown => weaponProfile != null ? weaponProfile.lightCooldown : lightAttackLock;
        public float HeavyCooldown => weaponProfile != null ? weaponProfile.heavyCooldown : heavyAttackLock;
        public float AttackRemaining => Mathf.Max(0f, attackUntil - Time.time);

        private float LightDamage => weaponProfile != null ? weaponProfile.lightDamage : lightDamage;
        private float HeavyDamage => weaponProfile != null ? weaponProfile.heavyDamage : heavyDamage;
        private float LightRange => weaponProfile != null ? weaponProfile.lightRange : attackRange;
        private float HeavyRange => weaponProfile != null ? weaponProfile.heavyRange : attackRange;
        private float LightRadius => weaponProfile != null ? weaponProfile.lightRadius : attackRadius;
        private float HeavyRadius => weaponProfile != null ? weaponProfile.heavyRadius : attackRadius;
    }
}
