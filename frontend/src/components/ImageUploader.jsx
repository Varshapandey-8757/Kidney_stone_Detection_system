import { useEffect, useRef, useState } from "react";

const MAX_MB = 5;
const OK_TYPES = ["image/jpeg", "image/png"];

export default function ImageUploader({ file, onFile }) {
  const inputRef = useRef(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [over, setOver] = useState(false);

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const pick = (f) => {
    setError("");
    if (!f) return;
    if (!OK_TYPES.includes(f.type)) {
      onFile(null);
      return setError("Use a JPG or PNG image.");
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      onFile(null);
      return setError(`Image must be under ${MAX_MB} MB.`);
    }
    onFile(f);
  };

  return (
    <div>
      <div
        className={`scan-frame ${over ? "over" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files?.[0]); }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        aria-label="Choose an ultrasound image"
      >
        {preview ? (
          <img src={preview} alt="Selected ultrasound" />
        ) : (
          <p>Drop an ultrasound image here, or click to choose<br /><small>JPG or PNG, up to {MAX_MB} MB</small></p>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png"
        hidden
        onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ""; }}
      />
      {error && <p className="error" role="alert">{error}</p>}
    </div>
  );
}