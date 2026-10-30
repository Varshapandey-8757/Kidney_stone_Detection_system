import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const onLogout = async () => {
    setError("");
    try {
      await logout();
      navigate("/login");
    } catch (err) {
      setError(errorMessage(err, "Could not end the session. Please try again."));
    }
  };

  return (
    <header className="nav">
      <span className="brand">Renal Scan</span>
      {user && (
        <nav>
          <NavLink to="/" end>Analyze</NavLink>
          <NavLink to="/history">History</NavLink>
          {user.role === "admin" && <NavLink to="/admin">Admin</NavLink>}
          <span className="nav-user">{user.name}</span>
          <button className="link" onClick={onLogout}>Log out</button>
        </nav>
      )}
      {error && <p className="error" role="alert">{error}</p>}
    </header>
  );
}