"""
Simple test version of SmartLinks frontend
"""
import streamlit as st
import requests

st.title("🔗 SmartLinks Test")

# Test API connection
try:
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        st.success("✅ API connection successful!")
        data = response.json()
        st.json(data)
    else:
        st.error(f"❌ API returned status {response.status_code}")
except Exception as e:
    st.error(f"❌ Cannot connect to API: {e}")

# Simple form to create a link
st.header("Create a Link")
with st.form("simple_form"):
    keyword = st.text_input("Keyword")
    url = st.text_input("URL")

    if st.form_submit_button("Create"):
        if keyword and url:
            try:
                data = {
                    "keyword": keyword,
                    "url": url,
                    "title": keyword.title(),
                    "category": "General"
                }
                response = requests.post("http://localhost:8000/api/links", json=data)

                if response.status_code == 200:
                    st.success(f"✅ Created go/{keyword}!")
                    st.write(f"Test it: http://localhost:8000/go/{keyword}")
                else:
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Error creating link: {e}")
        else:
            st.error("Please fill in both fields")

# Show existing links
st.header("Existing Links")
try:
    response = requests.get("http://localhost:8000/api/links")
    if response.status_code == 200:
        links = response.json()
        for link in links:
            st.write(f"**go/{link['keyword']}** → {link['url']}")
    else:
        st.error("Failed to load links")
except Exception as e:
    st.error(f"Error loading links: {e}")