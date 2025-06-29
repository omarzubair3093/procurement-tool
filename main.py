# Configure Streamlit page FIRST - before any other imports
import streamlit as st

st.set_page_config(
    page_title="Procurement Management System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other modules
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
from config import *
from rfp_pages import show_create_rfp_page, show_edit_rfp_page, show_view_rfp_page
from vendor_pages import show_vendors_page
from proposal_pages import show_proposals_page, show_proposal_evaluations
from evaluation_pages import show_evaluations_page, show_evaluate_proposal_page, show_pending_tasks_page
from analytics_pages import show_reports_page
from simple_evaluation import show_simple_evaluate_proposal_page

# Initialize session state
init_session_state()

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1e3a8a;
    text-align: center;
    margin-bottom: 2rem;
}
.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: bold;
    font-size: 0.875rem;
    color: white;
}
.rfp-card {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
    background-color: white;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}
.notification-badge {
    background-color: #ef4444;
    color: white;
    border-radius: 50%;
    padding: 2px 6px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# Authentication Functions
def show_login_page():
    """Display login page"""
    st.markdown('<h1 class="main-header">🏢 Procurement Management System</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Welcome Back")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("Login", use_container_width=True)

            if login_button:
                if email and password:
                    success, message = login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both email and password")

        st.markdown("---")

        # Registration form
        with st.expander("Don't have an account? Register here"):
            with st.form("register_form"):
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                reg_full_name = st.text_input("Full Name", key="reg_full_name")
                reg_role = st.selectbox("Role", USER_ROLES, key="reg_role")
                register_button = st.form_submit_button("Register")

                if register_button:
                    if reg_email and reg_password and reg_full_name:
                        success, message = register_user(reg_email, reg_password, reg_full_name, reg_role)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.error("Please fill in all fields")


def show_navigation():
    """Display navigation menu"""
    if not st.session_state.user_profile:
        return None

    role = st.session_state.user_profile['role']

    # Get unread notifications count
    db = get_db()
    notifications = db.get_user_notifications(st.session_state.user.id, unread_only=True)
    unread_count = len(notifications)

    # Define menu options based on user role - REMOVED TEST FROM ALL ROLES
    if role == 'procurement_manager':
        menu_options = [
            "Dashboard", "My RFPs", "Create RFP", "Vendors",
            "Proposals", "Evaluations", "Reports"
        ]
        menu_icons = [
            "speedometer2", "file-earmark-text", "plus-circle",
            "building", "inbox", "clipboard-check", "graph-up"
        ]
    elif role == 'dept_head':
        menu_options = ["Dashboard", "Approvals", "My Evaluations", "Reports"]
        menu_icons = ["speedometer2", "check-circle", "clipboard-check", "graph-up"]
    elif role == 'it_admin':
        menu_options = ["Dashboard", "IT Evaluations", "Security Reviews", "Reports"]
        menu_icons = ["speedometer2", "shield-check", "lock", "graph-up"]
    else:  # evaluator
        menu_options = ["Dashboard", "My Evaluations", "Pending Tasks"]
        menu_icons = ["speedometer2", "clipboard-check", "clock"]

    # Add notifications to menu
    if unread_count > 0:
        notifications_label = f"Notifications ({unread_count})"
    else:
        notifications_label = "Notifications"

    menu_options.append(notifications_label)
    menu_icons.append("bell")

    # Display user info, navigation menu, and logout in sidebar
    with st.sidebar:
        # Navigation menu
        selected = option_menu(
            menu_title="Navigation",
            options=menu_options,
            icons=menu_icons,
            menu_icon="list",
            default_index=0,
        )

        st.markdown("---")
        st.markdown(f"**Welcome, {st.session_state.user_profile['full_name']}**")
        st.markdown(f"*{st.session_state.user_profile['role'].replace('_', ' ').title()}*")
        if st.button("Logout", key="logout_btn"):
            logout_user()
            st.rerun()
        st.markdown("---")

    return selected


# Dashboard Functions
def show_dashboard():
    """Display role-based dashboard"""
    role = st.session_state.user_profile['role']
    user_id = st.session_state.user.id

    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)

    if role == 'procurement_manager':
        show_procurement_manager_dashboard(user_id)
    elif role == 'dept_head':
        show_dept_head_dashboard(user_id)
    elif role == 'it_admin':
        show_it_admin_dashboard(user_id)
    else:
        show_evaluator_dashboard(user_id)


def show_procurement_manager_dashboard(user_id):
    """Dashboard for procurement managers"""
    # Debug information
    st.write(f"Debug - User ID: {user_id}")

    # Get user's RFPs
    db = get_db()
    try:
        rfps = db.get_rfps_for_user(user_id)
        st.write(f"Debug - Found {len(rfps)} RFPs")
    except Exception as e:
        st.error(f"Error loading RFPs: {str(e)}")
        rfps = []

    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_rfps = len(rfps)
        st.metric("Total RFPs", total_rfps)
    with col2:
        active_rfps = len([rfp for rfp in rfps if rfp['status'] in ['published', 'evaluation']])
        st.metric("Active RFPs", active_rfps)
    with col3:
        draft_rfps = len([rfp for rfp in rfps if rfp['status'] == 'draft'])
        st.metric("Draft RFPs", draft_rfps)
    with col4:
        completed_rfps = len([rfp for rfp in rfps if rfp['status'] == 'completed'])
        st.metric("Completed RFPs", completed_rfps)

    # Recent RFPs
    st.markdown("### Recent RFPs")
    if rfps:
        for rfp in rfps[:5]:  # Show last 5 RFPs
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{rfp['title']}**")
                    st.caption(f"Created: {format_date(rfp['created_at'])}")
                with col2:
                    status_color = get_status_color(rfp['status'])
                    st.markdown(
                        f'<span class="status-badge" style="background-color: {status_color};">{rfp["status"].replace("_", " ").title()}</span>',
                        unsafe_allow_html=True
                    )
                with col3:
                    if st.button("View", key=f"view_rfp_{rfp['id']}"):
                        st.session_state.rfp_id = rfp['id']
                        st.session_state.page = 'view_rfp'
                        st.rerun()
                st.markdown("---")
    else:
        st.info("No RFPs found. Create your first RFP to get started!")


def show_evaluator_dashboard(user_id):
    """Dashboard for evaluators"""
    # Get pending evaluations
    db = get_db()
    try:
        pending_evaluations = db.get_pending_evaluations_for_user(user_id)
        st.write(f"Debug - Found {len(pending_evaluations)} pending evaluations")
    except Exception as e:
        st.error(f"Error loading pending evaluations: {str(e)}")
        pending_evaluations = []

    # Get user's RFPs (where they are team members)
    try:
        rfps = db.get_rfps_for_user(user_id)
        st.write(f"Debug - Found {len(rfps)} accessible RFPs")
    except Exception as e:
        st.error(f"Error loading RFPs: {str(e)}")
        rfps = []

    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Evaluations", len(pending_evaluations))
    with col2:
        assigned_rfps = len(rfps)
        st.metric("Assigned RFPs", assigned_rfps)
    with col3:
        # Count completed evaluations - simplified
        completed_count = 0  # We'll calculate this properly
        st.metric("Completed Evaluations", completed_count)

    # Pending Tasks - Fixed version
    st.markdown("### Pending Evaluations")
    if pending_evaluations:
        for evaluation in pending_evaluations:
            # Safely get proposal details
            proposal_id = evaluation.get('proposal_id')
            if not proposal_id:
                continue

            try:
                # For now, show basic info until we fix the query
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown("**📝 Proposal Evaluation Required**")
                        st.caption(f"Proposal ID: {proposal_id}")
                        st.caption(f"Assigned: {format_date(evaluation.get('created_at', ''))}")
                    with col2:
                        st.markdown("⏳ Pending")
                    with col3:
                        if st.button("Evaluate", key=f"eval_{evaluation['id']}"):
                            st.session_state.evaluation_id = evaluation['id']
                            st.session_state.proposal_id = proposal_id
                            st.session_state.page = 'evaluate_proposal'
                            st.rerun()
                    st.markdown("---")
            except Exception as e:
                st.error(f"Error loading proposal details: {str(e)}")
                # Show basic evaluation info even if proposal details fail
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown("**📝 Evaluation Task**")
                        st.caption(f"Evaluation ID: {evaluation.get('id', 'Unknown')}")
                    with col2:
                        st.markdown("⏳ Pending")
                    with col3:
                        if st.button("View", key=f"eval_basic_{evaluation.get('id', 'unknown')}"):
                            st.session_state.evaluation_id = evaluation['id']
                            st.session_state.proposal_id = evaluation.get('proposal_id')
                            st.session_state.page = 'evaluate_proposal'
                            st.rerun()
                    st.markdown("---")
    else:
        st.info("No pending evaluations at the moment.")

    # Quick Actions section
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 View My Evaluations"):
            st.session_state.page = 'evaluations'
            st.rerun()

    with col2:
        if st.button("📋 View RFPs"):
            st.session_state.page = 'my_rfps'
            st.rerun()

    with col3:
        if st.button("🏢 View Proposals"):
            st.session_state.page = 'proposals'
            st.rerun()


def show_dept_head_dashboard(user_id):
    """Dashboard for department heads"""
    db = get_db()

    # Get pending approvals for department heads
    try:
        # Get all RFPs in the system
        all_rfps_response = db.supabase.table("rfps").select("*").execute()
        all_rfps = all_rfps_response.data if all_rfps_response.data else []

        pending_rfp_approvals = [rfp for rfp in all_rfps if rfp['status'] == 'pending_approval']

        # Get proposals ready for approval
        pending_proposal_approvals = []
        for rfp in all_rfps:
            try:
                proposals = db.get_proposals_for_rfp(rfp['id'])
                # Look for under_review proposals that are pending approval
                ready_proposals = [p for p in proposals if p['status'] == 'under_review'
                                   and p.get('proposal_summary', '').startswith('[PENDING_APPROVAL]')]
                pending_proposal_approvals.extend(ready_proposals)
            except:
                continue

    except Exception as e:
        st.error(f"Error loading approvals: {str(e)}")
        pending_rfp_approvals = []
        pending_proposal_approvals = []

    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending RFP Approvals", len(pending_rfp_approvals))
    with col2:
        st.metric("Pending Proposal Approvals", len(pending_proposal_approvals))
    with col3:
        total_pending = len(pending_rfp_approvals) + len(pending_proposal_approvals)
        st.metric("Total Pending Approvals", total_pending)

    # Show pending approvals
    if pending_proposal_approvals:
        st.markdown("### 📊 Proposals Ready for Approval")
        for proposal in pending_proposal_approvals[:3]:  # Show top 3
            vendor_name = proposal.get('vendors', {}).get('name', 'Unknown Vendor') if proposal.get(
                'vendors') else 'Unknown Vendor'
            st.write(f"• **{vendor_name}** - Proposal ready for final approval")

        if st.button("🎯 View All Approvals", type="primary"):
            st.session_state.page = 'approvals'
            st.rerun()

    if pending_rfp_approvals:
        st.markdown("### 📋 RFPs Pending Approval")
        for rfp in pending_rfp_approvals[:3]:  # Show top 3
            st.write(f"• **{rfp['title']}** - RFP pending approval")

    if not pending_rfp_approvals and not pending_proposal_approvals:
        st.success("🎉 No pending approvals at this time!")

    # Quick Actions section
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ View Approvals"):
            st.session_state.page = 'approvals'
            st.rerun()

    with col2:
        if st.button("📊 View My Evaluations"):
            st.session_state.page = 'evaluations'
            st.rerun()

    with col3:
        if st.button("📈 View Reports"):
            st.session_state.page = 'reports'
            st.rerun()


def show_it_admin_dashboard(user_id):
    """Dashboard for IT admins"""
    show_evaluator_dashboard(user_id)  # Same view as evaluator for now


# RFP Management Functions
def show_my_rfps():
    """Display user's RFPs"""
    st.markdown('<h1 class="main-header">📄 My RFPs</h1>', unsafe_allow_html=True)

    user_id = st.session_state.user.id
    db = get_db()

    try:
        rfps = db.get_rfps_for_user(user_id)
        st.write(f"Debug - Found {len(rfps)} RFPs for user {user_id}")
    except Exception as e:
        st.error(f"Error loading RFPs: {str(e)}")
        rfps = []

    # Filter and search
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("Search RFPs", placeholder="Search by title...")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All"] + RFP_STATUSES)
    with col3:
        if st.button("Create New RFP", type="primary"):
            st.session_state.page = 'create_rfp'
            st.rerun()

    # Apply filters
    filtered_rfps = rfps
    if search_term:
        filtered_rfps = [rfp for rfp in filtered_rfps if search_term.lower() in rfp['title'].lower()]
    if status_filter != "All":
        filtered_rfps = [rfp for rfp in filtered_rfps if rfp['status'] == status_filter]

    # Display RFPs
    if filtered_rfps:
        for rfp in filtered_rfps:
            with st.container():
                st.markdown('<div class="rfp-card">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"### {rfp['title']}")
                    if rfp['description']:
                        st.markdown(
                            rfp['description'][:100] + "..." if len(rfp['description']) > 100 else rfp['description'])
                    st.caption(f"Created: {format_date(rfp['created_at'])}")
                    if rfp['due_date']:
                        st.caption(f"Due: {format_date(rfp['due_date'])}")

                with col2:
                    status_color = get_status_color(rfp['status'])
                    st.markdown(
                        f'<span class="status-badge" style="background-color: {status_color};">{rfp["status"].replace("_", " ").title()}</span>',
                        unsafe_allow_html=True
                    )

                with col3:
                    # Count proposals - handle missing proposals gracefully
                    proposal_count = len(rfp.get('proposals', []))
                    st.metric("Proposals", proposal_count)

                with col4:
                    if st.button("View Details", key=f"view_rfp_{rfp['id']}"):
                        st.session_state.rfp_id = rfp['id']
                        st.session_state.page = 'view_rfp'
                        st.rerun()

                    if rfp['status'] == 'draft':
                        if st.button("Edit", key=f"edit_rfp_{rfp['id']}"):
                            st.session_state.rfp_id = rfp['id']
                            st.session_state.page = 'edit_rfp'
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        # Empty state with call to action
        st.markdown("### 🚀 Ready to Create Your First RFP?")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("""
**Get started with AI-powered RFP creation!**

✨ Use AI to generate comprehensive RFP content
📋 Choose from professional templates
👥 Add team members for evaluation
📊 Set custom evaluation criteria
""")
            if st.button("🎯 Create Your First RFP", type="primary", use_container_width=True):
                st.session_state.page = 'create_rfp'
                st.rerun()

        # Also show some helpful tips
        with st.expander("💡 RFP Creation Tips"):
            st.markdown("""
**Best Practices for RFP Creation:**
1. **Be Specific**: Clearly define your requirements and expectations
2. **Set Realistic Timelines**: Give vendors enough time to prepare quality proposals
3. **Define Evaluation Criteria**: Be transparent about how proposals will be scored
4. **Include Business Context**: Help vendors understand your organization and goals
5. **Use Templates**: Start with our proven templates and customize as needed
""")

        if search_term or status_filter != "All":
            st.caption("💡 No RFPs match your current filters. Try adjusting your search criteria.")


# Main Application Logic
def main():
    """Main application logic"""
    # Check if user is logged in
    if not st.session_state.user:
        show_login_page()
        return

    # Show navigation and get selected page
    selected_page = show_navigation()
    if not selected_page:
        return

    # Handle direct page navigation from session state first
    current_page = st.session_state.get('page', 'dashboard')

    # If we have a specific page set (like view_rfp, edit_rfp), prioritize that
    if current_page in ['view_rfp', 'edit_rfp', 'evaluate_proposal', 'proposal_evaluations']:
        # Keep the current page
        pass
    else:
        # Handle navigation menu selections
        navigation_to_page = {
            "Dashboard": "dashboard",
            "My RFPs": "my_rfps",
            "Create RFP": "create_rfp",
            "Vendors": "vendors",
            "Proposals": "proposals",
            "Evaluations": "evaluations",
            "My Evaluations": "evaluations",
            "Reports": "reports",
            "Approvals": "approvals",
            "IT Evaluations": "it_evaluations",
            "Security Reviews": "security_reviews",
            "Pending Tasks": "pending_tasks"
            # REMOVED: "🧪 Test": "test_workflow"
        }

        # Handle notifications with dynamic count
        if selected_page and selected_page.startswith("Notifications"):
            current_page = "notifications"
        elif selected_page in navigation_to_page:
            current_page = navigation_to_page[selected_page]

        # Update session state
        st.session_state.page = current_page

    # Render the appropriate page
    if current_page == "dashboard":
        show_dashboard()
    elif current_page == "my_rfps":
        show_my_rfps()
    elif current_page == "create_rfp":
        show_create_rfp_page()
    elif current_page == "edit_rfp":
        show_edit_rfp_page()
    elif current_page == "view_rfp":
        show_view_rfp_page()
    elif current_page == "vendors":
        show_vendors_page()
    elif current_page == "proposals":
        show_proposals_page()
    elif current_page == "proposal_evaluations":
        show_proposal_evaluations()
    elif current_page == "evaluations":
        try:
            show_evaluations_page()
        except Exception as e:
            st.error(f"Error loading evaluations: {str(e)}")
            st.info("There was an issue loading the evaluations page. Please try refreshing or contact support.")
    elif current_page == "evaluate_proposal":
        show_simple_evaluate_proposal_page()  # Use simplified version
    elif current_page == "pending_tasks":
        try:
            show_pending_tasks_page()
        except Exception as e:
            st.error(f"Error loading pending tasks: {str(e)}")
            st.info("There was an issue loading the pending tasks page. Please try refreshing.")
    elif current_page == "reports":
        show_reports_page()
    elif current_page == "notifications":
        show_notifications_page()
    elif current_page == "approvals":
        show_approvals_page()
    elif current_page == "it_evaluations":
        show_it_evaluations_page()
    elif current_page == "security_reviews":
        show_security_reviews_page()
    # REMOVED test_workflow case entirely
    else:
        show_dashboard()  # Default fallback


# Placeholder functions for remaining pages
def show_notifications_page():
    """Simple notifications page"""
    st.markdown('<h1 class="main-header">🔔 Notifications</h1>', unsafe_allow_html=True)

    db = get_db()
    user_id = st.session_state.user.id

    try:
        notifications = db.get_user_notifications(user_id)
        if notifications:
            st.markdown(f"### You have {len(notifications)} notifications")
            for notification in notifications:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{notification.get('title', 'Notification')}**")
                        st.write(notification.get('message', 'No message'))
                        st.caption(f"📅 {format_date(notification.get('created_at', ''))}")
                    with col2:
                        notification_type = notification.get('type', 'general')
                        type_emoji = {
                            'rfp_approval': '📋',
                            'evaluation_request': '📊',
                            'proposal_submitted': '📥',
                            'evaluation_completed': '✅'
                        }.get(notification_type, '📝')
                        st.write(f"{type_emoji} {notification_type.replace('_', ' ').title()}")
                    with col3:
                        is_read = notification.get('is_read', False)
                        if not is_read:
                            if st.button("Mark Read", key=f"read_{notification['id']}"):
                                db.mark_notification_read(notification['id'])
                                st.rerun()
                        else:
                            st.write("✅ Read")
                    st.markdown("---")
        else:
            st.success("🎉 No new notifications! You're all caught up.")
    except Exception as e:
        st.error(f"Error loading notifications: {str(e)}")


def show_approvals_page():
    """Approvals page for department heads - handles both RFPs and evaluated proposals"""
    st.markdown('<h1 class="main-header">✅ Approvals</h1>', unsafe_allow_html=True)

    user_role = st.session_state.user_profile.get('role', '')
    if user_role not in ['dept_head', 'procurement_manager']:
        st.warning("⚠️ You don't have permission to view approvals")
        return

    db = get_db()
    user_id = st.session_state.user.id

    # Get both RFPs pending approval AND proposals ready for approval
    pending_rfp_approvals = []
    pending_proposal_approvals = []

    try:
        if user_role == 'procurement_manager':
            # Procurement managers see their own items
            rfps = db.get_rfps_for_user(user_id)
            pending_rfp_approvals = [rfp for rfp in rfps if rfp['status'] == 'pending_approval']

            # Get proposals ready for approval from their RFPs
            for rfp in rfps:
                try:
                    proposals = db.get_proposals_for_rfp(rfp['id'])
                    # Look for under_review proposals that are pending approval
                    ready_proposals = [p for p in proposals if p['status'] == 'under_review'
                                       and p.get('proposal_summary', '').startswith('[PENDING_APPROVAL]')]
                    for proposal in ready_proposals:
                        proposal['rfp_title'] = rfp['title']
                        pending_proposal_approvals.append(proposal)
                except:
                    continue
        else:
            # Department heads see all pending approvals (get ALL RFPs, not just their own)
            try:
                # Get all RFPs in the system for department heads
                all_rfps_response = db.supabase.table("rfps").select("*").execute()
                all_rfps = all_rfps_response.data if all_rfps_response.data else []

                pending_rfp_approvals = [rfp for rfp in all_rfps if rfp['status'] == 'pending_approval']

                # Get all proposals ready for approval from ALL RFPs
                for rfp in all_rfps:
                    try:
                        proposals = db.get_proposals_for_rfp(rfp['id'])
                        # Look for under_review proposals that are pending approval
                        ready_proposals = [p for p in proposals if p['status'] == 'under_review'
                                           and p.get('proposal_summary', '').startswith('[PENDING_APPROVAL]')]
                        for proposal in ready_proposals:
                            proposal['rfp_title'] = rfp['title']
                            pending_proposal_approvals.append(proposal)
                    except:
                        continue
            except Exception as e:
                st.error(f"Error loading all RFPs for dept head: {str(e)}")
                # Fallback to user's RFPs if the above fails
                rfps = db.get_rfps_for_user(user_id)
                pending_rfp_approvals = [rfp for rfp in rfps if rfp['status'] == 'pending_approval']

    except Exception as e:
        st.error(f"Error loading approvals: {str(e)}")
        pending_rfp_approvals = []
        pending_proposal_approvals = []

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("RFP Approvals", len(pending_rfp_approvals))
    with col2:
        st.metric("Proposal Approvals", len(pending_proposal_approvals))
    with col3:
        total_pending = len(pending_rfp_approvals) + len(pending_proposal_approvals)
        st.metric("Total Pending", total_pending)
    with col4:
        st.metric("Approved Today", 0)  # Placeholder - would track daily approvals

    # Debug information
    if st.checkbox("Show Debug Info"):
        st.write(f"**Debug Info for {user_role}:**")
        st.write(f"- Found {len(pending_rfp_approvals)} RFPs pending approval")
        st.write(f"- Found {len(pending_proposal_approvals)} proposals pending approval")
        if pending_proposal_approvals:
            st.write("**Proposals found:**")
            for p in pending_proposal_approvals:
                summary = p.get('proposal_summary', '')
                has_approval_flag = '[PENDING_APPROVAL]' in summary
                st.write(
                    f"  - {p.get('rfp_title', 'Unknown')} - Status: {p.get('status', 'Unknown')} - Has Approval Flag: {has_approval_flag}")
        else:
            st.write("- No proposals with 'under_review' status and '[PENDING_APPROVAL]' flag found")

    # Tabs for different approval types
    tab1, tab2 = st.tabs(["📋 RFP Approvals", "📊 Proposal Approvals"])

    with tab1:
        st.markdown("### RFPs Pending Approval")
        if pending_rfp_approvals:
            for rfp in pending_rfp_approvals:
                with st.expander(f"📋 {rfp['title']}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Description:** {rfp['description']}")
                        st.caption(f"Created: {format_date(rfp['created_at'])}")
                        st.caption(f"Due Date: {format_date(rfp['due_date'])}")

                        # Show evaluation criteria
                        if rfp.get('evaluation_criteria'):
                            st.markdown("**Evaluation Criteria:**")
                            eval_criteria = rfp['evaluation_criteria']
                            for category, details in eval_criteria.items():
                                if isinstance(details, dict):
                                    st.write(f"• {category.replace('_', ' ').title()}: {details.get('weight', 0)}%")

                    with col2:
                        st.markdown("**Actions:**")
                        if st.button("✅ Approve RFP", key=f"approve_rfp_{rfp['id']}", type="primary"):
                            try:
                                db.update_rfp(rfp['id'], {"status": "approved", "approved_by": user_id})
                                st.success("✅ RFP Approved!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error approving RFP: {str(e)}")

                        if st.button("❌ Reject", key=f"reject_rfp_{rfp['id']}"):
                            try:
                                db.update_rfp(rfp['id'], {"status": "draft"})
                                st.warning("❌ RFP sent back to draft")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error rejecting RFP: {str(e)}")

                        if st.button("👁️ View Details", key=f"view_rfp_approval_{rfp['id']}"):
                            st.session_state.rfp_id = rfp['id']
                            st.session_state.page = 'view_rfp'
                            st.rerun()
        else:
            st.success("🎉 No RFPs pending approval!")

    with tab2:
        st.markdown("### Proposals Ready for Final Approval")
        st.info("💡 **Workflow**: Under Review + [PENDING_APPROVAL] → Shortlisted (Approved) | Rejected")

        if pending_proposal_approvals:
            for proposal in pending_proposal_approvals:
                vendor_info = proposal.get('vendors', {})

                with st.expander(
                        f"📊 {proposal.get('rfp_title', 'Unknown RFP')} - {vendor_info.get('name', 'Unknown Vendor')}"):
                    # Get evaluation summary for this proposal
                    try:
                        evaluations = db.get_evaluations_for_proposal(proposal['id'])
                        completed_evaluations = [e for e in evaluations if e.get('status') == 'completed']

                        if completed_evaluations:
                            # Calculate summary metrics
                            avg_overall = sum(e.get('overall_score', 0) for e in completed_evaluations) / len(
                                completed_evaluations)
                            recommend_count = sum(
                                1 for e in completed_evaluations if e.get('recommendation') == 'recommend')
                            total_evaluations = len(completed_evaluations)

                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.markdown(f"**Vendor:** {vendor_info.get('name', 'Unknown')}")
                                st.markdown(f"**RFP:** {proposal.get('rfp_title', 'Unknown')}")

                                # Evaluation summary
                                st.markdown("**Evaluation Summary:**")
                                st.write(f"• Average Score: **{avg_overall:.1f}/100**")
                                st.write(f"• Evaluations Completed: **{total_evaluations}**")
                                st.write(f"• Recommendations: **{recommend_count}/{total_evaluations}** recommend")

                                # Quick status
                                if avg_overall >= 70 and recommend_count > (total_evaluations - recommend_count):
                                    st.success("🟢 **Strong Candidate** - Recommended for approval")
                                elif avg_overall >= 50:
                                    st.warning("🟡 **Conditional** - Review carefully")
                                else:
                                    st.error("🔴 **Weak Candidate** - Consider rejecting")

                                # Show recent evaluator comments
                                st.markdown("**Key Comments:**")
                                for evaluation in completed_evaluations[-2:]:  # Show last 2 evaluations
                                    evaluator_name = evaluation.get('user_profiles', {}).get('full_name', 'Unknown')
                                    if evaluation.get('overall_comments'):
                                        st.write(f"• *{evaluator_name}*: {evaluation['overall_comments'][:100]}...")

                            with col2:
                                st.markdown("**Approval Actions:**")

                                if st.button("✅ Approve Proposal", key=f"approve_proposal_{proposal['id']}",
                                             type="primary"):
                                    try:
                                        # Clean up the approval note and set to shortlisted (final approved state)
                                        current_summary = proposal.get('proposal_summary', '')
                                        clean_summary = current_summary.replace('[PENDING_APPROVAL] ',
                                                                                '') if current_summary.startswith(
                                            '[PENDING_APPROVAL]') else current_summary

                                        db.update_proposal(proposal['id'], {
                                            "status": "shortlisted",
                                            "proposal_summary": clean_summary
                                        })

                                        # Try to create a notification (if table exists)
                                        try:
                                            # Get the RFP ID from the proposal
                                            rfp_id = proposal.get('rfp_id')
                                            if rfp_id:
                                                # Get the RFP to find the creator
                                                rfp = db.get_rfp_by_id(rfp_id)
                                                if rfp and rfp.get('created_by'):
                                                    notification_data = {
                                                        "user_id": rfp['created_by'],
                                                        "title": "Proposal Approved",
                                                        "message": f"Your proposal from {vendor_info.get('name', 'Unknown Vendor')} has been approved!",
                                                        "type": "proposal_approved",
                                                        "is_read": False
                                                    }
                                                    db.create_notification(notification_data)
                                        except:
                                            pass  # Don't fail if notifications don't work

                                        st.success(
                                            f"✅ Proposal from {vendor_info.get('name', 'Unknown Vendor')} has been approved!")
                                        st.info("💡 Proposal status updated to 'Shortlisted' (approved for selection)")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error approving proposal: {str(e)}")

                                if st.button("❌ Reject Proposal", key=f"reject_proposal_{proposal['id']}"):
                                    try:
                                        # Clean up the approval note and set to rejected
                                        current_summary = proposal.get('proposal_summary', '')
                                        clean_summary = current_summary.replace('[PENDING_APPROVAL] ',
                                                                                '') if current_summary.startswith(
                                            '[PENDING_APPROVAL]') else current_summary

                                        db.update_proposal(proposal['id'], {
                                            "status": "rejected",
                                            "proposal_summary": clean_summary
                                        })

                                        # Try to create a notification (if table exists)
                                        try:
                                            # Get the RFP ID from the proposal
                                            rfp_id = proposal.get('rfp_id')
                                            if rfp_id:
                                                # Get the RFP to find the creator
                                                rfp = db.get_rfp_by_id(rfp_id)
                                                if rfp and rfp.get('created_by'):
                                                    notification_data = {
                                                        "user_id": rfp['created_by'],
                                                        "title": "Proposal Rejected",
                                                        "message": f"The proposal from {vendor_info.get('name', 'Unknown Vendor')} has been rejected.",
                                                        "type": "proposal_rejected",
                                                        "is_read": False
                                                    }
                                                    db.create_notification(notification_data)
                                        except:
                                            pass  # Don't fail if notifications don't work

                                        st.warning(
                                            f"❌ Proposal from {vendor_info.get('name', 'Unknown Vendor')} has been rejected")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error rejecting proposal: {str(e)}")

                                if st.button("🔄 Send Back for Review", key=f"review_proposal_{proposal['id']}"):
                                    try:
                                        # Clean up the approval note and send back to review
                                        current_summary = proposal.get('proposal_summary', '')
                                        clean_summary = current_summary.replace('[PENDING_APPROVAL] ',
                                                                                '') if current_summary.startswith(
                                            '[PENDING_APPROVAL]') else current_summary

                                        db.update_proposal(proposal['id'], {
                                            "status": "under_review",
                                            "proposal_summary": clean_summary
                                        })
                                        st.info("🔄 Sent back for additional review")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error sending back for review: {str(e)}")

                                if st.button("📊 View Full Evaluation", key=f"view_eval_{proposal['id']}"):
                                    st.session_state.proposal_id = proposal['id']
                                    st.session_state.page = 'proposal_evaluations'
                                    st.rerun()

                        else:
                            st.warning("⚠️ No completed evaluations found for this proposal")

                    except Exception as e:
                        st.error(f"Error loading evaluation data: {str(e)}")
        else:
            st.success("🎉 No proposals pending approval!")

    # Summary section
    if not pending_rfp_approvals and not pending_proposal_approvals:
        st.markdown("### 🎉 All Caught Up!")
        st.info("No pending approvals at this time. Great job staying on top of the workflow!")
    else:
        st.markdown("### 💡 Approval Tips")
        with st.expander("Best Practices for Approvals"):
            st.markdown("""
            **For RFP Approvals:**
            - Verify evaluation criteria are appropriate and measurable
            - Check that timeline is realistic for vendors
            - Ensure compliance requirements are clearly stated

            **For Proposal Approvals:**
            - Review evaluation consistency across evaluators
            - Consider overall business impact and strategic fit
            - Verify all required evaluations are completed
            - Check for any red flags in evaluator comments
            """)


def show_it_evaluations_page():
    """IT-specific evaluations page"""
    st.markdown('<h1 class="main-header">🔒 IT Security Evaluations</h1>', unsafe_allow_html=True)
    st.info("Specialized IT security evaluation interface - Coming in future update")


def show_security_reviews_page():
    """Security reviews page"""
    st.markdown('<h1 class="main-header">🛡️ Security Reviews</h1>', unsafe_allow_html=True)
    st.info("Security review dashboard - Coming in future update")


if __name__ == "__main__":
    main()