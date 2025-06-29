import streamlit as st
from config import get_db, get_ai, format_date
from datetime import datetime


def show_evaluations_page():
    """Main evaluations page for team members"""
    st.markdown('<h1 class="main-header">📊 My Evaluations</h1>', unsafe_allow_html=True)

    db = get_db()
    user_id = st.session_state.user.id

    # Get pending evaluations for user
    try:
        pending_evaluations = db.get_pending_evaluations_for_user(user_id)
    except Exception as e:
        st.error(f"Error loading evaluations: {str(e)}")
        pending_evaluations = []

    # Show statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pending Evaluations", len(pending_evaluations))

    with col2:
        # Count completed evaluations (all evaluations where user is evaluator and status is completed)
        try:
            all_user_evaluations = []  # We'd need a method to get all user evaluations
            completed_count = 0  # Placeholder
            st.metric("Completed This Month", completed_count)
        except:
            st.metric("Completed This Month", "N/A")

    with col3:
        # Average score given (placeholder)
        st.metric("Average Score Given", "N/A")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["⏳ Pending", "✅ Completed", "📈 My Performance"])

    with tab1:
        show_pending_evaluations(pending_evaluations)

    with tab2:
        show_completed_evaluations(user_id)

    with tab3:
        show_evaluation_performance(user_id)


def show_pending_evaluations(pending_evaluations):
    """Show pending evaluations for the user"""
    st.markdown("### ⏳ Pending Evaluations")

    if not pending_evaluations:
        st.info("🎉 No pending evaluations! You're all caught up.")
        return

    db = get_db()

    for evaluation in pending_evaluations:
        # For now, we'll work with basic evaluation data
        # In a full implementation, you'd have proposal and RFP details in the query

        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**Evaluation Request**")
                st.write(f"Proposal ID: {evaluation.get('proposal_id', 'Unknown')}")
                st.caption(f"Assigned: {format_date(evaluation.get('created_at', ''))}")

            with col2:
                st.write("⏳ Pending")

            with col3:
                if st.button("📝 Start Evaluation", key=f"eval_{evaluation['id']}"):
                    st.session_state.evaluation_id = evaluation['id']
                    st.session_state.proposal_id = evaluation['proposal_id']
                    st.session_state.page = 'evaluate_proposal'
                    st.rerun()

            st.markdown("---")


def show_completed_evaluations(user_id):
    """Show completed evaluations by the user"""
    st.markdown("### ✅ Completed Evaluations")
    st.info("Completed evaluations view - Coming in next update")


def show_evaluation_performance(user_id):
    """Show user's evaluation performance metrics"""
    st.markdown("### 📈 My Evaluation Performance")
    st.info("Performance analytics - Coming in next update")


def show_evaluate_proposal_page():
    """Comprehensive proposal evaluation form"""
    if not st.session_state.get('proposal_id') or not st.session_state.get('evaluation_id'):
        st.error("No proposal or evaluation selected")
        return

    st.markdown('<h1 class="main-header">📝 Evaluate Proposal</h1>', unsafe_allow_html=True)

    db = get_db()
    proposal_id = st.session_state.proposal_id
    evaluation_id = st.session_state.evaluation_id

    # Get evaluation details
    try:
        evaluation = db.get_evaluation(proposal_id, st.session_state.user.id)
        if not evaluation:
            st.error("Evaluation not found")
            return
    except Exception as e:
        st.error(f"Error loading evaluation: {str(e)}")
        return

    # Get RFP details for criteria (simplified for now)
    try:
        # We'll need to get RFP details through the proposal
        # For now, we'll use default criteria
        evaluation_criteria = {
            "functional": {"weight": 40, "criteria": "Technical capabilities and feature requirements"},
            "it_security": {"weight": 30, "criteria": "Security standards, compliance, and data protection"},
            "business": {"weight": 30, "criteria": "Cost, timeline, company stability, and references"}
        }
    except:
        # Default criteria
        evaluation_criteria = {
            "functional": {"weight": 40, "criteria": "Technical capabilities"},
            "it_security": {"weight": 30, "criteria": "Security requirements"},
            "business": {"weight": 30, "criteria": "Business requirements"}
        }

    # Show proposal info (simplified)
    with st.expander("📄 Proposal Information"):
        st.write(f"**Proposal ID:** {proposal_id}")
        st.write("**Vendor:** Unknown")  # We'd get this from a proper query
        st.write("**RFP:** Unknown")  # We'd get this from a proper query
        st.info("Full proposal details would be shown here in a complete implementation")

    # Evaluation form
    with st.form(f"evaluation_form_{evaluation_id}"):
        st.markdown("### 📊 Evaluation Criteria")

        # Get existing scores if any
        existing_functional = evaluation.get('functional_score', 0)
        existing_security = evaluation.get('it_security_score', 0)
        existing_business = evaluation.get('business_score', 0)
        existing_overall = evaluation.get('overall_score', 0)
        existing_recommendation = evaluation.get('recommendation', 'recommend')
        existing_comments = evaluation.get('overall_comments', '')

        # Functional evaluation
        st.markdown("#### 🔧 Functional Requirements")
        col1, col2 = st.columns([1, 3])

        with col1:
            functional_score = st.slider(
                "Functional Score",
                0, 100, existing_functional,
                help=f"Weight: {evaluation_criteria['functional']['weight']}%"
            )

        with col2:
            st.markdown(f"**Criteria:** {evaluation_criteria['functional']['criteria']}")
            functional_comments = st.text_area(
                "Functional Comments",
                value=evaluation.get('functional_comments', ''),
                placeholder="Evaluate technical capabilities, feature completeness, etc.",
                key="func_comments"
            )

        # IT Security evaluation
        st.markdown("#### 🔒 IT Security")
        col1, col2 = st.columns([1, 3])

        with col1:
            security_score = st.slider(
                "Security Score",
                0, 100, existing_security,
                help=f"Weight: {evaluation_criteria['it_security']['weight']}%"
            )

        with col2:
            st.markdown(f"**Criteria:** {evaluation_criteria['it_security']['criteria']}")
            security_comments = st.text_area(
                "Security Comments",
                value=evaluation.get('it_security_comments', ''),
                placeholder="Evaluate security measures, compliance, data protection, etc.",
                key="sec_comments"
            )

        # Business evaluation
        st.markdown("#### 💼 Business Requirements")
        col1, col2 = st.columns([1, 3])

        with col1:
            business_score = st.slider(
                "Business Score",
                0, 100, existing_business,
                help=f"Weight: {evaluation_criteria['business']['weight']}%"
            )

        with col2:
            st.markdown(f"**Criteria:** {evaluation_criteria['business']['criteria']}")
            business_comments = st.text_area(
                "Business Comments",
                value=evaluation.get('business_comments', ''),
                placeholder="Evaluate cost, timeline, company stability, references, etc.",
                key="biz_comments"
            )

        # Calculate weighted overall score
        functional_weight = evaluation_criteria['functional']['weight'] / 100
        security_weight = evaluation_criteria['it_security']['weight'] / 100
        business_weight = evaluation_criteria['business']['weight'] / 100

        calculated_overall = int(
            (functional_score * functional_weight) +
            (security_score * security_weight) +
            (business_score * business_weight)
        )

        # Overall evaluation
        st.markdown("#### 🎯 Overall Assessment")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Calculated Score", f"{calculated_overall}/100")
            overall_score = st.slider(
                "Final Overall Score",
                0, 100, calculated_overall,
                help="You can adjust the calculated score if needed"
            )

            recommendation = st.selectbox(
                "Recommendation",
                ["recommend", "conditional", "not_recommend"],
                index=["recommend", "conditional", "not_recommend"].index(
                    existing_recommendation) if existing_recommendation in ["recommend", "conditional",
                                                                            "not_recommend"] else 0,
                format_func=lambda x: {
                    "recommend": "✅ Recommend",
                    "conditional": "⚠️ Conditional",
                    "not_recommend": "❌ Not Recommend"
                }[x]
            )

        with col2:
            overall_comments = st.text_area(
                "Overall Comments & Rationale",
                value=existing_comments,
                placeholder="Provide your overall assessment, key strengths, concerns, and recommendation rationale...",
                height=150
            )

        # AI assistance (move outside form)
        # st.markdown("#### 🤖 AI Assistance")
        # with st.expander("Get AI suggestions for evaluation"):
        #     if st.button("🔍 Generate Evaluation Questions"):
        #         ai = get_ai()
        #         st.info("AI-generated evaluation questions would appear here")
        #
        #     if st.button("📊 Analyze Proposal"):
        #         st.info("AI proposal analysis would appear here")

        # Form submission
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)

        with col2:
            submit_evaluation = st.form_submit_button("✅ Submit Evaluation", type="primary", use_container_width=True)

        with col3:
            cancel_evaluation = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancel_evaluation:
            st.session_state.page = 'evaluations'
            st.session_state.evaluation_id = None
            st.session_state.proposal_id = None
            st.rerun()

        if save_draft or submit_evaluation:
            # Prepare evaluation data
            evaluation_updates = {
                "functional_score": functional_score,
                "functional_comments": functional_comments,
                "it_security_score": security_score,
                "it_security_comments": security_comments,
                "business_score": business_score,
                "business_comments": business_comments,
                "overall_score": overall_score,
                "overall_comments": overall_comments,
                "recommendation": recommendation,
                "status": "completed" if submit_evaluation else "pending"
            }

            if submit_evaluation:
                evaluation_updates["submitted_at"] = datetime.now().isoformat()

            # Update evaluation
            try:
                updated_evaluation = db.update_evaluation(evaluation_id, evaluation_updates)
                if updated_evaluation:
                    if submit_evaluation:
                        st.success("🎉 Evaluation submitted successfully!")

                        # Update proposal status to under review
                        db.update_proposal(proposal_id, {"status": "under_review"})

                        # Check if all evaluations are complete for this proposal
                        all_evaluations = db.get_evaluations_for_proposal(proposal_id)
                        completed_evaluations = [e for e in all_evaluations if e.get('status') == 'completed']

                        if len(completed_evaluations) == len(all_evaluations):
                            st.info("✅ All evaluations completed for this proposal!")
                    else:
                        st.success("💾 Evaluation draft saved!")

                    # Navigate back
                    st.session_state.page = 'evaluations'
                    st.session_state.evaluation_id = None
                    st.session_state.proposal_id = None
                    st.rerun()
                else:
                    st.error("Failed to save evaluation")
            except Exception as e:
                st.error(f"Error saving evaluation: {str(e)}")


def show_pending_tasks_page():
    """Show pending tasks for evaluators"""
    st.markdown('<h1 class="main-header">📋 Pending Tasks</h1>', unsafe_allow_html=True)

    db = get_db()
    user_id = st.session_state.user.id

    # Get pending evaluations
    try:
        pending_evaluations = db.get_pending_evaluations_for_user(user_id)
    except Exception as e:
        st.error(f"Error loading tasks: {str(e)}")
        pending_evaluations = []

    # Quick stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("⏳ Pending Evaluations", len(pending_evaluations))

    with col2:
        st.metric("📅 Due Today", 0)  # Placeholder - would calculate based on due dates

    with col3:
        st.metric("🔴 Overdue", 0)  # Placeholder - would calculate based on due dates

    # Tasks list
    if pending_evaluations:
        st.markdown("### Your Pending Tasks")

        for evaluation in pending_evaluations:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown("**📝 Proposal Evaluation**")
                    st.write(f"Proposal ID: {evaluation.get('proposal_id', 'Unknown')}")
                    st.caption(f"Assigned: {format_date(evaluation.get('created_at', ''))}")

                with col2:
                    st.write("🔴 High Priority")  # Could be dynamic based on due dates

                with col3:
                    if st.button("📝 Evaluate", key=f"task_eval_{evaluation['id']}"):
                        st.session_state.evaluation_id = evaluation['id']
                        st.session_state.proposal_id = evaluation['proposal_id']
                        st.session_state.page = 'evaluate_proposal'
                        st.rerun()

                st.markdown("---")
    else:
        st.success("🎉 No pending tasks! You're all caught up.")

        # Show some helpful actions
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