from functools import lru_cache

from supabase import Client, create_client

from .config import get_settings


@lru_cache
def get_supabase_client(service_mode: bool = False) -> Client:
    """
    Create a singleton Supabase client. Set service_mode=True for elevated inserts/updates.
    """
    settings = get_settings()
    key = settings.supabase_service_role_key if service_mode and settings.supabase_service_role_key else settings.supabase_anon_key
    return create_client(settings.supabase_url, key)


supabase = get_supabase_client()
