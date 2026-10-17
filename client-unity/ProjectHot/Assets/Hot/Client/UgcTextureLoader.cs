using System;
using System.IO;
using UnityEngine;

namespace Hot.Client
{
    /// <summary>Local-only UGC prototype: fixed-size PNG -> material texture override.</summary>
    public class UgcTextureLoader
    {
        public const int MaxBytes = 2 * 1024 * 1024;
        public const int MaxSize = 1024;

        public static bool TryLoad(string path, out Texture2D texture, out string error)
        {
            texture = null;
            error = null;
            try
            {
                if (!File.Exists(path)) { error = "missing file"; return false; }
                var info = new FileInfo(path);
                if (info.Length <= 0 || info.Length > MaxBytes) { error = "file size out of range"; return false; }

                byte[] bytes = File.ReadAllBytes(path);
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (!tex.LoadImage(bytes, true)) { error = "decode failed"; return false; }
                if (tex.width > MaxSize || tex.height > MaxSize) { error = "texture too large"; return false; }
                tex.filterMode = FilterMode.Point;
                tex.wrapMode = TextureWrapMode.Clamp;
                texture = tex;
                return true;
            }
            catch (Exception e)
            {
                error = e.Message;
                return false;
            }
        }
    }
}
