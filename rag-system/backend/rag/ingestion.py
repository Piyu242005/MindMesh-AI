import os
from typing import List, Dict, Any
import pypdf
import docx
import pandas as pd
import logging
from config import settings
from .vectorstore import vector_store

logger = logging.getLogger(__name__)

class SimpleTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            
            # If we are not at the end of text, try to find a break point
            if end < text_len:
                # Try to break at paragraph
                next_break = text.rfind("\n\n", start, end)
                if next_break == -1:
                    # Try newline
                    next_break = text.rfind("\n", start, end)
                if next_break == -1:
                    # Try space
                    next_break = text.rfind(" ", start, end)
                
                if next_break != -1 and next_break > start:
                    end = next_break + 1 # Include the delimiter
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start forward, accounting for overlap
            start += (self.chunk_size - self.chunk_overlap)
            
            # Prevent infinite loop if no progress
            if start >= end:
                start = end

        return chunks

class IngestionPipeline:
    def __init__(self):
        self.text_splitter = SimpleTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse file content based on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        content = ""
        metadata = {"source": os.path.basename(file_path)}
        
        try:
            if ext == ".pdf":
                reader = pypdf.PdfReader(file_path)
                content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif ext == ".docx":
                doc = docx.Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            elif ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            elif ext == ".csv":
                df = pd.read_csv(file_path)
                content = df.to_string() # Simple CSV to text conversion
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return []
                
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise

        return self._create_chunks(content, metadata)

    def _create_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks."""
        if not text:
            return []
            
        chunks = self.text_splitter.split_text(text)
        
        # Convert to list of dicts
        return [
            {"text": chunk, "metadata": metadata}
            for chunk in chunks
        ]

    async def process_upload(self, file_path: str):
        """Asynchronous processing of uploaded file."""
        logger.info(f"Processing upload: {file_path}")
        chunks_data = self.parse_file(file_path)
        
        if chunks_data:
            texts = [c["text"] for c in chunks_data]
            metadatas = [c["metadata"] for c in chunks_data]
            vector_store.add_documents(texts, metadatas)
            logger.info(f"Successfully processed and indexed {file_path}")
        else:
            logger.warning(f"No content extracted from {file_path}")

# Singleton
ingestion_pipeline = IngestionPipeline()
