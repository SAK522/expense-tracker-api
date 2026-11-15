"""
Authentication routes: /auth/signup and /auth/login.

WHY a separate router file:
Grouping related endpoints into a "router" keeps main.py tiny and the project
navigable. As the app grows (transactions, summary...), each group gets its
own file instead of one giant main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import UserCreate, UserOut, Token
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create an account.
    Steps: reject duplicate email -> hash the password -> save -> return the
    safe public view (UserOut has no password field, so none can leak).
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)       # reload so user.id / created_at are populated
    return user


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Log in and receive a JWT.
    We use OAuth2PasswordRequestForm (fields: username, password) because it's
    the standard FastAPI login shape and makes the /docs 'Authorize' button
    work out of the box. Here 'username' is the user's email.

    SECURITY NOTE: whether the email is unknown OR the password is wrong, we
    return the SAME 401 message. Telling them 'no such email' would let an
    attacker discover which emails are registered.
    """
    user = db.query(User).filter(User.email == form.username).first()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def who_am_i(current_user: User = Depends(get_current_user)):
    """Return the account that owns the token (handy for checking auth)."""
    return current_user
