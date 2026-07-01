import os
import time

def download_models():
    print("Pre-downloading models for offline hackathon use...")
    start_time = time.time()
    
    # Create models directory
    os.makedirs("./models/minilm", exist_ok=True)
    os.makedirs("./models/cross_encoder", exist_ok=True)
    
    # 1. Download SentenceTransformer MiniLM (80MB, fast CPU embedding)
    try:
        from sentence_transformers import SentenceTransformer
        print("Downloading all-MiniLM-L6-v2...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        model.save('./models/minilm/')
        print("MiniLM downloaded and saved successfully.")
    except Exception as e:
        print(f"Failed to download MiniLM: {e}")
        
    # 2. Although ranker.py was updated to not use cross_encoder, if we ever needed it:
    try:
        from sentence_transformers import CrossEncoder
        print("Downloading cross-encoder/ms-marco-MiniLM-L-6-v2...")
        ce_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        ce_model.save('./models/cross_encoder/')
        print("CrossEncoder downloaded successfully.")
    except Exception as e:
        print(f"Failed to download CrossEncoder: {e}")

    print(f"Pre-download completed in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    download_models()
