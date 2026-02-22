"""Wait for PostgreSQL to be ready. Used by Docker entrypoint."""
import os
import sys
import time

def main():
    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/ratemaster")
    # psycopg2 uses postgresql:// (no +asyncpg)
    sync_url = url.replace("+asyncpg", "").replace("postgresql+psycopg2://", "postgresql://")
    if sync_url.startswith("postgresql+asyncpg"):
        sync_url = "postgresql://" + sync_url.split("postgresql+asyncpg://")[1]

    for i in range(30):
        try:
            import psycopg2
            conn = psycopg2.connect(sync_url)
            conn.close()
            print("PostgreSQL is ready.")
            return 0
        except Exception as e:
            print(f"Waiting for PostgreSQL... ({i+1}/30) {e}")
            time.sleep(2)
    print("PostgreSQL did not become ready in time.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
