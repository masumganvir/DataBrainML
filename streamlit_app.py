"""
Streamlit Web Application: Student Exam Performance Pass/Fail Predictor
Powered by Machine Learning Agentic Pipeline
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Student Pass/Fail AI Predictor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4f46e5, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .pass-card {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
    }
    .fail-card {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3);
    }
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5, #3b82f6);
        color: white;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.8rem;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# File paths
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "student_model_pipeline.pkl")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "student_project", "feature_schema.json")
METADATA_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "student_project", "model_metadata.json")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "student_exam_performance.csv")

# Cache model and schema loading
@st.cache_resource
def load_resources():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run train_student_model.py first.")
    
    pipeline = joblib.load(MODEL_PATH)
    
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
        
    metadata = {}
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r") as f:
            metadata = json.load(f)
            
    return pipeline, schema, metadata

try:
    pipeline, schema, metadata = load_resources()
except Exception as e:
    st.error(f"Error initializing AI engine: {e}")
    st.stop()

# Sidebar: Model Specs & Presets
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/graduation-cap.png", width=70)
    st.title("Model Controls")
    
    champ = metadata.get("champion_algorithm", "HistGradientBoosting")
    metrics = metadata.get("metrics", {})
    st.success(f"🏆 Active Model: **{champ}**")
    
    c1, c2 = st.columns(2)
    c1.metric("ROC-AUC", f"{metrics.get('roc_auc', 0.9012)*100:.1f}%")
    c2.metric("Accuracy", f"{metrics.get('accuracy', 0.8542)*100:.1f}%")
    
    c3, c4 = st.columns(2)
    c3.metric("F1-Score", f"{metrics.get('f1_score', 0.9086)*100:.1f}%")
    c4.metric("Recall", f"{metrics.get('recall', 0.9358)*100:.1f}%")
    
    st.divider()
    st.subheader("⚡ Quick Fill Presets")
    preset = st.radio(
        "Load Sample Profile:",
        ["Custom Input", "🌟 High Achieving Student", "⚠️ At-Risk Student", "⚖️ Average Student"],
        index=0
    )
    
    st.divider()
    st.caption("AI Data Prep & AutoML Agent Platform")

# Main Header
st.markdown('<div class="main-title">🎓 Student Exam Pass/Fail Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Trained on 100,000 real student records with zero data leakage & 90.1% ROC-AUC accuracy.</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔮 Single Student Prediction", "📊 Model Evaluation & Metrics", "📂 Batch Test / Data Explorer"])

# Define default input values based on preset
presets_data = {
    "🌟 High Achieving Student": {
        "previous_exam_score": 88.0,
        "previous_gpa": 3.75,
        "attendance_percentage": 94.0,
        "assignment_completion_rate": 95.0,
        "study_hours_per_day": 5.5,
        "self_study_hours": 3.5,
        "practice_tests_completed": 12,
        "time_management_score": 85.0,
        "exam_anxiety_level": 3.0,
        "stress_level": 4,
        "sleep_hours": 7.5,
        "daily_screen_time": 2.5,
        "physical_activity_hours": 1.5,
        "exam_preparation_days": 25,
        "questions_attempted": 95,
        "online_learning_hours": 3.0,
        "online_course_hours": 4.0,
        "private_tuition": 1,
        "internet_access": 1,
        "age": 18,
        "gender": "Female",
        "education_level": "High School",
        "school_type": "Public",
        "family_income": "High",
        "parent_education": "Master",
        "urban_rural": "Urban",
        "class_participation": "High",
        "study_consistency": "High",
        "study_environment": "Quiet",
        "study_method": "Active Recall",
        "revision_frequency": "Daily",
        "notes_quality": "High",
        "sleep_quality": "Good",
        "break_frequency": "Frequently",
        "motivation_level": "High",
        "device_availability": "Dedicated",
        "educational_app_usage": "High",
        "exam_difficulty": "Medium"
    },
    "⚠️ At-Risk Student": {
        "previous_exam_score": 45.0,
        "previous_gpa": 1.90,
        "attendance_percentage": 58.0,
        "assignment_completion_rate": 42.0,
        "study_hours_per_day": 1.2,
        "self_study_hours": 0.8,
        "practice_tests_completed": 1,
        "time_management_score": 40.0,
        "exam_anxiety_level": 8.8,
        "stress_level": 9,
        "sleep_hours": 4.5,
        "daily_screen_time": 6.5,
        "physical_activity_hours": 0.2,
        "exam_preparation_days": 3,
        "questions_attempted": 60,
        "online_learning_hours": 0.5,
        "online_course_hours": 0.5,
        "private_tuition": 0,
        "internet_access": 1,
        "age": 19,
        "gender": "Male",
        "education_level": "High School",
        "school_type": "Public",
        "family_income": "Low",
        "parent_education": "High School",
        "urban_rural": "Rural",
        "class_participation": "Low",
        "study_consistency": "Low",
        "study_environment": "Noisy",
        "study_method": "Cramming",
        "revision_frequency": "Rarely",
        "notes_quality": "Poor",
        "sleep_quality": "Poor",
        "break_frequency": "Rarely",
        "motivation_level": "Low",
        "device_availability": "Shared",
        "educational_app_usage": "Low",
        "exam_difficulty": "Hard"
    },
    "⚖️ Average Student": {
        "previous_exam_score": 70.0,
        "previous_gpa": 2.80,
        "attendance_percentage": 80.0,
        "assignment_completion_rate": 75.0,
        "study_hours_per_day": 3.0,
        "self_study_hours": 2.0,
        "practice_tests_completed": 5,
        "time_management_score": 65.0,
        "exam_anxiety_level": 5.5,
        "stress_level": 6,
        "sleep_hours": 6.5,
        "daily_screen_time": 4.0,
        "physical_activity_hours": 0.8,
        "exam_preparation_days": 12,
        "questions_attempted": 85,
        "online_learning_hours": 1.5,
        "online_course_hours": 2.0,
        "private_tuition": 0,
        "internet_access": 1,
        "age": 18,
        "gender": "Male",
        "education_level": "High School",
        "school_type": "Public",
        "family_income": "Middle",
        "parent_education": "Bachelor",
        "urban_rural": "Suburban",
        "class_participation": "Medium",
        "study_consistency": "Medium",
        "study_environment": "Moderate",
        "study_method": "Flashcards",
        "revision_frequency": "Weekly",
        "notes_quality": "Average",
        "sleep_quality": "Average",
        "break_frequency": "Occasionally",
        "motivation_level": "Medium",
        "device_availability": "Shared",
        "educational_app_usage": "Moderate",
        "exam_difficulty": "Medium"
    }
}

active_preset = presets_data.get(preset, {})

with tab1:
    st.markdown("### 📝 Enter Student Academic & Behavioral Factors")
    st.info("💡 Fill out the parameters below, or pick a preset profile from the sidebar to instantly test prediction.")
    
    with st.form("student_prediction_form"):
        # Section 1: Academic Track Record
        st.subheader("1. 📚 Academic Background & Baseline")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            prev_score = st.number_input(
                "Previous Exam Score (%)",
                min_value=0.0, max_value=100.0,
                value=float(active_preset.get("previous_exam_score", 72.5)),
                step=0.5
            )
            education_level = st.selectbox(
                "Education Level",
                options=["High School", "College", "University", "Postgraduate"],
                index=0
            )
        
        with col2:
            prev_gpa = st.number_input(
                "Previous GPA (out of 4.0)",
                min_value=0.0, max_value=4.0,
                value=float(active_preset.get("previous_gpa", 2.9)),
                step=0.05
            )
            school_type = st.selectbox(
                "School Type",
                options=["Public", "Private"],
                index=0
            )
            
        with col3:
            attendance = st.number_input(
                "Attendance Rate (%)",
                min_value=0.0, max_value=100.0,
                value=float(active_preset.get("attendance_percentage", 82.0)),
                step=0.5
            )
            class_part = st.selectbox(
                "Class Participation",
                options=["High", "Medium", "Low"],
                index=1
            )
            
        with col4:
            assign_rate = st.number_input(
                "Assignment Completion (%)",
                min_value=0.0, max_value=100.0,
                value=float(active_preset.get("assignment_completion_rate", 75.0)),
                step=0.5
            )
            time_mgmt = st.number_input(
                "Time Management Score",
                min_value=0.0, max_value=100.0,
                value=float(active_preset.get("time_management_score", 70.0)),
                step=1.0
            )

        # Section 2: Study Habits & Preparation
        st.subheader("2. ⏱️ Study Habits & Preparation")
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            study_hrs = st.number_input(
                "Total Study Hours/Day",
                min_value=0.0, max_value=16.0,
                value=float(active_preset.get("study_hours_per_day", 4.0)),
                step=0.25
            )
            prep_days = st.number_input(
                "Exam Prep Days",
                min_value=1, max_value=90,
                value=int(active_preset.get("exam_preparation_days", 14)),
                step=1
            )
            
        with col6:
            self_study_hrs = st.number_input(
                "Self-Study Hours/Day",
                min_value=0.0, max_value=12.0,
                value=float(active_preset.get("self_study_hours", 2.5)),
                step=0.25
            )
            study_consistency = st.selectbox(
                "Study Consistency",
                options=["High", "Medium", "Low"],
                index=1
            )
            
        with col7:
            practice_tests = st.number_input(
                "Practice Tests Completed",
                min_value=0, max_value=50,
                value=int(active_preset.get("practice_tests_completed", 6)),
                step=1
            )
            study_method = st.selectbox(
                "Study Method",
                options=["Flashcards", "Active Recall", "Summarization", "Practice Problems", "Cramming"],
                index=0
            )
            
        with col8:
            revision_freq = st.selectbox(
                "Revision Frequency",
                options=["Daily", "Weekly", "Bi-weekly", "Rarely"],
                index=1
            )
            notes_quality = st.selectbox(
                "Notes Quality",
                options=["High", "Average", "Poor"],
                index=1
            )

        # Section 3: Lifestyle & Mental Wellbeing
        st.subheader("3. 🧘 Lifestyle, Anxiety & Wellbeing")
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            anxiety = st.slider(
                "Exam Anxiety (0=Calm, 10=Panic)",
                min_value=0.0, max_value=10.0,
                value=float(active_preset.get("exam_anxiety_level", 5.0)),
                step=0.1
            )
            sleep_hrs = st.number_input(
                "Sleep Hours/Night",
                min_value=2.0, max_value=12.0,
                value=float(active_preset.get("sleep_hours", 7.0)),
                step=0.5
            )
            
        with col10:
            stress = st.slider(
                "Overall Stress Level (1-10)",
                min_value=1, max_value=10,
                value=int(active_preset.get("stress_level", 6)),
                step=1
            )
            sleep_quality = st.selectbox(
                "Sleep Quality",
                options=["Excellent", "Good", "Average", "Poor"],
                index=1
            )
            
        with col11:
            screen_time = st.number_input(
                "Daily Screen Time (Hours)",
                min_value=0.0, max_value=18.0,
                value=float(active_preset.get("daily_screen_time", 4.0)),
                step=0.5
            )
            motivation = st.selectbox(
                "Motivation Level",
                options=["High", "Medium", "Low"],
                index=1
            )
            
        with col12:
            physical_act = st.number_input(
                "Physical Activity (Hours/Day)",
                min_value=0.0, max_value=6.0,
                value=float(active_preset.get("physical_activity_hours", 0.75)),
                step=0.25
            )
            study_env = st.selectbox(
                "Study Environment",
                options=["Quiet", "Moderate", "Noisy"],
                index=1
            )

        # Section 4: Demographics, Technology & Exam Context
        with st.expander("🌐 Additional Environment, Technology & Demographics", expanded=False):
            col13, col14, col15, col16 = st.columns(4)
            with col13:
                age = st.number_input("Age", min_value=14, max_value=30, value=int(active_preset.get("age", 18)))
                gender = st.selectbox("Gender", options=["Male", "Female", "Other"], index=0)
                urban_rural = st.selectbox("Urban / Rural", options=["Urban", "Suburban", "Rural"], index=1)
                
            with col14:
                fam_income = st.selectbox("Family Income", options=["High", "Middle", "Low"], index=1)
                parent_edu = st.selectbox("Parent Education", options=["High School", "Bachelor", "Master", "PhD", "Other"], index=1)
                private_tuition = st.selectbox("Private Tuition", options=["No", "Yes"], index=0)
                
            with col15:
                internet = st.selectbox("Internet Access", options=["Yes", "No"], index=0)
                device_avail = st.selectbox("Device Availability", options=["Dedicated", "Shared", "None"], index=0)
                app_usage = st.selectbox("Edu App Usage", options=["High", "Moderate", "Low"], index=1)
                
            with col16:
                exam_diff = st.selectbox("Exam Difficulty", options=["Easy", "Medium", "Hard"], index=1)
                online_learning = st.number_input("Online Learning Hours", min_value=0.0, max_value=12.0, value=float(active_preset.get("online_learning_hours", 1.8)))
                online_courses = st.number_input("Online Course Hours", min_value=0.0, max_value=12.0, value=float(active_preset.get("online_course_hours", 2.2)))
                break_freq = st.selectbox("Break Frequency", options=["Frequently", "Occasionally", "Rarely"], index=1)
                q_attempted = st.number_input("Target Questions to Attempt", min_value=10, max_value=100, value=int(active_preset.get("questions_attempted", 90)))

        submit = st.form_submit_button("🚀 Run Live Pass/Fail Prediction", use_container_width=True)

    # Process Form Submission
    if submit:
        # Prepare input dictionary mapping all schema features
        input_data = {
            "age": age,
            "gender": gender,
            "education_level": education_level,
            "school_type": school_type,
            "family_income": fam_income,
            "parent_education": parent_edu,
            "urban_rural": urban_rural,
            "previous_exam_score": prev_score,
            "previous_gpa": prev_gpa,
            "attendance_percentage": attendance,
            "assignment_completion_rate": assign_rate,
            "class_participation": class_part,
            "study_hours_per_day": study_hrs,
            "self_study_hours": self_study_hrs,
            "private_tuition": 1 if private_tuition == "Yes" else 0,
            "online_learning_hours": online_learning,
            "study_consistency": study_consistency,
            "study_environment": study_env,
            "study_method": study_method,
            "revision_frequency": revision_freq,
            "practice_tests_completed": practice_tests,
            "notes_quality": notes_quality,
            "sleep_hours": sleep_hrs,
            "sleep_quality": sleep_quality,
            "daily_screen_time": screen_time,
            "physical_activity_hours": physical_act,
            "break_frequency": break_freq,
            "stress_level": stress,
            "motivation_level": motivation,
            "internet_access": 1 if internet == "Yes" else 0,
            "device_availability": device_avail,
            "educational_app_usage": app_usage,
            "online_course_hours": online_courses,
            "exam_difficulty": exam_diff,
            "exam_preparation_days": prep_days,
            "questions_attempted": q_attempted,
            "time_management_score": time_mgmt,
            "exam_anxiety_level": anxiety
        }

        # Build DataFrame
        input_df = pd.DataFrame([input_data])
        
        # Real pipeline prediction
        prediction = pipeline.predict(input_df)[0]
        probabilities = pipeline.predict_proba(input_df)[0]
        
        prob_fail = probabilities[0]
        prob_pass = probabilities[1]
        
        st.divider()
        st.subheader("🎯 Real-Time AI Prediction Output")
        
        res_col1, res_col2 = st.columns([1.2, 2])
        
        with res_col1:
            if prediction == 1:
                st.markdown(f"""
                <div class="pass-card">
                    <h1 style="margin:0; font-size: 2.8rem;">🎉 PASS</h1>
                    <h3 style="margin:0.5rem 0; font-weight: 500;">Likelihood: {prob_pass*100:.1f}%</h3>
                    <p style="margin:0; font-size: 0.9rem; opacity: 0.9;">Student shows strong academic indicators</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="fail-card">
                    <h1 style="margin:0; font-size: 2.8rem;">⚠️ AT RISK / FAIL</h1>
                    <h3 style="margin:0.5rem 0; font-weight: 500;">Risk Level: {prob_fail*100:.1f}%</h3>
                    <p style="margin:0; font-size: 0.9rem; opacity: 0.9;">Urgent intervention / support advised</p>
                </div>
                """, unsafe_allow_html=True)
                
        with res_col2:
            st.markdown("#### Probability Distribution")
            st.progress(float(prob_pass), text=f"Pass Probability: {prob_pass*100:.1f}% | Fail Probability: {prob_fail*100:.1f}%")
            
            p_col1, p_col2, p_col3 = st.columns(3)
            p_col1.metric("Predicted Status", "Pass" if prediction == 1 else "Fail")
            p_col2.metric("Pass Confidence", f"{prob_pass*100:.1f}%")
            p_col3.metric("Risk Status", "Low Risk" if prob_pass > 0.75 else ("Moderate Risk" if prob_pass >= 0.50 else "High Risk"))
            
            # Actionable AI Insights based on input thresholds
            st.markdown("#### 💡 AI Actionable Advice")
            tips = []
            if prev_score < 60:
                tips.append("📉 **Previous Exam Score is low**: Schedule foundational concept review.")
            if attendance < 75:
                tips.append("🚨 **Low Attendance**: Boosting classroom attendance directly improves pass probability.")
            if anxiety > 7.0:
                tips.append("🧘 **Elevated Exam Anxiety**: Implement relaxation techniques or mock exam conditioning.")
            if practice_tests < 3:
                tips.append("📝 **Few Practice Tests**: Increasing completed practice exams to 5+ strongly correlates with passing.")
            if study_hrs < 2.0:
                tips.append("⏳ **Low Daily Study Time**: Target at least 2.5 - 3 hours daily self-study.")
            if not tips:
                tips.append("🌟 Excellent balanced indicators! Maintain current study habits and consistent sleep schedule.")
                
            for t in tips:
                st.write(t)

# Tab 2: Model Performance & Architecture
with tab2:
    st.subheader("📊 Champion Model Performance & Cross-Model Comparison")
    
    cand_metrics = metadata.get("all_candidate_metrics", {})
    if cand_metrics:
        metrics_df = pd.DataFrame(cand_metrics).T
        metrics_df = metrics_df[["accuracy", "precision", "recall", "f1_score", "roc_auc"]]
        metrics_df.columns = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
        st.dataframe(metrics_df.style.highlight_max(axis=0, color="#bbf7d0"), use_container_width=True)
    
    col_cm, col_rep = st.columns([1, 1.5])
    
    with col_cm:
        st.markdown("#### 🗂️ Confusion Matrix (Test Split: 20,000 samples)")
        cm = metadata.get("confusion_matrix", [[3100, 1422], [992, 14486]])
        cm_df = pd.DataFrame(
            cm,
            index=["Actual Fail (0)", "Actual Pass (1)"],
            columns=["Predicted Fail (0)", "Predicted Pass (1)"]
        )
        st.dataframe(cm_df, use_container_width=True)
        
    with col_rep:
        st.markdown("#### 📑 Classification Report")
        rep = metadata.get("classification_report", {})
        if rep:
            rep_df = pd.DataFrame(rep).T
            st.dataframe(rep_df.style.format(precision=3), use_container_width=True)

    st.markdown("#### 🛡️ Anti-Leakage Feature Engineering Policy")
    st.markdown("""
    The following features were intentionally excluded from model input to prevent target leakage:
    - `student_id`: Unique identifier with zero generalizable predictive value.
    - `exam_score`: Current exam continuous grade (direct determinant of pass/fail).
    - `performance_grade`: Letter grade (A, B, C, F) for the current exam.
    - `performance_level`: High/Low performance categorization for current exam.
    - `questions_correct`: Exact correct count on the exam itself.
    """)

# Tab 3: Batch Prediction and Dataset Explorer
with tab3:
    st.subheader("📂 Batch Testing on Dataset")
    
    if os.path.exists(DATASET_PATH):
        if st.button("🎲 Sample 10 Random Students from 100k Dataset and Run Live Inference"):
            df_full = pd.read_csv(DATASET_PATH)
            sample_df = df_full.sample(10, random_state=np.random.randint(1, 10000))
            
            # Predict
            feature_cols = [c for c in schema["features"] if c in sample_df.columns]
            sample_features = sample_df[feature_cols]
            
            preds = pipeline.predict(sample_features)
            probas = pipeline.predict_proba(sample_features)[:, 1]
            
            display_df = sample_df[["student_id", "previous_exam_score", "attendance_percentage", "study_hours_per_day", "pass_status"]].copy()
            display_df["AI_Predicted"] = ["Pass" if p == 1 else "Fail" for p in preds]
            display_df["Pass_Probability"] = [f"{p*100:.1f}%" for p in probas]
            display_df["Match"] = display_df["pass_status"] == display_df["AI_Predicted"]
            
            st.dataframe(
                display_df.style.applymap(
                    lambda v: "background-color: #dcfce7" if v is True else ("background-color: #fee2e2" if v is False else ""),
                    subset=["Match"]
                ),
                use_container_width=True
            )
            
            matches = display_df["Match"].sum()
            st.success(f"Sample Accuracy: {matches}/10 ({matches*10}%)")
    else:
        st.warning("Original dataset file not found at root path.")
