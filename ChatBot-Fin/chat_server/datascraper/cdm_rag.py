from dotenv import load_dotenv
import os
# import re
import pickle
import numpy as np
import faiss
import openai
import ast  # For Python code parsing
import markdown  # For Markdown parsing
import logging

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

load_dotenv()
api_key = os.getenv("API_KEY7")
openai.api_key = api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Global variables for index and embeddings
index = None
embeddings = None

current_dir = os.path.dirname(os.path.abspath(__file__))

def initialize_rag():
    """
    Initializes the RAG components by loading the FAISS index and embeddings.
    If either file is missing, reports that it's missing.
    """
    global index, embeddings
    index_file = os.path.join(current_dir, 'faiss_index.idx')
    embeddings_file = os.path.join(current_dir, 'embeddings.pkl')

    # Check if both files exist
    if os.path.exists(index_file) and os.path.exists(embeddings_file):
        index, embeddings = load_index_and_embeddings(index_file, embeddings_file)
        print("Loaded existing FAISS index and embeddings.")
    else:
        missing_files = []
        if not os.path.exists(index_file):
            missing_files.append(index_file)
        if not os.path.exists(embeddings_file):
            missing_files.append(embeddings_file)
        missing_files_str = ', '.join(missing_files)
        error_message = f"The following file(s) are missing: {missing_files_str}. Please ensure they are present."
        print(error_message)
        logging.error(error_message)
        # Raise an exception to be handled by the calling function
        raise FileNotFoundError(error_message)

def load_index_and_embeddings(index_file='faiss_index.idx', embeddings_file='embeddings.pkl'):
    """
    Loads the FAISS index and embeddings with metadata from disk.
    """
    index = faiss.read_index(index_file)
    with open(embeddings_file, 'rb') as f:
        embeddings = pickle.load(f)
    return index, embeddings

def embed_query(query, model="text-embedding-3-large"):
    """
    Generates an embedding for the query text.
    """
    response = openai.Embedding.create(
        input=query,
        model=model
    )
    return response['data'][0]['embedding']

def retrieve_chunks(query, index, embeddings, k=8):
    """
    Retrieves the most relevant text chunks for a given query.
    """
    query_embedding = embed_query(query)
    query_vector = np.array([query_embedding]).astype('float32')
    faiss.normalize_L2(query_vector)

    # Search the index
    distances, indices = index.search(query_vector, k)
    results = [embeddings[i] for i in indices[0]]

    return results

def generate_answer(query, relevant_chunks, model_name):
    """
    Generates an answer to the query using the specified model and the relevant context.
    """
    # Construct context from retrieved chunks
    context = ''
    for chunk in relevant_chunks:
        context += f"File: {chunk['metadata']['file_path']}\nContent:\n{chunk['text']}\n\n"

    prompt = f"""You are a CDM expert providing detailed and accurate answers.

Context:
{context}

Question:
{query}

Answer as thoroughly as possible based on the context provided."""

    # Use OpenAI's model
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            # {'role': 'system', 'content': 'You are a CDM expert providing detailed and accurate answers.'},
            {'role': 'user', 'content': prompt}
        ],
        #temperature=0.1,  # Lower temperature for more precise answers
        max_completion_tokens=3000  # Adjust as necessary
    )

    answer = response['choices'][0]['message']['content']
    return answer.strip()

def get_rag_response(question, model_name):
    """
    Generates a response using the RAG pipeline with the specified model.
    """
    global index, embeddings
    if index is None or embeddings is None:
        initialize_rag()

    # Retrieve relevant chunks
    relevant_chunks = retrieve_chunks(question, index, embeddings)

    # Log the retrieved chunks at INFO level
    logging.info("\nRetrieved Chunks:")
    for i, chunk in enumerate(relevant_chunks):
        logging.info(f"\nChunk {i + 1}:")
        logging.info(f"File: {chunk['metadata']['file_path']}")
        logging.info(f"Content:\n{chunk['text']}")

    # Generate answer
    answer = generate_answer(question, relevant_chunks, model_name)

    return answer


def get_rag_advanced_response(question, model_name):
    """
    Generates an advanced response using the RAG pipeline.
    """
    # For simplicity, we'll use the same as get_rag_response
    return get_rag_response(question, model_name)