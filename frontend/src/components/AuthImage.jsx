import { useEffect, useState } from "react";
import api from "../api/client.js";

// Images are protected by the API, so they're fetched with the token and shown from a blob URL.
export default function AuthImage({ path, alt }) {
  const [src, setSrc] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let url;
    let cancelled = false;
    setSrc(null);
    setFailed(false);
    api.get(path, { responseType: "blob" })
      .then((r) => {
        if (cancelled) return;
        url = URL.createObjectURL(r.data);
        setSrc(url);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [path]);

  if (failed) return <div className="img-placeholder">Image unavailable</div>;
  if (!src) return <div className="img-placeholder">Loading…</div>;
  return <img src={src} alt={alt} />;
}