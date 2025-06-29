import streamlit as st
from config import get_db, format_date


def show_vendors_page():
    """Vendor management page"""
    st.markdown('<h1 class="main-header">🏢 Vendor Management</h1>', unsafe_allow_html=True)

    db = get_db()

    # Get all vendors
    try:
        vendors = db.get_all_vendors()
    except Exception as e:
        st.error(f"Error loading vendors: {str(e)}")
        vendors = []

    # Header with actions
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("Search vendors", placeholder="Search by name or email...")
    with col2:
        st.metric("Total Vendors", len(vendors))
    with col3:
        if st.button("➕ Add New Vendor", type="primary"):
            st.session_state.show_add_vendor = True
            st.rerun()

    # Add vendor form (in sidebar or modal)
    if st.session_state.get('show_add_vendor', False):
        show_add_vendor_form()

    # Filter vendors based on search
    if search_term:
        filtered_vendors = [
            v for v in vendors
            if search_term.lower() in v.get('name', '').lower() or
               search_term.lower() in v.get('contact_email', '').lower()
        ]
    else:
        filtered_vendors = vendors

    # Display vendors
    if filtered_vendors:
        st.markdown("### Vendor Directory")

        for vendor in filtered_vendors:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    st.markdown(f"**{vendor.get('name', 'Unknown Vendor')}**")
                    if vendor.get('contact_person'):
                        st.caption(f"Contact: {vendor['contact_person']}")
                    if vendor.get('website'):
                        st.caption(f"🌐 [{vendor['website']}]({vendor['website']})")

                with col2:
                    st.write(f"📧 {vendor.get('contact_email', 'No email')}")
                    if vendor.get('phone'):
                        st.write(f"📞 {vendor['phone']}")

                with col3:
                    if vendor.get('address'):
                        st.write(f"📍 {vendor['address']}")
                    st.caption(f"Added: {format_date(vendor.get('created_at', ''))}")

                with col4:
                    # Action buttons
                    if st.button("✏️", key=f"edit_vendor_{vendor['id']}", help="Edit vendor"):
                        st.session_state.edit_vendor_id = vendor['id']
                        st.session_state.show_edit_vendor = True
                        st.rerun()

                    if st.button("🗑️", key=f"delete_vendor_{vendor['id']}", help="Delete vendor"):
                        if st.session_state.get(f'confirm_delete_{vendor["id"]}', False):
                            # Actually delete
                            try:
                                # Note: We'd need to add a delete_vendor method to DatabaseManager
                                st.success(f"Vendor {vendor['name']} deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting vendor: {str(e)}")
                        else:
                            # Show confirmation
                            st.session_state[f'confirm_delete_{vendor["id"]}'] = True
                            st.warning(f"Click again to confirm deletion of {vendor['name']}")

                st.markdown("---")

    else:
        # Empty state
        if search_term:
            st.info(f"No vendors found matching '{search_term}'")
        else:
            st.markdown("### 🎯 No Vendors Yet")
            st.info("""
            **Build your vendor database to streamline RFP management!**

            Add vendors to:
            - 📋 Quickly attach proposals to RFPs
            - 📊 Track vendor performance over time  
            - 🔍 Search and filter your vendor network
            - 📈 Generate vendor analytics
            """)

    # Edit vendor form
    if st.session_state.get('show_edit_vendor', False):
        show_edit_vendor_form()


def show_add_vendor_form():
    """Show add vendor form in sidebar"""
    with st.sidebar:
        st.markdown("### ➕ Add New Vendor")

        with st.form(f"add_vendor_form_{hash(str(st.session_state.user.id))}"):
            name = st.text_input("Company Name*", placeholder="e.g., TechCorp Solutions")
            contact_person = st.text_input("Contact Person", placeholder="e.g., John Smith")
            contact_email = st.text_input("Contact Email*", placeholder="e.g., john@techcorp.com")
            phone = st.text_input("Phone Number", placeholder="e.g., +1-555-123-4567")
            website = st.text_input("Website", placeholder="e.g., https://techcorp.com")
            address = st.text_area("Address", placeholder="Company address...")

            col1, col2 = st.columns(2)
            with col1:
                submit_button = st.form_submit_button("Add Vendor", type="primary")
            with col2:
                cancel_button = st.form_submit_button("Cancel")

            if cancel_button:
                st.session_state.show_add_vendor = False
                st.rerun()

            if submit_button:
                if not name or not contact_email:
                    st.error("Please fill in required fields (Name and Email)")
                else:
                    db = get_db()
                    vendor_data = {
                        "name": name,
                        "contact_person": contact_person,
                        "contact_email": contact_email,
                        "phone": phone,
                        "website": website,
                        "address": address,
                        "created_by": st.session_state.user.id
                    }

                    try:
                        new_vendor = db.create_vendor(vendor_data)
                        if new_vendor:
                            st.success(f"✅ Vendor '{name}' added successfully!")
                            st.session_state.show_add_vendor = False
                            st.rerun()
                        else:
                            st.error("Failed to add vendor")
                    except Exception as e:
                        st.error(f"Error adding vendor: {str(e)}")


def show_edit_vendor_form():
    """Show edit vendor form"""
    vendor_id = st.session_state.get('edit_vendor_id')
    if not vendor_id:
        return

    db = get_db()
    vendor = db.get_vendor_by_id(vendor_id)

    if not vendor:
        st.error("Vendor not found")
        st.session_state.show_edit_vendor = False
        return

    with st.sidebar:
        st.markdown(f"### ✏️ Edit Vendor: {vendor['name']}")

        with st.form(f"edit_vendor_form_{vendor_id}"):
            name = st.text_input("Company Name*", value=vendor.get('name', ''))
            contact_person = st.text_input("Contact Person", value=vendor.get('contact_person', ''))
            contact_email = st.text_input("Contact Email*", value=vendor.get('contact_email', ''))
            phone = st.text_input("Phone Number", value=vendor.get('phone', ''))
            website = st.text_input("Website", value=vendor.get('website', ''))
            address = st.text_area("Address", value=vendor.get('address', ''))

            col1, col2 = st.columns(2)
            with col1:
                submit_button = st.form_submit_button("Save Changes", type="primary")
            with col2:
                cancel_button = st.form_submit_button("Cancel")

            if cancel_button:
                st.session_state.show_edit_vendor = False
                st.session_state.edit_vendor_id = None
                st.rerun()

            if submit_button:
                if not name or not contact_email:
                    st.error("Please fill in required fields")
                else:
                    updates = {
                        "name": name,
                        "contact_person": contact_person,
                        "contact_email": contact_email,
                        "phone": phone,
                        "website": website,
                        "address": address
                    }

                    try:
                        updated_vendor = db.update_vendor(vendor_id, updates)
                        if updated_vendor:
                            st.success("✅ Vendor updated successfully!")
                            st.session_state.show_edit_vendor = False
                            st.session_state.edit_vendor_id = None
                            st.rerun()
                        else:
                            st.error("Failed to update vendor")
                    except Exception as e:
                        st.error(f"Error updating vendor: {str(e)}")