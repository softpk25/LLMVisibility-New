# RAG Module

A Retrieval-Augmented Generation (RAG) system that processes PDF documents and answers questions using local LLM models via Ollama.

## Features

- PDF text extraction and intelligent chunking using LangChain
- Text embeddings using BGE-M3 model (via Ollama)
- Fast vector similarity search with FAISS (Euclidean distance)
- Question answering using Llama3 model (via Ollama)
- Persistent vector storage
- CLI interface for easy usage
- Programmatic API for integration

## Architecture

```
RAG Pipeline Flow:
1. PDF → Text Extraction → Chunking (500 chars, 50 overlap)
2. Chunks → BGE-M3 Embeddings (768-dim vectors)
3. Embeddings → FAISS Vector Store (Euclidean distance)
4. Query → Embedding → Similarity Search → Top-K Retrieval
5. Retrieved Context + Query → Llama3 → Generated Answer
```

## Requirements

- Python 3.8+
- Ollama running locally with the following models:
  - `bge-m3:latest` (for embeddings)
  - `llama3:latest` (for generation)

## Installation

### 1. Install Ollama (if not already installed)

Visit [Ollama](https://ollama.ai) and follow installation instructions.

### 2. Pull required models

```bash
ollama pull bge-m3
ollama pull llama3
```

Verify models are available:
```bash
ollama list
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

## Usage

### CLI Interface

#### 1. Ingest a PDF

```bash
python main.py ingest data/pdfs/document.pdf
```

This will:
- Extract text from the PDF
- Split into chunks
- Generate embeddings using BGE-M3
- Store in FAISS index
- Save index to disk

#### 2. Query the system

```bash
python main.py query "What are the main conclusions?"
```

This will:
- Load the saved index (if not already loaded)
- Embed your question
- Search for top-3 most relevant chunks (Euclidean distance)
- Generate answer using Llama3 with retrieved context
- Display answer with source page citations

#### 3. List system status

```bash
python main.py list
```

Shows:
- Number of documents in vector store
- Ingested PDFs
- Configuration settings
- Model information

#### 4. Clear all embeddings

```bash
python main.py clear
```

Removes all documents from the vector store and deletes saved index files.

### Programmatic API

```python
from src.rag_pipeline import RAGPipeline

# Initialize pipeline
rag = RAGPipeline()

# Ingest a PDF
stats = rag.ingest_pdf("data/pdfs/document.pdf")
print(f"Ingested {stats['num_chunks']} chunks from {stats['num_pages']} pages")

# Query
response = rag.query("What is the summary?")
print(f"Answer: {response['answer']}")
print(f"Sources: Pages {response['sources']}")

# Get system stats
stats = rag.get_stats()
print(f"Total documents: {stats['vector_store']['num_documents']}")
```

## Configuration

Edit `config/config.yaml` to customize:

```yaml
models:
  embedding:
    name: "bge-m3:latest"      # Embedding model
  generation:
    name: "llama3:latest"      # Generation model
    temperature: 0.7           # Sampling temperature
    max_tokens: 512            # Max response length

chunking:
  chunk_size: 500              # Characters per chunk
  chunk_overlap: 50            # Overlap between chunks

retrieval:
  top_k: 3                     # Number of chunks to retrieve
```

## Project Structure

```
D:\Facebook smm\RAG\
├── src/
│   ├── __init__.py            # Package initialization
│   ├── pdf_processor.py       # PDF text extraction and chunking
│   ├── embedder.py            # BGE-M3 embedding generation
│   ├── vector_store.py        # FAISS vector storage (Euclidean)
│   ├── generator.py           # Llama3 response generation
│   └── rag_pipeline.py        # Main RAG orchestration
├── data/
│   ├── pdfs/                  # Input PDF files
│   └── embeddings/            # Persisted FAISS indices
├── config/
│   └── config.yaml            # Configuration settings
├── main.py                    # CLI interface
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## How It Works

### 1. PDF Processing

- Uses LangChain's `PyPDFLoader` to extract text from PDFs
- Splits text into chunks using `RecursiveCharacterTextSplitter`
- Default: 500 character chunks with 50 character overlap
- Preserves metadata (page numbers, source file)

### 2. Embedding Generation

- Uses BGE-M3 model via Ollama for text embeddings
- Generates 768-dimensional vectors
- Batch processing for efficiency
- Verifies Ollama connection on initialization

### 3. Vector Storage & Retrieval

- Uses FAISS (Facebook AI Similarity Search)
- IndexFlatL2 for exact Euclidean distance calculation
- Lower distance = more similar documents
- Fast similarity search (<100ms)
- Persistent storage (save/load indices)

### 4. Response Generation

- Uses Llama3 via Ollama for text generation
- RAG prompt template injects retrieved context
- Includes source page citations
- Configurable temperature and max tokens

## Example Output

```bash
$ python main.py query "What are the key findings?"

Initializing RAG pipeline...
RAG pipeline initialized successfully

Processing query: What are the key findings?
Generating query embedding...
Searching for top 3 relevant chunks...
Retrieved 3 chunks (distances: ['2.45', '2.78', '3.12'])
Generating response...

============================================================
ANSWER
============================================================
Based on the document, the key findings are:

1. The study identified three main factors that contribute to...
2. Results showed a significant correlation between...
3. The data suggests that future research should focus on...

These findings are primarily discussed on pages 5, 12, and 18.

============================================================
SOURCES
============================================================
Pages: 5, 12, 18

============================================================
RETRIEVED CONTEXT
============================================================

[Chunk 1 - Page 5, Distance: 2.45]
The analysis revealed three primary factors: first, the temporal distribution of...

[Chunk 2 - Page 12, Distance: 2.78]
Our findings demonstrate a strong correlation (r=0.82, p<0.01) between...

[Chunk 3 - Page 18, Distance: 3.12]
These results suggest that future investigations should prioritize...

============================================================
```

## Performance

- **Embedding**: ~1-2 seconds per chunk (BGE-M3 via Ollama)
- **Search**: <100ms (FAISS is very fast)
- **Generation**: ~5-10 seconds (Llama3 via Ollama)

For a typical 20-page PDF:
- Ingestion: ~2-3 minutes
- Query: ~10-15 seconds

## Troubleshooting

### Error: "Failed to connect to Ollama"

**Solution**: Make sure Ollama is running
```bash
ollama serve
```

### Error: "Model not found in Ollama"

**Solution**: Pull the required models
```bash
ollama pull bge-m3
ollama pull llama3
```

### Error: "No documents in vector store"

**Solution**: Ingest a PDF first
```bash
python main.py ingest data/pdfs/document.pdf
```

### Poor retrieval quality

**Solution**: Tune parameters in `config/config.yaml`:
- Increase `chunk_overlap` for better context preservation
- Adjust `chunk_size` based on document structure
- Increase `top_k` to retrieve more context

## Advanced Features

### Multiple PDFs

Ingest multiple PDFs to query across documents:
```bash
python main.py ingest doc1.pdf
python main.py ingest doc2.pdf
python main.py query "Compare findings across documents"
```

### Custom Configuration

Create a custom config file and pass it programmatically:
```python
rag = RAGPipeline(config_path="custom_config.yaml")
```

### Streaming Responses

Use the streaming API for real-time output:
```python
for chunk in rag.generator.generate_stream(question, context_docs):
    print(chunk, end='', flush=True)
```

## Future Enhancements

- [ ] Support for DOCX, TXT, HTML formats
- [ ] Web interface (Streamlit/Gradio)
- [ ] Conversation history/memory
- [ ] Hybrid search (combine with keyword matching)
- [ ] Multi-document cross-referencing
- [ ] Question rephrasing for better retrieval
- [ ] Export chat history

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for the RAG framework
- [Ollama](https://ollama.ai) for local LLM serving
- [FAISS](https://github.com/facebookresearch/faiss) for vector similarity search
- BGE-M3 and Llama3 model creators
