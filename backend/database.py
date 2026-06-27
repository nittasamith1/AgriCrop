"""
AgriCrop – MongoDB Database Client Setup
Handles Motor client connections, GridFS setup, and automatic database indexing.
"""

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from backend.config import settings

import sys
import socket
from urllib.parse import urlparse
import pymongo.errors

class Database:
    """Async database client wrapper for Motor (MongoDB)."""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None
        self.gridfs_bucket: AsyncIOMotorGridFSBucket = None
        self.is_connected = False

    @staticmethod
    def diagnose_connection_error(uri: str, error: Exception) -> str:
        """Analyze connection error to distinguish URI, DNS, auth, or network issues."""
        if not (uri.startswith("mongodb://") or uri.startswith("mongodb+srv://")):
            return "Invalid URI: Connection string must start with 'mongodb://' or 'mongodb+srv://'."
        
        host_part = "unknown"
        try:
            if "@" in uri:
                host_part = uri.split("@")[-1].split("/")[0].split("?")[0]
            else:
                scheme_len = len("mongodb+srv://") if uri.startswith("mongodb+srv://") else len("mongodb://")
                host_part = uri[scheme_len:].split("/")[0].split("?")[0]
        except Exception:
            return "Invalid URI: Failed to parse host from connection string."

        dns_host = host_part.split(":")[0]
        is_srv = uri.startswith("mongodb+srv://")

        # 1. DNS check for the primary host
        try:
            socket.gethostbyname(dns_host)
        except socket.gaierror:
            return (
                f"DNS Resolution Failure: Could not resolve hostname '{dns_host}'. "
                "Please check your internet connection and local DNS nameserver settings."
            )

        # 2. SRV DNS lookup check if srv URI
        if is_srv:
            srv_name = f"_mongodb._tcp.{dns_host}"
            try:
                import dns.resolver
                dns.resolver.resolve(srv_name, 'SRV')
            except Exception as dns_err:
                return (
                    f"DNS Resolution Failure (SRV Record): Failed to query SRV record '{srv_name}'. "
                    f"Details: {dns_err}. If you are behind a restrictive network or VPN, SRV queries "
                    "might be blocked by your firewall or DNS provider."
                )

        # 3. Parse specific PyMongo exception details
        err_str = str(error).lower()
        if "auth failed" in err_str or "authentication" in err_str or "login" in err_str or "unauthorized" in err_str:
            return "Authentication Failure: The username or password specified in MONGODB_URI is incorrect."
        
        if "timeout" in err_str or "timed out" in err_str or "serverselectiontimeouterror" in err_str:
            return (
                "Network Timeout: Connection to MongoDB timed out. Verify your firewall rules, "
                "database port access (usually 27017), and MongoDB Atlas IP Access List."
            )

        if isinstance(error, pymongo.errors.ConfigurationError):
            return f"DNS Resolution Failure / Configuration Error: Nameservers failed to resolve the SRV record. Details: {error}"

        return f"Database Connectivity Error: {error}"

    async def connect(self):
        """Establish async connection to MongoDB Atlas or local MongoDB."""
        self.is_connected = False
        
        # Override default DNS resolver nameservers if it is an srv URI,
        # to prevent "Server answered REFUSED" errors on restrictive local networks
        uri = settings.MONGODB_URI
        if uri.startswith("mongodb+srv://"):
            try:
                import dns.resolver
                resolver = dns.resolver.get_default_resolver()
                # Prepend public resolvers so they are tried first
                public_dns = ["1.1.1.1", "8.8.8.8"]
                resolver.nameservers = public_dns + [ns for ns in resolver.nameservers if ns not in public_dns]
                logger.info(f"DNS Resolver configured with public fallbacks: {resolver.nameservers}")
            except Exception as dns_err:
                logger.warning(f"Could not configure custom DNS resolver: {dns_err}")

        # Safe host extraction for logging
        host = "unknown"
        try:
            if "@" in uri:
                host = uri.split("@")[-1].split("/")[0].split("?")[0]
            else:
                scheme = "mongodb+srv://" if uri.startswith("mongodb+srv://") else "mongodb://"
                host = uri[len(scheme):].split("/")[0].split("?")[0]
        except Exception:
            pass
            
        logger.info(f"Connecting to MongoDB database host: {host}")
        
        try:
            # Set serverSelectionTimeoutMS to fail fast (5 seconds instead of default 30)
            self.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[settings.MONGODB_DB_NAME]
            self.gridfs_bucket = AsyncIOMotorGridFSBucket(self.db)
            
            # Test connectivity
            await self.client.admin.command('ping')
            self.is_connected = True
            logger.success("✅ Successfully connected to MongoDB database")
            await self._create_indexes()
        except Exception as e:
            self.is_connected = False
            diag_message = self.diagnose_connection_error(settings.MONGODB_URI, e)
            logger.critical(f"❌ DATABASE CONNECTION FAILED:\n{'='*60}\n{diag_message}\n{'='*60}")
            
            if settings.APP_ENV == "production":
                logger.critical("Application shutting down: database connectivity is mandatory in production environment.")
                sys.exit(1)
            else:
                logger.warning(
                    f"Application starting in OFFLINE mode (APP_ENV={settings.APP_ENV}). "
                    "Database-dependent endpoints will be unavailable."
                )

    async def disconnect(self):
        """Close connection to MongoDB."""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("👋 Disconnected from MongoDB")


    async def _create_indexes(self):
        """Create indexes automatically on startup for performance optimization."""
        logger.info("Creating MongoDB indexes...")
        
        # User collection indexes
        await self.db[settings.COLLECTION_USERS].create_index("email", unique=True)
        await self.db[settings.COLLECTION_USERS].create_index("uid", unique=True)
        
        # Farm collection indexes
        await self.db[settings.COLLECTION_FARMS].create_index("farm_id", unique=True)
        await self.db[settings.COLLECTION_FARMS].create_index("user_id")
        
        # Disease predictions indexes
        await self.db[settings.COLLECTION_DISEASE_PREDICTIONS].create_index("prediction_id", unique=True)
        await self.db[settings.COLLECTION_DISEASE_PREDICTIONS].create_index("user_id")
        await self.db[settings.COLLECTION_DISEASE_PREDICTIONS].create_index("created_at")
        
        # Soil predictions indexes
        await self.db[settings.COLLECTION_SOIL_PREDICTIONS].create_index("prediction_id", unique=True)
        await self.db[settings.COLLECTION_SOIL_PREDICTIONS].create_index("user_id")
        await self.db[settings.COLLECTION_SOIL_PREDICTIONS].create_index("created_at")
        
        # Notifications indexes
        await self.db[settings.COLLECTION_NOTIFICATIONS].create_index("notification_id", unique=True)
        await self.db[settings.COLLECTION_NOTIFICATIONS].create_index("user_id")
        await self.db[settings.COLLECTION_NOTIFICATIONS].create_index("created_at")
        
        # Reports indexes
        await self.db[settings.COLLECTION_REPORTS].create_index("report_id", unique=True)
        await self.db[settings.COLLECTION_REPORTS].create_index("user_id")
        await self.db[settings.COLLECTION_REPORTS].create_index("created_at")
        
        # Refresh tokens & reset tokens
        await self.db[settings.COLLECTION_REFRESH_TOKENS].create_index("token", unique=True)
        await self.db[settings.COLLECTION_REFRESH_TOKENS].create_index("expires_at", expireAfterSeconds=0)
        
        await self.db[settings.COLLECTION_RESET_TOKENS].create_index("token", unique=True)
        await self.db[settings.COLLECTION_RESET_TOKENS].create_index("expires_at", expireAfterSeconds=0)
        
        logger.success("✅ MongoDB indexes created successfully")

db = Database()

def get_database():
    """Dependency helper to get database instance."""
    return db.db

def get_gridfs():
    """Dependency helper to get GridFS bucket."""
    return db.gridfs_bucket
