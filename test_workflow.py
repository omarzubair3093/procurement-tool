import streamlit as st
from config import get_db, format_date


def show_test_workflow():
    """Simple test workflow to verify system functionality"""
    st.markdown('<h1 class="main-header">🧪 Test Workflow</h1>', unsafe_allow_html=True)

    st.info("This is a simplified test interface to verify core functionality")

    db = get_db()
    user_id = st.session_state.user.id
    user_profile = st.session_state.user_profile

    # Show user info
    st.markdown("### 👤 Current User")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Name:** {user_profile['full_name']}")
    with col2:
        st.write(f"**Role:** {user_profile['role']}")
    with col3:
        st.write(f"**Email:** {user_profile['email']}")

    st.markdown("---")

    # Test database connections
    st.markdown("### 🔌 Database Connection Tests")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Test RFPs Query"):
            try:
                rfps = db.get_rfps_for_user(user_id)
                st.success(f"✅ Found {len(rfps)} RFPs")
                if rfps:
                    for rfp in rfps[:3]:
                        st.write(f"- {rfp['title']} ({rfp['status']})")
            except Exception as e:
                st.error(f"❌ RFPs Query Failed: {str(e)}")

    with col2:
        if st.button("Test Users Query"):
            try:
                users = db.get_all_users()
                st.success(f"✅ Found {len(users)} users")
                for user in users[:3]:
                    st.write(f"- {user['full_name']} ({user['role']})")
            except Exception as e:
                st.error(f"❌ Users Query Failed: {str(e)}")

    if st.button("Test Vendors Query"):
        try:
            vendors = db.get_all_vendors()
            st.success(f"✅ Found {len(vendors)} vendors")
            for vendor in vendors[:3]:
                st.write(f"- {vendor['name']}")
        except Exception as e:
            st.error(f"❌ Vendors Query Failed: {str(e)}")

    if st.button("Test Evaluations Query"):
        try:
            evaluations = db.get_pending_evaluations_for_user(user_id)
            st.success(f"✅ Found {len(evaluations)} pending evaluations")
        except Exception as e:
            st.error(f"❌ Evaluations Query Failed: {str(e)}")

    st.markdown("---")

    # Simple form test
    st.markdown("### 📝 Simple Form Test")

    with st.form("test_form"):
        test_input = st.text_input("Test Input")
        test_select = st.selectbox("Test Select", ["Option 1", "Option 2", "Option 3"])
        test_number = st.number_input("Test Number", min_value=0, max_value=100, value=50)

        if st.form_submit_button("Test Submit"):
            st.success(f"✅ Form submitted successfully!")
            st.write(f"Input: {test_input}")
            st.write(f"Select: {test_select}")
            st.write(f"Number: {test_number}")

    st.markdown("---")

    # Navigation test
    st.markdown("### 🧭 Navigation Test")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📋 Go to RFPs"):
            st.session_state.page = 'my_rfps'
            st.rerun()

    with col2:
        if st.button("🏢 Go to Vendors"):
            st.session_state.page = 'vendors'
            st.rerun()

    with col3:
        if st.button("📊 Go to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()

    with col4:
        if st.button("📥 Go to Proposals"):
            st.session_state.page = 'proposals'
            st.rerun()

    st.markdown("---")

    # System info
    st.markdown("### ℹ️ System Information")

    st.write(f"**Streamlit Version:** {st.__version__}")

    # Session state info
    st.markdown("### 🔧 Session State")

    with st.expander("View Session State"):
        for key, value in st.session_state.items():
            if key in ['user', 'user_profile', 'page', 'rfp_id', 'proposal_id']:
                if key == 'user' and value:
                    st.write(f"**{key}:** User ID: {value.id}")
                elif isinstance(value, dict):
                    st.write(f"**{key}:** {value}")
                else:
                    st.write(f"**{key}:** {value}")