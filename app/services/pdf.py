from pypdf import PdfReader
import io

class PDFService:
    def extract_text(self, file_bytes: bytes):
        # WHAT: Reads all pages of a PDF
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def chunk_text(self, text: str, chunk_size=500, overlap=50):
        # WHAT: Slices text into 500-char blocks with 50-char overlap
        # WHY: Overlap ensures that a sentence split between two chunks isn't "cut in half"
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks

pdf_service = PDFService()