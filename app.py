import streamlit as st
import os
import json
from PIL import Image, ImageDraw
from retriever.search import FashionRetriever
from utils.database import FashionImageDB

# Page configurations
st.set_page_config(
    page_title="Fashion & Context Retrieval Engine",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark-themed premium look)
st.markdown("""
    <style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8F00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 15px;
    }
    .score-badge {
        background-color: #FF4B4B;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .metric-text {
        font-size: 0.8rem;
        color: #555;
    }
    </style>
""", unsafe_allow_name_tags=True, unsafe_allow_html=True)

# Cache the retriever to avoid loading CLIP models on every rerun
@st.cache_resource
def get_retriever(db_path):
    return FashionRetriever(db_path=db_path, device="cpu")

# Database path configuration
DB_PATH = "fashion_search.db"
DATASET_DIR = r"c:\Users\swaro\Desktop\glance assgn\val_test2020\test"

# Main Layout
st.markdown('<div class="main-title">👕 Multimodal Fashion & Context Retrieval</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Search 1,000+ fashion images using natural language, powered by crop-based Multi-Vector CLIP search.</div>', unsafe_allow_html=True)

# Check database existence
if not os.path.exists(DB_PATH):
    st.error(f"Database not found at `{DB_PATH}`. Please run the indexing pipeline first using `python run.py index`.")
    st.stop()

# Load DB stats in sidebar
db_temp = FashionImageDB(DB_PATH)
total_records = db_temp.get_count()
db_temp.close()

with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown(f"**Database Size**: `{total_records}` indexed images")
    
    # K slider
    k_val = st.slider("Number of results to retrieve (K)", min_value=1, max_value=20, value=5)
    
    st.markdown("---")
    st.header("📝 Benchmark Prompts")
    st.write("Click any benchmark query below to populate the search bar:")
    
    benchmarks = {
        "Attribute Specific": "A person in a bright yellow raincoat.",
        "Contextual/Place": "Professional business attire inside a modern office.",
        "Complex Semantic": "Someone wearing a blue shirt sitting on a park bench.",
        "Style Inference": "Casual weekend outfit for a city walk.",
        "Compositional": "A red tie and a white shirt in a formal setting."
    }
    
    # Store selected query in session state
    if "selected_query" not in st.session_state:
        st.session_state.selected_query = ""
        
    for name, text in benchmarks.items():
        if st.button(name, use_container_width=True):
            st.session_state.selected_query = text

# Text Search Box
query_input = st.text_input(
    "Enter your fashion / environment search description:", 
    value=st.session_state.selected_query,
    placeholder="e.g. Someone in a red jacket and blue jeans walking in a park"
)

if query_input:
    # Get retriever
    with st.spinner("Loading models and search cache..."):
        retriever = get_retriever(DB_PATH)
        
    # Run search
    with st.spinner("Running retrieval..."):
        results = retriever.search(query_input, k=k_val)
        
    # Render query decomposition details
    parsed_queries = retriever.parser.parse_query(query_input)
    
    st.markdown("### 🔍 Query Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Global Context**\n\n`{parsed_queries['global']}`")
    with col2:
        st.success(f"**Upper Body Query**\n\n`{parsed_queries['upper'] if parsed_queries['upper'] else '[Unspecified]'}`")
    with col3:
        st.warning(f"**Lower Body Query**\n\n`{parsed_queries['lower'] if parsed_queries['lower'] else '[Unspecified]'}`")
        
    st.markdown("---")
    st.markdown(f"### 🎯 Top {len(results)} Search Results")
    
    if not results:
        st.warning("No matches found.")
    else:
        # Display images in a responsive grid layout
        # We can dynamically set columns (e.g. 2 columns for smaller screen heights, or 3-4 columns)
        grid_cols = st.columns(3)
        
        for idx, res in enumerate(results):
            col = grid_cols[idx % 3]
            img_id = res['image_id']
            score = res['score']
            box_person = res['box_person']
            
            img_path = os.path.join(DATASET_DIR, img_id)
            
            with col:
                # Build result card container
                with st.container():
                    st.markdown(f"#### Rank {idx+1}")
                    
                    if os.path.exists(img_path):
                        img = Image.open(img_path).convert("RGB")
                        
                        # Draw bounding box on image if present
                        if box_person:
                            draw = ImageDraw.Draw(img)
                            draw.rectangle(
                                [box_person['xmin'], box_person['ymin'], box_person['xmax'], box_person['ymax']],
                                outline="red",
                                width=6
                            )
                            
                        st.image(img, use_container_width=True)
                    else:
                        st.error("Image file missing from local path.")
                        
                    # Display metrics
                    st.markdown(f"<span class=\"score-badge\">Score: {score:.4f}</span>", unsafe_allow_html=True)
                    st.markdown(f"**File**: `{img_id}`")
                    
                    # Expandable score breakdown
                    with st.expander("Score Breakdown", expanded=False):
                        st.markdown(f"<div class=\"metric-text\">Global Sim: <code>{res['sim_global']:.4f}</code></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class=\"metric-text\">Upper Sim: <code>{res['sim_upper']:.4f}</code></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class=\"metric-text\">Lower Sim: <code>{res['sim_lower']:.4f}</code></div>", unsafe_allow_html=True)
                        if box_person:
                            st.markdown(f"<div class=\"metric-text\">Detection Conf: <code>{box_person['score']:.2f}</code></div>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
