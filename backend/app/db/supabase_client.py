import logging
from typing import Optional
from supabase import Client, create_client
from app.core.config import settings

logger = logging.getLogger(__name__)

_supabase_admin_client: Optional[Client] = None


def get_supabase_admin() -> Client:
    """Returns a singleton Supabase client authenticated with the service role key.
    Used for server-side writes and administrative checks that bypass RLS.
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        try:
            _supabase_admin_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Supabase admin client: {e}")
            raise RuntimeError(f"Supabase connection failed: {e}")
    return _supabase_admin_client
