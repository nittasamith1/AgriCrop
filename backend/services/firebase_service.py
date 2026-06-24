"""
AgriCrop – Firebase Service
Initializes Firebase Admin SDK and exposes typed wrappers
for Firestore CRUD operations.
"""

import json
import os
import uuid
import base64
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1 import Client as FirestoreClient
from loguru import logger

from backend.config import settings

# ── Mock/Fallback Classes for Local Development ───────────────────────────────

class MockDocumentSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data

class MockDocumentReference:
    def __init__(self, collection, doc_id):
        self.collection = collection
        self.id = doc_id

    def get(self):
        data = self.collection._docs.get(self.id)
        return MockDocumentSnapshot(self.id, data)

    def set(self, data):
        self.collection._docs[self.id] = dict(data)
        return True

    def update(self, data):
        if self.id not in self.collection._docs:
            self.collection._docs[self.id] = {}
        self.collection._docs[self.id].update(data)
        return True

    def delete(self):
        if self.id in self.collection._docs:
            del self.collection._docs[self.id]
        return True

class MockQuery:
    def __init__(self, collection, filters=None, order_field=None, order_descending=False, limit_val=None):
        self.collection = collection
        self.filters = filters or []
        self.order_field = order_field
        self.order_descending = order_descending
        self.limit_val = limit_val

    def where(self, field, op, value):
        new_filters = list(self.filters)
        new_filters.append((field, op, value))
        return MockQuery(self.collection, new_filters, self.order_field, self.order_descending, self.limit_val)

    def order_by(self, field, direction=None):
        descending = False
        if direction:
            descending = "DESCENDING" in str(direction) or direction == -1
        return MockQuery(self.collection, self.filters, field, descending, self.limit_val)

    def limit(self, count):
        return MockQuery(self.collection, self.filters, self.order_field, self.order_descending, count)

    def stream(self):
        results = []
        for doc_id, data in self.collection._docs.items():
            match = True
            for field, op, value in self.filters:
                doc_val = data.get(field)
                if op == "==":
                    if doc_val != value:
                        match = False
                elif op == "<":
                    if doc_val is None or not (doc_val < value):
                        match = False
                elif op == "<=":
                    if doc_val is None or not (doc_val <= value):
                        match = False
                elif op == ">":
                    if doc_val is None or not (doc_val > value):
                        match = False
                elif op == ">=":
                    if doc_val is None or not (doc_val >= value):
                        match = False
                elif op == "in":
                    if doc_val not in value:
                        match = False
                elif op == "array_contains":
                    if not isinstance(doc_val, list) or value not in doc_val:
                        match = False
            if match:
                results.append((doc_id, data))

        if self.order_field:
            def sort_key(item):
                val = item[1].get(self.order_field)
                if val is None:
                    return "" if isinstance(self.order_field, str) else 0
                return val
            results.sort(key=sort_key, reverse=self.order_descending)

        if self.limit_val:
            results = results[:self.limit_val]

        return [MockDocumentSnapshot(doc_id, data) for doc_id, data in results]

class MockCollectionReference(MockQuery):
    def __init__(self, name):
        self.name = name
        self._docs = {}
        super().__init__(self)

    def document(self, document_id=None):
        if not document_id:
            document_id = uuid.uuid4().hex
        return MockDocumentReference(self, document_id)

class MockFirestoreClient:
    def __init__(self):
        self._collections = {}

    def collection(self, name):
        if name not in self._collections:
            self._collections[name] = MockCollectionReference(name)
        return self._collections[name]


# Module-level Firebase app and Firestore client
_firebase_app: Optional[Any] = None
_firestore_client: Optional[Any] = None
_mock_users_db = {}


def _setup_mock_fallback():
    global _firestore_client, _firebase_app
    logger.warning("⚠️ Running in development mode without valid Firebase credentials.")
    logger.info("Initializing in-memory Mock Firestore, Mock Auth, and Mock Storage...")
    
    _firestore_client = MockFirestoreClient()
    
    # Patch Auth
    import firebase_admin.auth as fb_auth
    
    class MockUserRecord:
        def __init__(self, uid, email, display_name):
            self.uid = uid
            self.email = email
            self.display_name = display_name
            self.email_verified = True
            
    def mock_create_user(email, password=None, display_name=None, email_verified=False, uid=None):
        if not uid:
            uid = "mock-uid-" + base64.b64encode(email.encode()).decode().replace("=", "")[:10]
        user_rec = MockUserRecord(uid, email, display_name)
        _mock_users_db[uid] = {
            "uid": uid,
            "email": email,
            "name": display_name or email.split("@")[0].capitalize(),
            "role": "admin" if "admin" in email else "farmer"
        }
        return user_rec

    def mock_verify_id_token(token, check_revoked=True):
        email = "farmer@example.com"
        if token.startswith("mock-token-"):
            email = token.replace("mock-token-", "")
        elif token == "mock-admin-token":
            email = "admin@agricrop.com"
        elif token == "mock-farmer-token":
            email = "farmer@example.com"
            
        uid = "mock-uid-" + base64.b64encode(email.encode()).decode().replace("=", "")[:10]
        role = "admin" if "admin" in email else "farmer"
        name = email.split("@")[0].capitalize()
        
        if uid not in _mock_users_db:
            _mock_users_db[uid] = {
                "uid": uid,
                "email": email,
                "name": name,
                "role": role,
                "email_verified": True
            }
        return {
            "uid": uid,
            "email": email,
            "name": name,
            "role": role,
            "email_verified": True
        }

    def mock_generate_email_verification_link(email, action_code_settings=None):
        return f"http://localhost:8000/api/v1/auth/verify-email?email={email}"

    def mock_generate_password_reset_link(email, action_code_settings=None):
        return f"http://localhost:8000/api/v1/auth/reset-password?email={email}"

    def mock_get_user(uid):
        if uid in _mock_users_db:
            u = _mock_users_db[uid]
            return MockUserRecord(u["uid"], u["email"], u.get("name"))
        return MockUserRecord(uid, "farmer@example.com", "Mock Farmer")
        
    fb_auth.create_user = mock_create_user
    fb_auth.verify_id_token = mock_verify_id_token
    fb_auth.generate_email_verification_link = mock_generate_email_verification_link
    fb_auth.generate_password_reset_link = mock_generate_password_reset_link
    fb_auth.get_user = mock_get_user
    
    # Patch Storage
    import firebase_admin.storage as fb_storage
    
    class MockStorageBlob:
        def __init__(self, bucket, name):
            self.bucket = bucket
            self.name = name
            self.public_url = f"http://localhost:8000/static/uploads/{name}"
            
        def upload_from_string(self, content, content_type=None):
            logger.info(f"[Mock Storage] Uploading blob: {self.name}")
            local_path = os.path.join(settings.UPLOAD_TEMP_DIR, self.name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(content)
            return True
            
        def make_public(self):
            return True
            
        def generate_signed_url(self, expiration, method=None):
            return self.public_url
            
        def delete(self):
            logger.info(f"[Mock Storage] Deleting blob: {self.name}")
            local_path = os.path.join(settings.UPLOAD_TEMP_DIR, self.name)
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception as ex:
                    logger.error(f"Failed to delete local mock storage file: {ex}")
            return True
            
    class MockStorageBucket:
        def blob(self, name):
            return MockStorageBlob(self, name)
            
    def mock_bucket(name=None):
        return MockStorageBucket()
        
    fb_storage.bucket = mock_bucket
    
    class DummyApp:
        pass
    _firebase_app = DummyApp()
    logger.success("✅ Mock Firebase environment initialized successfully")
    return _firebase_app


def initialize_firebase() -> firebase_admin.App:
    """
    Initialize the Firebase Admin SDK (idempotent).
    Prefers a local serviceAccountKey.json file; falls back
    to building credentials from individual env vars.
    """
    global _firebase_app, _firestore_client

    if _firebase_app is not None:
        return _firebase_app

    is_configured = True
    if not settings.FIREBASE_PROJECT_ID or settings.FIREBASE_PROJECT_ID == "your-firebase-project-id":
        is_configured = False
    if not settings.FIREBASE_API_KEY or settings.FIREBASE_API_KEY == "your-firebase-api-key":
        is_configured = False

    if not is_configured:
        if settings.APP_ENV == "production":
            raise RuntimeError("Missing or invalid Firebase credentials in production environment.")
        return _setup_mock_fallback()

    try:
        # Attempt 1: local service account JSON file
        if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            logger.info(f"Firebase: loading credentials from {settings.FIREBASE_SERVICE_ACCOUNT_PATH}")
        else:
            # Attempt 2: build credentials dict from env vars
            service_account_info = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
                "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "client_id": settings.FIREBASE_CLIENT_ID,
                "auth_uri": settings.FIREBASE_AUTH_URI,
                "token_uri": settings.FIREBASE_TOKEN_URI,
            }
            cred = credentials.Certificate(service_account_info)
            logger.info("Firebase: loading credentials from environment variables")

        # Initialize the app
        _firebase_app = firebase_admin.initialize_app(cred, {
            "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
        })

        # Set Firestore emulator if configured
        if settings.USE_FIRESTORE_EMULATOR and settings.FIRESTORE_EMULATOR_HOST:
            os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIRESTORE_EMULATOR_HOST
            logger.info(f"Using Firestore emulator: {settings.FIRESTORE_EMULATOR_HOST}")

        _firestore_client = firestore.client()
        logger.success("✅ Firebase Admin SDK initialized successfully")
        return _firebase_app

    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        if settings.APP_ENV == "production":
            raise RuntimeError(f"Firebase initialization failed: {e}")
        return _setup_mock_fallback()


def get_firestore_client() -> FirestoreClient:
    """Return the active Firestore client, initializing if needed."""
    global _firestore_client
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client


# ── Firestore CRUD Helpers ────────────────────────────────────────────────────

class FirestoreService:
    """
    Generic Firestore CRUD service.
    All methods are synchronous (Firestore Admin SDK is sync).
    All returned dicts are JSON-safe (datetimes converted to ISO strings).
    """

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    @property
    def collection(self):
        return get_firestore_client().collection(self.collection_name)

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """
        Convert a value to a JSON-safe type.
        Handles Firestore DatetimeWithNanoseconds, Python datetime, and nested dicts/lists.
        """
        import datetime as dt
        if value is None:
            return None
        # Firestore Timestamp / Python datetime → ISO string
        if hasattr(value, 'isoformat'):
            try:
                return value.isoformat()
            except Exception:
                return str(value)
        # Nested dict
        if isinstance(value, dict):
            return {k: FirestoreService._serialize_value(v) for k, v in value.items()}
        # Nested list
        if isinstance(value, list):
            return [FirestoreService._serialize_value(i) for i in value]
        return value

    @classmethod
    def _serialize_doc(cls, doc_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize all values in a Firestore document dict to JSON-safe types."""
        return {k: cls._serialize_value(v) for k, v in doc_dict.items()}

    def create(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or overwrite a document."""
        self.collection.document(doc_id).set(data)
        return {"id": doc_id, **data}

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single document by ID. Returns None if not found."""
        doc = self.collection.document(doc_id).get()
        if doc.exists:
            raw = doc.to_dict() or {}
            return self._serialize_doc({"id": doc.id, **raw})
        return None

    def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update specific fields in a document."""
        try:
            self.collection.document(doc_id).update(data)
        except Exception:
            # Document may not exist yet — use set with merge
            self.collection.document(doc_id).set(data, merge=True)
        return True

    def delete(self, doc_id: str) -> bool:
        """Delete a document."""
        self.collection.document(doc_id).delete()
        return True

    def list_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return all documents in the collection (up to limit)."""
        docs = self.collection.limit(limit).stream()
        return [self._serialize_doc({"id": d.id, **(d.to_dict() or {})}) for d in docs]

    def query(
        self,
        field: str,
        op: str,
        value: Any,
        order_by: Optional[str] = None,
        limit: int = 50,
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Simple single-field query.
        op: '==' | '<' | '<=' | '>' | '>=' | 'in' | 'array_contains'
        """
        try:
            q = self.collection.where(field, op, value)
            if order_by:
                try:
                    direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
                    q = q.order_by(order_by, direction=direction)
                except Exception:
                    pass  # order_by may fail if index not created; results still returned
            q = q.limit(limit)
            return [self._serialize_doc({"id": d.id, **(d.to_dict() or {})}) for d in q.stream()]
        except Exception as e:
            logger.error(f"Firestore query failed ({self.collection_name}): {e}")
            return []

    def query_by_user(self, user_id: str, limit: int = 50, order_by: str = "created_at") -> List[Dict[str, Any]]:
        """Convenience: query all docs belonging to a specific user."""
        return self.query("user_id", "==", user_id, order_by=order_by, limit=limit)

    def count(self, field: Optional[str] = None, value: Any = None) -> int:
        """Count documents (optionally filtered)."""
        try:
            if field and value is not None:
                docs = self.collection.where(field, "==", value).stream()
            else:
                docs = self.collection.stream()
            return sum(1 for _ in docs)
        except Exception as e:
            logger.error(f"Firestore count failed ({self.collection_name}): {e}")
            return 0
