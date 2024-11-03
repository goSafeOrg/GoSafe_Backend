from supabaseInit import create_client, Client
import os

# Set up Supabase client
SUPABASE_URL = "https://igbtezppidteqhbauxlv.supabase.co"  # Add your Supabase URL here or set it as an environment variable
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlnYnRlenBwaWR0ZXFoYmF1eGx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkxODU5MDUsImV4cCI6MjA0NDc2MTkwNX0.MnP_05Bb5fA4G3DEyzeO4KmU6xVkyazj6ruzosPZyJk"  # Add your Supabase API key here or set it as an environment variable
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)