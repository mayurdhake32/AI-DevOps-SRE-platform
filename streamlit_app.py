import streamlit as st
import requests
import json
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="OpsPilot - AI DevOps SRE Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 30px rgba(102,126,234,0.3);
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    .fix-box {
        background: #f0f7ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
    }
    .severity-high { color: #e53935; font-weight: bold; }
    .severity-medium { color: #fb8c00; font-weight: bold; }
    .severity-low { color: #43a047; font-weight: bold; }
    .severity-critical { color: #d32f2f; font-weight: bold; background: #ffebee; padding: 2px 8px; border-radius: 4px; }
    .step-success { color: #43a047; }
    .step-failed { color: #e53935; }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102,126,234,0.4);
    }
    .sidebar-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 1rem;
    }
    .doc-result {
        background: #fafafa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    .similarity-badge {
        background: #e3f2fd;
        color: #1976d2;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── API Config ─────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

def api_get(endpoint):
    try:
        return requests.get(f"{API_BASE}{endpoint}", timeout=10)
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")
        return None

def api_post(endpoint, data):
    try:
        return requests.post(f"{API_BASE}{endpoint}", json=data, timeout=30)
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")
        return None

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">OpsPilot - AI DevOps SRE</div>', unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Dashboard", "Knowledge Base", "AI Analysis", "Training", "API Docs"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**Backend Status**")

    health_resp = api_get("/health")
    if health_resp and health_resp.status_code == 200:
        health = health_resp.json()
        st.success("Online")
        st.caption(f"v{health.get('version', '1.0.0')}")
    else:
        st.error("Offline")
        st.caption("Start server: uvicorn src.app:app")

    st.markdown("---")
    st.markdown("Built By Lokesh Chudhary, Mayur Dhake, Harshwardhan Mohite and Pritam Dolse (GID - 17) Under the guidance of Prof. Dr. U. C. Patkar , Department of Computer Engineering, BVCOEL, Pune.")

# ── Dashboard Page ────────────────────────────────────────────────
if page == "Dashboard":
    st.markdown('<div class="main-header">OpsPilot - AI DevOps SRE Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent incident response powered by RAG + Grok-2</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="status-card">
            <div style="font-size: 2rem;">📚</div>
            <div style="font-size: 1.5rem; font-weight: 700;">75+</div>
            <div style="opacity: 0.9;">Knowledge Entries</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="status-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div style="font-size: 2rem;">🎯</div>
            <div style="font-size: 1.5rem; font-weight: 700;">10</div>
            <div style="opacity: 0.9;">Error Categories</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="status-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div style="font-size: 2rem;">🧠</div>
            <div style="font-size: 1.5rem; font-weight: 700;">Grok-2</div>
            <div style="opacity: 0.9;">LLM Engine</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="status-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <div style="font-size: 2rem;">⚡</div>
            <div style="font-size: 1.5rem; font-weight: 700;">&lt; 5s</div>
            <div style="opacity: 0.9;">Avg Response</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("Quick Actions")

    qa_col1, qa_col2, qa_col3 = st.columns(3)

    with qa_col1:
        st.markdown("#### Search KB")
        quick_query = st.text_input("Search docs", placeholder="e.g. CrashLoopBackOff", key="dash_search")
        if st.button("Search", key="btn_dash_search"):
            if quick_query:
                resp = api_get(f"/knowledge-base/search?query={quick_query}&top_k=3")
                if resp and resp.status_code == 200:
                    results = resp.json().get("results", [])
                    for r in results[:2]:
                        st.markdown(f"**{r.get('source', 'Unknown')}** — Score: {r.get('similarity_score', 0):.3f}")
                        st.caption(r.get("content", "")[:120] + "...")

    with qa_col2:
        st.markdown("#### Quick Analyze")
        quick_error = st.text_area("Error log", placeholder="Paste error here...", height=80, key="dash_error")
        if st.button("Analyze", key="btn_dash_analyze"):
            if quick_error:
                with st.spinner("AI is analyzing your logs..."):
                    resp = api_post("/analyze", {
                        "log_content": quick_error,
                        "repo_name": "quick-test"
                    })
                    if resp and resp.status_code == 200:
                        data = resp.json()
                        status = data.get("status", "unknown")
                        if status == "completed":
                            rc = data.get("root_cause", {})

                            # Show full category and confidence
                            cat = rc.get("category", "Unknown")
                            conf = rc.get("confidence", 0)
                            sev = rc.get("severity", "low")

                            st.success(f"Category: {cat.upper()} | Confidence: {conf:.0%} | Severity: {sev.upper()}")

                            # Full description
                            desc = rc.get("description", "No description available.")
                            st.info(desc)

                            # Suggested fixes
                            fixes = rc.get("suggested_fixes", [])
                            if fixes:
                                st.markdown("**Suggested Fixes:**")
                                for fix in fixes:
                                    st.markdown(f'- {fix}')

                            # Prevention
                            prevention = rc.get("prevention", "")
                            if prevention:
                                st.markdown("**Prevention:**")
                                st.success(prevention)

                            # Show workflow steps
                            steps = data.get("steps", [])
                            if steps:
                                with st.expander("View Analysis Steps"):
                                    for step in steps:
                                        icon = "✅" if step.get("status") == "success" else "❌"
                                        st.markdown(f"{icon} **{step.get('step', '').replace('_', ' ').title()}**: {step.get('status', '').title()}")
                        else:
                            st.error("Analysis failed")
                            errors = data.get("errors", [])
                            for err in errors:
                                st.error(err)

    with qa_col3:
        st.markdown("#### System Health")
        if health_resp and health_resp.status_code == 200:
            health = health_resp.json()
            st.markdown(f"**Status:** {health.get('status', 'unknown')}")
            st.markdown(f"**Version:** {health.get('version', '1.0.0')}")
            st.markdown(f"**Last Check:** {health.get('timestamp', 'N/A')[:19]}")
        else:
            st.warning("Backend not connected")

# ── Knowledge Base Page ─────────────────────────────────────────
elif page == "Knowledge Base":
    st.markdown('<div class="main-header">Knowledge Base Search</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Search 75+ DevOps runbooks and troubleshooting guides</div>', unsafe_allow_html=True)

    search_col1, search_col2 = st.columns([3, 1])

    with search_col1:
        query = st.text_input("Search Query", placeholder="e.g. 'pod crash', 'database connection', 'docker daemon'...", key="kb_query")

    with search_col2:
        top_k = st.slider("Results", 1, 10, 5)

    category_filter = st.selectbox(
        "Filter by Category",
        ["All", "kubernetes", "docker", "database", "terraform", "yaml", "monitoring", "security"],
        key="kb_cat"
    )

    if st.button("Search Knowledge Base", use_container_width=True):
        if not query:
            st.warning("Please enter a search query")
        else:
            with st.spinner("Searching vector database..."):
                cat_param = f"&category={category_filter}" if category_filter != "All" else ""
                resp = api_get(f"/knowledge-base/search?query={query}{cat_param}&top_k={top_k}")

                if resp and resp.status_code == 200:
                    results = resp.json().get("results", [])

                    if not results:
                        st.info("No results found. Try a different query.")
                    else:
                        st.success(f"Found {len(results)} relevant documents")

                        for i, r in enumerate(results, 1):
                            score = r.get("similarity_score", 0)

                            with st.container():
                                st.markdown(f"**{i}. {r.get('source', 'Unknown')}** — Relevance: `{score:.3f}`")
                                with st.expander("View Content"):
                                    st.code(r.get("content", ""), language="markdown")
                                st.caption(f"Category: {r.get('category', 'general')}")
                                st.divider()
                else:
                    st.error("Failed to search knowledge base")

# ── AI Analysis Page ────────────────────────────────────────────
elif page == "AI Analysis":
    st.markdown('<div class="main-header">AI Error Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Let AI diagnose your infrastructure failures</div>', unsafe_allow_html=True)

    with st.form("analysis_form"):
        col1, col2 = st.columns(2)

        with col1:
            repo_name = st.text_input("Repository Name", value="my-org/payment-api", 
                                      help="Format: owner/repo-name")

        with col2:
            log_content = st.text_area("Error Logs / Error Message", 
                                       height=150,
                                       placeholder="Paste your error logs here...\n\nExample:\nBack-off restarting failed container\nError: Cannot find module 'express'",
                                       help="Paste CI/CD logs, stack traces, or error messages")

        submitted = st.form_submit_button("Run AI Analysis", use_container_width=True)

    if submitted:
        if not log_content:
            st.warning("Please paste some error logs")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("AI is analyzing your logs..."):
                progress_bar.progress(10)
                status_text.text("Step 1/5: Parsing logs...")

                resp = api_post("/analyze", {
                    "log_content": log_content,
                    "repo_name": repo_name
                })

                progress_bar.progress(100)
                status_text.empty()

                if resp and resp.status_code == 200:
                    data = resp.json()

                    # Workflow Steps
                    st.subheader("Analysis Workflow")
                    steps = data.get("steps", [])

                    if steps:
                        step_cols = st.columns(len(steps))
                        for i, step in enumerate(steps):
                            status_icon = "✅" if step.get("status") == "success" else "❌" if step.get("status") == "failed" else "⏳"
                            with step_cols[i]:
                                st.markdown(f"""
                                <div style="text-align:center; padding:1rem; background:#f8f9fa; border-radius:10px;">
                                    <div style="font-size:1.5rem;">{status_icon}</div>
                                    <div style="font-weight:600; font-size:0.85rem;">
                                        {step.get("step", "").replace("_", " ").title()}
                                    </div>
                                    <div style="font-size:0.75rem; color:{'#43a047' if step.get('status')=='success' else '#e53935'};">
                                        {step.get("status", "").title()}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                    # Root Cause
                    root_cause = data.get("root_cause", {})
                    if root_cause and root_cause.get("category") != "unknown":
                        st.markdown("---")
                        st.subheader("Root Cause Analysis")

                        rc_col1, rc_col2, rc_col3 = st.columns(3)

                        with rc_col1:
                            category = root_cause.get("category", "unknown")
                            st.metric("Category", category.upper())

                        with rc_col2:
                            confidence = root_cause.get("confidence", 0)
                            st.metric("Confidence", f"{confidence:.0%}")

                        with rc_col3:
                            severity = root_cause.get("severity", "low")
                            st.markdown(f"**Severity:** `{severity.upper()}`")

                        st.markdown("#### Description")
                        st.info(root_cause.get("description", "No description available"))

                        # Suggested Fixes
                        fixes = root_cause.get("suggested_fixes", [])
                        if fixes:
                            st.markdown("#### Suggested Fixes")
                            for fix in fixes:
                                st.markdown(f'<div class="fix-box">{fix}</div>', unsafe_allow_html=True)

                        # Prevention
                        prevention = root_cause.get("prevention", "")
                        if prevention:
                            st.markdown("#### Prevention")
                            st.success(prevention)
                    else:
                        st.info("AI could not determine a specific root cause. Try providing more detailed logs.")

                    # Errors
                    errors = data.get("errors", [])
                    if errors:
                        st.markdown("---")
                        st.subheader("Errors")
                        for err in errors:
                            st.error(err)

                    # Raw JSON
                    with st.expander("Raw Response"):
                        st.json(data)

                else:
                    st.error("Analysis failed. Is the backend running?")

# ── Training Page ────────────────────────────────────────────────
elif page == "Training":
    st.markdown('<div class="main-header">Model Training</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Train the error classifier with labeled data</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Upload Training Data", "Manual Entry"])

    with tab1:
        uploaded_file = st.file_uploader("Upload training_data.json", type=["json"])
        if uploaded_file:
            try:
                training_data = json.load(uploaded_file)
                st.success(f"Loaded {len(training_data)} training samples")

                # Show distribution
                from collections import Counter
                all_labels = [label for item in training_data for label in item.get("labels", [])]
                dist = Counter(all_labels)

                st.bar_chart(dict(dist))

                if st.button("Start Training", use_container_width=True):
                    with st.spinner("Training RandomForest model... This may take a minute"):
                        resp = api_post("/train", {
                            "logs": training_data,
                            "deployments": []
                        })
                        if resp and resp.status_code == 200:
                            result = resp.json()
                            st.success("Training completed!")

                            if "error_classifier" in result:
                                ec = result["error_classifier"]
                                st.subheader("Classification Metrics")

                                metrics_data = []
                                for cat, metrics in ec.items():
                                    if isinstance(metrics, dict) and "precision" in metrics:
                                        metrics_data.append({
                                            "Category": cat,
                                            "Precision": metrics.get("precision", 0),
                                            "Recall": metrics.get("recall", 0),
                                            "F1": metrics.get("f1", 0)
                                        })

                                if metrics_data:
                                    import pandas as pd
                                    df = pd.DataFrame(metrics_data)
                                    st.dataframe(df, use_container_width=True)

                                    # F1 Chart
                                    st.bar_chart(df.set_index("Category")["F1"])
                        else:
                            st.error("Training failed")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    with tab2:
        st.markdown("Add individual training samples")
        with st.form("manual_training"):
            train_text = st.text_area("Error Text", height=100)
            train_labels = st.multiselect("Labels", 
                ["docker", "kubernetes", "terraform", "yaml", "network", "permission", "resource", "syntax", "test_failure", "unknown"])
            add_sample = st.form_submit_button("Add Sample")

        if "training_samples" not in st.session_state:
            st.session_state.training_samples = []

        if add_sample and train_text and train_labels:
            st.session_state.training_samples.append({"text": train_text, "labels": train_labels})
            st.success(f"Added! Total samples: {len(st.session_state.training_samples)}")

        if st.session_state.training_samples:
            st.markdown(f"**Samples collected:** {len(st.session_state.training_samples)}")
            if st.button("Train with Collected Samples"):
                with st.spinner("Training..."):
                    resp = api_post("/train", {
                        "logs": st.session_state.training_samples,
                        "deployments": []
                    })
                    if resp and resp.status_code == 200:
                        st.success("Training completed!")
                        st.session_state.training_samples = []

# ── API Docs Page ──────────────────────────────────────────────
elif page == "API Docs":
    st.markdown('<div class="main-header">API Documentation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">REST API endpoints reference</div>', unsafe_allow_html=True)

    endpoints = [
        {
            "method": "GET",
            "path": "/health",
            "desc": "Check system health and status",
            "request": "None",
            "response": '{"status": "healthy", "version": "1.0.0"}'
        },
        {
            "method": "POST",
            "path": "/analyze",
            "desc": "Main AI analysis endpoint. Classifies error, searches KB, generates root cause",
            "request": '{"log_content": "...", "repo_name": "owner/repo"}',
            "response": '{"status": "completed", "root_cause": {...}, "steps": [...]}'
        },
        {
            "method": "POST",
            "path": "/predict",
            "desc": "Pre-deployment failure prediction based on deployment metrics",
            "request": '{"deployment_info": {"lines_added": 500, ...}}',
            "response": '{"failure_probability": 0.23, "risk_level": "low"}'
        },
        {
            "method": "POST",
            "path": "/train",
            "desc": "Train error classifier and failure predictor models",
            "request": '{"logs": [{"text": "...", "labels": ["docker"]}]}',
            "response": '{"error_classifier": {"docker": {"f1": 0.92}}}'
        },
        {
            "method": "GET",
            "path": "/knowledge-base/search",
            "desc": "Search knowledge base with semantic similarity",
            "request": "Query params: ?query=pod+crash&top_k=5",
            "response": '{"results": [{"content": "...", "similarity_score": 0.91}]}'
        },
        {
            "method": "POST",
            "path": "/webhook/github",
            "desc": "GitHub Actions webhook for auto-triggering analysis on failed workflows",
            "request": "GitHub webhook payload",
            "response": '{"status": "processing", "repo": "..."}'
        }
    ]

    for ep in endpoints:
        with st.container():
            badge_color = "#43a047" if ep["method"] == "GET" else "#2196F3"
            st.markdown(f"""
            <div class="result-card">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:0.5rem;">
                    <span style="background:{badge_color}; color:white; padding:2px 10px; border-radius:4px; font-weight:600; font-size:0.85rem;">
                        {ep["method"]}
                    </span>
                    <code style="font-size:1rem; font-weight:600;">{ep["path"]}</code>
                </div>
                <div style="color:#666; margin-bottom:0.5rem;">{ep["desc"]}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("View Details"):
                st.markdown("**Request:**")
                st.code(ep["request"])
                st.markdown("**Response:**")
                st.code(ep["response"])

    st.markdown("---")
    st.info("Full interactive docs available at: http://localhost:8000/docs")