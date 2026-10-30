import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      await register(form.name, form.email, form.password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(errorMessage(err, "Could not create the account."));
    } finally { setBusy(false); }
  };

  return (
    <div className="auth-box">
      <h1>Create account</h1>
      <form onSubmit={submit}>
        <label>Name
          <input value={form.name} onChange={set("name")} required minLength={2} autoComplete="name" />
        </label>
        <label>Email
          <input type="email" value={form.email} onChange={set("email")} required autoComplete="email" />
        </label>
        <label>Password
          <input type="password" value={form.password} onChange={set("password")} required minLength={8} autoComplete="new-password" />
          <small>At least 8 characters with an uppercase letter, a lowercase letter and a digit.</small>
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
      </form>
      <p className="muted">Already registered? <Link to="/login">Log in</Link></p>
    </div>
  );
}