#Imports
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import faiss  # FAISS for fast similarity search
from tqdm import tqdm

# Load CLIP Model
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Paths
current_file_path = os.path.dirname(os.path.abspath(__file__))
vector_store_path = os.path.join(current_file_path, "store", "vector_store.npy")
faiss_index_path = os.path.join(current_file_path, "store", "faiss_index.index")
# Create directories if they do not exist
store_dir = os.path.join(current_file_path, "store")
if not os.path.exists(store_dir):
    os.makedirs(store_dir)

def generate_store_embeddings(folder_path,update_progress_callback):
    image_features = []
    total_images = len(os.listdir(folder_path))
    
    if os.path.exists(vector_store_path):
        vector_store = np.load(vector_store_path, allow_pickle=True).item()
    else:
        vector_store = {}
            
    for i, img_file in enumerate(os.listdir(folder_path)):
        if img_file.endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(folder_path, img_file)
            
            # Check if image feature is already generated
            if img_path in vector_store:
                continue  # Skip if already processed
            
            image = Image.open(img_path).convert("RGB")
            
            # Generate Image Features
            inputs = processor(images=image, return_tensors="pt").to(device)
            outputs = model.get_image_features(**inputs)
            outputs = outputs / outputs.norm(p=2, dim=-1, keepdim=True)  # Normalize to unit length
            
            # Store Image Embeddings with Folder Information
            vector_store[img_path] = outputs.detach().cpu().numpy()
            image_features.append(outputs.detach().cpu().numpy())

        update_progress_callback((i + 1) / total_images)

    
    # Convert to NumPy for FAISS
    if len(image_features) > 0:
        image_features = np.vstack(image_features)

        # Save vector store
        np.save(vector_store_path, vector_store)  # Save embeddings with folder details
        

        if os.path.exists(faiss_index_path):
            faiss_index = faiss.read_index(faiss_index_path)
            faiss_index.add(image_features)
        else:
            dimension = image_features.shape[1]  # Reduced feature dimension
            faiss_index = faiss.IndexFlatIP(dimension)  # Use inner product (IP) for cosine similarity
            faiss_index.add(image_features)  # Add vectors to the index

        # Save FAISS index to file
        faiss.write_index(faiss_index, faiss_index_path)

    return 

def search(query,top_k):
    if os.path.exists(vector_store_path):
        vector_store = np.load(vector_store_path, allow_pickle=True).item()
    else:
        vector_store = {}

    if os.path.exists(faiss_index_path):
        faiss_index = faiss.read_index(faiss_index_path)
    else:
        faiss_index = None
    # Query
    query_inputs = processor(text=[query], return_tensors="pt").to(device)
    query_vector = model.get_text_features(**query_inputs)
    query_vector = query_vector / query_vector.norm(p=2, dim=-1, keepdim=True)  # Normalize to unit length

    # Perform top-k search using FAISS
    distances, top_k_indices = faiss_index.search(query_vector.cpu().detach().numpy(), top_k)
    print(distances)
    # Retrieve top-k results (excluding cluster information)
    top_k_results = [
        list(vector_store.keys())[i]
        for j, i in enumerate(top_k_indices[0])
    ]
    
    return top_k_results

def check_stores():
    if not os.path.exists(vector_store_path) or not os.path.exists(faiss_index_path):
        return False
    else:
        return True