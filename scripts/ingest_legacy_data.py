from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
import urllib

# __file__ is 'experiment/phase-0/ingest_legacy_data.py'
script_dir = Path(__file__).resolve().parent # points to experiment/phase-0
project_root = script_dir.parents[0] # climbs up 1 levels to project root

data_path = project_root / "data" / "raw" / "dynamic_supply_chain_logistics_dataset.csv"

# 1. Load the raw dataset
print(f"Loading CSV from {data_path}...")
df = pd.read_csv(data_path)

# 2. Map clean columns to a messy 2000s legacy enterprise schema
legacy_mapping = {
    'timestamp': 'TS_UTC',
    'vehicle_gps_latitude': 'V_LAT',
    'vehicle_gps_longitude': 'V_LON',
    'iot_temperature': 'IOT_TEMP_VAL_C',
    'cargo_condition_status': 'CGO_COND_CD',
    'risk_classification': 'RISK_CLS_TXT',
    'delay_probability': 'DELAY_PROB_DEC',
    'port_congestion_level': 'PRT_CNG_LVL',
    'route_risk_level': 'RT_RSK_IDX'
}

# Keep only the columns we mapped for this demo and rename them
df_legacy = df[list(legacy_mapping.keys())].rename(columns=legacy_mapping)

# Add a fake ingestion flag to make it look like an automated legacy system
df_legacy['SYS_INGEST_FLAG'] = 'Y'

# 3. Connect to Docker MSSQL Server
print("Connecting to legacy MSSQL Database...")
# Use the pyodbc driver. (Ensure you have ODBC Driver 17 or 18 for SQL Server installed on your OS)
params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    # "SERVER=localhost,1433;"
    # For deployemnt : replace localhost with ec2-xx-xxx-xxx-xxx.compute-1.amazonaws.com
    "SERVER=ec2-15-206-82-169.ap-south-1.compute.amazonaws.com,1433;"
    "DATABASE=master;"
    "UID=sa;"
    "PWD=FdeEnterprisePass123!;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# 4. Ingest data into the messy table name
table_name = 'TBL_SC_FLEET_HIST_RAW'
print(f"Ingesting into {table_name}. This may take a minute...")
df_legacy.to_sql(table_name, engine, if_exists='replace', index=False, schema='dbo')

print("✅ Legacy data ingestion complete!")