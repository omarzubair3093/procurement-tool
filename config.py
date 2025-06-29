import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Initialize Supabase client
def init_supabase() -> Client:
    """Initialize and return Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# Initialize OpenAI client
def init_openai():
    """Initialize OpenAI client"""
    # The OpenAI client is now initialized within each function call
    return True


# Database helper functions
class DatabaseManager:
    def __init__(self):
        self.supabase = init_supabase()

    # User Profile Functions
    def get_user_profile(self, user_id: str):
        """Get user profile by ID"""
        response = self.supabase.table("user_profiles").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None

    def create_user_profile(self, user_data: dict):
        """Create new user profile"""
        try:
            response = self.supabase.table("user_profiles").insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating user profile: {str(e)}")
            return None

    def update_user_profile(self, user_id: str, updates: dict):
        """Update user profile"""
        response = self.supabase.table("user_profiles").update(updates).eq("id", user_id).execute()
        return response.data[0] if response.data else None

    # RFP Functions
    def create_rfp(self, rfp_data: dict):
        """Create new RFP with simplified approach"""
        try:
            # Use direct insert since we temporarily disabled RLS
            response = self.supabase.table("rfps").insert(rfp_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating RFP: {str(e)}")
            return None

    def get_rfps_for_user(self, user_id: str):
        """Get all RFPs accessible to user"""
        try:
            # Simple approach - get user's created RFPs since RLS is disabled
            response = self.supabase.table("rfps").select("""
                *
            """).eq("created_by", user_id).order("created_at", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error in get_rfps_for_user: {str(e)}")
            return []

    def get_rfp_by_id(self, rfp_id: str):
        """Get RFP by ID with related data"""
        try:
            response = self.supabase.table("rfps").select("*").eq("id", rfp_id).execute()
            if response.data:
                rfp = response.data[0]
                # Get creator info separately
                try:
                    creator_response = self.supabase.table("user_profiles").select("full_name").eq("id", rfp[
                        'created_by']).execute()
                    if creator_response.data:
                        rfp['creator_name'] = creator_response.data[0]['full_name']
                    else:
                        rfp['creator_name'] = 'Unknown'
                except:
                    rfp['creator_name'] = 'Unknown'
                return rfp
            return None
        except Exception as e:
            print(f"Error getting RFP: {str(e)}")
            return None

    def update_rfp(self, rfp_id: str, updates: dict):
        """Update RFP"""
        response = self.supabase.table("rfps").update(updates).eq("id", rfp_id).execute()
        return response.data[0] if response.data else None

    def delete_rfp(self, rfp_id: str):
        """Delete RFP"""
        response = self.supabase.table("rfps").delete().eq("id", rfp_id).execute()
        return response.data

    # RFP Team Members Functions
    def add_team_member(self, team_data: dict):
        """Add team member to RFP"""
        response = self.supabase.table("rfp_team_members").insert(team_data).execute()
        return response.data[0] if response.data else None

    def remove_team_member(self, rfp_id: str, user_id: str):
        """Remove team member from RFP"""
        response = self.supabase.table("rfp_team_members").delete().eq("rfp_id", rfp_id).eq("user_id",
                                                                                            user_id).execute()
        return response.data

    def get_team_members(self, rfp_id: str):
        """Get team members for RFP"""
        response = self.supabase.table("rfp_team_members").select("""
            *, user_profiles(full_name, email, role)
        """).eq("rfp_id", rfp_id).execute()
        return response.data

    # Vendor Functions
    def create_vendor(self, vendor_data: dict):
        """Create new vendor"""
        response = self.supabase.table("vendors").insert(vendor_data).execute()
        return response.data[0] if response.data else None

    def get_all_vendors(self):
        """Get all vendors"""
        response = self.supabase.table("vendors").select("*").execute()
        return response.data

    def get_vendor_by_id(self, vendor_id: str):
        """Get vendor by ID"""
        response = self.supabase.table("vendors").select("*").eq("id", vendor_id).execute()
        return response.data[0] if response.data else None

    def update_vendor(self, vendor_id: str, updates: dict):
        """Update vendor"""
        response = self.supabase.table("vendors").update(updates).eq("id", vendor_id).execute()
        return response.data[0] if response.data else None

    # Proposal Functions
    def create_proposal(self, proposal_data: dict):
        """Create new proposal"""
        response = self.supabase.table("proposals").insert(proposal_data).execute()
        return response.data[0] if response.data else None

    def get_proposals_for_rfp(self, rfp_id: str):
        """Get all proposals for RFP"""
        response = self.supabase.table("proposals").select("""
            *, vendors(name, contact_email, contact_person),
            evaluations(*, user_profiles(full_name))
        """).eq("rfp_id", rfp_id).execute()
        return response.data

    def update_proposal(self, proposal_id: str, updates: dict):
        """Update proposal"""
        response = self.supabase.table("proposals").update(updates).eq("id", proposal_id).execute()
        return response.data[0] if response.data else None

    def update_multiple_proposals(self, proposal_ids: list, updates: dict):
        """Update multiple proposals"""
        response = self.supabase.table("proposals").update(updates).in_("id", proposal_ids).execute()
        return response.data

    # Evaluation Functions
    def create_evaluation(self, evaluation_data: dict):
        """Create new evaluation"""
        response = self.supabase.table("evaluations").insert(evaluation_data).execute()
        return response.data[0] if response.data else None

    def get_evaluation(self, proposal_id: str, evaluator_id: str):
        """Get evaluation for proposal by evaluator"""
        response = self.supabase.table("evaluations").select("*").eq("proposal_id", proposal_id).eq("evaluator_id",
                                                                                                    evaluator_id).execute()
        return response.data[0] if response.data else None

    def update_evaluation(self, evaluation_id: str, updates: dict):
        """Update evaluation"""
        response = self.supabase.table("evaluations").update(updates).eq("id", evaluation_id).execute()
        return response.data[0] if response.data else None

    def get_evaluations_for_proposal(self, proposal_id: str):
        """Get all evaluations for a proposal"""
        response = self.supabase.table("evaluations").select("""
            *, user_profiles(full_name, role)
        """).eq("proposal_id", proposal_id).execute()
        return response.data

    def get_pending_evaluations_for_user(self, user_id: str):
        """Get pending evaluations for user"""
        try:
            response = self.supabase.table("evaluations").select("*").eq("evaluator_id", user_id).eq("status",
                                                                                                     "pending").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error in get_pending_evaluations_for_user: {str(e)}")
            return []

    # RFP Template Functions
    def get_rfp_templates(self):
        """Get all active RFP templates"""
        response = self.supabase.table("rfp_templates").select("*").eq("is_active", True).execute()
        return response.data

    def create_rfp_template(self, template_data: dict):
        """Create new RFP template"""
        response = self.supabase.table("rfp_templates").insert(template_data).execute()
        return response.data[0] if response.data else None

    # Notification Functions
    def create_notification(self, notification_data: dict):
        """Create new notification"""
        response = self.supabase.table("notifications").insert(notification_data).execute()
        return response.data[0] if response.data else None

    def get_user_notifications(self, user_id: str, unread_only: bool = False):
        """Get notifications for user"""
        query = self.supabase.table("notifications").select("*").eq("user_id", user_id)
        if unread_only:
            query = query.eq("is_read", False)
        response = query.order("created_at", desc=True).execute()
        return response.data

    def mark_notification_read(self, notification_id: str):
        """Mark notification as read"""
        response = self.supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        return response.data

    # Utility Functions
    def get_all_users(self):
        """Get all users for team assignment"""
        response = self.supabase.table("user_profiles").select("id, full_name, email, role").execute()
        return response.data

    def get_users_by_role(self, role: str):
        """Get users by role"""
        response = self.supabase.table("user_profiles").select("*").eq("role", role).execute()
        return response.data


# AI Helper Functions
class AIManager:
    def __init__(self):
        self.client = init_openai()

    def generate_rfp_content(self, title: str, description: str, template: str = None, business_criteria: dict = None):
        """Generate RFP content using OpenAI"""
        prompt = f"""
Generate a comprehensive Request for Proposal (RFP) document for:

Title: {title}
Description: {description}
"""

        if template:
            prompt += f"\nBase Template:\n{template}\n"

        if business_criteria:
            prompt += f"\nBusiness Criteria:\n{business_criteria}\n"

        prompt += """
Please create a detailed, professional RFP that includes:
1. Executive Summary
2. Project Overview
3. Scope of Work
4. Technical Requirements
5. Evaluation Criteria
6. Submission Requirements
7. Timeline
8. Terms and Conditions

Make it comprehensive and professional.
"""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            import streamlit as st
            st.error(f"Error generating RFP content: {str(e)}")
            return None

    def analyze_proposal(self, proposal_text: str, rfp_criteria: dict):
        """Analyze proposal against RFP criteria"""
        prompt = f"""
Analyze the following proposal against the RFP criteria and provide:
1. Summary of key points
2. Compliance with requirements
3. Strengths and weaknesses
4. Recommended questions for evaluation

RFP Criteria: {rfp_criteria}

Proposal: {proposal_text}
"""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.5
            )
            return response.choices[0].message.content
        except Exception as e:
            import streamlit as st
            st.error(f"Error analyzing proposal: {str(e)}")
            return None

    def suggest_evaluation_questions(self, rfp_content: str, category: str):
        """Suggest evaluation questions for different categories"""
        prompt = f"""
Based on the following RFP content, suggest 5-7 specific evaluation questions for the {category} category.
Make them specific, measurable, and relevant to the RFP requirements.

RFP Content: {rfp_content}
Category: {category}

Format as a numbered list.
"""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.6
            )
            return response.choices[0].message.content
        except Exception as e:
            import streamlit as st
            st.error(f"Error generating evaluation questions: {str(e)}")
            return None


# Session state management
def init_session_state():
    """Initialize session state variables"""
    # Only initialize if streamlit is available and session_state exists
    try:
        import streamlit as st
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = None
        if 'page' not in st.session_state:
            st.session_state.page = 'login'
        if 'rfp_id' not in st.session_state:
            st.session_state.rfp_id = None
        if 'proposal_id' not in st.session_state:
            st.session_state.proposal_id = None
        if 'show_add_vendor' not in st.session_state:
            st.session_state.show_add_vendor = False
        if 'show_edit_vendor' not in st.session_state:
            st.session_state.show_edit_vendor = False
        if 'edit_vendor_id' not in st.session_state:
            st.session_state.edit_vendor_id = None
    except:
        pass


# Authentication helper functions
def login_user(email: str, password: str):
    """Login user with email and password"""
    try:
        import streamlit as st
        supabase = init_supabase()

        response = supabase.auth.sign_in_with_password({"email": email, "password": password})

        if response.user:
            st.session_state.user = response.user
            db = DatabaseManager()
            profile = db.get_user_profile(response.user.id)
            st.session_state.user_profile = profile
            return True, "Login successful!"

        return False, "Invalid credentials"
    except Exception as e:
        return False, f"Login error: {str(e)}"


def logout_user():
    """Logout current user"""
    try:
        import streamlit as st
        supabase = init_supabase()
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.user_profile = None
        st.session_state.page = 'login'
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Logout error: {str(e)}")
        return False


def register_user(email: str, password: str, full_name: str, role: str):
    """Register new user"""
    try:
        supabase = init_supabase()

        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "role": role
                }
            }
        })

        if response.user:
            return True, "Registration successful! Please check your email for verification."

        return False, "Registration failed"
    except Exception as e:
        return False, f"Registration error: {str(e)}"


# Utility functions
def format_date(date_str):
    """Format date string for display"""
    if not date_str:
        return "Not set"
    try:
        from datetime import datetime
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y at %I:%M %p")
    except:
        return date_str


def get_status_color(status: str) -> str:
    """Get color for status display"""
    status_colors = {
        'draft': 'gray',
        'pending_approval': 'orange',
        'approved': 'blue',
        'published': 'green',
        'evaluation': 'purple',
        'completed': 'darkgreen',
        'cancelled': 'red',
        'submitted': 'blue',
        'under_review': 'orange',
        'shortlisted': 'green',
        'rejected': 'red',
        'ready_for_approval': 'purple',
        'pending': 'orange',
        'recommend': 'green',
        'conditional': 'yellow',
        'not_recommend': 'red'
    }
    return status_colors.get(status, 'gray')


# Constants - Updated to include new workflow statuses
USER_ROLES = ['procurement_manager', 'evaluator', 'dept_head', 'it_admin']
RFP_STATUSES = ['draft', 'pending_approval', 'approved', 'published', 'evaluation', 'completed', 'cancelled']
PROPOSAL_STATUSES = ['submitted', 'under_review', 'shortlisted', 'rejected']
EVALUATION_STATUSES = ['pending', 'completed']
RECOMMENDATION_OPTIONS = ['recommend', 'conditional', 'not_recommend']


# Initialize globals - these will be imported when needed
def get_db():
    """Get database manager instance"""
    return DatabaseManager()


def get_ai():
    """Get AI manager instance"""
    return AIManager()