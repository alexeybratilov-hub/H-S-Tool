"""
Streamlit UI module for document upload and classification.
Allows single and batch document uploads with AI-based classification.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import streamlit as st
from datetime import datetime

# Import document classifier
from ot_agent.document_classifier import (
    classify_document,
    get_all_document_types,
    get_all_document_categories,
)
from ot_agent.baseline_db import get_connection, init_baseline_schema


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

# Ensure baseline schema exists
try:
    conn = get_connection(DB_PATH)
    init_baseline_schema(conn)
    conn.close()
except Exception as e:
    st.error(f"Failed to initialize database schema: {e}")


def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text content from a file.
    Supports .txt, .md, .pdf (if pdfplumber available), .docx (if python-docx available).
    """
    try:
        if file_path.suffix == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif file_path.suffix == ".md":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif file_path.suffix == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join([page.extract_text() for page in pdf.pages])
                    return text or ""
            except ImportError:
                st.warning("PDF support requires pdfplumber: pip install pdfplumber")
                return ""
        elif file_path.suffix == ".docx":
            try:
                from docx import Document
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                st.warning("DOCX support requires python-docx: pip install python-docx")
                return ""
        else:
            # Try to read as text
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        st.error(f"Failed to read file {file_path}: {e}")
        return ""


def save_document_to_db(
    conn,
    document_id: str,
    type_id: str,
    code: str,
    title: str,
    topic: str,
    category: str,
    file_content: Optional[bytes] = None,
    filename: Optional[str] = None,
    source_note: str = "Uploaded via document upload form",
) -> bool:
    """
    Save classified document to the database.
    """
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO baseline_documents (
                document_id, type_id, code, title, topic, category,
                lifecycle_stage, applicability_note, legal_basis_note,
                template_id, status, verification_status, user_note, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                type_id,
                code,
                title,
                topic,
                category,
                "ACTIVE",
                "Requires verification",
                "Uploaded document",
                None,
                "SUGGESTED",
                "REQUIRES_VERIFICATION",
                source_note,
                100,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Failed to save document: {e}")
        return False


def get_type_id_by_code(conn, type_code: str) -> Optional[str]:
    """Get type_id from document_types table by code."""
    row = conn.execute(
        "SELECT type_id FROM document_types WHERE code = ?",
        (type_code,),
    ).fetchone()
    return row["type_id"] if row else None


def create_type_if_not_exists(conn, type_code: str, title: str, topic: str = "OT") -> str:
    """Create document type if it doesn't exist, return type_id."""
    type_id = f"TYPE_{type_code}"
    
    # Check if exists
    existing = get_type_id_by_code(conn, type_code)
    if existing:
        return existing
    
    # Create new type
    try:
        conn.execute(
            """
            INSERT INTO document_types (type_id, code, title, topic, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (type_id, type_code, title, topic, f"Auto-created type for {title}"),
        )
        conn.commit()
        return type_id
    except Exception as e:
        st.error(f"Failed to create document type: {e}")
        return type_id  # Return the intended ID anyway


def render_document_upload():
    """Main render function for document upload page."""
    st.title("\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432")
    st.markdown("""
    \u0417\u0434\u0435\u0441\u044c \u0432\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u0437\u0430\u0433\u0440\u0443\u0436\u0430\u0442\u044c \u043e\u0434\u0438\u043d \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442 \u0438\u043b\u0438 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e.
    \u041d\u0435\u0439\u0440\u043e\u0441\u0435\u0442\u044c \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442 \u0442\u0438\u043f \u0438 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430.
    """)
    
    # Show upload statistics
    show_statistics()
    
    # Upload mode selection
    upload_mode = st.radio(
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0435\u0436\u0438\u043c:",
        ["\u041e\u0434\u0438\u043d \u0444\u0430\u0439\u043b", "\u041d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0444\u0430\u0439\u043b\u043e\u0432"],
        horizontal=True,
    )
    
    if upload_mode == "\u041e\u0431\u043d\u0438\u0439 \u0444\u0430\u0439\u043b":
        upload_single_document()
    else:
        upload_multiple_documents()


def show_statistics():
    """Show document upload statistics."""
    conn = get_connection(DB_PATH)
    try:
        total_docs = conn.execute("SELECT COUNT(*) FROM baseline_documents").fetchone()[0]
        total_types = conn.execute("SELECT COUNT(*) FROM document_types").fetchone()[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("\u0412\u0441\u0435\u0433\u043e \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432", total_docs)
        col2.metric("\u0412\u0438\u0434\u044b \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432", total_types)
        col3.metric("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0439", "N/A")
    finally:
        conn.close()


def upload_single_document():
    """Upload and classify a single document."""
    st.subheader("\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043e\u0434\u043d\u043e\u0433\u043e \u0444\u0430\u0439\u043b\u0430")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b",
        type=["txt", "md", "pdf", "docx"],
        accept_multiple_files=False,
    )
    
    if uploaded_file is None:
        st.info("\u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430 \u0432\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b \u0438\u0437 \u0441\u0438\u0441\u0442\u0435\u043c\u043d\u043e\u0433\u043e \u043f\u0440\u043e\u0432\u043e\u0434\u043d\u0438\u043a\u0430")
        return
    
    # Process the file
    process_uploaded_file(uploaded_file)


def upload_multiple_documents():
    """Upload and classify multiple documents."""
    st.subheader("\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u0438\u0445 \u0444\u0430\u0439\u043b\u043e\u0432")
    
    # File uploader for multiple files
    uploaded_files = st.file_uploader(
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0444\u0430\u0439\u043b\u043e\u0432",
        type=["txt", "md", "pdf", "docx"],
        accept_multiple_files=True,
    )
    
    if uploaded_files is None or len(uploaded_files) == 0:
        st.info("\u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430 \u0432\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043f \u0444\u0430\u0439\u043b\u043e\u0432")
        return
    
    st.info(f"\u0412\u044b\u0431\u0440\u0430\u043d\u043e {len(uploaded_files)} \u0444\u0430\u0439\u043b\u043e\u0432")
    
    # Process each file
    progress_bar = st.progress(0)
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        progress_bar.progress((i + 1) / len(uploaded_files))
        result = process_uploaded_file(uploaded_file, show_details=False)
        if result:
            results.append(result)
    
    progress_bar.empty()
    
    # Show summary
    if results:
        st.success(f"\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u043e {len(results)} \u0444\u0430\u0439\u043b\u043e\u0432")
        
        # Show results table
        st.subheader("\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442")
        display_results_table(results)


def process_uploaded_file(uploaded_file, show_details: bool = True) -> Optional[Dict]:
    """
    Process an uploaded file: extract text, classify, and save to database.
    Returns classification result or None if failed.
    """
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=uploaded_file.name, delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)
        
        # Extract text
        with st.spinner(f"\u0418\u0437\u0432\u043b\u0435\u043a\u0430\u0435\u043c \u0442\u0435\u043a\u0441\u0442 \u0438\u0437 {uploaded_file.name}..."):
            text = extract_text_from_file(tmp_path)
        
        if not text or len(text.strip()) == 0:
            st.error(f"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0438\u0437\u0432\u043b\u0435\u0447\u044c \u0442\u0435\u043a\u0441\u0442 \u0438\u0437 \u0444\u0430\u0439\u043b\u0430: {uploaded_file.name}")
            os.unlink(tmp_path)
            return None
        
        # Classify document
        classification = classify_document(text, uploaded_file.name)
        
        # Generate document ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        document_id = f"DOC_{timestamp}_{i}" if 'i' in locals() else f"DOC_{timestamp}"
        
        # Save to database
        conn = get_connection(DB_PATH)
        try:
            # Create type if not exists
            type_id = create_type_if_not_exists(
                conn,
                classification["type_code"],
                classification["type_title"],
                classification["topic"]
            )
            
            # Save document
            success = save_document_to_db(
                conn,
                document_id=document_id,
                type_id=type_id,
                code=classification["code"],
                title=classification["title"],
                topic=classification["topic"],
                category=classification["category"],
                filename=uploaded_file.name,
                source_note=f"Uploaded: {uploaded_file.name}",
            )
            
            if success:
                classification["document_id"] = document_id
                classification["filename"] = uploaded_file.name
                classification["status"] = "\u0423\u0441\u043f\u0435\u0448\u043d\u043e \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e"
            else:
                classification["status"] = "\u041e\u0448\u0438\u0431\u043a\u0430"
        finally:
            conn.close()
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Show results if requested
        if show_details:
            display_classification_results(classification, uploaded_file.name)
        
        return classification
        
    except Exception as e:
        st.error(f"\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0435: {e}")
        return None


def display_classification_results(classification: Dict, filename: str):
    """Display classification results in a nice format."""
    st.subheader("\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442 \u043a\u043b\u0430\u0441\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**\u0418\u043c\u044f \u0444\u0430\u0439\u043b\u0430:**")
        st.write(filename)
        
        st.markdown("**\u0412\u043e\u043f\u0440\u043e\u0441\u044b \u043d\u0435\u0439\u0440\u043e\u0441\u0435\u0442\u0438:**")
        st.write(f"\u0422\u0438\u043f: {classification.get('type_title', 'N/A')}")
        st.write(f"\u041a\u043e\u0434: {classification.get('type_code', 'N/A')}")
        
        st.markdown("**\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:**")
        st.write(classification.get('category_title', 'N/A'))
    
    with col2:
        st.markdown("**\u0422\u0435\u043c\u0430:**")
        st.write(classification.get('topic', 'N/A'))
        
        st.markdown("**\u041a\u043e\u0434 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430:**")
        st.write(classification.get('code', 'N/A'))
        
        st.markdown("**\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:**")
        st.write(classification.get('title', 'N/A')[:100])
    
    # Confidence
    st.markdown(f"**\u0414\u043e\u0432\u0435\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0441\u0442\u044c \u043a\u043b\u0430\u0441\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438:** {classification.get('confidence', 0) * 100:.1f}%")
    
    # Status
    if classification.get('status'):
        st.success(classification['status'])
    
    st.divider()


def display_results_table(results: List[Dict]):
    """Display results in a table format."""
    if not results:
        return
    
    # Prepare data for table
    table_data = []
    for r in results:
        table_data.append({
            "\u0418\u043c\u044f": r.get('filename', 'N/A'),
            "\u0422\u0438\u043f": r.get('type_title', 'N/A'),
            "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f": r.get('category_title', 'N/A'),
            "\u041a\u043e\u0434": r.get('code', 'N/A'),
            "\u0414\u043e\u0432\u0435\u0440\u0438\u0435": f"{r.get('confidence', 0) * 100:.1f}%",
            "\u0421\u0442\u0430\u0442\u0443\u0441": r.get('status', 'N/A'),
        })
    
    st.table(table_data)


# Main render function
render = render_document_upload
