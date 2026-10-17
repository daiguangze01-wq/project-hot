using UnityEngine;

namespace Hot.Client
{
    /// <summary>
    /// Maps the local U0 movement/attack state to the KayKit animator states.
    /// The 3D model is a placeholder for the final pixel-textured low-poly character.
    /// </summary>
    public class CharacterAnimationDriver : MonoBehaviour
    {
        public Animator animator;
        public PlayerMotor motor;

        private string currentState;

        private void Awake()
        {
            if (animator == null) animator = GetComponent<Animator>();
            animator.applyRootMotion = false;
        }

        private void Update()
        {
            if (animator == null || motor == null) return;

            string next;
            if (motor.IsAttacking)
            {
                if (!motor.IsGrounded) next = "JumpAttack";
                else if (motor.AttackStartedRunning) next = motor.AttackKind == 0 ? "RunLightAttack" : "RunHeavyAttack";
                else next = motor.AttackKind == 0 ? "LightAttack" : "HeavyAttack";
            }
            else if (!motor.IsGrounded) next = "Jump";
            else if (motor.IsGuarding) next = "Guard";
            else if (motor.IsRunning) next = "Run";
            else if (motor.IsMoving) next = "Walk";
            else next = "Idle";

            if (next != currentState)
            {
                currentState = next;
                animator.CrossFadeInFixedTime(next, 0.08f);
            }
        }
    }
}
