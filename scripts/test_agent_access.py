from sqlalchemy import create_engine, text
import urllib
from pathlib import Path

# Connect using the NEW Read-Only Agent Credentials
print("Authenticating as AI Agent (USR_FDE_RO)...")
params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=master;"
    "UID=USR_FDE_RO;"  # <--- Note the restricted user
    "PWD=AgentPassword2026!;"
    "Encrypt=no;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

try:
    with engine.connect() as conn:
        # TEST 1: Execute a valid query against the clean view
        print("\n[TEST 1] Querying Semantic View...")
        query = text("SELECT TOP 3 Latitude, Longitude, Current_Temperature_C FROM FDE_VIEWS.VW_ACTIVE_FLEET")
        result = conn.execute(query).fetchall()
        for row in result:
            print(f"Success -> {row}")

        # TEST 2: Attempt to query the raw legacy table (Should Fail)
        print("\n[TEST 2] Attempting to bypass view and query raw table...")
        try:
            conn.execute(text("SELECT TOP 3 * FROM dbo.TBL_SC_FLEET_HIST_RAW"))
        except Exception as e:
            print("Blocked! (Expected behavior) -> Access denied to raw table.")

        # TEST 3: Attempt SQL Injection / Mutation (Should Fail)
        print("\n[TEST 3] Attempting malicious LLM UPDATE command...")
        try:
            conn.execute(text("UPDATE FDE_VIEWS.VW_ACTIVE_FLEET SET Current_Temperature_C = 0.0"))
            conn.commit()
        except Exception as e:
            print("Blocked! (Expected behavior) -> Mutation denied.")

except Exception as e:
    print(f"Connection failed: {e}")