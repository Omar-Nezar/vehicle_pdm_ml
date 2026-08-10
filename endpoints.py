from fastapi import FastAPI, UploadFile, File, HTTPException
from pymongo import MongoClient
import pandas as pd
import io
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env file

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")

app = FastAPI()

# MongoDB connection
client = MongoClient(mongo_uri) 
db = client[db_name]
collection = db["vehicles"]

try:
    client.admin.command("ping")
    print("MongoDB connection successful")
except Exception as e:
    print("MongoDB connection failed:", e)

allowed_collections = {
    "vehicles",
    "vehicle_registry",
    "service_history",
}

@app.post("/uploadcsv/{collection_name}")
async def upload_csv(
    collection_name: str,
    file: UploadFile = File(...)
    ):
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files allowed"
            )

        if not collection_name or collection_name not in allowed_collections: 
            raise HTTPException( 
                status_code=400, 
                detail="Collection name is required / invalid name" 
            )

        # Get requested collection 
        collection = db[collection_name]

        contents = await file.read()

        df = pd.read_csv(
            io.StringIO(contents.decode("utf-8"))
        )

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="CSV is empty"
            )

        records = df.to_dict(orient="records")

        result = collection.insert_many(records)

        return {
            "message": "Upload successful",
            "collection": collection_name,
            "csv_rows": len(df),
            "inserted_count": len(result.inserted_ids),
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )