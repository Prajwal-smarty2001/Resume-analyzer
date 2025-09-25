import streamlit as st
import PyPDF2
import docx
import io
import re
from openai import AzureOpenAI
import json
from typing import Dict, List, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }

    .analysis-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }

    .skill-match {
        background: #e8f5e8;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem;
        display: inline-block;
        border: 1px solid #4caf50;
    }

    .skill-gap {
        background: #ffe8e8;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem;
        display: inline-block;
        border: 1px solid #f44336;
    }

    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


class ResumeAnalyzer:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key='6CwE55InRG2OQa59XCrGSjqMX1RmvXDqrNoD4w2MiGWl7nUxUgxYJQQJ99BIAC77bzfXJ3w3AAAAACOGEovm',
            api_version='2025-01-01-preview',
            azure_endpoint='https://ltts-cariad-ddd-mvp-ai-foundry.cognitiveservices.azure.com/openai/deployments'
                           '/gpt-4.1-mini/chat/completions?api-version=2025-01-01-preview'
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
            prompt = f"""
            As a senior HR analyst and recruitment expert, analyze the following resume comprehensively:

            RESUME TEXT:
            {resume_text}

            TARGET ROLE: {target_role if target_role else "General Analysis"}

            Please provide a detailed analysis in JSON format with the following structure:
            {{
                "candidate_summary": {{
                    "name": "extracted name",
                    "email": "extracted email",
                    "phone": "extracted phone",
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
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system",
                     "content": "You are a senior HR analyst and recruitment expert with 15+ years of experience in talent acquisition, resume screening, and candidate evaluation. You specialize in comprehensive resume analysis and role-fit assessment."},
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


def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI-Powered Resume Analyzer</h1>
        <p>Upload your resume and get detailed analysis with role-fit assessment</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize analyzer
    analyzer = ResumeAnalyzer()

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Temperature setting
        temperature = st.slider(
            "AI Analysis Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Lower values = more focused, Higher values = more creative"
        )

        st.markdown("---")
        st.markdown("### 📊 Analysis Features")
        st.markdown("""
        ✅ **Skills Extraction**  
        ✅ **Experience Analysis**  
        ✅ **Role-Fit Assessment**  
        ✅ **Improvement Suggestions**  
        ✅ **Comprehensive Scoring**
        """)

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📁 Upload Resume")
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose your resume file",
            type=['pdf', 'docx', 'doc'],
            help="Supported formats: PDF, DOCX, DOC"
        )

        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")

            # File details
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB",
                "File type": uploaded_file.type
            }
            st.json(file_details)

    with col2:
        st.header("🎯 Target Role")
        target_role = st.text_area(
            "Enter the role you're analyzing for:",
            placeholder="e.g., Senior Software Engineer, Data Scientist, Product Manager, etc.",
            height=100,
            help="Provide detailed role description for better analysis"
        )

        if target_role:
            st.info(f"🎯 Analyzing for: {target_role}")

    # Analysis section
    if uploaded_file and st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
        # Store analysis timestamp
        import datetime
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
                    # Display results
                    st.header("📊 Analysis Results")

                    # Candidate Summary
                    if "candidate_summary" in analysis_result:
                        st.subheader("👤 Candidate Summary")
                        summary = analysis_result["candidate_summary"]

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown('<div class="metric-card"><h3>Name</h3><p>' + str(
                                summary.get("name", "N/A")) + '</p></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown('<div class="metric-card"><h3>Experience</h3><p>' + str(
                                summary.get("total_experience", "N/A")) + '</p></div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown('<div class="metric-card"><h3>Current Role</h3><p>' + str(
                                summary.get("current_role", "N/A")) + '</p></div>', unsafe_allow_html=True)

                    # Skills Analysis
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("🛠️ Technical Skills")
                        if "technical_skills" in analysis_result:
                            for skill in analysis_result["technical_skills"]:
                                st.markdown(f'<span class="skill-match">• {skill}</span>', unsafe_allow_html=True)

                    with col2:
                        st.subheader("🤝 Soft Skills")
                        if "soft_skills" in analysis_result:
                            for skill in analysis_result["soft_skills"]:
                                st.markdown(f'<span class="skill-match">• {skill}</span>', unsafe_allow_html=True)

                    # Role Fit Analysis
                    if "role_fit_analysis" in analysis_result and target_role:
                        st.subheader("🎯 Role Fit Analysis")

                        role_fit = analysis_result["role_fit_analysis"]

                        # Fit percentage
                        fit_percentage = role_fit.get("fit_percentage", "0")
                        st.progress(int(fit_percentage.replace('%', '')) / 100 if '%' in fit_percentage else int(
                            fit_percentage) / 100)
                        st.markdown(f"**Overall Fit: {fit_percentage}**")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**✅ Matching Skills:**")
                            for skill in role_fit.get("matching_skills", []):
                                st.markdown(f'<span class="skill-match">{skill}</span>', unsafe_allow_html=True)

                        with col2:
                            st.markdown("**❌ Missing Skills:**")
                            for skill in role_fit.get("missing_skills", []):
                                st.markdown(f'<span class="skill-gap">{skill}</span>', unsafe_allow_html=True)

                        st.markdown("**🎯 Recommendation:**")
                        st.info(role_fit.get("recommendation", "No specific recommendation available"))

                    # Scoring
                    if "overall_score" in analysis_result:
                        st.subheader("📈 Overall Scoring")
                        scores = analysis_result["overall_score"]

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            tech_score = scores.get("technical_score", "0").split('/')[0]
                            st.metric("Technical Score", f"{tech_score}/10")
                        with col2:
                            exp_score = scores.get("experience_score", "0").split('/')[0]
                            st.metric("Experience Score", f"{exp_score}/10")
                        with col3:
                            overall_score = scores.get("overall_rating", "0").split('/')[0]
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

                    # Prepare the analysis data for download
                    try:
                        # Create a comprehensive report
                        report_data = {
                            "resume_analysis_report": {
                                "file_name": uploaded_file.name,
                                "analysis_date": st.session_state.get('analysis_date', 'Not available'),
                                "target_role": target_role if target_role else "General Analysis",
                                **analysis_result
                            }
                        }

                        # Convert to JSON string with proper formatting
                        json_str = json.dumps(report_data, indent=4, ensure_ascii=False)

                        # Create download button
                        st.download_button(
                            label="📄 Download JSON Report",
                            data=json_str.encode('utf-8'),
                            file_name=f"resume_analysis_{uploaded_file.name.split('.')[0]}.json",
                            mime="application/json",
                            help="Click to download the complete analysis report as JSON file"
                        )

                        # Also provide a text format option
                        # Create readable text format
                        text_report = analyzer.create_text_report(analysis_result, uploaded_file.name, target_role)

                        st.download_button(
                            label="📝 Download Text Report",
                            data=text_report.encode('utf-8'),
                            file_name=f"resume_analysis_{uploaded_file.name.split('.')[0]}.txt",
                            mime="text/plain",
                            help="Click to download the analysis report as readable text file"
                        )

                    except Exception as e:
                        st.error(f"Error preparing download: {str(e)}")
                        st.info("Try refreshing the page and running the analysis again.")

                else:
                    st.error("Failed to analyze resume. Please try again.")
            else:
                st.error("Could not extract text from the uploaded file. Please check the file format and try again.")


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🤖 Powered by Azure OpenAI | Built with Streamlit</p>
    <p><em>Upload your resume and discover your strengths and improvement areas!</em></p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()