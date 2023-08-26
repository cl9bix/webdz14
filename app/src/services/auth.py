from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import settings



class Auth:
     
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    """
    Клас для автентифікації та генерації токенів.

    Використовується для перевірки паролів, створення та перевірки JWT токенів.
    """

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)
        """
        Перевірка пароля.

        :param plain_password: Пароль від користувача.
        :type plain_password: str
        :param hashed_password: Хеш пароля.
        :type hashed_password: str
        :return: True, якщо пароль співпадає, інакше False.
        :rtype: bool
        """

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)
        """
        Отримання хешу пароля.

        :param password: Пароль користувача.
        :type password: str
        :return: Хеш пароля.
        :rtype: str
        """

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=150)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token
        """
        Створення токену доступу.

        :param data: Дані для включення в токен.
        :type data: dict
        :param expires_delta: Опціональний параметр для вказання терміну дії токену.
        :type expires_delta: Optional[float]
        :return: Згенерований токен доступу.
        :rtype: str
        """

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token
        """
        Створення токену доступу.

        :param data: Дані для включення в токен.
        :type data: dict
        :param expires_delta: Опціональний параметр для вказання терміну дії токену.
        :type expires_delta: Optional[float]
        :return: Згенерований токен доступу.
        :rtype: str
        """

    async def decode_refresh_token(self, refresh_token: str):
        
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')
        """
        Розкодування токену оновлення.

        :param refresh_token: Токен оновлення.
        :type refresh_token: str
        :return: Email з токену оновлення.
        :rtype: str
        """
    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception
        

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user
        """
        Отримання поточного користувача на основі токену.

        :param token: Токен доступу.
        :type token: str
        :param db: Сесія бази даних.
        :type db: Session
        :return: Об'єкт користувача.
        :rtype: User
        """
    
    def create_email_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
        """
        Створення токену для підтвердження електронної пошти.

        :param data: Дані для включення в токен.
        :type data: dict
        :return: Згенерований токен.
        :rtype: str
        """

    async def get_email_from_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


        """
        Отримання електронної пошти з токену.

        :param token: Токен для підтвердження електронної пошти.
        :type token: str
        :return: Електронна пошта.
        :rtype: str
        """
auth_service = Auth()