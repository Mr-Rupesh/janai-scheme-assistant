import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Filter function (same as before)
def filter_eligible_schemes(schemes, profile):
    eligible = []
    for scheme in schemes:
        elig = scheme['eligibility']
        is_eligible = True
        
        if 'age_min' in elig and profile['age'] < elig['age_min']:
            is_eligible = False
            continue
        if 'age_max' in elig and profile['age'] > elig['age_max']:
            is_eligible = False
            continue
        if 'income_max' in elig and profile['income'] > elig['income_max']:
            is_eligible = False
            continue
        if 'income_max_EWS' in elig:
            max_allowed = elig.get('income_max_MIG', elig.get('income_max_LIG', elig.get('income_max_EWS', 0)))
            if profile['income'] > max_allowed:
                is_eligible = False
                continue
        if 'occupation' in elig and profile.get('occupation'):
            if profile['occupation'].lower() not in elig['occupation'].lower():
                is_eligible = False
                continue
        if 'gender' in elig and profile.get('gender'):
            if profile['gender'].lower() not in elig['gender'].lower():
                is_eligible = False
                continue
        
        if is_eligible:
            eligible.append(scheme)
    
    return eligible

# Load schemes
@st.cache_data
def load_schemes():
    with open('schemes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Initialize LLM
@st.cache_resource
def init_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0.3
    )

# Create retriever (LANGCHAIN WAY!)
@st.cache_resource
def create_retriever(_schemes):
    """
    Create Chroma retriever from schemes JSON
    Pure LangChain approach
    """
    # Convert schemes to Documents
    docs = [
        Document(
            page_content=f"{s['name']}: {s['benefits']} | Eligibility: {s['eligibility']} | Docs: {s['documents']}",
            metadata={"name": s['name'], "category": s['category'], "link": s['link']}
        )
        for s in _schemes
    ]
    
    # Create embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
    )
    
    # Create vectorstore and return retriever
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    
    return vectorstore.as_retriever(search_kwargs={"k": 3})

# Page setup
st.set_page_config(page_title="JanAI", page_icon="🇮🇳")
st.title("🇮🇳 JanAI - Government Scheme Assistant")

# Load everything
schemes = load_schemes()
llm = init_llm()
retriever = create_retriever(schemes)  # Direct retriever!

# Sidebar
st.sidebar.header("📋 Your Profile")
age = st.sidebar.number_input("Age", 0, 100, 25)
income = st.sidebar.number_input("Annual Income (₹)", 0, 10000000, 300000, 50000)
state = st.sidebar.selectbox("State", ["Maharashtra", "Karnataka", "Delhi"])
occupation = st.sidebar.selectbox("Occupation", ["", "Farmer", "Street Vendor", "Artisan", "Student", "Self-Employed"])
gender = st.sidebar.selectbox("Gender", ["", "Male", "Female", "Other"])

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Find Schemes", "💬 Ask Questions", "📚 Browse All"])

# TAB 1: Find Schemes (same as before)
with tab1:
    st.subheader("Schemes You May Be Eligible For")
    
    if st.button("🔍 Find My Schemes", type="primary"):
        profile = {'age': age, 'income': income, 'state': state, 'occupation': occupation, 'gender': gender}
        eligible = filter_eligible_schemes(schemes, profile)
        
        if eligible:
            st.success(f"✅ Found {len(eligible)} schemes!")
            for idx, scheme in enumerate(eligible, 1):
                with st.expander(f"{idx}. {scheme['name']}", expanded=(idx==1)):
                    st.info(scheme['benefits'])
                    st.write(f"**Documents:** {', '.join(scheme['documents'])}")
                    st.link_button("Apply", scheme['link'])
        else:
            st.warning("No schemes found. Try adjusting your profile.")

# TAB 2: Ask Questions (USING RETRIEVER!)
# TAB 2: Ask Questions (SIMPLEST WORKING VERSION)
# TAB 2: Ask Questions (FIXED VERSION)
with tab2:
    st.subheader("💬 Ask Questions About Schemes")
    
    question = st.text_area(
        "Your question:",
        placeholder="e.g., What schemes are available for farmers?",
        height=100
    )
    
    if st.button("🔎 Ask", type="primary") and question:
        with st.spinner("Searching schemes..."):
            
            # Step 1: Get relevant schemes (FIXED!)
            relevant_docs = retriever.invoke(question)  # Changed from get_relevant_documents
            
            # Step 2: Build context
            context = ""
            for doc in relevant_docs:
                context += f"\n{doc.page_content}\n"
            
            # Step 3: Ask LLM with context
            full_prompt = f"""
You are helping someone find Indian government schemes.

Here are the most relevant schemes:
{context}

User's question: {question}

Provide a helpful answer mentioning specific scheme names and key benefits.
            """
            
            answer = llm.invoke(full_prompt)
            
            # Step 4: Display results
            # Step 5: Show source schemes
            st.divider()
            st.markdown("**📚 Relevant Schemes Found:**")
            
            for idx, doc in enumerate(relevant_docs, 1):
                with st.expander(f"{idx}. {doc.metadata['name']} - {doc.metadata['category']}"):
                    # Get full scheme details
                    full_scheme = next((s for s in schemes if s['name'] == doc.metadata['name']), None)
                    if full_scheme:
                        st.write(f"**Benefits:** {full_scheme['benefits']}")
                        st.write(f"**Documents:** {', '.join(full_scheme['documents'])}")
                        st.link_button("Apply Now", doc.metadata['link'], use_container_width=True)