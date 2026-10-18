using UnityEngine;

namespace Hot.Client
{
    /// <summary>
    /// Equipment-bound combat timing/damage. Attack rate is a property of the
    /// equipped weapon, never a global player constant (ADR-005/013).
    /// </summary>
    [CreateAssetMenu(menuName = "Hot/Weapon Profile", fileName = "WeaponProfile")]
    public class WeaponProfile : ScriptableObject
    {
        public string weaponId = "unarmed";
        public string displayName = "空手";
        public bool isUnarmed = true;

        [Header("Light attack")]
        public float lightDamage = 18f;
        public float lightCooldown = 0.32f;
        public float lightRange = 2.0f;
        public float lightRadius = 1.15f;

        [Header("Heavy attack")]
        public float heavyDamage = 45f;
        public float heavyCooldown = 0.55f;
        public float heavyRange = 2.2f;
        public float heavyRadius = 1.2f;
    }
}
