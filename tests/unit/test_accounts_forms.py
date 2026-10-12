from __future__ import annotations

from apps.accounts.forms import SignupForm
from apps.accounts.repository import UserRepository


def test_signup_rejects_password_similar_to_username_without_error(
    monkeypatch,
) -> None:
    monkeypatch.setattr(UserRepository, "username_taken_ci", lambda self, username: False)
    form = SignupForm(
        {
            "username": "newperson-account",
            "password1": "newperson-account",
            "password2": "newperson-account",
        }
    )

    assert not form.is_valid()
    assert "password2" in form.errors
    assert "too similar to the username" in str(form.errors["password2"])
