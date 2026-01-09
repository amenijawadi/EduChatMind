import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import pymongo
from io import BytesIO
import hashlib
import secrets
import os  


# Configuration de la page
st.set_page_config(
    page_title="EduChatMind",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration RASA
if "rasa" in st.secrets:
    RASA_API_URL = st.secrets["rasa"]["url"]
else:
    RASA_API_URL = "http://localhost:5005/webhooks/rest/webhook"

# Connexion MongoDB
try:
    # Configuration MongoDB avec Priority aux Secrets
    if "mongo" in st.secrets:
        mongo_uri = st.secrets["mongo"]["uri"]
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    else:
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client["rasa"] 
    tracker_collection = db["tracker"]
    users_collection = db["users"]  # Nouvelle collection pour les utilisateurs
    MONGODB_AVAILABLE = True
    init_admin_account() # Créer le compte admin par défaut s'il n'existe pas
except:
    MONGODB_AVAILABLE = False

# Styles CSS
# Remplacez la section CSS actuelle par celle-ci (lignes ~30-80) :

st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Background avec gradient animé */
    .main {
        background: linear-gradient(-45deg, #667eea, #764ba2, #4c63d2, #5a67d8);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Login Container */
    .login-container {
        max-width: 450px;
        margin: 100px auto;
        padding: 50px 40px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        box-shadow: 0 20px 80px rgba(0, 0, 0, 0.3);
        animation: fadeInUp 0.6s ease;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Logo et titre */
    .login-logo {
        text-align: center;
        font-size: 5rem;
        margin-bottom: 20px;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .login-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 10px 0;
    }
    
    .login-subtitle {
        text-align: center;
        color: #667eea;
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 40px;
        letter-spacing: 0.5px;
    }
    
    /* Input fields styling */
    .stTextInput > div > div > input {
        border: 2px solid #e8ecf1;
        border-radius: 12px;
        padding: 15px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
        background: #f8fafc;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        background: white;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
    }
    
    .stTextInput > label {
        font-weight: 400;
        color: #2d3748;
        font-size: 0.95rem;
        margin-bottom: 8px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px 30px;
        font-size: 17px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
    }
    
    /* Info box styling */
    .stAlert {
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 12px;
        font-weight: 600;
        border: 2px solid #e8ecf1;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==================== GESTION DES UTILISATEURS ====================

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_admin_account():
    """Créer le compte admin par défaut s'il n'existe pas"""
    if not MONGODB_AVAILABLE:
        return False
    
    admin_exists = users_collection.find_one({'role': 'admin'})
    
    if not admin_exists:
        admin_data = {
            'email': 'admin@educhatmind.com',
            'password': hash_password('admin123'),
            'role': 'admin',
            'name': 'Administrator',
            'created_at': datetime.now().isoformat()
        }
        users_collection.insert_one(admin_data)
        return True
    return False

def authenticate_user(email, password):
    """Authentifier un utilisateur"""
    if not MONGODB_AVAILABLE:
        return None
    
    hashed_password = hash_password(password)
    user = users_collection.find_one({
        'email': email,
        'password': hashed_password
    })
    
    return user

def create_student(email, password, name, student_class, school_year):
    """Créer un nouveau compte étudiant"""
    if not MONGODB_AVAILABLE:
        return False, "Database not available"
    
    # Vérifier si l'email existe déjà
    existing = users_collection.find_one({'email': email})
    if existing:
        return False, "Email already exists"
    
    student_data = {
        'email': email,
        'password': hash_password(password),
        'role': 'student',
        'name': name,
        'student_class': student_class,
        'school_year': school_year,
        'created_at': datetime.now().isoformat(),
        'student_id': f"student_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    
    users_collection.insert_one(student_data)
    return True, "Student created successfully"

def get_all_students():
    """Récupérer tous les étudiants"""
    if not MONGODB_AVAILABLE:
        return []
    
    students = list(users_collection.find({'role': 'student'}))
    return students

def delete_student(email):
    """Supprimer un étudiant"""
    if not MONGODB_AVAILABLE:
        return False
    
    result = users_collection.delete_one({'email': email, 'role': 'student'})
    return result.deleted_count > 0

# ==================== SESSION STATE ====================

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'user_data' not in st.session_state:
    st.session_state.user_data = None

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'student_id' not in st.session_state:
    st.session_state.student_id = None

if 'emotions_timeline' not in st.session_state:
    st.session_state.emotions_timeline = []

# ==================== FONCTIONS CHATBOT ====================

def send_message_to_rasa(message, sender_id):
    """Envoyer un message à Rasa et récupérer la réponse"""
    try:
        payload = {
            "sender": sender_id,
            "message": message
        }
        response = requests.post(RASA_API_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            return [{"text": "Error connecting to chatbot. Please try again."}]
    except Exception as e:
        return [{"text": f"Connection error: {str(e)}"}]

def get_emotion_emoji(emotion):
    """Retourner un emoji pour chaque émotion"""
    emoji_map = {
        'positive': '😊',
        'sadness': '😢',
        'anger': '😠',
        'fear': '😰',
        'confusion': '😕',
        'curiosity': '🤔',
        'caring': '🤗',
        'approval': '👍',
        'disapproval': '👎',
        'embarrassment': '😳',
        'neutral': '😐',
        'isolation': '😔'
    }
    return emoji_map.get(emotion, '❓')

def get_risk_color(risk_level):
    """Retourner une couleur selon le niveau de risque"""
    colors_map = {
        'low': '#4CAF50',
        'medium': '#FFC107',
        'high': '#FF9800',
        'critical': '#F44336'
    }
    return colors_map.get(risk_level, '#9E9E9E')

def get_all_conversations():
    """Récupérer toutes les conversations depuis tracker"""
    if not MONGODB_AVAILABLE:
        return {"count": 0, "conversations": []}
    
    total_conversations = tracker_collection.count_documents({})
    conversations = []
    trackers = tracker_collection.find({})
    
    for tracker in trackers:
        sender_id = tracker.get('sender_id', 'unknown')
        conv_history = tracker.get('slots', {}).get('conversation_history', [])
        
        for conv in conv_history:
            conversations.append({
                'sender_id': sender_id,
                'message': conv.get('message'),
                'timestamp': conv.get('timestamp'),
                'emotion': conv.get('sentiment', {}).get('detected_emotions', []),
                'sentiment': conv.get('sentiment', {})
            })
    
    return {
    "total_conversations": total_conversations,
    "conversations": conversations
}


def admin_critical_alerts():
    """Afficher uniquement les alertes critiques NON résolues et récentes"""
    st.title("🚨 CRITICAL ALERTS")
    
    # Charger les alertes critiques depuis le dossier alerts/
    import glob
    from datetime import datetime, timedelta
    
    alert_files = glob.glob("alerts/CRITICAL_*.json")
    
    if not alert_files:
        st.success("✅ No critical alerts at the moment")
        return
    
    critical_alerts = []
    current_time = datetime.now()
    
    for file in alert_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                alert = json.load(f)
                
                # Filtrer les alertes de plus de 7 jours
                alert_time = datetime.fromisoformat(alert['timestamp'])
                days_old = (current_time - alert_time).days
                
                if days_old <= 7:
                    alert['days_old'] = days_old
                    alert['file_path'] = file
                    critical_alerts.append(alert)
                else:
                    # Déplacer automatiquement les vieilles alertes
                    import shutil
                    os.makedirs("alerts/resolved/old", exist_ok=True)
                    shutil.move(file, f"alerts/resolved/old/{os.path.basename(file)}")
                    print(f"[INFO] Moved old alert to resolved: {file}")
        except Exception as e:
            print(f"[ERROR] Failed to load alert {file}: {e}")
            continue
    
    if not critical_alerts:
        st.success("✅ No recent critical alerts")
        st.info("ℹ️ Old alerts (>7 days) have been automatically archived")
        return
    
    # Trier par timestamp (plus récent en premier)
    critical_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    st.error(f"⚠️ {len(critical_alerts)} CRITICAL ALERT(S) REQUIRE IMMEDIATE ATTENTION")
    
    for alert in critical_alerts:
        days_text = "Today" if alert['days_old'] == 0 else f"{alert['days_old']} day(s) ago"
        
        # ✅ FIX: Gérer les deux structures d'alerte
        # Nouvelle structure : alert_level
        # Ancienne structure : risk_level
        alert_level = alert.get('alert_level', alert.get('risk_level', 'unknown')).upper()
        student_id = alert.get('student_id', 'unknown')
        timestamp = alert.get('timestamp', 'N/A')[:16]
        
        # ✅ Extraire les informations selon la structure
        if 'session_stats' in alert:
            # NOUVELLE STRUCTURE (analyse de session)
            alert_type = "SESSION_ANALYSIS"
            
            session_stats = alert.get('session_stats', {})
            risk_summary = alert.get('risk_summary', {})
            
            total_messages = session_stats.get('total_messages', 0)
            negative_ratio = session_stats.get('negative_emotion_ratio', 0)
            top_emotions = session_stats.get('top_emotions', [])
            
            risk_categories = [cat['category'] for cat in risk_summary.get('risk_categories', [])]
            total_risk_messages = risk_summary.get('total_risk_messages', 0)
            
            message = alert.get('most_critical_message', 'N/A')
            emotions_text = ", ".join([f"{e['emotion']} ({e['count']})" for e in top_emotions[:3]])
            
        else:
            # ANCIENNE STRUCTURE (alerte immédiate)
            alert_type = "IMMEDIATE_ALERT"
            
            total_messages = alert.get('messages_analyzed', 1)
            negative_ratio = 0
            
            risk_categories = alert.get('risk_categories', [])
            total_risk_messages = alert.get('total_critical_messages', 1)
            
            message = alert.get('message', alert.get('first_critical_message', 'N/A'))
            emotions_text = alert.get('emotion', 'N/A')
        
        with st.expander(
            f"🚨 {alert_level} - Student: {student_id} - {timestamp} ({days_text})",
            expanded=(alert['days_old'] == 0)
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📋 Session Summary")
                st.markdown(f"**Alert Type:** {alert_type}")
                st.markdown(f"**Total Messages:** {total_messages}")
                
                if alert_type == "SESSION_ANALYSIS":
                    st.markdown(f"**Negative Emotions:** {negative_ratio:.1f}%")
                    st.markdown(f"**Risk Messages:** {total_risk_messages}")
                
                st.markdown("---")
                
                st.markdown("### 💬 Most Critical Message")
                st.warning(message[:200] + ("..." if len(message) > 200 else ""))
                
                st.markdown("---")
                
                st.markdown("### 🎭 Detected Emotions")
                st.markdown(emotions_text)
                
                
                st.caption(f"⏰ Alert created: {days_text}")
            
            with col2:
                st.markdown("### ⚠️ ACTIONS REQUIRED")
                st.markdown("- [ ] Contact student immediately")
                st.markdown("- [ ] Notify parents/guardians")
                st.markdown("- [ ] Schedule counseling session")
                
                st.markdown("---")
                
                if st.button(f"📄 Generate Full Report", key=f"report_{student_id}_{timestamp}"):
                    buffer, error = generate_pdf_report(student_id)
                    if buffer:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=buffer,
                            file_name=f"CRITICAL_REPORT_{student_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error(f"Error: {error}")
                
                if st.button(f"✅ Mark as Resolved", key=f"resolve_{student_id}_{timestamp}"):
                    import shutil
                    os.makedirs("alerts/resolved", exist_ok=True)
                    
                    try:
                        shutil.move(alert['file_path'], f"alerts/resolved/{os.path.basename(alert['file_path'])}")
                        st.success("✅ Alert marked as resolved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

def get_all_alerts():
    """Récupérer toutes les alertes depuis les FICHIERS (pas MongoDB)"""
    import glob
    
    alert_files = glob.glob("alerts/CRITICAL_*.json")
    
    if not alert_files:
        return []
    
    alerts = []
    
    for file in alert_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                alert = json.load(f)
                
                # ✅ Normaliser la structure pour compatibilité
                if 'session_stats' in alert:
                    # Nouvelle structure (SESSION_ANALYSIS)
                    alert_normalized = {
                        'sender_id': alert.get('student_id'),
                        'student_id': alert.get('student_id'),
                        'timestamp': alert.get('timestamp'),
                        'risk_level': alert.get('alert_level', 'unknown'),
                        'risk_categories': [cat['category'] for cat in alert.get('risk_summary', {}).get('risk_categories', [])],
                        'message': alert.get('most_critical_message', 'N/A'),
                        'detected_emotions': [e['emotion'] for e in alert.get('session_stats', {}).get('top_emotions', [])[:3]],
                        'priority': alert.get('alert_level', 'unknown').upper()
                    }
                else:
                    # Ancienne structure (IMMEDIATE_ALERT)
                    alert_normalized = {
                        'sender_id': alert.get('student_id'),
                        'student_id': alert.get('student_id'),
                        'timestamp': alert.get('timestamp'),
                        'risk_level': alert.get('risk_level', alert.get('alert_level', 'unknown')),
                        'risk_categories': alert.get('risk_categories', []),
                        'message': alert.get('message', alert.get('first_critical_message', 'N/A')),
                        'detected_emotions': [alert.get('emotion', 'N/A')],
                        'priority': alert.get('risk_level', alert.get('alert_level', 'unknown')).upper()
                    }
                
                alerts.append(alert_normalized)
                
        except Exception as e:
            print(f"[ERROR] Failed to load alert {file}: {e}")
            continue
    
    return alerts

def generate_pdf_report(student_id):
    """Génère un rapport PDF professionnel et complet pour un étudiant"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, 
                                    TableStyle, PageBreak, HRFlowable)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from collections import Counter
    
    if not MONGODB_AVAILABLE:
        return None, "MongoDB not available"
    
    # ✅ FIX 1: Récupérer les données avec plusieurs méthodes
    print(f"[DEBUG] Searching for student: {student_id}")
    
    # Méthode 1: sender_id
    tracker = tracker_collection.find_one({'sender_id': student_id})
    
    # Méthode 2: Si non trouvé, essayer avec _id
    if not tracker:
        print(f"[DEBUG] Not found with sender_id, trying _id")
        tracker = tracker_collection.find_one({'_id': student_id})
    
    # Méthode 3: Chercher dans tous les trackers
    if not tracker:
        print(f"[DEBUG] Searching in all trackers...")
        all_trackers = list(tracker_collection.find({}))
        for t in all_trackers:
            if student_id in str(t.get('sender_id', '')):
                tracker = t
                break
    
    if not tracker:
        error_msg = f"No conversation data found for student: {student_id}"
        print(f"[ERROR] {error_msg}")
        return None, error_msg
    
    print(f"[DEBUG] Tracker found: {tracker.get('sender_id')}")
    
    # Récupérer student info
    student_info = users_collection.find_one({'student_id': student_id})
    if not student_info:
        print(f"[DEBUG] Student info not found, trying with email")
        student_info = users_collection.find_one({'_id': student_id})
    
    # ✅ FIX 2: Récupérer les slots correctement
    slots = tracker.get('slots', {})
    conversation_history = slots.get('conversation_history', [])
    risk_indicators = slots.get('risk_indicators', [])
    
    print(f"[DEBUG] Conversations found: {len(conversation_history)}")
    print(f"[DEBUG] Risk indicators found: {len(risk_indicators)}")
    
    # ✅ FIX 3: Vérifier si conversation_history est vide
    if not conversation_history or len(conversation_history) == 0:
        error_msg = "No conversation data found - conversation_history is empty"
        print(f"[ERROR] {error_msg}")
        print(f"[DEBUG] Slots content: {slots.keys()}")
        return None, error_msg
    
    # Créer le PDF en mémoire
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Configuration des styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#1e3c72'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e3c72'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderPadding=10,
        backColor=colors.HexColor('#f0f6ff'),
        leftIndent=10
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#2d3748')
    )
    
    alert_style = ParagraphStyle(
        'Alert',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#c62828'),
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#ffebee'),
        borderPadding=10
    )
    
    story = []
    
    # ==================== EN-TÊTE ====================
    story.append(Paragraph("🧠", ParagraphStyle('Logo', fontSize=48, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("EduChatMind", title_style))
    story.append(Paragraph("Rapport d'Analyse Psychologique", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#667eea'), spaceAfter=20))
    
    # ==================== INFORMATIONS GÉNÉRALES ====================
    story.append(Paragraph("📋 INFORMATIONS GÉNÉRALES", section_header_style))
    
    student_name = student_info.get('name', 'N/A') if student_info else 'N/A'
    student_class = student_info.get('student_class', 'N/A') if student_info else 'N/A'
    school_year = student_info.get('school_year', 'N/A') if student_info else 'N/A'
    
    # ✅ FIX 4: Gérer les timestamps manquants
    try:
        first_timestamp = conversation_history[0].get('timestamp', 'N/A')[:10]
        last_timestamp = conversation_history[-1].get('timestamp', 'N/A')[:10]
        period_text = f"{first_timestamp} - {last_timestamp}"
    except:
        period_text = datetime.now().strftime('%Y-%m-%d')
    
    info_data = [
        ['Nom de l\'élève:', student_name],
        ['Classe:', student_class],
        ['Année scolaire:', school_year],
        ['ID Élève:', student_id],
        ['Date du rapport:', datetime.now().strftime('%d/%m/%Y à %H:%M')],
        ['Période analysée:', period_text],
        ['Nombre de messages:', str(len(conversation_history))],
        ['Nombre d\'alertes:', str(len(risk_indicators))]
    ]
    
    info_table = Table(info_data, colWidths=[6*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f6ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#667eea'))
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ==================== RÉSUMÉ EXÉCUTIF ====================
    story.append(Paragraph("📊 RÉSUMÉ EXÉCUTIF", section_header_style))
    
    # ✅ FIX 5: Extraire les émotions correctement
    all_emotions = []
    for conv in conversation_history:
        sentiment = conv.get('sentiment', {})
        
        # Méthode 1: dominant_emotion
        dominant = sentiment.get('dominant_emotion')
        if dominant:
            all_emotions.append(dominant)
        
        # Méthode 2: detected_emotions (liste)
        detected = sentiment.get('detected_emotions', [])
        if detected:
            all_emotions.extend(detected)
    
    print(f"[DEBUG] Total emotions collected: {len(all_emotions)}")
    print(f"[DEBUG] Emotions: {all_emotions[:10]}...")
    
    if not all_emotions:
        all_emotions = ['neutral'] * len(conversation_history)
        print(f"[WARNING] No emotions found, using default 'neutral'")
    
    emotion_counts = Counter(all_emotions)
    dominant_emotions = emotion_counts.most_common(3)
    
    risk_level = "Faible"
    risk_color = colors.HexColor('#4CAF50')
    if risk_indicators:
        risk_levels = [risk.get('risk_analysis', {}).get('risk_level', 'low') for risk in risk_indicators]
        if 'critical' in risk_levels:
            risk_level = "CRITIQUE"
            risk_color = colors.HexColor('#F44336')
        elif 'high' in risk_levels:
            risk_level = "ÉLEVÉ"
            risk_color = colors.HexColor('#FF9800')
        elif 'medium' in risk_levels:
            risk_level = "MOYEN"
            risk_color = colors.HexColor('#FFC107')
    
    summary_text = f"""
    Cette analyse porte sur <b>{len(conversation_history)} messages</b> échangés avec l'élève {student_name}.
    <br/><br/>
    <b>Émotions dominantes détectées:</b><br/>
    """
    
    for emotion, count in dominant_emotions:
        percentage = (count / len(all_emotions) * 100) if all_emotions else 0
        summary_text += f"• {emotion.capitalize()}: {count} occurrences ({percentage:.1f}%)<br/>"
    
    summary_text += f"""<br/><b>Niveau de risque global:</b> <font color="{risk_color.hexval()}"><b>{risk_level}</b></font>"""
    
    if risk_level in ["CRITIQUE", "ÉLEVÉ"]:
        summary_text += """<br/><br/><font color="red"><b>⚠ ATTENTION:</b> Des indicateurs de risque psychologique ont été détectés. Un suivi professionnel est fortement recommandé.</font>"""
    
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 0.5*cm))
    
    # ==================== ANALYSE DES ÉMOTIONS ====================
    story.append(Paragraph("🎭 ANALYSE DÉTAILLÉE DES ÉMOTIONS", section_header_style))
    
    if emotion_counts:
        emotion_data = [['Émotion', 'Occurrences', 'Pourcentage', 'Interprétation']]
        total_emotions = sum(emotion_counts.values())
        
        # ✅ FIX 6: Mapping complet des 28 émotions
        emotion_interpretations = {
            'admiration': 'Admiration, respect',
            'amusement': 'Amusement, joie',
            'approval': 'Approbation',
            'caring': 'Bienveillance, empathie',
            'desire': 'Désir, envie',
            'excitement': 'Excitation, enthousiasme',
            'gratitude': 'Gratitude, reconnaissance',
            'joy': 'Joie, bonheur',
            'love': 'Amour, affection',
            'optimism': 'Optimisme, espoir',
            'pride': 'Fierté',
            'relief': 'Soulagement',
            'anger': 'Colère, frustration',
            'annoyance': 'Agacement, irritation',
            'disappointment': 'Déception',
            'disapproval': 'Désapprobation',
            'disgust': 'Dégoût',
            'embarrassment': 'Gêne, honte',
            'fear': 'Peur, anxiété',
            'grief': 'Chagrin, deuil',
            'nervousness': 'Nervosité, inquiétude',
            'remorse': 'Remords, regret',
            'sadness': 'Tristesse',
            'confusion': 'Confusion, perplexité',
            'curiosity': 'Curiosité, intérêt',
            'neutral': 'État neutre',
            'realization': 'Prise de conscience',
            'surprise': 'Surprise'
        }
        
        for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_emotions * 100)
            interpretation = emotion_interpretations.get(emotion, 'À analyser')
            emotion_data.append([
                emotion.capitalize(),
                str(count),
                f"{percentage:.1f}%",
                interpretation
            ])
        
        emotion_table = Table(emotion_data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 7.5*cm])
        emotion_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(emotion_table)
    
    story.append(Spacer(1, 0.5*cm))
    
    # ==================== ANALYSE DES RISQUES ====================
    story.append(Paragraph("⚠️ ANALYSE DES RISQUES PSYCHOLOGIQUES", section_header_style))
    
    if not risk_indicators:
        story.append(Paragraph("✓ <b>Aucun indicateur de risque significatif détecté.</b>", body_style))
    else:
        all_categories = {}
        for risk in risk_indicators:
            categories = risk.get('risk_analysis', {}).get('categories', {})
            for category, details in categories.items():
                if category not in all_categories:
                    all_categories[category] = {'count': 0, 'keywords': set()}
                all_categories[category]['count'] += details.get('count', 0)
                keywords = details.get('keywords', [])
                if keywords:
                    all_categories[category]['keywords'].update(keywords)
        
        risk_data = [['Catégorie de Risque', 'Niveau', 'Occurrences', 'Mots-clés']]
        
        risk_labels = {
            'bullying': ('🔴 Harcèlement', 'CRITIQUE'),
            'depression': ('🔴 Dépression', 'CRITIQUE'),
            'sleep': ('🟡 Troubles du sommeil', 'MOYEN'),
            'anxiety': ('🟠 Anxiété', 'ÉLEVÉ'),
            'isolation': ('🟠 Isolement social', 'ÉLEVÉ'),
            'academic': ('🟡 Difficultés scolaires', 'MOYEN')
        }
        
        for category, data in sorted(all_categories.items(), key=lambda x: x[1]['count'], reverse=True):
            label, level = risk_labels.get(category, (category.capitalize(), 'MOYEN'))
            keywords = ', '.join(list(data['keywords'])[:5]) if data['keywords'] else 'N/A'
            risk_data.append([label, level, str(data['count']), keywords])
        
        risk_table = Table(risk_data, colWidths=[4.5*cm, 3*cm, 2.5*cm, 6*cm])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F44336')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fff5f5'), colors.HexColor('#ffe0e0')])
        ]))
        
        story.append(risk_table)
        story.append(Spacer(1, 0.3*cm))
        
        critical_categories = ['bullying', 'depression']
        if any(cat in all_categories for cat in critical_categories):
            alert_text = """<b>⚠️ ALERTE - RISQUE CRITIQUE DÉTECTÉ</b><br/><br/>
            Des indicateurs graves ont été identifiés. Consultation <b>IMMÉDIATE</b> avec un professionnel requis."""
            story.append(Paragraph(alert_text, alert_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    # ==================== EXTRAITS ====================
    story.append(PageBreak())
    story.append(Paragraph("💬 EXTRAITS DE CONVERSATIONS", section_header_style))
    
    if risk_indicators:
        for i, risk in enumerate(risk_indicators[:5], 1):
            time_str = risk.get('timestamp', 'N/A')[:19]
            message = risk.get('message', 'N/A')[:300]
            categories = ', '.join(risk.get('risk_analysis', {}).get('categories', {}).keys())
            emotions = ', '.join(risk.get('detected_emotions', ['N/A']))
            
            excerpt_html = f"""<b>[{time_str}] Extrait {i}:</b><br/>
            <i>"{message}"</i><br/><br/>
            <b>🎭 Émotions:</b> {emotions}<br/>
            <font color="red"><b>⚠️ Risques:</b> {categories}</font>"""
            
            story.append(Paragraph(excerpt_html, body_style))
            story.append(Spacer(1, 0.4*cm))
            story.append(HRFlowable(width="80%", thickness=0.5, color=colors.HexColor('#e0e0e0'), spaceAfter=10))
    else:
        for i, conv in enumerate(conversation_history[:5], 1):
            time_str = conv.get('timestamp', 'N/A')[:19]
            message = conv.get('message', 'N/A')[:300]
            sentiment = conv.get('sentiment', {})
            emotion = sentiment.get('dominant_emotion', 'N/A')
            
            excerpt_html = f"""<b>[{time_str}] Message {i}:</b><br/>
            <i>"{message}"</i><br/><br/>
            <b>🎭 Émotion détectée:</b> {emotion}"""
            
            story.append(Paragraph(excerpt_html, body_style))
            story.append(Spacer(1, 0.4*cm))
            story.append(HRFlowable(width="80%", thickness=0.5, color=colors.HexColor('#e0e0e0'), spaceAfter=10))
    
    # ==================== RECOMMANDATIONS ====================
    story.append(PageBreak())
    story.append(Paragraph("📋 RECOMMANDATIONS", section_header_style))
    
    recommendations = [
        "• <b>Suivi régulier:</b> Maintenir un contact hebdomadaire avec l'élève",
        "• <b>Communication:</b> Encourager l'expression des émotions",
        "• <b>Réseau de soutien:</b> Impliquer famille et professionnels si nécessaire"
    ]
    
    if risk_indicators:
        recommendations.insert(0, "• <b>PRIORITÉ:</b> Contacter immédiatement un professionnel de santé mentale")
    
    for rec in recommendations:
        story.append(Paragraph(rec, body_style))
        story.append(Spacer(1, 0.2*cm))
    
    # ==================== FOOTER ====================
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#667eea')))
    
    footer_text = f"""<i><b>Confidentialité:</b> Document confidentiel - RGPD</i><br/>
    <i>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | EduChatMind v1.0</i>"""
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                  textColor=colors.HexColor('#666666'), alignment=TA_JUSTIFY)
    
    story.append(Paragraph(footer_text, footer_style))
    
    # ==================== GÉNÉRATION ====================
    try:
        doc.build(story)
        buffer.seek(0)
        print(f"[SUCCESS] PDF generated successfully for {student_id}")
        return buffer, None
    except Exception as e:
        error_msg = f"Error generating PDF: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return None, error_msg



# =================== PAGES ====================

def login_page():
    """Page de connexion avec design moderne"""
    
    # HTML pour le header
    st.markdown("""
        <h1 class='login-title'>EduChatMind</h1>
        <p class='login-subtitle'>AI-Powered Psychological Support</p>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    email = st.text_input("📧 Email Address", placeholder="your.email@school.com", key="email_input")
    password = st.text_input("🔑 Password", type="password", placeholder="••••••••", key="pwd_input")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(" Login", key="login_btn"):
            if email and password:
                user = authenticate_user(email, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_data = user
                    if user['role'] == 'student':
                        st.session_state.student_id = user.get('student_id', f"student_{user['_id']}")
                    st.success(f"Welcome, {user['name']}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(" Invalid credentials")
            else:
                st.warning(" Please fill all fields")
    
    
    
   
    
def student_chat_page():
    """Interface de chat pour les étudiants"""
    st.title("💬 EduChatMind - Student Chat")
    
    user_name = st.session_state.user_data.get('name', 'Student')
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.info(f" Welcome {user_name}! I'm here to listen.")
    
    with col2:
        st.markdown(f"**Student ID:** `{st.session_state.student_id}`")
    
    with col3:
        if st.button("🔄 New Chat"):
            st.session_state.conversation_history = []
            st.rerun()
    
    st.divider()
    
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.conversation_history:
            if msg['sender'] == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.write(msg['text'])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(msg['text'])
                    
                    if 'emotion' in msg and msg['emotion']:
                        st.caption(f"{get_emotion_emoji(msg['emotion'])} Detected: {msg['emotion']}")
    
    st.divider()
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Your message:",
            key="user_input",
            placeholder="Type your message here...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send 📤", use_container_width=True)
    
    if send_button and user_input:
        st.session_state.conversation_history.append({
            'sender': 'user',
            'text': user_input,
            'timestamp': datetime.now()
        })
        
        with st.spinner("Thinking..."):
            responses = send_message_to_rasa(user_input, st.session_state.student_id)
        
        for response in responses:
            st.session_state.conversation_history.append({
                'sender': 'bot',
                'text': response.get('text', ''),
                'emotion': response.get('custom', {}).get('emotion'),
                'timestamp': datetime.now()
            })
        
        st.rerun()

def admin_student_management():
    """Gestion des étudiants (Admin)"""
    st.title("👥 Student Management")
    
    tab1, tab2 = st.tabs(["➕ Add Student", "📋 View Students"])
    
    with tab1:
        st.subheader("Add New Student")
        
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name*")
                email = st.text_input("Email*")
                student_class = st.text_input("Class (e.g., 5DS2)")
            
            with col2:
                password = st.text_input("Password*", type="password", 
                                        help="Temporary password - student should change it")
                confirm_password = st.text_input("Confirm Password*", type="password")
                school_year = st.text_input("School Year (e.g., 2024-2025)")
            
            submitted = st.form_submit_button(" Create Student Account", use_container_width=True)
            
            if submitted:
                if not all([name, email, password, confirm_password]):
                    st.error(" Please fill all required fields")
                elif password != confirm_password:
                    st.error(" Passwords don't match")
                elif len(password) < 6:
                    st.error(" Password must be at least 6 characters")
                else:
                    success, message = create_student(email, password, name, student_class, school_year)
                    if success:
                        st.success(f" {message}")
                        st.info(f"""
                        **Student Credentials:**
                        - Email: {email}
                        - Password: {password}
                        
                         Please provide these credentials to the student securely.
                        """)
                    else:
                        st.error(f" {message}")
    
    with tab2:
        st.subheader("Registered Students")
        
        students = get_all_students()
        
        if students:
            for student in students:
                with st.expander(f"👤 {student['name']} - {student['email']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Class:** {student.get('student_class', 'N/A')}")
                        st.write(f"**School Year:** {student.get('school_year', 'N/A')}")
                        st.write(f"**Student ID:** {student.get('student_id', 'N/A')}")
                        st.write(f"**Created:** {student.get('created_at', 'N/A')[:10]}")
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_{student['email']}"):
                            if delete_student(student['email']):
                                st.success("Student deleted")
                                st.rerun()
                            else:
                                st.error("Error deleting student")
        else:
            st.info("No students registered yet.")

def admin_dashboard():
    """Dashboard pour les administrateurs"""
    st.title("📊 Admin Dashboard")
    
    if not MONGODB_AVAILABLE:
        st.error("⚠️ MongoDB not available. Dashboard requires database connection.")
        return
    
    # Afficher les alertes critiques en premier
    admin_critical_alerts()
    
    st.divider()
    
    # ✅ CORRECTION : Compter depuis les FICHIERS, pas MongoDB
    all_students = get_all_students()
    all_conversations = get_all_conversations()
    
    # ✅ Compter les alertes depuis les fichiers
    import glob
    alert_files = glob.glob("alerts/CRITICAL_*.json")
    total_alerts = len(alert_files)
    
    st.subheader("📈 Global Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Students", len(all_students))
    
    with col2:
        st.metric("Total Conversations", all_conversations['total_conversations'])
    
    with col3:
        st.metric("Total Alerts", total_alerts)
    
    st.divider()
    
    # ✅ Afficher les alertes récentes depuis les fichiers
    st.subheader("🚨 Recent Alerts")
    
    all_alerts = get_all_alerts()
    
    if all_alerts:
        # Trier par timestamp
        all_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Afficher les 10 dernières
        for alert in all_alerts[:10]:
            risk_level = alert.get('risk_level', 'unknown')
            color = get_risk_color(risk_level)
            
            with st.expander(
                f"🚨 {alert.get('priority', 'UNKNOWN')} - {alert['student_id']} - {alert.get('timestamp', 'N/A')[:16]}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Message:**")
                    st.write(alert.get('message', 'N/A'))
                    
                    st.write("**Emotions:**")
                    emotions = alert.get('detected_emotions', [])
                    st.write(", ".join([f"{e}" for e in emotions]))
                
                with col2:
                    st.write("**Risk Categories:**")
                    categories = alert.get('risk_categories', [])
                    st.write(", ".join(categories) if categories else "N/A")
                    
                    st.write("**Priority:**")
                    st.markdown(f"<span style='background-color: {color}; color: white; padding: 5px 10px; border-radius: 5px;'>{alert.get('priority', 'N/A')}</span>", unsafe_allow_html=True)
                
                if st.button(f"📄 Generate Report", key=f"btn_{alert['student_id']}_{alert.get('timestamp', '')}"):
                    buffer, error = generate_pdf_report(alert['student_id'])
                    if buffer:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=buffer,
                            file_name=f"report_{alert['student_id']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error(f"Error: {error}")
    else:
        st.info("No alerts found.")
# ==================== MAIN ====================

def main():
    init_admin_account()
    
    if not st.session_state.authenticated:
        login_page()
        return
    
    user_role = st.session_state.user_data.get('role')
    user_name = st.session_state.user_data.get('name')
    
    # Sidebar
    st.sidebar.title(f"👤 {user_name}")
    st.sidebar.caption(f"Role: {user_role.upper()}")
    st.sidebar.divider()
    
    if user_role == 'admin':
        page = st.sidebar.radio(
            "🧭 Navigation",
            ["📊 Dashboard", "👥 Student Management"]
        )
        
        st.sidebar.divider()
        
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.rerun()
        
        with st.sidebar.expander("ℹ️ About EduChatMind"):
            st.write("""
            **EduChatMind** - AI Psychological Support
            
            **Features:**
            - 🤖 Emotion detection (RoBERTa)
            - 🚨 Risk alerts
            - 📊 Analytics dashboard
            - 📄 PDF reports
            
            **Developed by:** Jaouadi Amani
            """)
        
        if page == "📊 Dashboard":
            admin_dashboard()
        elif page == "👥 Student Management":
            admin_student_management()
    
    elif user_role == 'student':
        st.sidebar.info("💬 Chat with our AI counselor")
        st.sidebar.divider()
        
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.conversation_history = []
            st.rerun()
        
        with st.sidebar.expander("ℹ️ About"):
            st.write("""
            **EduChatMind** helps you express your feelings.
            
            Your conversations are confidential and analyzed
            to provide better support.
            
            If you need urgent help, please contact a trusted adult.
            """)
        
        student_chat_page()

if __name__ == "__main__":
    main()