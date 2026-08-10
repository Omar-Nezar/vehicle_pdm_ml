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
collection = db["vehicle_registry"]

try:
    client.admin.command("ping")
    print("MongoDB connection successful")
except Exception as e:
    print("MongoDB connection failed:", e)

@app.post("/uploadcsv/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files allowed"
            )

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
            "csv_rows": len(df),
            "inserted_count": len(result.inserted_ids),
            "vehicles": (
                df["vehicle_id"].unique().tolist()
                if "vehicle_id" in df.columns
                else []
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )