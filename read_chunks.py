import requests
import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import concurrent.futures

def create_embedding(text_list):
    # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "bge-m3",
        "input": text_list
    })

    embedding = r.json()["embeddings"] 
    return embedding


def process_file(json_file):
    print(f"Creating Embeddings for {json_file}")
    try:
        with open(f"jsons/{json_file}") as f:
            content = json.load(f)
        
        embeddings = create_embedding([c['text'] for c in content['chunks']])
        
        file_chunks = []
        for i, chunk in enumerate(content['chunks']):
            chunk['embedding'] = embeddings[i]
            file_chunks.append(chunk)
            
        return file_chunks
    except Exception as e:
        print(f"Error processing {json_file}: {e}")
        return []

if __name__ == "__main__":
    jsons = os.listdir("jsons")  # List all the jsons 
    my_dicts = []
    chunk_id = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(process_file, jsons)
        
        for file_chunks in results:
            for chunk in file_chunks:
                chunk['chunk_id'] = chunk_id
                chunk_id += 1
                my_dicts.append(chunk)

    # print(my_dicts)

    df = pd.DataFrame.from_records(my_dicts)
    # Save this dataframe
    joblib.dump(df, 'embeddings.joblib')

