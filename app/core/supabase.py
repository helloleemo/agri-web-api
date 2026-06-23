import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase_client = create_client(  # type: ignore[no-untyped-call]
    SUPABASE_URL,  # type: ignore[arg-type]
    SUPABASE_SERVICE_KEY,  # type: ignore[arg-type]
)