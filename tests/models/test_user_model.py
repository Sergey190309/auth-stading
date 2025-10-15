from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from src.core.settings import settings
from src.models.user_model import User


# @pytest.mark.active
def test_hash_password_creates_valid_bcrypt_hash(raw_password: str) -> None:
    """Ensure password hashing produces a valid bcrypt hash string."""
    hashed_password: str = User.hash_password(raw_password)
    print(f'\n\nhashed_password: {hashed_password}\n\n')
    assert isinstance(hashed_password, str)
    assert hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$')
    # bcrypt should verify successfully
    assert bcrypt.checkpw(raw_password.encode(), hashed_password.encode())


# @pytest.mark.active
def test_validate_password_success(test_user: User, raw_password: str) -> None:
    """User.validate_password should return True for correct password."""
    assert test_user.validate_password(raw_password) is True

    """User.validate_password should return False for wrong password."""
    assert test_user.validate_password('WrongPassword') is False


# @pytest.mark.active
def test_generate_token_returns_valid_jwt(test_user: User) -> None:
    """User.generate_token should return a valid JWT with correct claims."""
    token_dict: dict[str, str] = test_user.generate_token()
    token: str = token_dict['access_token']

    assert isinstance(token, str)
    assert len(token) > 10

    decoded_payload = jwt.decode(
        token,
        str(settings.secret_key),
        algorithms=[str(settings.algorithm)],
    )

    # print(f'\n\ntoken_dict: {token_dict}')
    # print(f'decoded_payload: {decoded_payload}\n\n')

    assert decoded_payload['user_id'] == str(test_user.id)
    assert 'exp' in decoded_payload

    exp_time = datetime.fromtimestamp(decoded_payload['exp'], tz=timezone.utc)
    expected_min = datetime.now(timezone.utc)
    expected_max = expected_min + timedelta(
        minutes=settings.access_token_expire_minutes + 1
    )
    assert expected_min < exp_time < expected_max


# @pytest.mark.active
def test_generate_token_contains_required_fields(test_user: User) -> None:
    """Ensure returned token dict contains exactly 'access_token'."""
    token_data: dict[str, str] = test_user.generate_token()
    print(f'\n\ntoken_data: {token_data}\n\n')
    assert set(token_data.keys()) == {'access_token'}
    assert isinstance(token_data['access_token'], str)
