def test_admin_can_list_and_disable_users(client, make_user):
    admin_id = make_user(email="admin@example.com", role="admin")
    target_id = make_user(email="target@example.com")
    token = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Strong-Pass-123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    listed = client.get("/admin/users", headers=headers)
    assert listed.status_code == 200
    assert {user["id"] for user in listed.json()} == {admin_id, target_id}

    updated = client.patch(
        f"/admin/users/{target_id}/active",
        params={"active": "false"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

    self_update = client.patch(
        f"/admin/users/{admin_id}/active",
        params={"active": "false"},
        headers=headers,
    )
    assert self_update.status_code == 400


def test_regular_user_cannot_manage_accounts(client, auth_headers):
    response = client.get("/admin/users", headers=auth_headers)
    assert response.status_code == 403
