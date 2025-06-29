import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import get_db, format_date
from datetime import datetime, timedelta


def show_reports_page():
    """Comprehensive analytics and reporting dashboard"""
    st.markdown('<h1 class="main-header">📈 Analytics & Reports</h1>', unsafe_allow_html=True)

    db = get_db()
    user_id = st.session_state.user.id

    # Get user's RFPs for analysis
    try:
        rfps = db.get_rfps_for_user(user_id)
    except Exception as e:
        st.error(f"Error loading RFPs: {str(e)}")
        rfps = []

    if not rfps:
        st.info("📊 No RFPs available for analysis. Create some RFPs first!")
        return

    # Tabs for different report types
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🏆 Evaluation Results",
        "📋 RFP Performance",
        "🏢 Vendor Analysis",
        "📑 Export Reports"
    ])

    with tab1:
        show_overview_analytics(rfps)

    with tab2:
        show_evaluation_analytics(rfps)

    with tab3:
        show_rfp_performance(rfps)

    with tab4:
        show_vendor_analytics(rfps)

    with tab5:
        show_export_options(rfps)


def show_overview_analytics(rfps):
    """High-level overview analytics"""
    st.markdown("### 📊 Procurement Overview")

    db = get_db()

    # Calculate summary statistics
    total_rfps = len(rfps)
    active_rfps = len([rfp for rfp in rfps if rfp['status'] in ['published', 'evaluation']])
    completed_rfps = len([rfp for rfp in rfps if rfp['status'] == 'completed'])
    draft_rfps = len([rfp for rfp in rfps if rfp['status'] == 'draft'])

    # Get total proposals across all RFPs
    total_proposals = 0
    shortlisted_proposals = 0

    for rfp in rfps:
        try:
            proposals = db.get_proposals_for_rfp(rfp['id'])
            total_proposals += len(proposals)
            shortlisted_proposals += len([p for p in proposals if p['status'] == 'shortlisted'])
        except:
            continue

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total RFPs", total_rfps)

    with col2:
        st.metric("Active RFPs", active_rfps)

    with col3:
        st.metric("Total Proposals", total_proposals)

    with col4:
        completion_rate = round((completed_rfps / total_rfps * 100) if total_rfps > 0 else 0, 1)
        st.metric("Completion Rate", f"{completion_rate}%")

    # RFP Status Distribution
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### RFP Status Distribution")
        status_counts = {}
        for rfp in rfps:
            status = rfp['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        if status_counts:
            # Create pie chart
            fig = px.pie(
                values=list(status_counts.values()),
                names=[s.replace('_', ' ').title() for s in status_counts.keys()],
                title="RFP Status Breakdown"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    with col2:
        st.markdown("#### Proposal Status Distribution")
        proposal_statuses = {'submitted': 0, 'under_review': 0, 'shortlisted': 0, 'rejected': 0}

        for rfp in rfps:
            try:
                proposals = db.get_proposals_for_rfp(rfp['id'])
                for proposal in proposals:
                    status = proposal['status']
                    if status in proposal_statuses:
                        proposal_statuses[status] += 1
            except:
                continue

        if sum(proposal_statuses.values()) > 0:
            fig = px.pie(
                values=list(proposal_statuses.values()),
                names=[s.replace('_', ' ').title() for s in proposal_statuses.keys()],
                title="Proposal Status Breakdown"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No proposals to analyze")

    # Recent Activity Timeline
    st.markdown("#### Recent Activity")

    # Create timeline data
    timeline_data = []
    for rfp in rfps:
        timeline_data.append({
            'Date': rfp['created_at'][:10] if rfp['created_at'] else 'Unknown',
            'Event': f"RFP Created: {rfp['title']}",
            'Type': 'RFP Created'
        })

        if rfp.get('due_date'):
            timeline_data.append({
                'Date': rfp['due_date'][:10],
                'Event': f"RFP Due: {rfp['title']}",
                'Type': 'RFP Due'
            })

    if timeline_data:
        df = pd.DataFrame(timeline_data)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date', ascending=False).head(10)

        # Display as a simple table
        st.dataframe(df[['Date', 'Event', 'Type']], use_container_width=True)
    else:
        st.info("No recent activity to display")


def show_evaluation_analytics(rfps):
    """Detailed evaluation results and analysis"""
    st.markdown("### 🏆 Evaluation Results Analysis")

    db = get_db()

    # RFP selector for detailed analysis
    if len(rfps) > 1:
        rfp_options = {rfp['title']: rfp['id'] for rfp in rfps}
        selected_rfp_title = st.selectbox("Select RFP for Detailed Analysis", ["All RFPs"] + list(rfp_options.keys()))

        if selected_rfp_title == "All RFPs":
            selected_rfps = rfps
        else:
            selected_rfp_id = rfp_options[selected_rfp_title]
            selected_rfps = [rfp for rfp in rfps if rfp['id'] == selected_rfp_id]
    else:
        selected_rfps = rfps

    # Collect evaluation data
    evaluation_data = []

    for rfp in selected_rfps:
        try:
            proposals = db.get_proposals_for_rfp(rfp['id'])

            for proposal in proposals:
                try:
                    evaluations = db.get_evaluations_for_proposal(proposal['id'])

                    for evaluation in evaluations:
                        if evaluation.get('status') == 'completed':
                            evaluation_data.append({
                                'RFP': rfp['title'],
                                'Vendor': proposal.get('vendors', {}).get('name', 'Unknown'),
                                'Evaluator': evaluation.get('user_profiles', {}).get('full_name', 'Unknown'),
                                'Functional': evaluation.get('functional_score', 0),
                                'Security': evaluation.get('it_security_score', 0),
                                'Business': evaluation.get('business_score', 0),
                                'Overall': evaluation.get('overall_score', 0),
                                'Recommendation': evaluation.get('recommendation', 'not_recommend'),
                                'Submitted': evaluation.get('submitted_at', '')
                            })
                except:
                    continue
        except:
            continue

    if not evaluation_data:
        st.info("📊 No completed evaluations available for analysis")
        return

    # Convert to DataFrame
    df = pd.DataFrame(evaluation_data)

    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Evaluations", len(df))

    with col2:
        avg_score = round(df['Overall'].mean(), 1) if len(df) > 0 else 0
        st.metric("Average Score", f"{avg_score}/100")

    with col3:
        recommended = len(df[df['Recommendation'] == 'recommend'])
        st.metric("Recommended", recommended)

    with col4:
        unique_vendors = df['Vendor'].nunique()
        st.metric("Vendors Evaluated", unique_vendors)

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Overall Scores by Vendor")
        if len(df) > 0:
            vendor_scores = df.groupby('Vendor')['Overall'].mean().reset_index()
            vendor_scores = vendor_scores.sort_values('Overall', ascending=False)

            fig = px.bar(
                vendor_scores,
                x='Vendor',
                y='Overall',
                title="Average Overall Scores",
                color='Overall',
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Score Distribution by Category")
        if len(df) > 0:
            # Melt the dataframe for category comparison
            score_cols = ['Functional', 'Security', 'Business', 'Overall']
            df_melted = df[score_cols].melt(var_name='Category', value_name='Score')

            fig = px.box(
                df_melted,
                x='Category',
                y='Score',
                title="Score Distribution by Category"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Recommendation Analysis
    st.markdown("#### Recommendation Analysis")

    col1, col2 = st.columns(2)

    with col1:
        recommendation_counts = df['Recommendation'].value_counts()

        fig = px.pie(
            values=recommendation_counts.values,
            names=[r.replace('_', ' ').title() for r in recommendation_counts.index],
            title="Recommendation Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top performing vendors
        st.markdown("**Top Performing Vendors:**")

        if len(df) > 0:
            vendor_performance = df.groupby('Vendor').agg({
                'Overall': 'mean',
                'Recommendation': lambda x: (x == 'recommend').sum() / len(x) * 100
            }).round(2)

            vendor_performance.columns = ['Avg Score', 'Recommend %']
            vendor_performance = vendor_performance.sort_values('Avg Score', ascending=False)

            st.dataframe(vendor_performance, use_container_width=True)

    # Detailed evaluation table
    st.markdown("#### Detailed Evaluation Results")

    # Add filters
    col1, col2, col3 = st.columns(3)

    with col1:
        vendor_filter = st.selectbox("Filter by Vendor", ["All"] + list(df['Vendor'].unique()))

    with col2:
        rec_filter = st.selectbox("Filter by Recommendation", ["All", "recommend", "conditional", "not_recommend"])

    with col3:
        min_score = st.slider("Minimum Overall Score", 0, 100, 0)

    # Apply filters
    filtered_df = df.copy()

    if vendor_filter != "All":
        filtered_df = filtered_df[filtered_df['Vendor'] == vendor_filter]

    if rec_filter != "All":
        filtered_df = filtered_df[filtered_df['Recommendation'] == rec_filter]

    filtered_df = filtered_df[filtered_df['Overall'] >= min_score]

    # Display filtered results
    st.dataframe(
        filtered_df[['RFP', 'Vendor', 'Evaluator', 'Functional', 'Security', 'Business', 'Overall', 'Recommendation']],
        use_container_width=True
    )


def show_rfp_performance(rfps):
    """RFP performance metrics and analysis"""
    st.markdown("### 📋 RFP Performance Analysis")

    db = get_db()

    # RFP performance data
    rfp_data = []

    for rfp in rfps:
        try:
            proposals = db.get_proposals_for_rfp(rfp['id'])

            # Count evaluations
            total_evaluations = 0
            completed_evaluations = 0

            for proposal in proposals:
                try:
                    evaluations = db.get_evaluations_for_proposal(proposal['id'])
                    total_evaluations += len(evaluations)
                    completed_evaluations += len([e for e in evaluations if e.get('status') == 'completed'])
                except:
                    continue

            # Calculate time metrics
            created_date = datetime.fromisoformat(rfp['created_at'].replace('Z', '+00:00')) if rfp[
                'created_at'] else None
            due_date = datetime.fromisoformat(rfp['due_date'].replace('Z', '+00:00')) if rfp.get('due_date') else None

            days_to_due = None
            if created_date and due_date:
                days_to_due = (due_date - created_date).days

            rfp_data.append({
                'Title': rfp['title'],
                'Status': rfp['status'],
                'Proposals': len(proposals),
                'Evaluations': completed_evaluations,
                'Total Eval Slots': total_evaluations,
                'Completion %': round((completed_evaluations / total_evaluations * 100) if total_evaluations > 0 else 0,
                                      1),
                'Days to Due': days_to_due,
                'Created': rfp['created_at'][:10] if rfp['created_at'] else 'Unknown'
            })
        except Exception as e:
            continue

    if not rfp_data:
        st.info("📊 No RFP data available for analysis")
        return

    df = pd.DataFrame(rfp_data)

    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_proposals = round(df['Proposals'].mean(), 1) if len(df) > 0 else 0
        st.metric("Avg Proposals per RFP", avg_proposals)

    with col2:
        avg_completion = round(df['Completion %'].mean(), 1) if len(df) > 0 else 0
        st.metric("Avg Evaluation Completion", f"{avg_completion}%")

    with col3:
        avg_timeline = round(df['Days to Due'].mean(), 1) if df['Days to Due'].notna().sum() > 0 else 0
        st.metric("Avg RFP Timeline", f"{avg_timeline} days")

    with col4:
        rfps_with_proposals = len(df[df['Proposals'] > 0])
        response_rate = round((rfps_with_proposals / len(df) * 100) if len(df) > 0 else 0, 1)
        st.metric("RFP Response Rate", f"{response_rate}%")

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Proposals per RFP")
        fig = px.bar(
            df,
            x='Title',
            y='Proposals',
            color='Status',
            title="Number of Proposals by RFP"
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Evaluation Completion Rate")
        fig = px.bar(
            df,
            x='Title',
            y='Completion %',
            color='Completion %',
            color_continuous_scale='RdYlGn',
            title="Evaluation Completion by RFP"
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Detailed RFP table
    st.markdown("#### RFP Performance Details")
    st.dataframe(df, use_container_width=True)


def show_vendor_analytics(rfps):
    """Vendor performance and analysis"""
    st.markdown("### 🏢 Vendor Analysis")

    db = get_db()

    # Get all vendors who have submitted proposals
    vendor_data = {}

    for rfp in rfps:
        try:
            proposals = db.get_proposals_for_rfp(rfp['id'])

            for proposal in proposals:
                vendor_name = proposal.get('vendors', {}).get('name', 'Unknown')

                if vendor_name not in vendor_data:
                    vendor_data[vendor_name] = {
                        'proposals': 0,
                        'rfps': set(),
                        'scores': [],
                        'recommendations': [],
                        'statuses': []
                    }

                vendor_data[vendor_name]['proposals'] += 1
                vendor_data[vendor_name]['rfps'].add(rfp['title'])
                vendor_data[vendor_name]['statuses'].append(proposal['status'])

                # Get evaluation scores
                try:
                    evaluations = db.get_evaluations_for_proposal(proposal['id'])
                    for evaluation in evaluations:
                        if evaluation.get('status') == 'completed':
                            vendor_data[vendor_name]['scores'].append(evaluation.get('overall_score', 0))
                            vendor_data[vendor_name]['recommendations'].append(
                                evaluation.get('recommendation', 'not_recommend'))
                except:
                    continue
        except:
            continue

    if not vendor_data:
        st.info("🏢 No vendor data available for analysis")
        return

    # Convert to DataFrame
    vendor_analysis = []

    for vendor, data in vendor_data.items():
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        recommend_rate = (data['recommendations'].count('recommend') / len(data['recommendations']) * 100) if data[
            'recommendations'] else 0
        shortlisted = data['statuses'].count('shortlisted')

        vendor_analysis.append({
            'Vendor': vendor,
            'Total Proposals': data['proposals'],
            'RFPs Participated': len(data['rfps']),
            'Avg Score': round(avg_score, 1),
            'Recommend Rate %': round(recommend_rate, 1),
            'Shortlisted': shortlisted,
            'Win Rate %': round((shortlisted / data['proposals'] * 100) if data['proposals'] > 0 else 0, 1)
        })

    df = pd.DataFrame(vendor_analysis)
    df = df.sort_values('Avg Score', ascending=False)

    # Vendor performance metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Vendors", len(df))

    with col2:
        avg_participation = round(df['RFPs Participated'].mean(), 1) if len(df) > 0 else 0
        st.metric("Avg RFP Participation", avg_participation)

    with col3:
        avg_vendor_score = round(df['Avg Score'].mean(), 1) if len(df) > 0 else 0
        st.metric("Avg Vendor Score", f"{avg_vendor_score}/100")

    with col4:
        avg_win_rate = round(df['Win Rate %'].mean(), 1) if len(df) > 0 else 0
        st.metric("Avg Win Rate", f"{avg_win_rate}%")

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Vendor Performance Scores")
        if len(df) > 0:
            fig = px.scatter(
                df,
                x='Total Proposals',
                y='Avg Score',
                size='RFPs Participated',
                hover_name='Vendor',
                color='Win Rate %',
                color_continuous_scale='RdYlGn',
                title="Vendor Performance Overview"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Top Performing Vendors")
        top_vendors = df.head(10)

        fig = px.bar(
            top_vendors,
            x='Vendor',
            y='Avg Score',
            color='Win Rate %',
            color_continuous_scale='RdYlGn',
            title="Top 10 Vendors by Score"
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Detailed vendor table
    st.markdown("#### Vendor Performance Details")
    st.dataframe(df, use_container_width=True)


def show_export_options(rfps):
    """Export and reporting options"""
    st.markdown("### 📑 Export Reports")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Available Reports")

        report_options = [
            "📊 Executive Summary",
            "🏆 Evaluation Results",
            "📋 RFP Performance Report",
            "🏢 Vendor Analysis Report",
            "📈 Detailed Analytics"
        ]

        selected_reports = st.multiselect("Select Reports to Export", report_options)

        export_format = st.selectbox("Export Format", ["PDF", "Excel", "CSV"])

        if st.button("📥 Generate Report", type="primary"):
            if selected_reports:
                st.success(f"✅ Generating {len(selected_reports)} reports in {export_format} format...")
                st.info("Report generation functionality would be implemented here")
            else:
                st.warning("Please select at least one report to export")

    with col2:
        st.markdown("#### Report Schedule")

        st.info("**Automated Reporting** (Coming Soon)")

        # Placeholder for scheduled reporting
        schedule_frequency = st.selectbox("Report Frequency", ["Weekly", "Monthly", "Quarterly"])
        email_recipients = st.text_input("Email Recipients", placeholder="email1@company.com, email2@company.com")

        if st.button("📧 Setup Automated Reports"):
            st.info("Automated reporting setup would be implemented here")

        st.markdown("---")

        st.markdown("#### Quick Actions")

        if st.button("📊 Refresh All Data"):
            st.success("Data refreshed!")
            st.rerun()

        if st.button("🔄 Sync with External Systems"):
            st.info("External system integration would be implemented here")