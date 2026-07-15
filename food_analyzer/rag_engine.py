# food_analyzer/rag_engine.py
import os
import re
import math
import pickle
import logging
import numpy as np

# Initialize logger
logger = logging.getLogger(__name__)

INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rag_index')
os.makedirs(INDEX_DIR, exist_ok=True)

FAISS_INDEX_PATH = os.path.join(INDEX_DIR, 'faiss_index.bin')
CHUNKS_PATH = os.path.join(INDEX_DIR, 'chunks.pkl')
TFIDF_INDEX_PATH = os.path.join(INDEX_DIR, 'tfidf_index.pkl')

def chunk_text(text, chunk_size=800, overlap=150):
    """Chunks text into overlapping blocks of characters."""
    chunks = []
    text = re.sub(r'\s+', ' ', text).strip()
    
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to find a sentence boundary near the end to make clean cuts
        if end < len(text):
            boundary = text.rfind('. ', start, end)
            if boundary != -1 and boundary > start + chunk_size // 2:
                end = boundary + 1
        
        chunks.append(text[start:end].strip())
        start += (chunk_size - overlap)
        if start >= len(text) or end == len(text):
            break
            
    return chunks

class SimpleTFIDF:
    """A pure-python TF-IDF vectorizer and retriever for fallback when Gemini API key is missing."""
    def __init__(self):
        self.doc_freqs = {}
        self.doc_lengths = []
        self.num_docs = 0
        self.doc_term_counts = []
        self.chunks = []
        self.vocab = set()

    def fit_transform(self, chunks):
        self.chunks = chunks
        self.num_docs = len(chunks)
        self.doc_term_counts = []
        self.doc_freqs = {}
        self.vocab = set()
        
        # Count term frequencies per doc
        for doc in chunks:
            words = self._tokenize(doc)
            self.doc_lengths.append(len(words))
            
            # Count terms in doc
            counts = {}
            for w in words:
                counts[w] = counts.get(w, 0) + 1
                self.vocab.add(w)
            self.doc_term_counts.append(counts)
            
            # Update doc frequency
            for w in set(words):
                self.doc_freqs[w] = self.doc_freqs.get(w, 0) + 1

    def _tokenize(self, text):
        return re.findall(r'\b[a-zA-Z]{3,15}\b', text.lower())

    def transform_query(self, query):
        words = self._tokenize(query)
        q_counts = {}
        for w in words:
            if w in self.vocab:
                q_counts[w] = q_counts.get(w, 0) + 1
        return q_counts

    def search(self, query, top_k=3):
        if not self.chunks:
            return []
            
        q_counts = self.transform_query(query)
        if not q_counts:
            # If no vocab overlap, return first top_k chunks
            return self.chunks[:top_k]
            
        scores = []
        for i in range(self.num_docs):
            doc_counts = self.doc_term_counts[i]
            doc_len = self.doc_lengths[i] or 1
            
            # Compute cosine similarity
            dot_product = 0.0
            q_norm = 0.0
            d_norm = 0.0
            
            for w, q_tf in q_counts.items():
                idf = math.log((1 + self.num_docs) / (1 + self.doc_freqs.get(w, 0))) + 1
                q_val = q_tf * idf
                q_norm += q_val * q_val
                
                if w in doc_counts:
                    d_tf = doc_counts[w]
                    d_val = d_tf * idf
                    dot_product += q_val * d_val
            
            for w, d_tf in doc_counts.items():
                idf = math.log((1 + self.num_docs) / (1 + self.doc_freqs.get(w, 0))) + 1
                d_val = d_tf * idf
                d_norm += d_val * d_val
                
            if q_norm > 0 and d_norm > 0:
                similarity = dot_product / (math.sqrt(q_norm) * math.sqrt(d_norm))
            else:
                similarity = 0.0
                
            scores.append((similarity, self.chunks[i]))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return [chunk for sim, chunk in scores[:top_k]]

def build_or_load_index(kb_dir="knowledge_base", force_rebuild=False):
    """
    Scans the knowledge_base folder, chunks all .txt files, and builds either a
    FAISS index (using Gemini text-embedding-004) or a SimpleTFIDF index.
    """
    from food_analyzer.ml_utils import gemini_client
    
    # Check if index already built and not forcing rebuild
    if not force_rebuild:
        if gemini_client and os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            try:
                import faiss
                index = faiss.read_index(FAISS_INDEX_PATH)
                with open(CHUNKS_PATH, 'rb') as f:
                    chunks = pickle.load(f)
                logger.info(f"Loaded existing FAISS index with {len(chunks)} chunks.")
                return "FAISS", index, chunks
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}. Rebuilding...")
        elif not gemini_client and os.path.exists(TFIDF_INDEX_PATH):
            try:
                with open(TFIDF_INDEX_PATH, 'rb') as f:
                    tfidf_data = pickle.load(f)
                logger.info(f"Loaded existing TF-IDF index with {len(tfidf_data.chunks)} chunks.")
                return "TF-IDF", tfidf_data, tfidf_data.chunks
            except Exception as e:
                logger.error(f"Error loading TF-IDF index: {e}. Rebuilding...")

    # Build new index
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_kb_path = os.path.join(project_root, kb_dir)
    
    if not os.path.exists(full_kb_path):
        os.makedirs(full_kb_path, exist_ok=True)
        logger.warning(f"Knowledge base directory {kb_dir} was empty or created. Please add text files.")
        return None, None, []
        
    all_chunks = []
    for filename in os.listdir(full_kb_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(full_kb_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                file_chunks = chunk_text(text)
                all_chunks.extend(file_chunks)
                logger.info(f"Parsed {filename}: created {len(file_chunks)} chunks.")
            except Exception as e:
                logger.error(f"Error reading {filename}: {e}")
                
    if not all_chunks:
        logger.warning("No nutrition documents parsed. Knowledge base is empty.")
        return None, None, []

    if gemini_client:
        try:
            import faiss
            logger.info("Generating embeddings with Gemini API...")
            embeddings = []
            
            # Batch embedding generation to be efficient
            batch_size = 20
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i+batch_size]
                # SDK Call
                response = gemini_client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=batch
                )
                
                # Depending on API response structure, parse embedding values
                # Typically, embed_content returns a list of embeddings or a single embedding
                # If batch, it returns list of objects.
                # response.embeddings is a list where each element has values as float list.
                # Let's inspect response and handle both single/multiple
                if hasattr(response, 'embeddings'):
                    for emb in response.embeddings:
                        embeddings.append(emb.values)
                elif hasattr(response, 'embedding'):
                    embeddings.append(response.embedding.values)
                else:
                    # Fallback lookup
                    for r in response:
                        if hasattr(r, 'values'):
                            embeddings.append(r.values)
            
            emb_matrix = np.array(embeddings, dtype='float32')
            dimension = emb_matrix.shape[1]
            
            index = faiss.IndexFlatL2(dimension)
            index.add(emb_matrix)
            
            # Write to disk
            faiss.write_index(index, FAISS_INDEX_PATH)
            with open(CHUNKS_PATH, 'wb') as f:
                pickle.dump(all_chunks, f)
                
            logger.info(f"Successfully built FAISS index with {len(all_chunks)} chunks.")
            return "FAISS", index, all_chunks
            
        except Exception as e:
            logger.error(f"Failed to build FAISS index via Gemini: {e}. Falling back to TF-IDF.")
            
    # Pure Python TF-IDF Indexing
    logger.info("Building pure-python TF-IDF index...")
    tfidf = SimpleTFIDF()
    tfidf.fit_transform(all_chunks)
    
    with open(TFIDF_INDEX_PATH, 'wb') as f:
        pickle.dump(tfidf, f)
        
    logger.info(f"Successfully built TF-IDF index with {len(all_chunks)} chunks.")
    return "TF-IDF", tfidf, all_chunks

def retrieve_relevant_chunks(query, top_k=3):
    """
    Retrieves the most relevant chunks from the nutrition knowledge base.
    Uses FAISS if Gemini Client + FAISS exists, otherwise TF-IDF.
    """
    from food_analyzer.ml_utils import gemini_client
    
    index_type, index_obj, chunks = build_or_load_index()
    if not chunks:
        return []
        
    if index_type == "FAISS" and gemini_client:
        try:
            import faiss
            response = gemini_client.models.embed_content(
                model="gemini-embedding-2",
                contents=query
            )
            if hasattr(response, 'embedding'):
                q_emb = np.array([response.embedding.values], dtype='float32')
            elif hasattr(response, 'embeddings'):
                q_emb = np.array([response.embeddings[0].values], dtype='float32')
            else:
                # Handle cases
                val = response.values if hasattr(response, 'values') else response[0].values
                q_emb = np.array([val], dtype='float32')
                
            distances, indices = index_obj.search(q_emb, top_k)
            retrieved = []
            for idx in indices[0]:
                if idx != -1 and idx < len(chunks):
                    retrieved.append(chunks[idx])
            return retrieved
        except Exception as e:
            logger.error(f"FAISS retrieval failed: {e}. Falling back to TF-IDF search.")
            
    # Search via SimpleTFIDF
    if index_type == "TF-IDF":
        return index_obj.search(query, top_k)
    else:
        # Build TF-IDF lazily
        tfidf = SimpleTFIDF()
        tfidf.fit_transform(chunks)
        return tfidf.search(query, top_k)
