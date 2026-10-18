using UnityEngine;

namespace Hot.Client
{
    public class TargetDummy : MonoBehaviour
    {
        public float maxHp = 5000f;
        public float hp = 5000f;
        public float respawnDelay = 2f;
        public Renderer bodyRenderer;
        public bool externalControl;

        private float respawnAt = -1f;
        private Color baseColor = Color.white;
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");

        private void Awake()
        {
            if (bodyRenderer == null) bodyRenderer = GetComponentInChildren<Renderer>();
            if (bodyRenderer != null && bodyRenderer.material != null)
                baseColor = bodyRenderer.material.HasProperty(BaseColorId) ? bodyRenderer.material.GetColor(BaseColorId) : bodyRenderer.material.color;
        }

        public void TakeDamage(float amount)
        {
            if (externalControl) return;
            if (hp <= 0f) return;
            hp = Mathf.Max(0f, hp - amount);
            StartCoroutine(Flash());
            if (hp <= 0f)
            {
                respawnAt = Time.time + respawnDelay;
                transform.localScale = new Vector3(1f, 0.25f, 1f);
            }
        }

        public void SyncFromSim(float simHp, bool alive)
        {
            externalControl = true;
            hp = simHp;
            transform.localScale = alive ? Vector3.one : new Vector3(1f, 0.25f, 1f);
        }

        private System.Collections.IEnumerator Flash()
        {
            if (bodyRenderer == null || bodyRenderer.material == null) yield break;
            var mat = bodyRenderer.material;
            if (mat.HasProperty(BaseColorId)) mat.SetColor(BaseColorId, Color.white);
            else mat.color = Color.white;
            yield return new WaitForSeconds(0.06f);
            if (mat.HasProperty(BaseColorId)) mat.SetColor(BaseColorId, baseColor);
            else mat.color = baseColor;
        }

        private void Update()
        {
            if (externalControl) return;
            if (hp <= 0f && respawnAt > 0f && Time.time >= respawnAt)
            {
                hp = maxHp;
                respawnAt = -1f;
                transform.localScale = Vector3.one;
            }
        }
    }
}
