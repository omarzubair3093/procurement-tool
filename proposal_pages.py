import streamlit as st
from config import get_db, get_ai, format_date
import io
import base64
from datetime import datetime


def show_proposals_page():
    """Main proposals management page"""
    st.markdown('<h1 class="main-header">📋 Proposal Management</h1>', unsafe_allow_html=True)

    db = get_db()
    user_id = st.session_state.user.id

    # Get user's RFPs to show proposals for
    try:
        rfps = db.get_rfps_for_user(user_id)
        # Filter to only published RFPs that can receive proposals
        active_rfps = [rfp for rfp in rfps if rfp['status'] in ['published', 'evaluation']]
    except Exception as e:
        st.error(f"Error loading RFPs: {str(e)}")
        active_rfps = []

    if not active_rfps:
        st.info(
            "📌 No active RFPs available for proposal submission. Publish an RFP first to start receiving proposals.")
        return

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📥 Submit Proposal", "📊 Proposal Overview", "🔍 Proposal Details"])

    with tab1:
        show_submit_proposal_form(active_rfps)
    with tab2:
        show_proposal_overview(active_rfps)
    with tab3:
        show_proposal_details(active_rfps)


def show_submit_proposal_form(active_rfps):
    """Form to submit new proposals"""
    st.markdown("### 📥 Submit New Proposal")

    if not active_rfps:
        st.warning("No active RFPs available for proposals")
        return

    db = get_db()

    with st.form(f"submit_proposal_{hash(str(st.session_state.user.id))}", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            # RFP selection
            rfp_options = {f"{rfp['title']} (Due: {format_date(rfp['due_date'])})": rfp['id'] for rfp in active_rfps}
            selected_rfp_display = st.selectbox("Select RFP*", list(rfp_options.keys()))
            selected_rfp_id = rfp_options[selected_rfp_display]

            # Get selected RFP details
            selected_rfp = next(rfp for rfp in active_rfps if rfp['id'] == selected_rfp_id)

            # Show RFP details
            with st.expander("📋 RFP Details"):
                st.markdown(f"**Description:** {selected_rfp['description']}")

                # Show evaluation criteria
                if selected_rfp.get('evaluation_criteria'):
                    eval_criteria = selected_rfp['evaluation_criteria']
                    st.markdown("**Evaluation Criteria:**")
                    for category, details in eval_criteria.items():
                        if isinstance(details, dict):
                            st.write(f"• {category.replace('_', ' ').title()}: {details.get('weight', 0)}%")

        with col2:
            st.markdown("### Vendor Information")
            # Vendor selection or creation
            vendors = db.get_all_vendors()
            if vendors:
                vendor_options = {f"{v['name']} ({v['contact_email']})": v['id'] for v in vendors}
                vendor_options["➕ Add New Vendor"] = "new"
                selected_vendor_display = st.selectbox("Select Vendor*", list(vendor_options.keys()))
                selected_vendor_id = vendor_options[selected_vendor_display]

                if selected_vendor_id == "new":
                    # Inline vendor creation
                    st.markdown("**New Vendor Details:**")
                    new_vendor_name = st.text_input("Company Name*", key="new_vendor_name")
                    new_vendor_email = st.text_input("Contact Email*", key="new_vendor_email")
                    new_vendor_person = st.text_input("Contact Person", key="new_vendor_person")
                    new_vendor_phone = st.text_input("Phone", key="new_vendor_phone")
            else:
                selected_vendor_id = "new"
                st.info("No vendors in database. Please add vendor details below:")
                new_vendor_name = st.text_input("Company Name*")
                new_vendor_email = st.text_input("Contact Email*")
                new_vendor_person = st.text_input("Contact Person")
                new_vendor_phone = st.text_input("Phone")

        # Proposal details
        st.markdown("### Proposal Submission")
        col1, col2 = st.columns([2, 1])

        with col1:
            # File upload
            uploaded_file = st.file_uploader(
                "Upload Proposal Document*",
                type=['pdf', 'docx', 'doc', 'txt'],
                help="Upload the vendor's proposal document"
            )

            # Proposal summary
            proposal_summary = st.text_area(
                "Proposal Summary",
                placeholder="Brief summary of the proposal (will be auto-generated if left empty)",
                height=100
            )

        with col2:
            st.markdown("### Options")
            auto_analyze = st.checkbox("🤖 Use AI to analyze proposal", value=True)
            send_to_evaluation = st.checkbox("📊 Send to evaluation team", value=True)

            if auto_analyze:
                st.caption("AI will analyze the proposal against RFP criteria")
            if send_to_evaluation:
                st.caption("Team members will be notified for evaluation")

        # Submit button
        submitted = st.form_submit_button("📤 Submit Proposal", type="primary")

        if submitted:
            # Validation
            if not uploaded_file:
                st.error("Please upload a proposal document")
                return

            if selected_vendor_id == "new":
                if not new_vendor_name or not new_vendor_email:
                    st.error("Please provide vendor name and email")
                    return

            # Create vendor if new
            if selected_vendor_id == "new":
                vendor_data = {
                    "name": new_vendor_name,
                    "contact_email": new_vendor_email,
                    "contact_person": new_vendor_person,
                    "phone": new_vendor_phone,
                    "created_by": st.session_state.user.id
                }

                try:
                    new_vendor = db.create_vendor(vendor_data)
                    if new_vendor:
                        selected_vendor_id = new_vendor['id']
                        st.success(f"✅ Created new vendor: {new_vendor_name}")
                    else:
                        st.error("Failed to create vendor")
                        return
                except Exception as e:
                    st.error(f"Error creating vendor: {str(e)}")
                    return

            # Process file upload
            try:
                file_content = uploaded_file.read()

                # For now, we'll store the file content as base64 in the database
                # In production, you'd upload to cloud storage (S3, GCS, etc.)
                file_base64 = base64.b64encode(file_content).decode()
                file_url = f"data:{uploaded_file.type};base64,{file_base64}"

                # Extract text for AI analysis if needed
                proposal_text = ""
                if auto_analyze:
                    # Simple text extraction (in production, use proper PDF/Word parsers)
                    if uploaded_file.type == "text/plain":
                        proposal_text = file_content.decode('utf-8')
                    else:
                        proposal_text = f"File: {uploaded_file.name} ({uploaded_file.type})"

                # Generate AI summary if not provided
                if not proposal_summary and auto_analyze:
                    with st.spinner("🤖 Analyzing proposal..."):
                        ai = get_ai()
                        # Get RFP criteria for analysis
                        rfp_criteria = selected_rfp.get('evaluation_criteria', {})
                        analysis = ai.analyze_proposal(proposal_text, rfp_criteria)
                        proposal_summary = analysis if analysis else "AI analysis failed - please add manual summary"

                # Create proposal
                proposal_data = {
                    "rfp_id": selected_rfp_id,
                    "vendor_id": selected_vendor_id,
                    "proposal_file_url": file_url,
                    "proposal_summary": proposal_summary or f"Proposal from {vendors[0]['name'] if vendors else new_vendor_name}",
                    "created_by": st.session_state.user.id,
                    "status": "submitted"
                }

                new_proposal = db.create_proposal(proposal_data)

                if new_proposal:
                    st.success("🎉 Proposal submitted successfully!")

                    # Create evaluation records for team members if requested
                    if send_to_evaluation:
                        team_members = db.get_team_members(selected_rfp_id)
                        evaluators = [member for member in team_members if member.get('role') == 'evaluator']

                        for evaluator in evaluators:
                            evaluation_data = {
                                "proposal_id": new_proposal['id'],
                                "evaluator_id": evaluator['user_id'],
                                "status": "pending"
                            }
                            db.create_evaluation(evaluation_data)

                        st.info(f"📨 Evaluation requests sent to {len(evaluators)} team members")

                    # Update RFP status to evaluation if it was just published
                    if selected_rfp['status'] == 'published':
                        db.update_rfp(selected_rfp_id, {"status": "evaluation"})

                    st.rerun()
                else:
                    st.error("Failed to submit proposal")

            except Exception as e:
                st.error(f"Error processing proposal: {str(e)}")


def show_proposal_overview(active_rfps):
    """Overview of all proposals"""
    st.markdown("### 📊 Proposal Overview")

    db = get_db()

    # Get proposals for each RFP
    all_proposals = []
    for rfp in active_rfps:
        try:
            proposals = db.get_proposals_for_rfp(rfp['id'])
            for proposal in proposals:
                proposal['rfp_title'] = rfp['title']
            all_proposals.extend(proposals)
        except Exception as e:
            st.error(f"Error loading proposals for {rfp['title']}: {str(e)}")

    if not all_proposals:
        st.info("📭 No proposals submitted yet")
        return

    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Proposals", len(all_proposals))
    with col2:
        submitted_count = len([p for p in all_proposals if p['status'] == 'submitted'])
        st.metric("New Submissions", submitted_count)
    with col3:
        shortlisted_count = len([p for p in all_proposals if p['status'] == 'shortlisted'])
        st.metric("Shortlisted", shortlisted_count)
    with col4:
        under_review_count = len([p for p in all_proposals if p['status'] == 'under_review'])
        st.metric("Under Review", under_review_count)

    # Proposals table
    st.markdown("### Proposal List")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        rfp_filter = st.selectbox("Filter by RFP", ["All"] + [rfp['title'] for rfp in active_rfps])
    with col2:
        status_filter = st.selectbox("Filter by Status",
                                     ["All", "submitted", "under_review", "shortlisted", "rejected"])
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Apply filters
    filtered_proposals = all_proposals
    if rfp_filter != "All":
        filtered_proposals = [p for p in filtered_proposals if p['rfp_title'] == rfp_filter]
    if status_filter != "All":
        filtered_proposals = [p for p in filtered_proposals if p['status'] == status_filter]

    # Display proposals
    for proposal in filtered_proposals:
        with st.expander(
                f"📄 {proposal.get('rfp_title', 'Unknown RFP')} - {proposal.get('vendors', {}).get('name', 'Unknown Vendor')}"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"**Vendor:** {proposal.get('vendors', {}).get('name', 'Unknown')}")
                st.markdown(f"**Contact:** {proposal.get('vendors', {}).get('contact_email', 'No email')}")
                if proposal.get('proposal_summary'):
                    st.markdown(f"**Summary:** {proposal['proposal_summary'][:200]}...")
                st.caption(f"Submitted: {format_date(proposal.get('submitted_date', ''))}")

            with col2:
                current_status = proposal['status']
                status_color = {
                    'submitted': 'blue',
                    'under_review': 'orange',
                    'shortlisted': 'green',
                    'rejected': 'red'
                }.get(current_status, 'gray')

                st.markdown(
                    f'<span class="status-badge" style="background-color: {status_color};">{current_status.replace("_", " ").title()}</span>',
                    unsafe_allow_html=True
                )

                # Quick status change
                new_status = st.selectbox(
                    "Change Status",
                    ["submitted", "under_review", "shortlisted", "rejected"],
                    index=["submitted", "under_review", "shortlisted", "rejected"].index(current_status),
                    key=f"status_{proposal['id']}"
                )

                if new_status != current_status:
                    if st.button("Update", key=f"update_{proposal['id']}"):
                        try:
                            db.update_proposal(proposal['id'], {"status": new_status})
                            st.success("Status updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating status: {str(e)}")

            with col3:
                if st.button("📊 View Evaluations", key=f"eval_{proposal['id']}"):
                    st.session_state.proposal_id = proposal['id']
                    st.session_state.page = 'proposal_evaluations'
                    st.rerun()

                if proposal.get('proposal_file_url'):
                    if st.button("📁 Download", key=f"download_{proposal['id']}"):
                        # Handle file download
                        st.info("File download functionality - implementation depends on storage solution")


def show_proposal_details(active_rfps):
    """Detailed proposal analysis"""
    st.markdown("### 🔍 Detailed Proposal Analysis")

    db = get_db()

    # RFP selection for detailed analysis
    if active_rfps:
        rfp_options = {rfp['title']: rfp['id'] for rfp in active_rfps}
        selected_rfp_title = st.selectbox("Select RFP for Analysis", list(rfp_options.keys()))
        selected_rfp_id = rfp_options[selected_rfp_title]

        # Get proposals for selected RFP
        try:
            proposals = db.get_proposals_for_rfp(selected_rfp_id)
        except Exception as e:
            st.error(f"Error loading proposals: {str(e)}")
            proposals = []

        if not proposals:
            st.info(f"📭 No proposals submitted for '{selected_rfp_title}' yet")
            return

        # Show detailed analysis
        st.markdown(f"### Analysis for: {selected_rfp_title}")

        # Get evaluation data
        proposal_scores = []
        for proposal in proposals:
            try:
                evaluations = db.get_evaluations_for_proposal(proposal['id'])

                if evaluations:
                    # Calculate average scores
                    total_functional = sum(
                        [e.get('functional_score', 0) for e in evaluations if e.get('functional_score')])
                    total_security = sum(
                        [e.get('it_security_score', 0) for e in evaluations if e.get('it_security_score')])
                    total_business = sum([e.get('business_score', 0) for e in evaluations if e.get('business_score')])
                    total_overall = sum([e.get('overall_score', 0) for e in evaluations if e.get('overall_score')])
                    eval_count = len([e for e in evaluations if e.get('status') == 'completed'])

                    if eval_count > 0:
                        proposal_scores.append({
                            'vendor': proposal.get('vendors', {}).get('name', 'Unknown'),
                            'functional': total_functional / eval_count,
                            'security': total_security / eval_count,
                            'business': total_business / eval_count,
                            'overall': total_overall / eval_count,
                            'evaluations': eval_count,
                            'status': proposal['status']
                        })
                    else:
                        proposal_scores.append({
                            'vendor': proposal.get('vendors', {}).get('name', 'Unknown'),
                            'functional': 0,
                            'security': 0,
                            'business': 0,
                            'overall': 0,
                            'evaluations': 0,
                            'status': proposal['status']
                        })
                else:
                    proposal_scores.append({
                        'vendor': proposal.get('vendors', {}).get('name', 'Unknown'),
                        'functional': 0,
                        'security': 0,
                        'business': 0,
                        'overall': 0,
                        'evaluations': 0,
                        'status': proposal['status']
                    })
            except Exception as e:
                st.error(f"Error loading evaluations: {str(e)}")

        # Display scores table
        if proposal_scores:
            import pandas as pd
            df = pd.DataFrame(proposal_scores)
            st.markdown("#### Evaluation Summary")
            st.dataframe(df, use_container_width=True)

            # Simple chart
            if len([p for p in proposal_scores if p['evaluations'] > 0]) > 0:
                st.markdown("#### Overall Scores Comparison")
                chart_data = pd.DataFrame([
                    {'Vendor': p['vendor'], 'Overall Score': p['overall']}
                    for p in proposal_scores if p['evaluations'] > 0
                ])
                if not chart_data.empty:
                    st.bar_chart(chart_data.set_index('Vendor'))
            else:
                st.info("📊 No completed evaluations yet for detailed analysis")
        else:
            st.info("📊 No evaluation data available")
    else:
        st.info("📋 No active RFPs available for analysis")


def show_proposal_evaluations():
    """Show evaluation details for a specific proposal with comprehensive scorecard"""
    if not st.session_state.get('proposal_id'):
        st.error("No proposal selected")
        return

    st.markdown('<h1 class="main-header">📊 Proposal Evaluations</h1>', unsafe_allow_html=True)

    db = get_db()
    proposal_id = st.session_state.proposal_id

    # Get proposal details first
    try:
        # We need to get the proposal details - for now we'll get evaluations and work backwards
        evaluations = db.get_evaluations_for_proposal(proposal_id)

        if not evaluations:
            st.info("📭 No evaluations submitted yet")
            if st.button("← Back to Proposals"):
                st.session_state.page = 'proposals'
                st.session_state.proposal_id = None
                st.rerun()
            return

        # Get basic proposal info from first evaluation (we need to improve this)
        # For now, let's create a comprehensive view with what we have

        # Calculate aggregated scores
        completed_evaluations = [e for e in evaluations if e.get('status') == 'completed']

        if completed_evaluations:
            # Calculate averages
            avg_functional = sum(e.get('functional_score', 0) for e in completed_evaluations) / len(
                completed_evaluations)
            avg_security = sum(e.get('it_security_score', 0) for e in completed_evaluations) / len(
                completed_evaluations)
            avg_business = sum(e.get('business_score', 0) for e in completed_evaluations) / len(completed_evaluations)
            avg_overall = sum(e.get('overall_score', 0) for e in completed_evaluations) / len(completed_evaluations)

            # Count recommendations
            recommend_count = sum(1 for e in completed_evaluations if e.get('recommendation') == 'recommend')
            conditional_count = sum(1 for e in completed_evaluations if e.get('recommendation') == 'conditional')
            not_recommend_count = sum(1 for e in completed_evaluations if e.get('recommendation') == 'not_recommend')

            # Show comprehensive scorecard
            st.markdown("### 🏆 Proposal Scorecard")

            # Overall summary cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Score", f"{avg_overall:.1f}/100",
                          delta=f"{avg_overall - 50:.1f}" if avg_overall > 50 else f"{avg_overall - 50:.1f}")
            with col2:
                total_evaluations = len(completed_evaluations)
                st.metric("Completed Evaluations", f"{total_evaluations}/{len(evaluations)}")
            with col3:
                recommend_rate = (recommend_count / len(completed_evaluations)) * 100
                st.metric("Recommendation Rate", f"{recommend_rate:.0f}%")
            with col4:
                # Overall status based on scores and recommendations
                if avg_overall >= 70 and recommend_count > not_recommend_count:
                    status = "🟢 Strong Candidate"
                elif avg_overall >= 50 and recommend_count >= not_recommend_count:
                    status = "🟡 Conditional"
                else:
                    status = "🔴 Not Recommended"

                # Fix the logic - if we have more recommends than not recommends, it should be positive
                if recommend_count > not_recommend_count:
                    if avg_overall >= 70:
                        status = "🟢 Strong Candidate"
                    else:
                        status = "🟡 Conditional"
                elif recommend_count == not_recommend_count:
                    status = "🟡 Conditional"
                else:
                    status = "🔴 Not Recommended"

                st.metric("Status", status)

            # Detailed score breakdown
            st.markdown("### 📊 Score Breakdown")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Average Scores by Category")
                score_data = {
                    'Category': ['Functional', 'IT Security', 'Business', 'Overall'],
                    'Score': [avg_functional, avg_security, avg_business, avg_overall],
                    'Color': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                }

                # Simple bar chart using Streamlit
                import pandas as pd
                df = pd.DataFrame({
                    'Category': score_data['Category'],
                    'Score': score_data['Score']
                })
                st.bar_chart(df.set_index('Category'))

                # Show detailed breakdown
                st.markdown("**Detailed Scores:**")
                st.write(f"🔧 **Functional:** {avg_functional:.1f}/100")
                st.write(f"🔒 **IT Security:** {avg_security:.1f}/100")
                st.write(f"💼 **Business:** {avg_business:.1f}/100")
                st.write(f"🎯 **Overall:** {avg_overall:.1f}/100")

            with col2:
                st.markdown("#### Recommendation Summary")

                # Recommendation pie chart data
                rec_data = {
                    'Recommendation': ['Recommend', 'Conditional', 'Not Recommend'],
                    'Count': [recommend_count, conditional_count, not_recommend_count]
                }
                rec_df = pd.DataFrame(rec_data)
                rec_df = rec_df[rec_df['Count'] > 0]  # Only show non-zero values

                if not rec_df.empty:
                    st.bar_chart(rec_df.set_index('Recommendation'))

                st.markdown("**Recommendation Breakdown:**")
                st.write(f"✅ **Recommend:** {recommend_count}")
                st.write(f"⚠️ **Conditional:** {conditional_count}")
                st.write(f"❌ **Not Recommend:** {not_recommend_count}")

                # Decision helper
                st.markdown("**Decision Guidance:**")
                if recommend_count > not_recommend_count and avg_overall >= 70:
                    st.success("🎯 **Strong candidate for selection**")
                elif recommend_count > not_recommend_count and avg_overall >= 50:
                    st.success("✅ **Good candidate - recommended for selection**")
                elif recommend_count >= not_recommend_count and avg_overall >= 50:
                    st.warning("⚠️ **Proceed with caution - review conditions**")
                else:
                    st.error("❌ **Consider rejecting or requesting improvements**")

        # Individual evaluations section
        st.markdown("### 👥 Individual Evaluations")

        if completed_evaluations:
            for i, evaluation in enumerate(completed_evaluations):
                evaluator_info = evaluation.get('user_profiles', {})

                with st.expander(
                        f"📝 Evaluation #{i + 1} by {evaluator_info.get('full_name', 'Unknown')} ({evaluator_info.get('role', 'Unknown')})"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Individual Scores:**")
                        st.write(f"Functional: {evaluation.get('functional_score', 'Not scored')}/100")
                        st.write(f"IT Security: {evaluation.get('it_security_score', 'Not scored')}/100")
                        st.write(f"Business: {evaluation.get('business_score', 'Not scored')}/100")
                        st.write(f"**Overall: {evaluation.get('overall_score', 'Not scored')}/100**")

                    with col2:
                        st.markdown("**Recommendation & Status:**")
                        rec = evaluation.get('recommendation', 'Not provided')
                        rec_color = {'recommend': 'green', 'conditional': 'orange', 'not_recommend': 'red'}.get(rec,
                                                                                                                'gray')
                        st.markdown(
                            f'<span style="color: {rec_color}; font-weight: bold;">{rec.replace("_", " ").title()}</span>',
                            unsafe_allow_html=True)

                        status = evaluation.get('status', 'pending')
                        st.write(f"Status: {status.title()}")
                        if evaluation.get('submitted_at'):
                            st.caption(f"Submitted: {format_date(evaluation['submitted_at'])}")

                    # Show comments if available
                    st.markdown("**Comments:**")
                    comments_shown = False

                    if evaluation.get('functional_comments'):
                        st.write(f"**Functional:** {evaluation['functional_comments']}")
                        comments_shown = True
                    if evaluation.get('it_security_comments'):
                        st.write(f"**Security:** {evaluation['it_security_comments']}")
                        comments_shown = True
                    if evaluation.get('business_comments'):
                        st.write(f"**Business:** {evaluation['business_comments']}")
                        comments_shown = True
                    if evaluation.get('overall_comments'):
                        st.write(f"**Overall:** {evaluation['overall_comments']}")
                        comments_shown = True

                    if not comments_shown:
                        st.write("No detailed comments provided.")

        # Pending evaluations
        pending_evaluations = [e for e in evaluations if e.get('status') == 'pending']
        if pending_evaluations:
            st.markdown("### ⏳ Pending Evaluations")
            st.warning(f"⚠️ {len(pending_evaluations)} evaluations still pending completion")

            for evaluation in pending_evaluations:
                evaluator_info = evaluation.get('user_profiles', {})
                st.write(f"• {evaluator_info.get('full_name', 'Unknown')} ({evaluator_info.get('role', 'Unknown')})")

        # Action buttons for procurement manager
        st.markdown("### 🎯 Actions")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("← Back to Proposals"):
                st.session_state.page = 'proposals'
                st.session_state.proposal_id = None
                st.rerun()

        with col2:
            if len(completed_evaluations) == len(evaluations) and len(completed_evaluations) > 0:
                if st.button("📋 Send for Approval", type="primary"):
                    # Move proposal to approval workflow
                    try:
                        # Get current proposal data to preserve the existing summary
                        current_proposals = db.get_proposals_for_rfp(
                            "dummy")  # We need a better way to get proposal by ID
                        # For now, let's use a simple approach
                        current_summary = "Proposal ready for approval"
                        approval_note = "[PENDING_APPROVAL] " + current_summary

                        db.update_proposal(proposal_id, {
                            "status": "under_review",
                            "proposal_summary": approval_note
                        })

                        st.success("🎉 Proposal sent for final approval!")
                        st.info("Department heads will be notified to review the evaluation results.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error sending for approval: {str(e)}")
            else:
                st.info("All evaluations must be completed before sending for approval")

        with col3:
            # Option to request additional evaluation
            if st.button("👥 Request More Evaluations"):
                st.info("Feature to add more evaluators - Coming soon")

        with col4:
            # Download report option
            if st.button("📥 Download Report"):
                st.info("Report download feature - Coming soon")

    except Exception as e:
        st.error(f"Error loading evaluations: {str(e)}")
        if st.button("← Back to Proposals"):
            st.session_state.page = 'proposals'
            st.session_state.proposal_id = None
            st.rerun()