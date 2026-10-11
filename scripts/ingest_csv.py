import sys
import os
import pandas as pd
from datetime import datetime

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.database import SessionLocal, engine, Base
from backend.database.models import Dataset, Document

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

def ingest_csv(file_path: str, version: str = "v1.0"):
    print(f"Ingesting dataset from {file_path}...")
    
    # Read CSV
    df = pd.read_csv(file_path)
    
    db = SessionLocal()
    try:
        # Check if dataset version already exists
        dataset = db.query(Dataset).filter(Dataset.version == version).first()
        if dataset:
            print(f"Dataset version {version} already exists. Skipping ingestion.")
            return

        # Create new dataset entry
        dataset = Dataset(
            version=version,
            source="initial_csv",
            total_records=len(df),
            upload_date=datetime.utcnow()
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Prepare documents for bulk insert
        documents = []
        for index, row in df.iterrows():
            # Handle NaN values safely
            row_dict = {k: (v if pd.notna(v) else None) for k, v in row.to_dict().items()}
            
            doc = Document(
                original_id=str(row_dict.get('id')),
                text=row_dict.get('text', ''),
                scheme=row_dict.get('scheme'),
                intent=row_dict.get('intent'),
                awareness_gap=row_dict.get('awareness_gap'),
                gap_type=row_dict.get('gap_type'),
                state=row_dict.get('state'),
                district=row_dict.get('district'),
                source=row_dict.get('source'),
                source_type=row_dict.get('source_type'),
                language=row_dict.get('language'),
                source_url=row_dict.get('source_url'),
                is_synthetic=row_dict.get('is_synthetic'),
                confidence=row_dict.get('confidence'),
                notes=row_dict.get('notes'),
                split=row_dict.get('split'),
                dataset_id=dataset.id
            )
            documents.append(doc)
            
        # Bulk save
        db.bulk_save_objects(documents)
        db.commit()
        
        print(f"Successfully ingested {len(documents)} records into dataset {version}.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during ingestion: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    
    csv_path = os.path.join("data", "raw", "welfare_awareness_dataset_with_split.csv")
    if os.path.exists(csv_path):
        ingest_csv(csv_path)
    else:
        print(f"File not found: {csv_path}")
