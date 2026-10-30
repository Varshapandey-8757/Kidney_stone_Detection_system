import AuthImage from "./AuthImage.jsx";

export default function ResultCard({ result }) {
  const stone = result.result === "Stone";
  return (
    <section className={`result ${stone ? "stone" : "clear"}`} aria-live="polite">
      <h2>{stone ? "Stone detected" : "No stone detected"}</h2>
      <p className="confidence">Confidence {(result.confidence * 100).toFixed(1)}%</p>
      <div className="pair">
        <figure>
          <AuthImage path={`/history/${result.id}/image`} alt="Uploaded scan" />
          <figcaption>Your scan</figcaption>
        </figure>
        <figure>
          <AuthImage path={`/history/${result.id}/gradcam`} alt="Heatmap of regions the model focused on" />
          <figcaption>Where the model looked</figcaption>
        </figure>
      </div>
      <p className="muted small">
        Research prototype. This is decision support only and not a medical diagnosis.
        Please consult a doctor.
      </p>
    </section>
  );
}