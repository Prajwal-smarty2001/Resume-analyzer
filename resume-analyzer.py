import streamlit as st
import PyPDF2
import docx
import io
import re
from openai import AzureOpenAI
import json
from typing import Dict, List, Optional
import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for better styling with dark mode support
st.markdown("""
<style>
    /* Light theme colors */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8f9ff;
        --text-primary: #333333;
        --text-secondary: #666666;
        --border-color: #e0e0e0;
        --card-bg: #ffffff;
        --header-gradient: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        --success-bg: #e8f5e8;
        --success-border: #4caf50;
        --error-bg: #ffe8e8;
        --error-border: #f44336;
        --shadow: rgba(0,0,0,0.1);
    }

    /* Dark theme colors */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #0e1117;
            --bg-secondary: #262730;
            --text-primary: #fafafa;
            --text-secondary: #a0a0a0;
            --border-color: #404040;
            --card-bg: #1e1e1e;
            --header-gradient: linear-gradient(90deg, #4a5568 0%, #553c9a 100%);
            --success-bg: #1a2e1a;
            --success-border: #2d5a2d;
            --error-bg: #2e1a1a;
            --error-border: #5a2d2d;
            --shadow: rgba(0,0,0,0.3);
        }
    }

    /* Force dark mode styles for Streamlit */
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }

    .main-header {
        background: var(--header-gradient);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px var(--shadow);
    }

    .main-footer {
        background: var(--header-gradient);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-top: 3rem;
        box-shadow: 0 4px 6px var(--shadow);
    }

    .analysis-card {
        background: var(--card-bg);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px var(--shadow);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }

    .skill-match {
        background: var(--success-bg);
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem;
        display: inline-block;
        border: 1px solid var(--success-border);
        color: var(--text-primary);
    }

    .skill-gap {
        background: var(--error-bg);
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem;
        display: inline-block;
        border: 1px solid var(--error-border);
        color: var(--text-primary);
    }

    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: var(--bg-secondary);
        color: var(--text-primary);
    }

    .metric-card {
        background: var(--header-gradient);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px var(--shadow);
    }

    .alert-success {
        background: var(--success-bg);
        border: 1px solid var(--success-border);
        color: var(--text-primary);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        font-weight: bold;
        text-align: center;
    }

    .alert-info {
        background: var(--bg-secondary);
        border: 1px solid #667eea;
        color: var(--text-primary);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        text-align: center;
    }

    /* Fix Streamlit elements for dark mode */
    .stTextArea > div > div > textarea {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
    }

    .stSelectbox > div > div > div {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }

    .stSidebar {
        background-color: var(--bg-secondary) !important;
    }

    .stSidebar .stMarkdown {
        color: var(--text-primary) !important;
    }

    div[data-testid="metric-container"] {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 5px;
        padding: 1rem;
    }

    .stProgress > div > div > div {
        background-color: #667eea !important;
    }

    /* JSON display styling */
    .stJson {
        background-color: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* File uploader styling */
    .stFileUploader > div {
        background-color: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }

    .streamlit-expanderContent {
        background-color: var(--card-bg) !important;
        color: var(--text-primary) !important;
    }
</style>
""", unsafe_allow_html=True)


class ResumeAnalyzer:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key='2ba3acaa3aed450d849854da591b2a9d',
            api_version='2023-05-15',
            azure_endpoint='https://ltts-openai.openai.azure.com'
        )

    def extract_text_from_pdf(self, uploaded_file) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return ""

    def extract_text_from_docx(self, uploaded_file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(uploaded_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading DOCX: {str(e)}")
            return ""

    def extract_text_from_doc(self, uploaded_file) -> str:
        """Extract text from DOC file (basic text extraction)"""
        try:
            # For .doc files, we'll need python-docx2txt or similar
            # This is a simplified approach
            content = uploaded_file.read()
            text = content.decode('utf-8', errors='ignore')
            # Clean up the text
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)
            return text
        except Exception as e:
            st.error(f"Error reading DOC: {str(e)}")
            return ""

    def extract_text_from_file(self, uploaded_file) -> str:
        """Extract text based on file type"""
        file_type = uploaded_file.type

        if file_type == "application/pdf":
            return self.extract_text_from_pdf(uploaded_file)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self.extract_text_from_docx(uploaded_file)
        elif file_type == "application/msword":
            return self.extract_text_from_doc(uploaded_file)
        else:
            st.error(f"Unsupported file type: {file_type}")
            return ""

    def create_text_report(self, analysis_result: Dict, file_name: str, target_role: str) -> str:
        """Create a readable text format report"""
        report = f"""
==============================================
        RESUME ANALYSIS REPORT
==============================================

File: {file_name}
Target Role: {target_role if target_role else "General Analysis"}
Analysis Date: {st.session_state.get('analysis_date', 'Not available')}

==============================================
CANDIDATE SUMMARY
==============================================
"""

        if "candidate_summary" in analysis_result:
            summary = analysis_result["candidate_summary"]
            report += f"""
Name: {summary.get('name', 'N/A')}
Email: {summary.get('email', 'N/A')}
Phone: {summary.get('phone', 'N/A')}
Location: {summary.get('location', 'N/A')}
Total Experience: {summary.get('total_experience', 'N/A')}
Current Role: {summary.get('current_role', 'N/A')}
"""

        # Technical Skills
        if "technical_skills" in analysis_result:
            report += f"""
==============================================
TECHNICAL SKILLS
==============================================
{chr(10).join(f"• {skill}" for skill in analysis_result["technical_skills"])}
"""

        # Soft Skills
        if "soft_skills" in analysis_result:
            report += f"""
==============================================
SOFT SKILLS
==============================================
{chr(10).join(f"• {skill}" for skill in analysis_result["soft_skills"])}
"""

        # Role Fit Analysis
        if "role_fit_analysis" in analysis_result and target_role:
            role_fit = analysis_result["role_fit_analysis"]
            report += f"""
==============================================
ROLE FIT ANALYSIS
==============================================
Overall Fit: {role_fit.get('fit_percentage', 'N/A')}

Matching Skills:
{chr(10).join(f"✓ {skill}" for skill in role_fit.get('matching_skills', []))}

Missing Skills:
{chr(10).join(f"✗ {skill}" for skill in role_fit.get('missing_skills', []))}

Recommendation:
{role_fit.get('recommendation', 'No recommendation available')}
"""

        # Overall Scoring
        if "overall_score" in analysis_result:
            scores = analysis_result["overall_score"]
            report += f"""
==============================================
OVERALL SCORING
==============================================
Technical Score: {scores.get('technical_score', 'N/A')}
Experience Score: {scores.get('experience_score', 'N/A')}
Overall Rating: {scores.get('overall_rating', 'N/A')}
"""

        # Strengths
        if "strengths" in analysis_result:
            report += f"""
==============================================
STRENGTHS
==============================================
{chr(10).join(f"• {strength}" for strength in analysis_result["strengths"])}
"""

        # Improvement Areas
        if "improvement_areas" in analysis_result:
            report += f"""
==============================================
AREAS FOR IMPROVEMENT
==============================================
{chr(10).join(f"• {area}" for area in analysis_result["improvement_areas"])}
"""

        report += """
==============================================
END OF REPORT
==============================================
"""
        return report

    def analyze_resume(self, resume_text: str, target_role: str = "", temp: float = 0.7) -> Dict:
        """Analyze resume using Azure OpenAI"""
        try:
            target_role = target_role if target_role else "General Analysis"
            prompt = f"""
            TARGET ROLE: {target_role}
            RESUME TEXT: {resume_text}
            As a senior HR analyst and recruitment expert also expert in {target_role}, analyze the following resume 
            comprehensively:
            Please provide a detailed analysis in JSON format with the following structure:
            {{
                "candidate_summary": {{
                    "name": "extracted name",
                    "email": "extracted email",
                    "phone": "extracted phone",
                    "location": "extracted location/address",
                    "total_experience": "years of experience",
                    "current_role": "current position"
                }},
                "technical_skills": [
                    "list of technical skills found"
                ],
                "soft_skills": [
                    "list of soft skills identified"
                ],
                "certifications": [
                    "list of certifications"
                ],
                "education": [
                    "educational qualifications"
                ],
                "experience_analysis": {{
                    "total_years": "number",
                    "key_companies": ["company names"],
                    "career_progression": "analysis of career growth",
                    "domain_expertise": ["domains/industries"]
                }},
                "strengths": [
                    "key strengths identified"
                ],
                "improvement_areas": [
                    "areas for improvement"
                ],
                "role_fit_analysis": {{
                    "matching_skills": ["skills that match the target role"],
                    "missing_skills": ["skills needed for the target role but not present"],
                    "fit_percentage": "percentage match",
                    "recommendation": "hiring recommendation"
                }},
                "overall_score": {{
                    "technical_score": "out of 10",
                    "experience_score": "out of 10",
                    "overall_rating": "out of 10"
                }}
            }}

            Provide only the JSON response without any additional text or formatting.
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": f"You are a senior HR analyst and {target_role} and recruitment expert with 15+ years of experience in "
                                "talent acquisition, resume screening, and candidate evaluation. You specialize in "
                                "comprehensive resume analysis and role-fit assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temp
            )

            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            return result

        except json.JSONDecodeError as e:
            st.error("Error parsing AI response. Please try again.")
            return {"error": "JSON parsing failed"}
        except Exception as e:
            if "maximum context length" in str(e).lower() or "tokens" in str(e).lower():
                st.error("❌ Resume too long: exceeds token limit. Please use a shorter resume.")
                return {"error": "Token limit exceeded"}
            else:
                st.error(f"⚠️ Unexpected error occurred: {e}")
                return {"error": str(e)}


# Helper to safely parse a score that may be int (e.g., 8) or str (e.g., "8/10" or "8")
def _to_10_scale(value):
    # If value is None, use 0
    if value is None:
        return "0"
    # If already an int or float, clamp and return as int string
    if isinstance(value, (int, float)):
        # Optional: clamp to [0, 10]
        v = max(0, min(10, int(value)))
        return str(v)
    # If it's a string, try to extract the first numeric part
    s = str(value).strip()
    # Handle formats like "8/10", "8 / 10", "8 of 10", "8 out of 10"
    for sep in ["/", "of", "out of"]:
        if sep in s:
            # Take left part and strip spaces
            left = s.split(sep)[0].strip()
            if left.isdigit():
                v = max(0, min(10, int(left)))
                return str(v)
    # Fall back: if whole string is a number like "8"
    if s.isdigit():
        v = max(0, min(10, int(s)))
        return str(v)
    # Last resort: try regex to find first integer in string
    import re
    m = re.search(r"\d+", s)
    if m:
        v = max(0, min(10, int(m.group(0))))
        return str(v)
    # Default
    return "0"

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI-Powered Resume Analyzer</h1>
        <p>Upload your resume and get detailed analysis with role-fit assessment</p>
        <p>This Web app is created by <strong>Prajwal B P</strong> </p>
        <p>If you found any issue please feel free to contact to this mail : <strong> prajwal.bp@ltts.com | +91 8431101084 </strong> </p>
        <p><small>✨ Powered by Advanced AI Technology | Comprehensive Career Insights</small></p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize analyzer
    analyzer = ResumeAnalyzer()

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Temperature setting
        temperature = st.slider(
            "AI Analysis Temperature for LLM",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Lower values = more focused, Higher values = more creative"
        )

        st.markdown("---")
        st.markdown("### 📊 Analysis Features")
        st.write("These are the below things that web app is capable of")
        st.markdown("""
        ✅ **Skills Extraction**  
        ✅ **Experience Analysis**  
        ✅ **Role-Fit Assessment**  
        ✅ **Location Detection**  
        ✅ **Improvement Suggestions**  
        ✅ **Comprehensive Scoring**
        """)

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📁 Upload Resume")
        uploaded_file = st.file_uploader(
            "Choose your resume file",
            type=['pdf', 'docx', 'doc'],
            help="Supported formats: PDF, DOCX, DOC"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")

    with col2:
        st.header("🎯 Target Role")
        target_role = st.text_area(
            "Enter the role you're analyzing for:",
            placeholder="e.g., Senior Software Engineer, Data Scientist, Product Manager, etc.",
            height=100,
            help="Provide detailed role description for better analysis"
        )

        if target_role:
            st.markdown(f'<div class="alert-info">🎯 Analyzing for: {target_role}</div>', unsafe_allow_html=True)

    # Analysis section
    if uploaded_file and st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
        # Store analysis timestamp
        st.session_state['analysis_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with st.spinner("🔍 Analyzing resume... This may take a few moments."):
            # Extract text from file
            resume_text = analyzer.extract_text_from_file(uploaded_file)

            if resume_text.strip():
                st.success("✅ Text extracted successfully!")

                # Show extracted text preview
                with st.expander("📄 Preview Extracted Text"):
                    st.text_area("Extracted Content",
                                 resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text, height=200)

                # Analyze resume
                analysis_result = analyzer.analyze_resume(resume_text, target_role, temperature)

                if "error" not in analysis_result:
                    # Show Analysis Complete Alert
                    if "overall_score" in analysis_result:
                        st.balloons()
                        scores = analysis_result["overall_score"]
                        overall_rating = scores.get("overall_rating", "N/A")
                        technical_score = scores.get("technical_score", "N/A")
                        experience_score = scores.get("experience_score", "N/A")

                        # Create alert message
                        alert_message = f"""
                        Analysis Complete!

                        Overall Rating: {overall_rating}  
                        Technical Score: {technical_score}  
                        Experience Score: {experience_score}
                        
                        Your resume has been thoroughly analyzed. 
                        Check the detailed results below!
                        """
                        # st.markdown(f'<div class="alert-success">{alert_message}</div>', unsafe_allow_html=True)
                        st.success(alert_message,icon="🎉")
                    # Display results
                    st.header("📊 Analysis Results")

                    if "candidate_summary" in analysis_result:
                        st.subheader("👤 Candidate Summary")
                        summary = analysis_result["candidate_summary"]

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown('<div class="metric-card"><h3>Name</h3><p>' + str(
                                summary.get("name", "N/A")) + '</p></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown('<div class="metric-card"><h3>Experience</h3><p>' + str(
                                summary.get("total_experience", "N/A")) + '</p></div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown('<div class="metric-card"><h3>Current Role</h3><p>' + str(
                                summary.get("current_role", "N/A")) + '</p></div>', unsafe_allow_html=True)
                        with col4:
                            st.markdown('<div class="metric-card"><h3>Location</h3><p>' + str(
                                summary.get("location", "N/A")) + '</p></div>', unsafe_allow_html=True)

                        # Skills Analysis
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("🛠️ Technical Skills")
                        if "technical_skills" in analysis_result:
                            for skill in analysis_result["technical_skills"]:
                                # st.markdown(f'<span class="skill-match">• {skill}</span>', unsafe_allow_html=True)
                                st.markdown(f"🔬 {skill}")

                    with col2:
                        st.subheader("🤝 Soft Skills")
                        if "soft_skills" in analysis_result:
                            for skill in analysis_result["soft_skills"]:
                                # st.markdown(f'<span class="skill-match">• {skill}</span>', unsafe_allow_html=True)
                                st.markdown(f"🪶 {skill}")

                    # Role Fit Analysis
                    if "role_fit_analysis" in analysis_result and target_role:
                        st.subheader("🎯 Role Fit Analysis")

                        role_fit = analysis_result["role_fit_analysis"]

                        # Fit percentage
                        fit_percentage = role_fit.get("fit_percentage", "0")
                        try:
                            fit_value = int(fit_percentage.replace('%', '')) / 100 if '%' in fit_percentage else int(
                                fit_percentage) / 100
                        except:
                            fit_value = 0.5  # Default value if parsing fails

                        st.progress(fit_value)
                        st.markdown(f"**Overall Fit: {fit_percentage}**")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**✅ Matching Skills:**")
                            for skill in role_fit.get("matching_skills", []):
                                # st.markdown(f'<span class="skill-match">{skill}</span>', unsafe_allow_html=True)
                                st.markdown(f"🔒 {skill}")

                        with col2:
                            st.markdown("**❌ Missing Skills:**")
                            for skill in role_fit.get("missing_skills", []):
                                # st.markdown(f'<span class="skill-gap">{skill}</span>', unsafe_allow_html=True)
                                st.markdown(f"🔓 {skill}")

                        st.markdown("**🎯 Recommendation:**")
                        st.info(role_fit.get("recommendation", "No specific recommendation available"))

                    # Scoring
                    if "overall_score" in analysis_result:
                        st.subheader("📈 Overall Scoring")
                        scores = analysis_result["overall_score"]

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            tech_score = str(scores.get("technical_score", "0")).split('/')[0]
                            st.metric("Technical Score", f"{tech_score}/10")

                        with col2:
                            exp_score = str(scores.get("experience_score", "0")).split('/')[0]
                            st.metric("Experience Score", f"{exp_score}/10")

                        with col3:
                            overall_score = str(scores.get("overall_rating", "0")).split('/')[
                                0]
                            st.metric("Overall Rating", f"{overall_score}/10")

                    # Strengths and Improvements
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("💪 Strengths")
                        if "strengths" in analysis_result:
                            for strength in analysis_result["strengths"]:
                                st.markdown(f"✅ {strength}")

                    with col2:
                        st.subheader("📈 Areas for Improvement")
                        if "improvement_areas" in analysis_result:
                            for area in analysis_result["improvement_areas"]:
                                st.markdown(f"🔄 {area}")

                    # Export option
                    st.markdown("---")
                    st.subheader("📥 Export Analysis Report")

                    # Prepare the text report for download
                    try:
                        # Create readable text format
                        text_report = analyzer.create_text_report(analysis_result, uploaded_file.name, target_role)

                        st.download_button(
                            label="📝 Download Complete Analysis Report",
                            data=text_report.encode('utf-8'),
                            file_name=f"resume_analysis_{uploaded_file.name.split('.')[0]}.txt",
                            mime="text/plain",
                            help="Click to download the comprehensive analysis report as a readable text file",
                            use_container_width=True
                        )

                    except Exception as e:
                        st.error(f"Error preparing download: {str(e)}")
                        st.info("Try refreshing the page and running the analysis again.")

                else:
                    st.error("Failed to analyze resume. Please try again.")
            else:
                st.error("Could not extract text from the uploaded file. Please check the file format and try again.")

                # Footer
    st.markdown("""
                <div class="main-footer">
                <h3>🚀 Ready to Optimize Your Career?</h3>
                <p>Get professional insights and detailed feedback on your resume</p>
                <div style="margin-top: 1rem;">
                <p><strong>Features:</strong> AI-Powered Analysis | Role-Fit Assessment | Skills Gap Analysis 
                | Career Recommendations</p>
                <p><small>© 2024 AI Resume Analyzer | Built with ❤️ using Streamlit & Azure OpenAI by 
                <strong> Prajwal </strong></small></p>
                </div></div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
