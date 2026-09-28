import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from app.core.firebase import get_firestore_client, get_storage_bucket

logger = logging.getLogger(__name__)

# Thread-safe in-memory fallback store when live GCP Firestore is not connected (e.g. unit tests / offline dev)
_MEM_STORE: Dict[str, Dict[str, Any]] = {}
_MEM_STORAGE: Dict[str, bytes] = {}


def _get_path_key(path: str) -> str:
    return path.strip("/").lower()


class FirestoreClient:
    """
    Asynchronous, non-blocking interface to Google Cloud Firestore.
    Runs blocking gRPC/HTTP calls in background threads via asyncio.to_thread.
    Falls back gracefully to an in-memory document store for test suites or offline development.
    """

    @staticmethod
    def _is_live() -> bool:
        import os
        if os.environ.get("FIRESTORE_EMULATOR_HOST"):
            return True
        from app.core.config import settings
        if settings.FIREBASE_SERVICE_ACCOUNT_JSON and settings.FIREBASE_SERVICE_ACCOUNT_JSON.strip():
            return True
        if settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH.strip()):
            return True
        return False

    @classmethod
    async def get_document(cls, path: str) -> Optional[Dict[str, Any]]:
        """Fetch a single document by its path (e.g. 'users/uid123' or 'users/uid123/resumes/res456')."""
        if cls._is_live():
            try:
                client = get_firestore_client()
                doc_ref = client.document(path)
                snapshot = await asyncio.to_thread(doc_ref.get)
                if snapshot.exists:
                    data = snapshot.to_dict() or {}
                    data["id"] = snapshot.id
                    return data
                return None
            except Exception as e:
                logger.warning(f"Firestore live get failed for {path}, falling back: {e}")

        # In-memory store
        key = _get_path_key(path)
        data = _MEM_STORE.get(key)
        if data:
            copy = dict(data)
            copy["id"] = path.split("/")[-1]
            return copy
        return None

    @classmethod
    async def set_document(cls, path: str, data: Dict[str, Any], merge: bool = True) -> Dict[str, Any]:
        """Create or update a document at path."""
        data_clean = dict(data)
        doc_id = path.split("/")[-1]
        data_clean["id"] = doc_id

        if cls._is_live():
            try:
                client = get_firestore_client()
                doc_ref = client.document(path)
                await asyncio.to_thread(doc_ref.set, data_clean, merge=merge)
                return data_clean
            except Exception as e:
                logger.warning(f"Firestore live set failed for {path}, falling back: {e}")

        key = _get_path_key(path)
        if merge and key in _MEM_STORE:
            _MEM_STORE[key].update(data_clean)
        else:
            _MEM_STORE[key] = data_clean
        return dict(_MEM_STORE[key])

    @classmethod
    async def delete_document(cls, path: str) -> bool:
        """Delete a document at path."""
        if cls._is_live():
            try:
                client = get_firestore_client()
                doc_ref = client.document(path)
                await asyncio.to_thread(doc_ref.delete)
                return True
            except Exception as e:
                logger.warning(f"Firestore live delete failed for {path}: {e}")

        key = _get_path_key(path)
        return _MEM_STORE.pop(key, None) is not None

    @classmethod
    async def query_collection(
        cls,
        collection_path: str,
        filters: Optional[List[Tuple[str, str, Any]]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents in a collection or subcollection.
        Filters format: [('is_active', '==', True), ('priority', '==', 'High')]
        """
        filters = filters or []
        col_prefix = _get_path_key(collection_path) + "/"

        if cls._is_live():
            try:
                client = get_firestore_client()
                query = client.collection(collection_path)
                for field, op, val in filters:
                    query = query.where(field, op, val)
                if order_by:
                    import google.cloud.firestore as gcf
                    direction = gcf.Query.DESCENDING if descending else gcf.Query.ASCENDING
                    query = query.order_by(order_by, direction=direction)
                if limit:
                    query = query.limit(limit)

                docs = await asyncio.to_thread(query.get)
                results = []
                for d in docs:
                    item = d.to_dict() or {}
                    item["id"] = d.id
                    results.append(item)
                return results
            except Exception as e:
                logger.warning(f"Firestore live query failed for {collection_path}, falling back: {e}")

        # In-memory query
        results = []
        for k, v in _MEM_STORE.items():
            if k.startswith(col_prefix) and k.count("/") == col_prefix.count("/"):
                match = True
                for field, op, val in filters:
                    actual = v.get(field)
                    if op == "==" and actual != val:
                        match = False
                        break
                    elif op == "!=" and actual == val:
                        match = False
                        break
                    elif op == ">" and not (actual and actual > val):
                        match = False
                        break
                    elif op == "<" and not (actual and actual < val):
                        match = False
                        break
                if match:
                    item = dict(v)
                    item["id"] = k.split("/")[-1]
                    results.append(item)

        if order_by:
            results.sort(key=lambda x: str(x.get(order_by, "")), reverse=descending)
        if limit:
            results = results[:limit]
        return results

    @classmethod
    async def upload_file(cls, storage_path: str, content: bytes, content_type: Optional[str] = None) -> str:
        """Uploads bytes to Firebase Storage bucket and returns the storage path / URI."""
        if cls._is_live():
            bucket = get_storage_bucket()
            if bucket:
                try:
                    blob = bucket.blob(storage_path)
                    await asyncio.to_thread(blob.upload_from_string, content, content_type=content_type)
                    return f"gs://{bucket.name}/{storage_path}"
                except Exception as e:
                    logger.warning(f"Firebase Storage upload failed for {storage_path}: {e}")

        # In-memory fallback
        _MEM_STORAGE[storage_path] = content
        return f"gs://fallback-bucket/{storage_path}"

    @classmethod
    async def download_file(cls, storage_path: str) -> Optional[bytes]:
        """Downloads bytes from Firebase Storage bucket."""
        clean_path = storage_path.replace("gs://", "").split("/", 1)[-1] if "gs://" in storage_path else storage_path
        if cls._is_live():
            bucket = get_storage_bucket()
            if bucket:
                try:
                    blob = bucket.blob(clean_path)
                    return await asyncio.to_thread(blob.download_as_bytes)
                except Exception as e:
                    logger.warning(f"Firebase Storage download failed for {clean_path}: {e}")

        return _MEM_STORAGE.get(clean_path) or _MEM_STORAGE.get(storage_path)

    @classmethod
    def clear_test_data(cls):
        """Utility for test suites to reset memory store."""
        _MEM_STORE.clear()
        _MEM_STORAGE.clear()
