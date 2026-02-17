import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
import os
import json

load_dotenv()

# ============================================
# API KEY HANDLER (works locally + cloud)
# ============================================
def get_api_key():
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except:
        return os.getenv("GOOGLE_API_KEY")

# ============================================
# FILTER FUNCTION
# ============================================
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

# ============================================
# LOAD SCHEMES
# ============================================
@st.cache_data
def load_schemes():
    with open('schemes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# ============================================
# INIT LLM
# ============================================
@st.cache_resource
def init_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=get_api_key(),  # FIXED!
        temperature=0.3
    )

# ============================================
# CREATE RETRIEVER
# ============================================
@st.cache_resource
def create_retriever(_schemes):
    docs = [
        Document(
            page_content=f"{s['name']}: {s['benefits']} | Eligibility: {s['eligibility']} | Docs: {s['documents']}",
            metadata={"name": s['name'], "category": s['category'], "link": s['link']}
        )
        for s in _schemes
    ]
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",  
        google_api_key=get_api_key()        
    )
    
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings
      
    )
    
    return vectorstore.as_retriever(search_kwargs={"k": 3})

# ============================================
# PAGE SETUP
# ============================================
st.set_page_config(page_title="JanAI", page_icon="🇮🇳", layout="wide")

# ============================================
# LOAD EVERYTHING
# ============================================
schemes = load_schemes()
llm = init_llm()
retriever = create_retriever(schemes)

# ============================================
# SIDEBAR
# ============================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/4/41/Flag_of_India.svg", width=80)
st.sidebar.title("JanAI")
st.sidebar.markdown("*सरकारी योजना सहायक*")
st.sidebar.divider()

language = st.sidebar.radio("🌐 Language / भाषा", ["English", "हिंदी"], horizontal=True)
st.sidebar.divider()

if language == "हिंदी":
    st.sidebar.header("📋 आपकी जानकारी")
    age = st.sidebar.number_input("आयु (Age)", 0, 100, 25)
    income = st.sidebar.number_input("वार्षिक आय (₹)", 0, 10000000, 300000, 50000)
    state = st.sidebar.selectbox("राज्य (State)", ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat", "Uttar Pradesh"])
    occupation = st.sidebar.selectbox("व्यवसाय (Occupation)", ["", "Farmer", "Street Vendor", "Artisan", "Student", "Self-Employed", "Salaried", "Unemployed"])
    gender = st.sidebar.selectbox("लिंग (Gender)", ["", "Male", "Female", "Other"])
else:
    st.sidebar.header("📋 Your Profile")
    age = st.sidebar.number_input("Age", 0, 100, 25)
    income = st.sidebar.number_input("Annual Income (₹)", 0, 10000000, 300000, 50000)
    state = st.sidebar.selectbox("State", ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat", "Uttar Pradesh"])
    occupation = st.sidebar.selectbox("Occupation", ["", "Farmer", "Street Vendor", "Artisan", "Student", "Self-Employed", "Salaried", "Unemployed"])
    gender = st.sidebar.selectbox("Gender", ["", "Male", "Female", "Other"])

st.sidebar.divider()
st.sidebar.caption(f"📊 {len(schemes)} schemes loaded")
st.sidebar.caption("🔍 Vector DB: Active ✅")

# ============================================
# MAIN TITLE
# ============================================
if language == "हिंदी":
    st.title("🇮🇳 JanAI - सरकारी योजना सहायक")
    st.markdown("### अपने लिए सही सरकारी योजना खोजें")
else:
    st.title("🇮🇳 JanAI - Government Scheme Assistant")
    st.markdown("### Find Government Schemes You Qualify For")

# ============================================
# TABS
# ============================================
if language == "हिंदी":
    tab1, tab2, tab3 = st.tabs(["🎯 योजनाएं खोजें", "💬 सवाल पूछें", "📚 सभी योजनाएं"])
else:
    tab1, tab2, tab3 = st.tabs(["🎯 Find Schemes", "💬 Ask Questions", "📚 Browse All"])

# ============================================
# TAB 1 - FIND SCHEMES
# ============================================
with tab1:
    if language == "हिंदी":
        st.subheader("आपके लिए योग्य योजनाएं")
        btn_label = "🔍 मेरी योजनाएं खोजें"
    else:
        st.subheader("Schemes You May Be Eligible For")
        btn_label = "🔍 Find My Schemes"
    
    if st.button(btn_label, type="primary"):
        with st.spinner("Analyzing..." if language == "English" else "विश्लेषण हो रहा है..."):
            
            profile = {
                'age': age, 'income': income, 'state': state,
                'occupation': occupation, 'gender': gender
            }
            
            eligible_schemes = filter_eligible_schemes(schemes, profile)
            
            if eligible_schemes:
                if language == "हिंदी":
                    st.success(f"✅ आपके लिए **{len(eligible_schemes)}** योजनाएं मिलीं!")
                else:
                    st.success(f"✅ Found **{len(eligible_schemes)}** schemes you qualify for!")
                
                for idx, scheme in enumerate(eligible_schemes, 1):
                    with st.expander(f"**{idx}. {scheme['name']}** - {scheme['category']}", expanded=(idx==1)):
                        
                        st.markdown("**💰 लाभ:**" if language == "हिंदी" else "**💰 Benefits:**")
                        st.info(scheme['benefits'])
                        
                        st.markdown("**✅ आप क्यों योग्य हैं:**" if language == "हिंदी" else "**✅ Why You Qualify:**")
                        reasons = []
                        elig = scheme['eligibility']
                        if 'age_min' in elig:
                            if language == "हिंदी":
                                reasons.append(f"आपकी आयु ({age}) न्यूनतम आयु ({elig['age_min']}) से अधिक है")
                            else:
                                reasons.append(f"Your age ({age}) meets minimum requirement ({elig['age_min']})")
                        if 'income_max' in elig:
                            if language == "हिंदी":
                                reasons.append(f"आपकी आय (₹{income:,}) सीमा के अंदर है (₹{elig['income_max']:,})")
                            else:
                                reasons.append(f"Your income (₹{income:,}) is within the limit (₹{elig['income_max']:,})")
                        if 'income_max_EWS' in elig:
                            if income <= elig['income_max_EWS']:
                                reasons.append("EWS category (आर्थिक रूप से कमजोर वर्ग)")
                            elif income <= elig.get('income_max_LIG', 0):
                                reasons.append("LIG category (निम्न आय वर्ग)")
                            elif income <= elig.get('income_max_MIG', 0):
                                reasons.append("MIG category (मध्यम आय वर्ग)")
                        
                        for reason in reasons:
                            st.caption(f"• {reason}")
                        
                        st.markdown("**📄 आवश्यक दस्तावेज़:**" if language == "हिंदी" else "**📄 Required Documents:**")
                        cols = st.columns(2)
                        for i, doc in enumerate(scheme['documents']):
                            with cols[i % 2]:
                                st.write(f"✓ {doc}")
                        
                        st.link_button(
                            "🔗 आवेदन करें" if language == "हिंदी" else "🔗 Apply Online",
                            scheme['link'],
                            use_container_width=True
                        )
            else:
                if language == "हिंदी":
                    st.warning("😔 कोई योजना नहीं मिली।")
                    st.info("💡 आयु, आय या व्यवसाय बदलकर दोबारा कोशिश करें।")
                else:
                    st.warning("😔 No schemes found matching your profile.")
                    st.info("💡 Try adjusting your age, income or occupation.")

# ============================================
# TAB 2 - ASK QUESTIONS
# ============================================
with tab2:
    if language == "हिंदी":
        st.subheader("💬 सरकारी योजनाओं के बारे में सवाल पूछें")
        placeholder_text = "जैसे: किसानों के लिए कौन सी योजनाएं हैं?"
        btn_text = "🔎 खोजें"
    else:
        st.subheader("💬 Ask Questions About Schemes")
        placeholder_text = "e.g., What schemes are available for farmers?"
        btn_text = "🔎 Ask"
    
    question = st.text_area(
        "आपका सवाल:" if language == "हिंदी" else "Your question:",
        placeholder=placeholder_text,
        height=100
    )
    
    if st.button(btn_text, type="primary") and question:
        with st.spinner("खोज रहे हैं..." if language == "हिंदी" else "Searching..."):
            
            relevant_docs = retriever.invoke(question)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            if language == "हिंदी":
                full_prompt = f"""
आप एक सहायक हैं जो भारतीय सरकारी योजनाओं के बारे में जानकारी देते हैं।
यहाँ सबसे प्रासंगिक योजनाएं हैं:
{context}
उपयोगकर्ता का सवाल: {question}
कृपया हिंदी में स्पष्ट और सरल उत्तर दें। योजना का नाम और मुख्य लाभ बताएं।
                """
            else:
                full_prompt = f"""
You are helping someone find Indian government schemes.
Here are the most relevant schemes:
{context}
User's question: {question}
Provide a helpful answer mentioning specific scheme names and key benefits.
                """
            
            answer = llm.invoke(full_prompt)
            
            st.markdown("### 📖 उत्तर:" if language == "हिंदी" else "### 📖 Answer:")
            st.write(answer.content)
            
            st.divider()
            st.markdown("**📚 संबंधित योजनाएं:**" if language == "हिंदी" else "**📚 Relevant Schemes Found:**")
            
            for idx, doc in enumerate(relevant_docs, 1):
                with st.expander(f"{idx}. {doc.metadata['name']} - {doc.metadata['category']}"):
                    full_scheme = next((s for s in schemes if s['name'] == doc.metadata['name']), None)
                    if full_scheme:
                        st.write(f"**Benefits:** {full_scheme['benefits']}")
                        st.write(f"**Documents:** {', '.join(full_scheme['documents'])}")
                        st.link_button(
                            "आवेदन करें" if language == "हिंदी" else "Apply Now",
                            doc.metadata['link'],
                            use_container_width=True
                        )

# ============================================
# TAB 3 - BROWSE ALL
# ============================================
with tab3:
    st.subheader("📚 सभी योजनाएं देखें" if language == "हिंदी" else "📚 Browse All Schemes")
    
    categories = ["All / सभी"] + sorted(list(set([s['category'] for s in schemes])))
    selected = st.selectbox(
        "Category / श्रेणी" if language == "हिंदी" else "Filter by Category",
        categories
    )
    
    filtered = schemes if selected == "All / सभी" else [s for s in schemes if s['category'] == selected]
    st.caption(f"Showing {len(filtered)} of {len(schemes)} schemes")
    
    for scheme in filtered:
        with st.expander(f"**{scheme['name']}** - {scheme['category']}"):
            st.write(f"**Benefits:** {scheme['benefits']}")
            st.write(f"**Documents:** {', '.join(scheme['documents'])}")
            st.link_button(
                "आवेदन करें" if language == "हिंदी" else "Apply Here",
                scheme['link']
            )