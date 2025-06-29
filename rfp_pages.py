import streamlit as st
import json
import uuid
from datetime import datetime, timedelta
from config import get_db, get_ai, format_date


def show_create_rfp_page():
    """Create new RFP with AI assistance"""
    st.markdown('<h1 class="main-header">✨ Create New RFP</h1>', unsafe_allow_html=True)

    db = get_db()
    ai = get_ai()

    # Get RFP templates
    templates = db.get_rfp_templates()
    template_options = {t['name']: t for t in templates}
    template_options['Custom (No Template)'] = None

    with st.form(f"create_rfp_form_{hash(str(st.session_state.user.id))}", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Basic Information")
            title = st.text_input("RFP Title*", placeholder="e.g., Cloud Infrastructure Services")
            description = st.text_area("Description*", placeholder="Brief description of what you're looking for...")

            # Template selection
            st.markdown("### Template Selection")
            selected_template_name = st.selectbox("Choose a template", list(template_options.keys()))
            selected_template = template_options[selected_template_name]

            if selected_template:
                st.info(f"Using template: **{selected_template['name']}** ({selected_template['category']})")

        with col2:
            st.markdown("### Timeline")
            due_date = st.date_input("Proposal Due Date", value=datetime.now() + timedelta(days=30))

            st.markdown("### AI Generation")
            use_ai = st.checkbox("Use AI to generate RFP content", value=True)
            if use_ai:
                st.caption("AI will help create comprehensive RFP content based on your inputs")

        # Business Criteria Section
        st.markdown("### Business Criteria")
        col1, col2 = st.columns(2)

        with col1:
            budget_range = st.text_input("Budget Range", placeholder="e.g., $50,000 - $100,000")
            project_duration = st.text_input("Project Duration", placeholder="e.g., 6 months")
            required_experience = st.text_input("Required Experience", placeholder="e.g., 5+ years in cloud services")

        with col2:
            location_preference = st.text_input("Location Preference", placeholder="e.g., Remote, On-site, Hybrid")
            compliance_requirements = st.text_input("Compliance Requirements", placeholder="e.g., SOC2, GDPR")
            preferred_start_date = st.date_input("Preferred Start Date", value=datetime.now() + timedelta(days=45))

        # Evaluation Criteria
        st.markdown("### Evaluation Criteria")
        st.caption("Define how proposals will be evaluated (scores out of 100)")

        col1, col2, col3 = st.columns(3)
        with col1:
            functional_weight = st.slider("Functional Requirements", 0, 100, 40)
            functional_criteria = st.text_area("Functional Criteria Details",
                                               placeholder="Technical capabilities, feature requirements, etc.")

        with col2:
            it_security_weight = st.slider("IT Security", 0, 100, 30)
            it_security_criteria = st.text_area("IT Security Criteria Details",
                                                placeholder="Security standards, compliance, data protection, etc.")

        with col3:
            business_weight = st.slider("Business", 0, 100, 30)
            business_criteria = st.text_area("Business Criteria Details",
                                             placeholder="Cost, timeline, company stability, references, etc.")

        # Validation for weights
        total_weight = functional_weight + it_security_weight + business_weight
        if total_weight != 100:
            st.warning(f"⚠️ Evaluation criteria weights must total 100%. Current total: {total_weight}%")

        # Submit button
        submitted = st.form_submit_button("🚀 Create RFP", type="primary", disabled=(total_weight != 100))

        if submitted and total_weight == 100:
            if not title or not description:
                st.error("Please fill in the required fields (Title and Description)")
            else:
                # Prepare data
                business_criteria = {
                    "budget_range": budget_range,
                    "project_duration": project_duration,
                    "required_experience": required_experience,
                    "location_preference": location_preference,
                    "compliance_requirements": compliance_requirements,
                    "preferred_start_date": preferred_start_date.isoformat()
                }

                evaluation_criteria = {
                    "functional": {
                        "weight": functional_weight,
                        "criteria": functional_criteria
                    },
                    "it_security": {
                        "weight": it_security_weight,
                        "criteria": it_security_criteria
                    },
                    "business": {
                        "weight": business_weight,
                        "criteria": business_criteria
                    }
                }

                # Generate content
                with st.spinner("🤖 Generating RFP content..."):
                    if use_ai:
                        template_content = selected_template['template_content'] if selected_template else None
                        rfp_content = ai.generate_rfp_content(title, description, template_content, business_criteria)
                        if not rfp_content:
                            rfp_content = f"# {title}\n\n{description}\n\n[AI generation failed - please edit manually]"
                    else:
                        base_content = selected_template['template_content'] if selected_template else ""
                        rfp_content = f"# {title}\n\n{description}\n\n{base_content}"

                # Create RFP
                rfp_data = {
                    "title": title,
                    "description": description,
                    "content": rfp_content,
                    "business_criteria": business_criteria,
                    "evaluation_criteria": evaluation_criteria,
                    "due_date": due_date.isoformat(),
                    "created_by": st.session_state.user.id,
                    "status": "draft"
                }

                try:
                    new_rfp = db.create_rfp(rfp_data)
                    if new_rfp:
                        st.success("🎉 RFP created successfully!")
                        st.session_state.rfp_id = new_rfp['id']
                        st.session_state.page = 'view_rfp'
                        st.rerun()
                    else:
                        st.error("Failed to create RFP. Please try again.")
                except Exception as e:
                    st.error(f"Error creating RFP: {str(e)}")


def show_edit_rfp_page():
    """Edit existing RFP"""
    if not st.session_state.rfp_id:
        st.error("No RFP selected for editing")
        return

    st.markdown('<h1 class="main-header">✏️ Edit RFP</h1>', unsafe_allow_html=True)

    db = get_db()
    rfp = db.get_rfp_by_id(st.session_state.rfp_id)

    if not rfp:
        st.error("RFP not found")
        return

    # Check if user can edit (only creator can edit)
    if rfp['created_by'] != st.session_state.user.id:
        st.error("You don't have permission to edit this RFP")
        return

    # Only allow editing if status is draft
    if rfp['status'] != 'draft':
        st.warning("⚠️ This RFP cannot be edited because it's no longer in draft status")
        st.info(f"Current status: **{rfp['status'].replace('_', ' ').title()}**")
        return

    with st.form(f"edit_rfp_form_{st.session_state.rfp_id}", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Basic Information")
            title = st.text_input("RFP Title*", value=rfp['title'])
            description = st.text_area("Description*", value=rfp['description'])

        with col2:
            st.markdown("### Timeline")
            current_due_date = datetime.fromisoformat(rfp['due_date'].replace('Z', '+00:00')).date() if rfp[
                'due_date'] else datetime.now().date()
            due_date = st.date_input("Proposal Due Date", value=current_due_date)

        # Content editing
        st.markdown("### RFP Content")
        content = st.text_area("RFP Content", value=rfp['content'], height=400)

        # Business criteria editing
        st.markdown("### Business Criteria")
        business_criteria = rfp.get('business_criteria', {})

        col1, col2 = st.columns(2)
        with col1:
            budget_range = st.text_input("Budget Range", value=business_criteria.get('budget_range', ''))
            project_duration = st.text_input("Project Duration", value=business_criteria.get('project_duration', ''))
            required_experience = st.text_input("Required Experience",
                                                value=business_criteria.get('required_experience', ''))

        with col2:
            location_preference = st.text_input("Location Preference",
                                                value=business_criteria.get('location_preference', ''))
            compliance_requirements = st.text_input("Compliance Requirements",
                                                    value=business_criteria.get('compliance_requirements', ''))

        # Evaluation criteria editing
        st.markdown("### Evaluation Criteria")
        eval_criteria = rfp.get('evaluation_criteria', {})

        col1, col2, col3 = st.columns(3)
        with col1:
            functional_weight = st.slider("Functional Requirements", 0, 100,
                                          eval_criteria.get('functional', {}).get('weight', 40))
            functional_criteria = st.text_area("Functional Criteria",
                                               value=eval_criteria.get('functional', {}).get('criteria', ''))

        with col2:
            it_security_weight = st.slider("IT Security", 0, 100,
                                           eval_criteria.get('it_security', {}).get('weight', 30))
            it_security_criteria = st.text_area("IT Security Criteria",
                                                value=eval_criteria.get('it_security', {}).get('criteria', ''))

        with col3:
            business_weight = st.slider("Business", 0, 100,
                                        eval_criteria.get('business', {}).get('weight', 30))
            business_criteria_text = st.text_area("Business Criteria",
                                                  value=eval_criteria.get('business', {}).get('criteria', ''))

        total_weight = functional_weight + it_security_weight + business_weight
        if total_weight != 100:
            st.warning(f"⚠️ Evaluation criteria weights must total 100%. Current total: {total_weight}%")

        col1, col2, col3 = st.columns(3)
        with col1:
            save_button = st.form_submit_button("💾 Save Changes", type="primary", disabled=(total_weight != 100))
        with col2:
            submit_for_approval = st.form_submit_button("📋 Submit for Approval", disabled=(total_weight != 100))
        with col3:
            cancel_button = st.form_submit_button("❌ Cancel")

        if cancel_button:
            st.session_state.page = 'view_rfp'
            st.rerun()

        if save_button or submit_for_approval:
            if not title or not description:
                st.error("Please fill in the required fields")
            else:
                # Prepare updated data
                updated_business_criteria = {
                    "budget_range": budget_range,
                    "project_duration": project_duration,
                    "required_experience": required_experience,
                    "location_preference": location_preference,
                    "compliance_requirements": compliance_requirements,
                    "preferred_start_date": business_criteria.get('preferred_start_date', '')
                }

                updated_evaluation_criteria = {
                    "functional": {
                        "weight": functional_weight,
                        "criteria": functional_criteria
                    },
                    "it_security": {
                        "weight": it_security_weight,
                        "criteria": it_security_criteria
                    },
                    "business": {
                        "weight": business_weight,
                        "criteria": business_criteria_text
                    }
                }

                updates = {
                    "title": title,
                    "description": description,
                    "content": content,
                    "business_criteria": updated_business_criteria,
                    "evaluation_criteria": updated_evaluation_criteria,
                    "due_date": due_date.isoformat(),
                    "status": "pending_approval" if submit_for_approval else "draft"
                }

                try:
                    updated_rfp = db.update_rfp(st.session_state.rfp_id, updates)
                    if updated_rfp:
                        if submit_for_approval:
                            st.success("🎉 RFP submitted for approval!")
                        else:
                            st.success("💾 RFP saved successfully!")
                        st.session_state.page = 'view_rfp'
                        st.rerun()
                    else:
                        st.error("Failed to update RFP")
                except Exception as e:
                    st.error(f"Error updating RFP: {str(e)}")


def show_view_rfp_page():
    """View RFP details and manage team/proposals"""
    if not st.session_state.rfp_id:
        st.error("No RFP selected")
        st.write("Debug: RFP ID missing")
        return

    st.write(f"Debug: Loading RFP {st.session_state.rfp_id}")

    db = get_db()
    rfp = db.get_rfp_by_id(st.session_state.rfp_id)

    if not rfp:
        st.error("RFP not found")
        st.write(f"Debug: Could not find RFP with ID {st.session_state.rfp_id}")
        return

    st.write(f"Debug: RFP loaded successfully - {rfp['title']}")

    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f'<h1 class="main-header">📄 {rfp["title"]}</h1>', unsafe_allow_html=True)

    with col2:
        status_color = {
            'draft': 'gray',
            'pending_approval': 'orange',
            'approved': 'blue',
            'published': 'green',
            'evaluation': 'purple',
            'completed': 'darkgreen',
            'cancelled': 'red'
        }.get(rfp['status'], 'gray')

        st.markdown(
            f'<span class="status-badge" style="background-color: {status_color};">{rfp["status"].replace("_", " ").title()}</span>',
            unsafe_allow_html=True
        )

    with col3:
        # Back button
        if st.button("← Back to My RFPs"):
            st.session_state.page = 'my_rfps'
            st.session_state.rfp_id = None
            st.rerun()

        # Action buttons based on status and user role
        user_is_creator = rfp['created_by'] == st.session_state.user.id

        if user_is_creator and rfp['status'] == 'draft':
            if st.button("✏️ Edit RFP"):
                st.session_state.page = 'edit_rfp'
                st.rerun()

        if user_is_creator and rfp['status'] in ['draft', 'approved']:
            if st.button("📢 Publish RFP"):
                updates = {"status": "published"}
                db.update_rfp(st.session_state.rfp_id, updates)
                st.success("RFP published!")
                st.rerun()

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Details", "👥 Team", "🏢 Proposals", "📊 Evaluations", "📈 Analytics"])

    with tab1:
        show_rfp_details(rfp)

    with tab2:
        show_rfp_team_management(rfp)

    with tab3:
        show_rfp_proposals(rfp)

    with tab4:
        show_rfp_evaluations(rfp)

    with tab5:
        show_rfp_analytics(rfp)


def show_rfp_details(rfp):
    """Show RFP details tab"""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Description")
        st.write(rfp['description'])

        st.markdown("### RFP Content")
        st.markdown(rfp['content'])

    with col2:
        st.markdown("### Key Information")
        st.info(f"""
        **Created:** {format_date(rfp['created_at'])}
        **Due Date:** {format_date(rfp['due_date'])}
        **Created By:** {rfp.get('creator_name', 'Unknown')}
        """)

        # Business criteria
        if rfp.get('business_criteria'):
            st.markdown("### Business Criteria")
            criteria = rfp['business_criteria']
            for key, value in criteria.items():
                if value:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")

        # Evaluation criteria
        if rfp.get('evaluation_criteria'):
            st.markdown("### Evaluation Criteria")
            eval_criteria = rfp['evaluation_criteria']
            for category, details in eval_criteria.items():
                if isinstance(details, dict):
                    st.write(f"**{category.replace('_', ' ').title()}:** {details.get('weight', 0)}%")


def show_rfp_team_management(rfp):
    """Show team management tab"""
    db = get_db()
    user_is_creator = rfp['created_by'] == st.session_state.user.id

    st.markdown("### Team Members")

    # Get current team members
    try:
        team_members = db.get_team_members(st.session_state.rfp_id)
    except Exception as e:
        st.error(f"Error loading team members: {str(e)}")
        team_members = []

    if team_members:
        for member in team_members:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                user_info = member.get('user_profiles', {})
                st.write(f"**{user_info.get('full_name', 'Unknown')}**")
                st.caption(user_info.get('email', ''))
            with col2:
                st.write(user_info.get('role', 'Unknown').replace('_', ' ').title())
            with col3:
                st.write(member.get('role', 'evaluator').title())
            with col4:
                if user_is_creator:
                    if st.button("Remove", key=f"remove_{member['user_id']}"):
                        db.remove_team_member(st.session_state.rfp_id, member['user_id'])
                        st.success("Team member removed")
                        st.rerun()
    else:
        st.info("No team members added yet")

    # Add team member (only for creator)
    if user_is_creator:
        st.markdown("### Add Team Member")

        # Get all users
        try:
            all_users = db.get_all_users()
        except Exception as e:
            st.error(f"Error loading users: {str(e)}")
            all_users = []

        # Exclude creator and existing team members
        existing_member_ids = {m['user_id'] for m in team_members}
        existing_member_ids.add(rfp['created_by'])

        available_users = [u for u in all_users if u['id'] not in existing_member_ids]

        if available_users:
            with st.form(f"add_team_member_{st.session_state.rfp_id}"):
                user_options = {f"{u['full_name']} ({u['email']})": u['id'] for u in available_users}
                selected_user_display = st.selectbox("Select User", list(user_options.keys()))
                selected_user_id = user_options[selected_user_display]

                member_role = st.selectbox("Role", ["evaluator", "approver"])

                add_button = st.form_submit_button("Add Team Member", type="primary")

                if add_button:
                    team_data = {
                        "rfp_id": st.session_state.rfp_id,
                        "user_id": selected_user_id,
                        "role": member_role,
                        "added_by": st.session_state.user.id
                    }

                    try:
                        new_member = db.add_team_member(team_data)
                        if new_member:
                            st.success("Team member added!")
                            st.rerun()
                        else:
                            st.error("Failed to add team member")
                    except Exception as e:
                        st.error(f"Error adding team member: {str(e)}")
        else:
            # No users available - show options to create users
            st.warning("⚠️ No other users available to add to the team")

            st.markdown("### 🎯 Quick Solutions:")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Option 1: Create Test Users**")
                if st.button("🧪 Create Sample Users", type="primary"):
                    # Create some sample users for testing
                    sample_users = [
                        {
                            "email": "evaluator1@company.com",
                            "full_name": "Alice Johnson",
                            "role": "evaluator"
                        },
                        {
                            "email": "evaluator2@company.com",
                            "full_name": "Bob Smith",
                            "role": "evaluator"
                        },
                        {
                            "email": "depthead@company.com",
                            "full_name": "Carol Williams",
                            "role": "dept_head"
                        }
                    ]

                    created_count = 0
                    for user_data in sample_users:
                        try:
                            # Create user profile directly (since we can't create auth users without passwords)
                            import uuid
                            user_data["id"] = str(uuid.uuid4())
                            new_user = db.create_user_profile(user_data)
                            if new_user:
                                created_count += 1
                        except Exception as e:
                            st.error(f"Error creating user {user_data['full_name']}: {str(e)}")

                    if created_count > 0:
                        st.success(f"✅ Created {created_count} sample users! Refresh to see them.")
                        st.rerun()
                    else:
                        st.error("Failed to create sample users")

            with col2:
                st.markdown("**Option 2: Skip Team for Now**")
                st.info(
                    "You can proceed without team members and add them later when you have more users in the system.")

                if st.button("📢 Publish RFP Without Team"):
                    try:
                        db.update_rfp(st.session_state.rfp_id, {"status": "published"})
                        st.success("🎉 RFP published! You can add team members later.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error publishing RFP: {str(e)}")

            st.markdown("---")
            st.caption(
                "💡 **Tip:** In a real environment, your system admin would create user accounts for team members with proper authentication.")


def show_rfp_proposals(rfp):
    """Show proposals tab"""
    st.markdown("### 📥 Proposals")

    db = get_db()
    rfp_id = rfp['id']

    try:
        proposals = db.get_proposals_for_rfp(rfp_id)
    except Exception as e:
        st.error(f"Error loading proposals: {str(e)}")
        proposals = []

    if proposals:
        # Proposals summary
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Proposals", len(proposals))

        with col2:
            submitted = len([p for p in proposals if p['status'] == 'submitted'])
            st.metric("New Submissions", submitted)

        with col3:
            shortlisted = len([p for p in proposals if p['status'] == 'shortlisted'])
            st.metric("Shortlisted", shortlisted)

        with col4:
            under_review = len([p for p in proposals if p['status'] == 'under_review'])
            st.metric("Under Review", under_review)

        # Proposals list
        for proposal in proposals:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    vendor_info = proposal.get('vendors', {})
                    st.markdown(f"**{vendor_info.get('name', 'Unknown Vendor')}**")
                    st.write(f"📧 {vendor_info.get('contact_email', 'No email')}")
                    if proposal.get('proposal_summary'):
                        st.caption(proposal['proposal_summary'][:100] + "...")

                with col2:
                    status = proposal['status']
                    status_color = {
                        'submitted': 'blue',
                        'under_review': 'orange',
                        'shortlisted': 'green',
                        'rejected': 'red'
                    }.get(status, 'gray')

                    st.markdown(
                        f'<span class="status-badge" style="background-color: {status_color};">{status.replace("_", " ").title()}</span>',
                        unsafe_allow_html=True
                    )

                with col3:
                    # Count evaluations
                    try:
                        evaluations = db.get_evaluations_for_proposal(proposal['id'])
                        completed = len([e for e in evaluations if e.get('status') == 'completed'])
                        total = len(evaluations)
                        st.write(f"📊 {completed}/{total} evals")
                    except:
                        st.write("📊 0/0 evals")

                with col4:
                    if st.button("View", key=f"view_proposal_{proposal['id']}"):
                        st.session_state.proposal_id = proposal['id']
                        st.session_state.page = 'proposal_evaluations'
                        st.rerun()

                st.markdown("---")
    else:
        st.info("📭 No proposals submitted yet")

        # Quick action to go to proposals page
        if st.button("📥 Submit New Proposal"):
            st.session_state.page = 'proposals'
            st.rerun()


def show_rfp_evaluations(rfp):
    """Show evaluations tab"""
    st.markdown("### 📊 Evaluations Overview")

    db = get_db()
    rfp_id = rfp['id']

    try:
        proposals = db.get_proposals_for_rfp(rfp_id)

        if not proposals:
            st.info("📭 No proposals to evaluate yet")
            return

        # Evaluation summary
        total_evaluations = 0
        completed_evaluations = 0
        pending_evaluations = 0

        evaluation_data = []

        for proposal in proposals:
            try:
                evaluations = db.get_evaluations_for_proposal(proposal['id'])
                total_evaluations += len(evaluations)

                for evaluation in evaluations:
                    if evaluation.get('status') == 'completed':
                        completed_evaluations += 1
                        evaluation_data.append({
                            'vendor': proposal.get('vendors', {}).get('name', 'Unknown'),
                            'evaluator': evaluation.get('user_profiles', {}).get('full_name', 'Unknown'),
                            'overall_score': evaluation.get('overall_score', 0),
                            'recommendation': evaluation.get('recommendation', 'not_recommend')
                        })
                    else:
                        pending_evaluations += 1
            except:
                continue

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Evaluations", total_evaluations)

        with col2:
            st.metric("Completed", completed_evaluations)

        with col3:
            st.metric("Pending", pending_evaluations)

        with col4:
            completion_rate = round((completed_evaluations / total_evaluations * 100) if total_evaluations > 0 else 0,
                                    1)
            st.metric("Completion Rate", f"{completion_rate}%")

        # Evaluation results
        if evaluation_data:
            st.markdown("#### Evaluation Results")

            # Group by vendor
            vendor_scores = {}
            for eval_item in evaluation_data:
                vendor = eval_item['vendor']
                if vendor not in vendor_scores:
                    vendor_scores[vendor] = {'scores': [], 'recommendations': []}

                vendor_scores[vendor]['scores'].append(eval_item['overall_score'])
                vendor_scores[vendor]['recommendations'].append(eval_item['recommendation'])

            # Display vendor summary
            for vendor, data in vendor_scores.items():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"**{vendor}**")

                with col2:
                    avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
                    st.metric("Avg Score", f"{round(avg_score, 1)}/100")

                with col3:
                    recommend_count = data['recommendations'].count('recommend')
                    total_evals = len(data['recommendations'])
                    st.write(f"👍 {recommend_count}/{total_evals} recommend")
        else:
            st.info("📊 No completed evaluations yet")

    except Exception as e:
        st.error(f"Error loading evaluations: {str(e)}")


def show_rfp_analytics(rfp):
    """Show analytics tab"""
    st.markdown("### 📈 RFP Analytics")

    st.info("📊 Detailed analytics for this RFP")

    # Quick stats about this RFP
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Days Since Created", "X days")  # Would calculate from created_at

    with col2:
        st.metric("Days Until Due", "X days")  # Would calculate from due_date

    with col3:
        st.metric("Response Rate", "X%")  # Would calculate based on outreach vs proposals

    # Link to full analytics
    if st.button("📊 View Full Analytics Dashboard"):
        st.session_state.page = 'reports'
        st.rerun()