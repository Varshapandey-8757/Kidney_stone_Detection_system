import { useEffect, useState } from "react";
import api, { errorMessage } from "../api/client.js";
import ResultCard from "../components/ResultCard.jsx";

export default function History() {
  const [items, setItems] = useState(null);
  const [open, setOpen] = useState(null);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    api.get("/history?limit=50")
      .then((r) => setItems(r.data))
      .catch((e) => setError(errorMessage(e, "Could not load history.")));
  }, []);

  const remove = async (id) => {
    if (!window.confirm("Delete this scan and its result permanently?")) return;
    setActionError("");
    try {
      await api.delete(`/history/${id}`);
      setItems((list) => list.filter((i) => i.id !== id));
      if (open?.id === id) setOpen(null);
    } catch (e) { setActionError(errorMessage(e, "Could not delete.")); }
  };

  if (error) return <p className="error">{error}</p>;
  if (!items) return <p className="muted">Loading…</p>;

  return (
    <div className="dash">
      <section>
        <h1>History</h1>
        {actionError && <p className="error" role="alert">{actionError}</p>}
        {items.length === 0 && <p className="muted">No scans yet. Analyze one on the first page.</p>}
        <ul className="history">
          {items.map((i) => (
            <li key={i.id} className={open?.id === i.id ? "active" : ""}>
              <button className="row" onClick={() => setOpen(i)}>
                <strong className={i.result === "Stone" ? "tag stone" : "tag clear"}>{i.result}</strong>
                <span>{(i.confidence * 100).toFixed(1)}%</span>
                <span className="muted">{new Date(i.created_at + "Z").toLocaleString()}</span>
              </button>
              <button className="link danger" onClick={() => remove(i.id)}>Delete</button>
            </li>
          ))}
        </ul>
      </section>
      {open && <ResultCard result={open} />}
    </div>
  );
}