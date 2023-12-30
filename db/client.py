from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import os


def create_instance(
    schema: str = "public", url: str = os.getenv("SUPABASE_URL"), key: str = os.getenv("SUPABASE_KEY")
) -> Client:
    supabase_instance = create_client(supabase_url=url, supabase_key=key, options=ClientOptions(schema=schema))
    supabase_instance.schema = schema

    return supabase_instance
