import { useState } from "react";
import api, { errorMessage } from "../api/client.js";
import ImageUploader from "../components/ImageUploader.jsx";
import ResultCard from "../components/ResultCard.jsx";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const analyze = async () => {
    if (!file) return;
    setBusy(true); setError(""); setResult(null);
    const body = new FormData();
    body.append("file", file);
    try {
      setResult((await api.post("/predict", body)).data);
    } catch (err) {
      setError(errorMessage(err, "Analysis failed. Please try again."));
    } finally { setBusy(false); }
  };

  return (
    <div className="dash">
      <section>
        <h1>Analyze a kidney ultrasound</h1>
        <ImageUploader file={file} onFile={(f) => { setFile(f); setResult(null); setError(""); }} />
        <button className="primary" onClick={analyze} disabled={!file || busy}>
          {busy ? "Analyzing…" : "Analyze scan"}
        </button>
        {error && <p className="error" role="alert">{error}</p>}
      </section>
      {result && <ResultCard result={result} />}
    </div>
  );
}
