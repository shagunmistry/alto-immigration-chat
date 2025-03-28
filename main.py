import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import os
import numpy as np
from helpers import SYSTEM_PROMPT
import supabase
import time
from datetime import datetime, timedelta

from numpy import dot
from numpy.linalg import norm
from constants import us_websites, canada_websites

# load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Immigration Consultant Assistant",
    page_icon="🌍",
    layout="wide"
)

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_client = supabase.create_client(supabase_url, supabase_key)

scrape_interval_days = int(os.getenv("SCRAPE_INTERVAL_DAYS", 7))  # Default to 7 days if not set

# Function to check if scraping is needed
def should_scrape_website(category, url):
    try:
        # Query the last scrape time from Supabase
        response = supabase_client.table("immigration_website_scrape_status").select("*").eq("category", category).eq("url", url).execute()
        
        if response and response.data:
            # Parse the timestamp from Supabase
            last_scraped_str = response.data[0]['last_scraped']
            
            # Convert to datetime object, handling timezone
            try:
                # Try parsing ISO format with timezone
                last_scraped = datetime.fromisoformat(last_scraped_str)
                # Convert to naive datetime for comparison
                last_scraped = last_scraped.replace(tzinfo=None)
            except:
                # If format issues, try alternative parsing
                try:
                    # Parse without timezone info
                    last_scraped = datetime.strptime(last_scraped_str, "%Y-%m-%d %H:%M:%S")
                except:
                    # If all parsing fails, default to scraping
                    # Store the status in session state
                    st.session_state.scrape_status[f"{category}:{url}"] = "Unknown"
                    return True
            
            # Format the last scrape time for display
            now = datetime.now()
            diff = now - last_scraped
            
            if diff.days > 30:
                formatted_time = f"{last_scraped.strftime('%b %d, %Y')}"
            elif diff.days > 0:
                formatted_time = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds // 3600 > 0:
                hours = diff.seconds // 3600
                formatted_time = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds // 60 > 0:
                minutes = diff.seconds // 60
                formatted_time = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                formatted_time = "Just now"
            
            # Store the formatted time in session state
            st.session_state.scrape_status[f"{category}:{url}"] = formatted_time
            
            # Check if it's been more than scrape_interval_days since last scrape
            return now - last_scraped > timedelta(days=scrape_interval_days)
            
        # No record found, should scrape
        st.session_state.scrape_status[f"{category}:{url}"] = "Never"
        return True
    except Exception as e:
        st.sidebar.error(f"Error checking scrape status: {str(e)}")
        st.session_state.scrape_status[f"{category}:{url}"] = "Error retrieving time"
        return True  # In case of error, default to scraping
    
# Function to update scrape status
def update_scrape_status(category, url):
    try:
        # Check if record exists
        response = supabase_client.table("immigration_website_scrape_status").select("*").eq("category", category).eq("url", url).execute()
        
        if response and response.data:
            # Update existing record
            supabase_client.table("immigration_website_scrape_status").update({"last_scraped": datetime.now().isoformat()}).eq("category", category).eq("url", url).execute()
        else:
            # Insert new record
            supabase_client.table("immigration_website_scrape_status").insert({
                "category": category,
                "url": url,
                "last_scraped": datetime.now().isoformat()
            }).execute()
    except Exception as e:
        st.sidebar.error(f"Error updating scrape status: {str(e)}")

# Function to scrape website content
def scrape_website(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Remove blank lines
            text = ' '.join(chunk for chunk in chunks if chunk)
            return text
        else:
            return f"Failed to retrieve the webpage: Status code {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Function to split text into chunks
def split_into_chunks(text, chunk_size=1000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1  # +1 for the space

        if current_length >= chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

# Function to compute embeddings
def compute_embeddings(text_chunks):
    embeddings = []
    # Process chunks in batches to avoid rate limits
    batch_size = 20
    for i in range(0, len(text_chunks), batch_size):
        batch = text_chunks[i:i+batch_size]
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=batch,
            encoding_format="float"
        )
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
    return embeddings

# Function to store chunks and embeddings in Supabase
def store_in_supabase(category, url, chunks, embeddings):
    try:
        # First, delete any existing data for this URL
        supabase_client.table("immigration_website_chunks").delete().eq("category", category).eq("url", url).execute()
        
        # Insert new chunks and embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Convert numpy array to list if needed
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
                
            supabase_client.table("immigration_website_chunks").insert({
                "category": category,
                "url": url,
                "chunk_index": i,
                "chunk_text": chunk,
                "embedding": embedding
            }).execute()
        return True
    except Exception as e:
        st.sidebar.error(f"Error storing data in Supabase: {str(e)}")
        return False

# Function to retrieve chunks and embeddings from Supabase
def get_from_supabase(category):
    try:
        response = supabase_client.table("immigration_website_chunks").select("*").eq("category", category).execute()
        if response and response.data:
            chunks = []
            embeddings = []
            urls = set()
            
            # Sort by chunk_index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x['chunk_index'])
            
            for item in sorted_data:
                chunks.append(item['chunk_text'])
                # Convert embedding to numpy array if it's not already
                if isinstance(item['embedding'], (list, np.ndarray)):
                    embeddings.append(item['embedding'])
                elif isinstance(item['embedding'], str):
                    # Parse string representation of array to actual array
                    import json
                    try:
                        # Try parsing as JSON
                        embedding_array = json.loads(item['embedding'])
                        embeddings.append(embedding_array)
                    except json.JSONDecodeError:
                        # If not JSON, try parsing as string representation of array
                        import ast
                        try:
                            embedding_array = ast.literal_eval(item['embedding'])
                            embeddings.append(embedding_array)
                        except:
                            st.warning(f"Could not parse embedding for chunk {item['chunk_index']}")
                            continue
                urls.add(item['url'])
            
            # Convert embeddings to numpy arrays
            embeddings = [np.array(emb, dtype=np.float32) for emb in embeddings]
            
            return chunks, embeddings, list(urls)
        return [], [], []
    except Exception as e:
        st.sidebar.error(f"Error retrieving data from Supabase: {str(e)}")
        return [], [], []

# Function to retrieve relevant chunks based on query
def retrieve_relevant_chunks(query, text_chunks, embeddings, top_k=3):
    # Get embedding for the query
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=[query],
        encoding_format="float"
    )
    query_embedding = response.data[0].embedding

    # Calculate cosine similarity
    def cosine_similarity(a, b):
        return dot(a, b)/(norm(a)*norm(b))

    similarities = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return [text_chunks[i] for i in top_indices], [similarities[i] for i in top_indices]

# Function to call OpenAI API
def get_openai_response(query, context):
    try:
        combined_context = "\n\n".join(context)

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context information: {combined_context}\n\nQuestion: {query}"}
            ],
            temperature=0.2,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

# Sidebar for website selection and configuration
st.sidebar.title("Configuration")

country = st.sidebar.selectbox(
    "Select Country",
    ["United States", "Canada"]
)

if country == "United States":
    website_options = us_websites
elif country == "Canada":
    website_options = canada_websites


if 'scrape_status' not in st.session_state:
    st.session_state.scrape_status = {}

selected_websites = st.sidebar.multiselect(
    "Select Websites to Query",
    list(website_options.keys()),
    default=[list(website_options.keys())[0]]
)

# if selected_websites:
#     st.sidebar.subheader("Last Updated")
    
#     # Create a two-column layout for compact display
#     for category in selected_websites:
#         with st.sidebar.expander(f"{category}"):
#             urls = website_options[category]
            
#             # Force check scrape status for all selected websites
#             for url in urls:
#                 # This will populate the scrape_status dictionary
#                 # but we ignore the return value here
#                 should_scrape_website(category, url)
            
#             # Now display the status from our cached values
#             for url in urls:
#                 key = f"{category}:{url}"
#                 status = st.session_state.scrape_status.get(key, "Unknown")
                
#                 # Display with domain name for better readability
#                 domain = url.split('//')[-1].split('/')[0]
#                 st.write(f"**{domain}**: {status}")

st.sidebar.info(f"Current scrape interval: {scrape_interval_days} days")

scrape_button = st.sidebar.button("Check & Update Website Data")

# Main content area
st.title("Immigration Consultant Assistant")
st.markdown("Ask questions about immigration procedures and policies. The assistant will retrieve information from official government websites.")

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []



# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Check and update website data when requested
if scrape_button:
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    # Count total URLs to process
    total_urls = sum(len(website_options[category]) for category in selected_websites)
    processed_urls = 0
    updated_sites = 0

    for category in selected_websites:
        urls = website_options[category]
        
        for url in urls:
            status_text.text(f"Checking {category} - {url}...")
            
            # Check if scraping is needed
            if should_scrape_website(category, url):
                status_text.text(f"Scraping {category} - {url}...")
                
                # Scrape website
                website_text = scrape_website(url)
                
                # Split into chunks
                chunks = split_into_chunks(website_text)
                
                # Compute embeddings
                embeddings = compute_embeddings(chunks)
                
                # Store in Supabase
                if store_in_supabase(category, url, chunks, embeddings):
                    update_scrape_status(category, url)
                    updated_sites += 1
            
            processed_urls += 1
            progress_bar.progress(processed_urls / total_urls)
    
    if updated_sites > 0:
        status_text.text(f"Updated {updated_sites} websites successfully!")
    else:
        status_text.text("All websites are up to date!")
    
    time.sleep(2)  # Show the message for a moment
    progress_bar.empty()
    status_text.empty()

# Chat input
if prompt := st.chat_input("What would you like to know about immigration?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Retrieve relevant chunks from selected websites
        all_relevant_chunks = []
        all_sources = []

        for website_name in selected_websites:
            # Get chunks and embeddings from Supabase
            chunks, embeddings, urls = get_from_supabase(website_name)
            
            if chunks and embeddings:
                relevant_chunks, similarities = retrieve_relevant_chunks(prompt, chunks, embeddings)
                
                for chunk, similarity in zip(relevant_chunks, similarities):
                    if similarity > 0.3:  # Only include if similarity is above threshold
                        all_relevant_chunks.append(chunk)
                        all_sources.append(website_name)
            else:
                full_response = "Please check and update website data using the sidebar options before asking questions."
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                break

        if all_relevant_chunks:
            # Get response from OpenAI
            full_response = get_openai_response(prompt, all_relevant_chunks)

            # Add sources information
            sources_text = "\n\n**Sources:**\n"
            for category in set(all_sources):
                sources_text += f"- {category} category websites\n"
                sources_text += "\n".join([f"  - {url}" for url in set(urls)]) + "\n"
            
            full_response += sources_text
            message_placeholder.markdown(full_response)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add helpful information at the bottom
st.markdown("---")
st.markdown("""
**How to use this assistant:**
1. Select the country and specific websites from the sidebar
2. Set the scrape interval and click "Check & Update Website Data" to ensure you have the latest information
3. Ask your immigration-related questions in the chat
""")