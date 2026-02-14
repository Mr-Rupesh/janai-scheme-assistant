import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import json

# Load environment
load_dotenv()

# Function to filter eligible schemes
def filter_eligible_schemes(schemes, profile):
    """
    Filter schemes based on user profile.
    Returns list of schemes the user qualifies for.
    """
    eligible = []
    
    for scheme in schemes:
        elig = scheme['eligibility']
        is_eligible = True
        
        # Check age minimum
        if 'age_min' in elig:
            if profile['age'] < elig['age_min']:
                is_eligible = False
                continue
        
        # Check age maximum
        if 'age_max' in elig:
            if profile['age'] > elig['age_max']:
                is_eligible = False
                continue
        
        # Check income (handle different income fields)
        if 'income_max' in elig:
            if profile['income'] > elig['income_max']:
                is_eligible = False
                continue
        
        # For PMAY - check EWS/LIG/MIG categories
        if 'income_max_EWS' in elig:
            # Check if income fits in ANY category
            max_allowed = elig.get('income_max_MIG', elig.get('income_max_LIG', elig.get('income_max_EWS', 0)))
            if profile['income'] > max_allowed:
                is_eligible = False
                continue
        
        # Check occupation
        if 'occupation' in elig:
            if profile.get('occupation'):  # Only check if user selected occupation
                if profile['occupation'].lower() not in elig['occupation'].lower():
                    is_eligible = False
                    continue
        
        # Check gender
        if 'gender' in elig:
            if profile.get('gender'):  # Only check if user selected gender
                if profile['gender'].lower() not in elig['gender'].lower():
                    is_eligible = False
                    continue
        
        # If passed all checks, add to eligible list
        if is_eligible:
            eligible.append(scheme)
    
    return eligible

# Load schemes from JSON file
@st.cache_data
def load_schemes():
    with open('schemes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Initialize Gemini
@st.cache_resource
def init_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3
    )

# Page config
st.set_page_config(page_title="JanAI", page_icon="🇮🇳")

# Title
st.title("🇮🇳 JanAI - Government Scheme Assistant")
st.markdown("### Find Government Schemes You Qualify For")

# Load data FIRST
schemes = load_schemes()
llm = init_llm()

# Sidebar for user inputs
st.sidebar.header("📋 Your Profile")

age = st.sidebar.number_input("Age", min_value=0, max_value=100, value=25)
income = st.sidebar.number_input(
    "Annual Income (₹)", 
    min_value=0, 
    max_value=10000000, 
    value=300000,
    step=50000
)
state = st.sidebar.selectbox(
    "State",
    ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat", "Uttar Pradesh", "All States"]
)
occupation = st.sidebar.selectbox(
    "Occupation (Optional)",
    ["", "Farmer", "Street Vendor", "Artisan", "Student", "Self-Employed", "Salaried", "Unemployed"]
)
gender = st.sidebar.selectbox(
    "Gender (Optional)",
    ["", "Male", "Female", "Other"]
)

# Create tabs
tab1, tab2, tab3 = st.tabs(["🎯 Find Schemes", "💬 Ask Questions", "📚 Browse All"])

# TAB 1: Find Schemes
with tab1:
    st.subheader("Schemes You May Be Eligible For")
    
    if st.button("🔍 Find My Schemes", type="primary"):
        with st.spinner("Analyzing your profile..."):
            
            # Create profile dictionary
            profile = {
                'age': age,
                'income': income,
                'state': state,
                'occupation': occupation,
                'gender': gender
            }
            
            # Filter eligible schemes
            eligible_schemes = filter_eligible_schemes(schemes, profile)
            
            if eligible_schemes:
                st.success(f"✅ Found **{len(eligible_schemes)}** schemes you qualify for!")
                
                # Show each eligible scheme
                for idx, scheme in enumerate(eligible_schemes, 1):
                    with st.expander(
                        f"**{idx}. {scheme['name']}** - {scheme['category']}", 
                        expanded=(idx==1)
                    ):
                        
                        # Benefits
                        st.markdown("**💰 Benefits:**")
                        st.info(scheme['benefits'])
                        
                        # Why you qualify
                        st.markdown("**✅ Why You Qualify:**")
                        reasons = []
                        elig = scheme['eligibility']
                        
                        if 'age_min' in elig:
                            reasons.append(f"Your age ({age}) meets the minimum requirement ({elig['age_min']})")
                        
                        if 'income_max' in elig:
                            reasons.append(f"Your income (₹{income:,}) is within the limit (₹{elig['income_max']:,})")
                        
                        if 'income_max_EWS' in elig:
                            if income <= elig['income_max_EWS']:
                                reasons.append(f"You qualify for EWS category (income ≤ ₹{elig['income_max_EWS']:,})")
                            elif income <= elig.get('income_max_LIG', 0):
                                reasons.append(f"You qualify for LIG category (income ≤ ₹{elig['income_max_LIG']:,})")
                            elif income <= elig.get('income_max_MIG', 0):
                                reasons.append(f"You qualify for MIG category (income ≤ ₹{elig['income_max_MIG']:,})")
                        
                        if 'occupation' in elig and occupation:
                            reasons.append(f"Your occupation ({occupation}) matches the requirement")
                        
                        if 'gender' in elig and gender:
                            reasons.append(f"Gender requirement met")
                        
                        for reason in reasons:
                            st.caption(f"• {reason}")
                        
                        # Documents
                        st.markdown("**📄 Required Documents:**")
                        for doc in scheme['documents']:
                            st.write(f"- {doc}")
                        
                        # Apply link
                        st.markdown(f"**🔗 [Apply Online]({scheme['link']})**")
            
            else:
                st.warning("😔 No schemes found matching your exact profile.")
                st.info("💡 **Try:**\n- Adjusting your age or income\n- Selecting an occupation if applicable\n- Browse all schemes in the last tab")

# TAB 2: Ask Questions
with tab2:
    st.subheader("💬 Ask Me Anything")
    
    question = st.text_input(
        "Ask your question:",
        placeholder="e.g., What schemes are available for farmers?"
    )
    
    if question:
        with st.spinner("Thinking..."):
            # Create simple prompt with all schemes context
            schemes_text = "\n\n".join([
                f"Scheme: {s['name']}\nCategory: {s['category']}\nBenefits: {s['benefits']}\nEligibility: {s['eligibility']}"
                for s in schemes
            ])
            
            prompt = f"""
You are a helpful assistant for Indian government schemes.

Available schemes:
{schemes_text}

User question: {question}

Provide a clear, helpful answer based on the schemes above. Be specific and mention scheme names.
            """
            
            response = llm.invoke(prompt)
            st.write(response.content)

# TAB 3: Browse All
with tab3:
    st.subheader("📚 Browse All Schemes")
    
    # Category filter
    categories = ["All"] + sorted(list(set([s['category'] for s in schemes])))
    selected_cat = st.selectbox("Filter by Category", categories)
    
    if selected_cat != "All":
        filtered_schemes = [s for s in schemes if s['category'] == selected_cat]
    else:
        filtered_schemes = schemes
    
    st.caption(f"Showing {len(filtered_schemes)} of {len(schemes)} schemes")
    
    # Display schemes
    for scheme in filtered_schemes:
        with st.expander(f"**{scheme['name']}** - {scheme['category']}"):
            st.write(f"**Benefits:** {scheme['benefits']}")
            st.write(f"**Documents:** {', '.join(scheme['documents'])}")
            st.markdown(f"**[Apply Here]({scheme['link']})**")