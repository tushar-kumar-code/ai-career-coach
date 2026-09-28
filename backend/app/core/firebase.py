import os
import json
import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None
_firestore_client: Any = None
_storage_bucket: Any = None


def get_firebase_app() -> Optional[firebase_admin.App]:
    """
    Initializes or retrieves the Firebase Admin App instance safely.
    Supports:
    1. Service account JSON file path (FIREBASE_CREDENTIALS_PATH)
    2. Service account JSON raw string (FIREBASE_SERVICE_ACCOUNT_JSON)
    3. Project ID / Application Default Credentials (FIREBASE_PROJECT_ID)
    4. Firebase Auth Emulator (FIREBASE_AUTH_EMULATOR_HOST)
    """
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    if firebase_admin._apps:
        _firebase_app = firebase_admin.get_app()
        return _firebase_app

    try:
        cred = None
        # Option 1: Inline service account JSON from environment variable
        if settings.FIREBASE_SERVICE_ACCOUNT_JSON and settings.FIREBASE_SERVICE_ACCOUNT_JSON.strip():
            try:
                sa_data = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
                cred = credentials.Certificate(sa_data)
            except Exception as e:
                logger.error(f"Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

        # Option 2: Path to service account JSON file
        elif settings.FIREBASE_CREDENTIALS_PATH and settings.FIREBASE_CREDENTIALS_PATH.strip():
            cert_path = settings.FIREBASE_CREDENTIALS_PATH.strip()
            if os.path.exists(cert_path):
                cred = credentials.Certificate(cert_path)
            else:
                logger.warning(f"FIREBASE_CREDENTIALS_PATH specified but file not found: {cert_path}")

        options: Dict[str, Any] = {}
        if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PROJECT_ID.strip():
            options["projectId"] = settings.FIREBASE_PROJECT_ID.strip()

        if cred:
            _firebase_app = firebase_admin.initialize_app(cred, options=options if options else None)
            logger.info("Firebase Admin initialized successfully with Service Account credentials.")
        else:
            # Fallback to Application Default Credentials or Project Options (works with emulator too)
            _firebase_app = firebase_admin.initialize_app(options=options if options else None)
            logger.info("Firebase Admin initialized with default credentials / project options.")

        return _firebase_app
    except Exception as e:
        logger.warning(f"Firebase Admin initialization notice: {e}")
        return None


def verify_firebase_id_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token using Firebase Admin SDK.
    Raises Exception if token is invalid or expired.
    Returns decoded token dictionary containing 'uid', 'email', 'name', etc.
    """
    get_firebase_app()
    decoded = auth.verify_id_token(token, check_revoked=False)
    return decoded


def get_firestore_client() -> Any:
    """Returns the Firestore client instance safely."""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client
    app = get_firebase_app()
    if app:
        try:
            _firestore_client = firestore.client(app=app)
        except Exception as e:
            logger.warning(f"Firestore client initialization notice: {e}")
    return _firestore_client


def get_storage_bucket() -> Any:
    """Returns the default Firebase Storage bucket instance safely."""
    global _storage_bucket
    if _storage_bucket is not None:
        return _storage_bucket
    app = get_firebase_app()
    if app:
        try:
            bucket_name = settings.FIREBASE_STORAGE_BUCKET.strip() if settings.FIREBASE_STORAGE_BUCKET else None
            if not bucket_name and settings.FIREBASE_PROJECT_ID.strip():
                bucket_name = f"{settings.FIREBASE_PROJECT_ID.strip()}.appspot.com"
            if bucket_name:
                _storage_bucket = storage.bucket(bucket_name, app=app)
            else:
                _storage_bucket = storage.bucket(app=app)
        except Exception as e:
            logger.warning(f"Firebase Storage bucket initialization notice: {e}")
    return _storage_bucket
