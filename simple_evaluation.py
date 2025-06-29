import streamlit as st
from config import get_db, format_date
from datetime import datetime


def show_simple_evaluate_proposal_page():
    """Simplified proposal evaluation form - minimal working version"""

    if not st.session_state.get('proposal_id') or not st.session_state.get('evaluation_id'):
        st.error("No proposal or evaluation selected")
        return

    st.markdown('<h1 class="main-header">📝 Evaluate Proposal (Simple)</h1>', unsafe_allow_html=True)

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

    # Show proposal info
    with st.expander("📄 Proposal Information", expanded=True):
        st.write(f"**Proposal ID:** {proposal_id}")
        st.write(f"**Evaluation ID:** {evaluation_id}")
        st.info("Full proposal details would be shown here in a complete implementation")

    # Simple evaluation form
    st.markdown("### 📊 Simple Evaluation Form")

    with st.form(f"simple_evaluation_form_{evaluation_id}"):
        st.markdown("**Score each category from 0-100:**")

        # Get existing scores
        existing_functional = evaluation.get('functional_score', 50)
        existing_security = evaluation.get('it_security_score', 50)
        existing_business = evaluation.get('business_score', 50)
        existing_overall = evaluation.get('overall_score', 50)
        existing_recommendation = evaluation.get('recommendation', 'recommend')
        existing_comments = evaluation.get('overall_comments', '')

        # Simple scoring
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🔧 Functional")
            functional_score = st.slider("Technical Score", 0, 100, existing_functional)
            functional_comments = st.text_area("Technical Notes", value=evaluation.get('functional_comments', ''),
                                               height=100)

        with col2:
            st.markdown("#### 🔒 Security")
            security_score = st.slider("Security Score", 0, 100, existing_security)
            security_comments = st.text_area("Security Notes", value=evaluation.get('it_security_comments', ''),
                                             height=100)

        with col3:
            st.markdown("#### 💼 Business")
            business_score = st.slider("Business Score", 0, 100, existing_business)
            business_comments = st.text_area("Business Notes", value=evaluation.get('business_comments', ''),
                                             height=100)

        # Overall assessment
        st.markdown("#### 🎯 Overall Assessment")

        # Calculate simple average
        calculated_overall = int((functional_score + security_score + business_score) / 3)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Calculated Average", f"{calculated_overall}/100")
            overall_score = st.slider("Final Overall Score", 0, 100, calculated_overall)

            # Simple recommendation dropdown
            recommendation_options = ["recommend", "conditional", "not_recommend"]
            try:
                if existing_recommendation in recommendation_options:
                    rec_index = recommendation_options.index(existing_recommendation)
                else:
                    rec_index = 0
            except:
                rec_index = 0

            recommendation = st.selectbox(
                "Recommendation",
                recommendation_options,
                index=rec_index,
                format_func=lambda x: {
                    "recommend": "✅ Recommend",
                    "conditional": "⚠️ Conditional",
                    "not_recommend": "❌ Not Recommend"
                }.get(x, x)
            )

        with col2:
            overall_comments = st.text_area(
                "Overall Comments",
                value=existing_comments,
                height=150,
                placeholder="Your overall assessment and recommendation rationale..."
            )

        # Form submission buttons
        st.markdown("#### 📤 Submit Evaluation")

        col1, col2, col3 = st.columns(3)

        with col1:
            save_draft = st.form_submit_button("💾 Save Draft", use_container_width=True)

        with col2:
            submit_evaluation = st.form_submit_button("✅ Submit Final", type="primary", use_container_width=True)

        with col3:
            cancel_evaluation = st.form_submit_button("❌ Cancel", use_container_width=True)

        # Handle form submission
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

                        # Update proposal status
                        try:
                            db.update_proposal(proposal_id, {"status": "under_review"})
                        except:
                            pass  # Don't fail if this doesn't work

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

    # Help section outside the form
    st.markdown("---")
    st.markdown("### 💡 Evaluation Tips")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **Scoring Guidelines:**
        - 90-100: Excellent, exceeds requirements
        - 70-89: Good, meets requirements well  
        - 50-69: Acceptable, meets basic requirements
        - 30-49: Poor, below requirements
        - 0-29: Unacceptable
        """)

    with col2:
        st.info("""
        **Recommendation Guidelines:**
        - ✅ **Recommend**: Strong proposal, should proceed
        - ⚠️ **Conditional**: Good with reservations
        - ❌ **Not Recommend**: Does not meet needs
        """)