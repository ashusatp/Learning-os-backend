import logging

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.custom_exceptions import AlreadyExistsException, BadRequestException, InvalidCredentialsException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import create_access_token

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register(self, email: str, password: str, name: str):

        db = self.user_repository.db

        try:
            existing = await self.user_repository.get_by_email(email)

            if existing:
                raise AlreadyExistsException("User with this email already exists")

            hashed = hash_password(password)

            user = User(
                email=email,
                password_hash=hashed,
                name=name,
            )

            await self.user_repository.create(user)

            await db.commit()
            await db.refresh(user)

            logger.info(f"User registered: {email}")

            token = create_access_token(user.id)

            return {"access_token": token, "user": user}

        except AlreadyExistsException:
            raise

        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error while registering user: {email}")
            raise

        except Exception:
            await db.rollback()
            logger.exception(f"Error while registering user: {email}")
            raise

    async def login(self, email: str, password: str):

        user = await self.user_repository.get_by_email(email)

        if not user:
            raise InvalidCredentialsException()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        logger.info(f"User logged in: {email}")

        token = create_access_token(user.id)

        return {"access_token": token, "user": user}

    async def google_auth(self, code: str):
        import httpx
        from app.core.config import configs

        db = self.user_repository.db

        try:
            # Exchange code for tokens
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": configs.GOOGLE_CLIENT_ID,
                        "client_secret": configs.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": configs.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code",
                    },
                )

                if token_response.status_code != 200:
                    raise BadRequestException("Failed to exchange authorization code")

                token_data = token_response.json()
                access_token = token_data["access_token"]

                # Fetch user info
                userinfo_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                if userinfo_response.status_code != 200:
                    raise BadRequestException("Failed to fetch user info from Google")

                google_user = userinfo_response.json()

            google_id = google_user["id"]
            email = google_user["email"]
            name = google_user.get("name", email.split("@")[0])

            # Check if user exists by provider
            user = await self.user_repository.get_by_provider("google", google_id)

            if not user:
                # Check by email
                user = await self.user_repository.get_by_email(email)

                if user:
                    # Link existing account
                    user.auth_provider = "google"
                    user.auth_provider_id = google_id
                else:
                    # Create new user
                    user = User(
                        email=email,
                        name=name,
                        auth_provider="google",
                        auth_provider_id=google_id,
                    )
                    await self.user_repository.create(user)

            await db.commit()
            await db.refresh(user)

            logger.info(f"Google auth successful: {email}")

            jwt_token = create_access_token(user.id)

            return {"access_token": jwt_token, "user": user}

        except (BadRequestException, AlreadyExistsException):
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception(f"Database error during Google auth")
            raise
        except Exception:
            await db.rollback()
            logger.exception(f"Error during Google auth")
            raise
