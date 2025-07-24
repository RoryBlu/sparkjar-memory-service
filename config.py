# services/memory-service/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging

# Import centralized configuration validation
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
# REMOVED: sys.path.insert(0, str(project_root))

from shared.config.config_validator import validate_config_on_startup

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = "custom"  # "custom" or "openai"
    EMBEDDINGS_API_URL: str = "http://embeddings.railway.internal"
    EMBEDDING_MODEL: str = "Alibaba-NLP/gte-multilingual-base"
    EMBEDDING_DIMENSION: str = "768"
    
    # OpenAI Configuration (for embeddings when provider=openai)
    OPENAI_API_KEY: Optional[str] = None
    
    # API Configuration
    INTERNAL_API_HOST: str = "::"
    INTERNAL_API_PORT: int = 8001
    EXTERNAL_API_HOST: str = "0.0.0.0"
    EXTERNAL_API_PORT: int = 8443
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SSL Certificates (for external API)
    SSL_CERTFILE: Optional[str] = None
    SSL_KEYFILE: Optional[str] = None
    
    class Config:
        env_file = ".env"

def validate_memory_service_config() -> bool:
    """Validate memory service specific configuration requirements."""
    logger = logging.getLogger(__name__)
    
    try:
        # Run base configuration validation
        result = validate_config_on_startup(fail_fast=False)
        
        # Check memory service specific requirements
        memory_service_errors = []
        
        # Validate database connection
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            memory_service_errors.append("DATABASE_URL is required for memory service")
        
        # Validate Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        if not supabase_url or not supabase_key:
            memory_service_errors.append("SUPABASE_URL and SUPABASE_SERVICE_KEY are required for memory service")
        
        # Validate secret key
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key or len(secret_key) < 32:
            memory_service_errors.append("SECRET_KEY must be at least 32 characters long")
        
        # Validate embedding configuration
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "custom")
        if embedding_provider == "openai":
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                memory_service_errors.append("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        elif embedding_provider == "custom":
            embeddings_api_url = os.getenv("EMBEDDINGS_API_URL")
            if not embeddings_api_url:
                memory_service_errors.append("EMBEDDINGS_API_URL is required when EMBEDDING_PROVIDER=custom")
        
        # Check port conflicts
        internal_port = int(os.getenv("INTERNAL_API_PORT", "8001"))
        external_port = int(os.getenv("EXTERNAL_API_PORT", "8443"))
        if internal_port == external_port:
            memory_service_errors.append("INTERNAL_API_PORT and EXTERNAL_API_PORT cannot be the same")
        
        # Check SSL configuration consistency
        ssl_cert = os.getenv("SSL_CERTFILE")
        ssl_key = os.getenv("SSL_KEYFILE")
        if (ssl_cert and not ssl_key) or (ssl_key and not ssl_cert):
            memory_service_errors.append("Both SSL_CERTFILE and SSL_KEYFILE must be provided together")
        
        # Log results
        if memory_service_errors:
            logger.error("❌ Memory Service configuration validation failed:")
            for error in memory_service_errors:
                logger.error(f"  • {error}")
        
        # Overall validation status
        is_valid = result.is_valid and len(memory_service_errors) == 0
        
        if is_valid:
            logger.info("✅ Memory Service configuration validation passed")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"❌ Memory Service configuration validation error: {str(e)}")
        return False

# Initialize settings with validation
try:
    settings = Settings()
    
    # Run memory service specific validation on import
    if not os.getenv("SKIP_CONFIG_VALIDATION", "").lower() == "true":
        validate_memory_service_config()
        
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to initialize memory service settings: {str(e)}")
    if os.getenv("ENVIRONMENT", "development") != "development":
        raise