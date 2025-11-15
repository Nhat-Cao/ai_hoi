"""
Script to ingest restaurants knowledge from markdown file into Pinecone
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import AzureOpenAI
import re
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "ai-hoi"

# Initialize Azure OpenAI for embeddings
embedding_client = AzureOpenAI(
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_EMBEDDING_ENDPOINT"),
    api_key=os.getenv("AZURE_EMBEDDING_API_KEY"),
)

def parse_restaurant_markdown(file_path):
    """Parse restaurants_knowledge.md and extract restaurant information"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    restaurants = []
    
    # Split by restaurant sections (## Restaurant Name)
    sections = re.split(r'\n## ', content)
    
    for section in sections[1:]:  # Skip first section (header)
        lines = section.split('\n')
        name = lines[0].strip()
        
        restaurant = {
            'name': name,
            'cuisine': '',
            'location': '',
            'address': '',
            'price_range': '',
            'specialties': '',
            'opening_hours': '',
            'phone': '',
            'rating': '',
            'description': '',
            'highlights': ''
        }
        
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse markdown list items
            if line.startswith('- **Địa chỉ'):
                restaurant['address'] = re.sub(r'- \*\*Địa chỉ\*\*:\s*', '', line)
            elif line.startswith('- **Món đặc sắc'):
                restaurant['specialties'] = re.sub(r'- \*\*Món đặc sắc\*\*:\s*', '', line)
            elif line.startswith('- **Giá'):
                restaurant['price_range'] = re.sub(r'- \*\*Giá\*\*:\s*', '', line)
            elif line.startswith('- **Mô tả'):
                restaurant['description'] = re.sub(r'- \*\*Mô tả\*\*:\s*', '', line)
            elif line.startswith('- **Loại hình'):
                restaurant['cuisine'] = re.sub(r'- \*\*Loại hình\*\*:\s*', '', line)
            elif line.startswith('- **Khu vực'):
                restaurant['location'] = re.sub(r'- \*\*Khu vực\*\*:\s*', '', line)
            elif line.startswith('- **Giờ mở cửa'):
                restaurant['opening_hours'] = re.sub(r'- \*\*Giờ mở cửa\*\*:\s*', '', line)
            elif line.startswith('- **Điện thoại'):
                restaurant['phone'] = re.sub(r'- \*\*Điện thoại\*\*:\s*', '', line)
            elif line.startswith('- **Đánh giá'):
                restaurant['rating'] = re.sub(r'- \*\*Đánh giá\*\*:\s*', '', line)
            elif line.startswith('- **Điểm nổi bật'):
                restaurant['highlights'] = re.sub(r'- \*\*Điểm nổi bật\*\*:\s*', '', line)
        
        restaurants.append(restaurant)
    
    return restaurants

def create_embedding(text):
    """Create embedding using Azure OpenAI"""
    response = embedding_client.embeddings.create(
        model=os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-3-small"),
        input=text
    )
    return response.data[0].embedding

def ingest_to_pinecone(restaurants):
    """Ingest restaurant data into Pinecone"""
    # Connect to index (should already exist)
    index = pc.Index(index_name)
    
    print(f"\n📊 Starting ingestion of {len(restaurants)} restaurants...")
    
    vectors = []
    for i, restaurant in enumerate(restaurants):
        # Create text representation for embedding
        text_parts = [
            f"Tên quán: {restaurant['name']}",
        ]
        
        if restaurant['cuisine']:
            text_parts.append(f"Loại hình: {restaurant['cuisine']}")
        if restaurant['location']:
            text_parts.append(f"Khu vực: {restaurant['location']}")
        if restaurant['address']:
            text_parts.append(f"Địa chỉ: {restaurant['address']}")
        if restaurant['price_range']:
            text_parts.append(f"Giá: {restaurant['price_range']}")
        if restaurant['specialties']:
            text_parts.append(f"Món đặc sắc: {restaurant['specialties']}")
        if restaurant['description']:
            text_parts.append(f"Mô tả: {restaurant['description']}")
        if restaurant['highlights']:
            text_parts.append(f"Điểm nổi bật: {restaurant['highlights']}")
        
        text_for_embedding = ". ".join(text_parts)
        
        # Create embedding
        print(f"  {i+1}. Embedding: {restaurant['name']}...")
        embedding = create_embedding(text_for_embedding)
        
        # Prepare metadata
        metadata = {
            'name': restaurant['name'],
            'cuisine': restaurant['cuisine'],
            'location': restaurant['location'],
            'address': restaurant['address'],
            'price_range': restaurant['price_range'],
            'specialties': restaurant['specialties'],
            'opening_hours': restaurant['opening_hours'],
            'phone': restaurant['phone'],
            'rating': restaurant['rating'],
            'description': restaurant['description'],
            'highlights': restaurant['highlights'],
            'text': text_for_embedding,
            'ingested_at': datetime.now().isoformat()
        }
        
        # Create vector ID (ASCII only - use index and hash)
        import hashlib
        name_hash = hashlib.md5(restaurant['name'].encode()).hexdigest()[:8]
        vector_id = f"restaurant_{i}_{name_hash}"
        
        vectors.append({
            'id': vector_id,
            'values': embedding,
            'metadata': metadata
        })
        
        # Batch upsert every 10 vectors
        if len(vectors) >= 10:
            print(f"  ⬆️  Upserting batch of {len(vectors)} vectors...")
            index.upsert(vectors=vectors)
            vectors = []
    
    # Upsert remaining vectors
    if vectors:
        print(f"  ⬆️  Upserting final batch of {len(vectors)} vectors...")
        index.upsert(vectors=vectors)
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"\n✅ Ingestion complete!")
    print(f"📊 Index stats: {stats}")
    return stats

def main():
    """Main function"""
    print("🍜 Restaurant Knowledge Ingestion Tool")
    print("=" * 50)
    
    # Path to markdown file
    markdown_file = os.path.join(os.path.dirname(__file__), '..', 'restaurants_knowledge.md')
    
    if not os.path.exists(markdown_file):
        print(f"❌ Error: File not found: {markdown_file}")
        return
    
    print(f"\n📖 Reading: {markdown_file}")
    
    # Parse markdown
    restaurants = parse_restaurant_markdown(markdown_file)
    print(f"✅ Parsed {len(restaurants)} restaurants")
    
    # Show sample
    if restaurants:
        print(f"\n📝 Sample restaurant:")
        sample = restaurants[20]  # Show Fsoft sample
        print(f"  Name: {sample['name']}")
        print(f"  Address: {sample['address']}")
        print(f"  Specialties: {sample['specialties']}")
        print(f"  Price: {sample['price_range']}")
        print(f"  Description: {sample['description'][:50]}...")
    
    # Confirm
    response = input(f"\n❓ Ingest {len(restaurants)} restaurants to Pinecone index '{index_name}'? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    # Ingest to Pinecone
    ingest_to_pinecone(restaurants)
    
    print("\n🎉 Done!")

if __name__ == "__main__":
    main()
