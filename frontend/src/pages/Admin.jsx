import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import api, { errorMessage } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Admin() {
  const { user } = useAuth();
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const loadUsers = useCallback(async () => {
    setError("");
    try {
      const response = await api.get("/admin/users");
      setUsers(response.data);
    } catch (err) {
      setError(errorMessage(err, "Could not load users."));
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  if (user.role !== "admin") return <Navigate to="/" replace />;
  if (!users && !error) return <p className="muted">Loading users…</p>;

  const toggleActive = async (target) => {
    setError("");
    setBusyId(target.id);
    try {
      const response = await api.patch(`/admin/users/${target.id}/active`, null, {
        params: { active: !target.is_active },
      });
      setUsers((current) => current.map((item) => (
        item.id === target.id ? response.data : item
      )));
    } catch (err) {
      setError(errorMessage(err, "Could not update this account."));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section>
      <h1>Account administration</h1>
      <p className="muted">Review accounts and disable or restore access.</p>
      {error && <p className="error" role="alert">{error}</p>}
      {!users ? (
        <button className="link" onClick={loadUsers}>Retry</button>
      ) : (
        <div className="table-wrap">
          <table className="user-table">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Email</th>
                <th scope="col">Role</th>
                <th scope="col">Status</th>
                <th scope="col">Joined</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((account) => (
                <tr key={account.id}>
                  <td>{account.name}</td>
                  <td>{account.email}</td>
                  <td>{account.role}</td>
                  <td>{account.is_active ? "Active" : "Disabled"}</td>
                  <td>{new Date(`${account.created_at}Z`).toLocaleDateString()}</td>
                  <td>
                    <button
                      className={`link${account.is_active ? " danger" : ""}`}
                      disabled={busyId === account.id || account.id === user.id}
                      onClick={() => toggleActive(account)}
                    >
                      {busyId === account.id
                        ? "Saving…"
                        : account.is_active ? "Disable" : "Restore"}
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan="6" className="muted">No accounts found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
