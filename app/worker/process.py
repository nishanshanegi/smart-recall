import time
import json
import io
from PIL import Image
import pytesseract
from pypdf import PdfReader

from app.services.sqs import sqs_service
from app.models.base import SessionLocal, engine
from app.models.vault import VaultItem, VaultChunk
from app.services.ai import ai_service
from app.services.s3 import s3_service
from app.services.pdf import pdf_service # <--- 1. IMPORT THIS

pytesseract.pytesseract.tesseract_cmd = r'D:\tesseratc\tesseract.exe'

def start_worker():
    print("Worker checking database connection...")
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    print("Worker started. Listening for messages...")

    while True:
        try:
            response = sqs_service.client.receive_message(
                QueueUrl=sqs_service.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            messages = response.get("Messages", [])
            for msg in messages:
                body = json.loads(msg["Body"])
                item_id = body["item_id"]
                
                print(f"\n📦 Found Task for Item ID: {item_id}")

                with SessionLocal() as db:
                    item = db.query(VaultItem).filter(VaultItem.id == item_id).first()
                    
                    if not item:
                        print(f"⚠️ Warning: Item {item_id} not found.")
                        continue

                    # --- STEP 1: TEXT EXTRACTION (IMAGE OR PDF) ---
                    if item.s3_key:
                        print(f"📥 Downloading file from S3: {item.s3_key}")
                        file_bytes = s3_service.download_file(item.s3_key)

                        # Check the type and choose the right tool
                        if "pdf" in item.content_type.lower():
                            print("📄 PDF detected. Extracting text...")
                            item.extracted_content = pdf_service.extract_text(file_bytes)
                        
                        elif "image" in item.content_type.lower():
                            print("📷 Image detected. Running OCR...")
                            image = Image.open(io.BytesIO(file_bytes))
                            item.extracted_content = pytesseract.image_to_string(image)
                        
                        db.commit()

                    # --- STEP 2: CHUNKING & EMBEDDING ---
                    # We do this for ALL items (Text, Images, and PDFs)
                    if item.extracted_content:
                        print(f"✂️ Chunking and Embedding content for Item {item_id}...")
                        
                        # We use the PDF service's chunker even for text/images 
                        # because it's a great general-purpose chunker!
                        text_chunks = pdf_service.chunk_text(item.extracted_content)
                        
                        for chunk_text in text_chunks:
                            vector = ai_service.get_embedding(chunk_text)
                            new_chunk = VaultChunk(
                                item_id=item.id,
                                content=chunk_text,
                                embedding=vector
                            )
                            db.add(new_chunk)
                        
                        db.commit()
                        print(f"✅ Success: Created {len(text_chunks)} AI chunks.")
                    else:
                        print(f"⚠️ Warning: No content to process for Item {item_id}")

                # 3. Cleanup
                sqs_service.client.delete_message(
                    QueueUrl=sqs_service.queue_url,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
        
        except Exception as e:
            print(f"🔥 Worker Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()