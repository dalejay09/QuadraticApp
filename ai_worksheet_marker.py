import streamlit as st
import io
from PIL import Image
from google import genai
from pydantic import BaseModel
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Mark My Worksheet", page_icon="📝", layout="centered")

# Custom CSS for Colored Table Output
st.markdown("""
    <style>
    .result-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; }
    .result-table th { background-color: #f0f2f6; padding: 12px; text-align: left; border-bottom: 2px solid #ddd; }
    .result-table td { padding: 12px; border-bottom: 1px solid #ddd; vertical-align: top; }
    .row-CORRECT { background-color: rgba(50, 205, 50, 0.15); }       /* Soft Green */
    .row-NEARLY { background-color: rgba(255, 140, 0, 0.15); }        /* Soft Orange */
    .row-INCORRECT { background-color: rgba(255, 36, 0, 0.15); }      /* Soft Red */
    .status-badge { font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }
    .badge-CORRECT { color: #1e7e34; background-color: #d4edda; }
    .badge-NEARLY { color: #b06000; background-color: #ffe8cc; }
    .badge-INCORRECT { color: #a01818; background-color: #f8d7da; }
    </style>
""", unsafe_allow_html=True)

# --- STRUCTURED OUTPUT SCHEMA ---
class QuestionMarking(BaseModel):
    question_indicator: str
    status: str  # MUST be exactly "CORRECT", "NEARLY", or "INCORRECT"
    feedback: str

class MarkingReport(BaseModel):
    results: list[QuestionMarking]

# --- PDF GENERATOR ---
def create_pdf_report(report_data: MarkingReport) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Worksheet AI Marking Report", ln=True, align="C")
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(5)
    
    # Body
    for item in report_data.results:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, f"Question: {item.question_indicator} | Status: {item.status.upper()}", ln=True)
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 6, f"Feedback: {item.feedback}")
        pdf.ln(4)
        
    return pdf.output(dest="S")

# --- UI STATE ---
if "marking_results" not in st.session_state:
    st.session_state.marking_results = None

# --- APP LAYOUT ---
st.title("📝 Mark My Worksheet")
st.write("Snap a photo of the blank worksheet, then upload your handwritten workings. The AI Tutor will figure out which working belongs to which question and grade it!")

st.markdown("### 1. The Worksheet")
worksheet_file = st.camera_input("Take a clear photo of the worksheet questions:")

st.markdown("### 2. Your Workings")
workings_files = st.file_uploader("Take or upload photos of your handwritten workings:", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if st.button("🤖 Grade My Work", type="primary", use_container_width=True):
    if not worksheet_file:
        st.error("Please take a photo of the worksheet first!")
    elif not workings_files:
        st.error("Please upload at least one photo of your workings!")
    else:
        with st.spinner("The AI Tutor is cross-referencing your workings with the worksheet..."):
            try:
                # Prepare images for Gemini
                ws_img = Image.open(worksheet_file).convert('RGB')
                wk_imgs = [Image.open(f).convert('RGB') for f in workings_files]
                
                payload = [ws_img] + wk_imgs
                
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                prompt = """
                You are an expert, encouraging math tutor. 
                I am providing you with multiple images. 
                Image 1 is the master worksheet containing the questions.
                All subsequent images contain a student's unnumbered, handwritten workings and solutions.
                
                Your Task:
                1. Analyze the student's workings and logically map each block of working to the correct question on the worksheet.
                2. Grade each identified solution against the actual mathematical answer to the worksheet question.
                3. Determine the status: "CORRECT" (perfectly accurate), "NEARLY" (minor arithmetic error or unsimplified), or "INCORRECT" (wrong logic or incomplete).
                4. Write a concise, encouraging piece of feedback. If not completely correct, provide gentle advice on how to re-attempt it.
                
                You must return the exact structured JSON array requested.
                """
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt] + payload,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": MarkingReport,
                    },
                )
                
                # Parse strict JSON response via Pydantic schema structure
                st.session_state.marking_results = MarkingReport.model_validate_json(response.text)
                
            except Exception as e:
                st.error(f"Oops! The tutor had a glitch reading the pages: {e}")

# --- RENDER RESULTS ---
if st.session_state.marking_results:
    st.markdown("---")
    st.subheader("📊 Marking Results")
    
    # Generate HTML Table
    html_table = "<table class='result-table'><tr><th>Question</th><th>Status</th><th>Feedback</th></tr>"
    
    for row in st.session_state.marking_results.results:
        # Normalize status to match CSS classes
        safe_status = row.status.upper()
        if safe_status not in ["CORRECT", "NEARLY", "INCORRECT"]: 
            safe_status = "INCORRECT"
            
        html_table += f"""
        <tr class='row-{safe_status}'>
            <td><strong>{row.question_indicator}</strong></td>
            <td><span class='status-badge badge-{safe_status}'>{row.status.upper()}</span></td>
            <td>{row.feedback}</td>
        </tr>
        """
    html_table += "</table>"
    
    st.markdown(html_table, unsafe_allow_html=True)
    
    st.write("")
    
    # Render PDF Export Button
    pdf_bytes = create_pdf_report(st.session_state.marking_results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_bytes,
        file_name=f"worksheet_ai_marking_{timestamp}.pdf",
        mime="application/pdf",
        use_container_width=True
)
