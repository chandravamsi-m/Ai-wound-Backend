import firebase_admin
from firebase_admin import credentials, firestore
import os
from django.conf import settings

class FirestoreService:
    _db = None

    @classmethod
    def get_db(cls):
        if cls._db is None:
            # Initialize Firebase Admin SDK
            cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
            
            # If path is relative, make it absolute relative to BASE_DIR
            if not os.path.isabs(cred_path):
                cred_path = os.path.join(settings.BASE_DIR, cred_path)
            
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Firebase service account file not found at {cred_path}")

            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            cls._db = firestore.client()
        return cls._db

    @classmethod
    def collection(cls, name):
        return cls.get_db().collection(name)

    @classmethod
    def get_document(cls, collection_name, doc_id):
        doc_ref = cls.collection(collection_name).document(str(doc_id))
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    @classmethod
    def create_document(cls, collection_name, data, doc_id=None):
        if doc_id:
            doc_ref = cls.collection(collection_name).document(str(doc_id))
            doc_ref.set(data)
            return doc_id
        else:
            _, doc_ref = cls.collection(collection_name).add(data)
            return doc_ref.id

    @classmethod
    def update_document(cls, collection_name, doc_id, data):
        doc_ref = cls.collection(collection_name).document(str(doc_id))
        doc_ref.update(data)

    @classmethod
    def delete_document(cls, collection_name, doc_id):
        cls.collection(collection_name).document(str(doc_id)).delete()

    @classmethod
    def query(cls, collection_name, field, operator, value, limit=None):
        query = cls.collection(collection_name).where(field, operator, value)
        if limit:
            query = query.limit(limit)
        docs = query.stream()
        return [doc.to_dict() | {'id': doc.id} for doc in docs]

    @classmethod
    def count(cls, collection_name, filters=None):
        """
        Efficiently count documents using Firestore Aggregation (Count).
        filters: list of tuples (field, operator, value)
        """
        query = cls.collection(collection_name)
        if filters:
            for field, op, val in filters:
                query = query.where(field, op, val)
        
        # Using aggregation query for near-zero read cost
        results = query.count().get()
        return results[0][0].value
