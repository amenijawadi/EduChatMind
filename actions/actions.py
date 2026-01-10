from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import json
from datetime import datetime
import os
import random
import requests

# ============================================================================
# MODÈLE DE SENTIMENT - XLM-RoBERTa 28 ÉMOTIONS (via Hugging Face Inference API)
# ============================================================================
class SentimentModel:
    """Client léger pour appeler le modèle XLM-RoBERTa hébergé sur Hugging Face.

    On ne charge plus le modèle localement (pas de torch / transformers dans
    le container Render). À la place, on appelle l'API d'inférence Hugging Face
    et on reconstruit la même structure de sortie qu'avant.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentimentModel, cls).__new__(cls)

            model_path = "./models"
            print("[INFO] Initialisation SentimentModel (HF Inference API)...")

            # Charger metadata locale pour récupérer la liste d'émotions
            try:
                with open(os.path.join(model_path, "metadata.json"), "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                if "model_info" in metadata:
                    model_info = metadata["model_info"]
                    cls._instance.emotion_labels = model_info["emotion_labels"]
                else:
                    cls._instance.emotion_labels = metadata["emotion_labels"]

                cls._instance.threshold = metadata.get("threshold", 0.5)

                print(
                    f"[INFO] ✅ Metadata chargé: {len(cls._instance.emotion_labels)} émotions"
                )
            except Exception as e:
                print(f"[ERROR] Échec lecture metadata.json: {e}")
                # En dernier recours, liste vide (le modèle renverra tout de même des labels)
                cls._instance.emotion_labels = []
                cls._instance.threshold = 0.5

            # URL / Token pour l'API HF
            # HF_API_URL a la priorité, sinon on construit depuis HF_REPO_ID
            repo_id = os.getenv("HF_REPO_ID", "VOTRE_USERNAME/educhatmind-model")
            default_api_url = f"https://api-inference.huggingface.co/models/{repo_id}"

            cls._instance.hf_api_url = os.getenv("HF_API_URL", default_api_url)
            cls._instance.hf_api_token = os.getenv("HF_API_TOKEN")

            if not cls._instance.hf_api_token:
                print(
                    "[WARNING] Aucun HF_API_TOKEN défini. L'API HF publique sera utilisée si le modèle est public."
                )

            # Mapping émotions → sentiment global
            cls._instance.emotion_to_sentiment = {
                "admiration": "positive",
                "amusement": "positive",
                "approval": "positive",
                "caring": "positive",
                "desire": "positive",
                "excitement": "positive",
                "gratitude": "positive",
                "joy": "positive",
                "love": "positive",
                "optimism": "positive",
                "pride": "positive",
                "relief": "positive",
                "anger": "negative",
                "annoyance": "negative",
                "disappointment": "negative",
                "disapproval": "negative",
                "disgust": "negative",
                "embarrassment": "negative",
                "fear": "negative",
                "grief": "negative",
                "nervousness": "negative",
                "remorse": "negative",
                "sadness": "negative",
                "confusion": "neutral",
                "curiosity": "neutral",
                "neutral": "neutral",
                "realization": "neutral",
                "surprise": "neutral",
            }

            print(f"[INFO] ✅ SentimentModel prêt (HF API: {cls._instance.hf_api_url})")

        return cls._instance

    def _call_hf_api(self, text: str) -> List[Dict[str, Any]]:
        """Appelle l'API HF et renvoie une liste de {label, score}.

        On gère plusieurs formats possibles renvoyés par l'API de classification.
        """

        headers = {}
        if self.hf_api_token:
            headers["Authorization"] = f"Bearer {self.hf_api_token}"

        payload = {"inputs": text}

        try:
            resp = requests.post(self.hf_api_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[ERROR] Appel HF API échoué: {e}")
            return []

        # Cas 1 : [[{"label": "joy", "score": 0.9}, ...]]
        if isinstance(data, list) and data and isinstance(data[0], list):
            probs = data[0]
        # Cas 2 : [{"label": "joy", "score": 0.9}, ...]
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            probs = data
        else:
            print(f"[WARNING] Format de réponse HF inattendu: {data}")
            return []

        return probs

    def predict(self, text: str) -> Dict[str, Any]:
        """Prédit l'émotion dominante et calcule le sentiment global via HF API."""

        probs = self._call_hf_api(text)
        if not probs:
            # Fallback neutre en cas d'erreur
            return {
                "dominant_emotion": "neutral",
                "dominant_score": 0.0,
                "top_emotions": [("neutral", 1.0)],
                "sentiment": "neutral",
                "sentiment_id": 2,
                "confidence": 0.0,
                "all_emotion_scores": {"neutral": 1.0},
                "emotion_details": {
                    "neutral": {"score": 1.0, "is_dominant": True},
                },
            }

        # Construire un dict label -> score
        scores_by_label = {item["label"]: float(item["score"]) for item in probs}

        # S'assurer qu'on a une liste d'émotions cohérente
        if not self.emotion_labels:
            self.emotion_labels = list(scores_by_label.keys())

        # Trouver l'émotion dominante
        dominant_emotion = max(scores_by_label.items(), key=lambda x: x[1])[0]
        dominant_score = scores_by_label[dominant_emotion]

        # Top 3 émotions
        sorted_items = sorted(scores_by_label.items(), key=lambda x: x[1], reverse=True)
        top_emotions = sorted_items[:3]

        # Scores de toutes les émotions
        emotion_scores = {label: round(score, 3) for label, score in scores_by_label.items()}

        # Sentiment global
        overall_sentiment = self.emotion_to_sentiment.get(dominant_emotion, "neutral")

        sentiment_id_mapping = {"negative": 0, "neutral": 2, "positive": 4}

        return {
            "dominant_emotion": dominant_emotion,
            "dominant_score": round(dominant_score, 3),
            "top_emotions": [(e, float(s)) for e, s in top_emotions],
            "sentiment": overall_sentiment,
            "sentiment_id": sentiment_id_mapping[overall_sentiment],
            "confidence": round(dominant_score, 3),
            "all_emotion_scores": emotion_scores,
            "emotion_details": {
                emotion: {"score": emotion_scores[emotion], "is_dominant": emotion == dominant_emotion}
                for emotion in emotion_scores.keys()
            },
        }
# ============================================================================
# DÉTECTEUR DE NÉGATIONS ET INTENSIFICATEURS
# ============================================================================

class NegationIntensifierDetector:
    """Détecte les négations et intensificateurs en anglais"""
    
    NEGATIONS = [
        "not", "no", "never", "nothing", "nobody", 
        "none", "neither", "nor", "without", "hardly",
        "barely", "scarcely", "can't", "won't", "don't",
        "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't"
    ]
    
    INTENSIFIERS = [
        "very", "too", "extremely", "really", "super", 
        "quite", "completely", "totally", "absolutely",
        "so", "such", "pretty", "highly", "utterly",
        "deeply", "incredibly", "particularly"
    ]
    
    @staticmethod
    def detect(text: str) -> Dict[str, Any]:
        words = text.lower().split()
        
        negations_found = [w for w in words if w in NegationIntensifierDetector.NEGATIONS]
        intensifiers_found = [w for w in words if w in NegationIntensifierDetector.INTENSIFIERS]
        
        return {
            "has_negation": len(negations_found) > 0,
            "negations": negations_found,
            "has_intensifier": len(intensifiers_found) > 0,
            "intensifiers": intensifiers_found
        }


# ============================================================================
# DÉTECTEUR DE RISQUES - ADAPTÉ AUX 28 ÉMOTIONS
# ============================================================================

class RiskDetector:
    """Détecte les indicateurs de risque psychologique"""
    
    RISK_KEYWORDS = {
        "bullying": [
            "bully", "bullied", "mock", "insult", "hit", "push", 
            "exclude", "reject", "nobody wants", "everyone ignores",
            "cyberbullying", "attack", "violence", "threat", "harass"
        ],
        "sleep": [
            "can't sleep", "insomnia", "nightmare", "wake up",
            "tired", "exhausted", "no sleep", "sleep badly"
        ],
        "depression": [
            "depressed", "sad all the time", "suicide", "kill myself",
            "die", "disappear", "no point", "empty", "hopeless", "worthless"
        ],
        "anxiety": [
            "anxious", "anxiety", "panic", "scared", "stress",
            "nervous", "overwhelmed", "heart racing", "can't breathe"
        ],
        "isolation": [
            "lonely", "alone", "no friends", "isolated", "rejected",
            "ignored", "excluded", "nobody understands"
        ],
        "academic": [
            "grade", "failed", "failure", "bad at", "quit school",
            "unmotivated", "failing", "stupid"
        ]
    }
    
    # Mapping 28 émotions → risques
    EMOTION_RISK_MAPPING = {
        "sadness": ["depression", "isolation"],
        "grief": ["depression"],
        "anger": ["bullying"],
        "fear": ["anxiety", "bullying"],
        "nervousness": ["anxiety"],
        "embarrassment": ["bullying", "isolation"],
        "disappointment": ["academic"],
        "remorse": ["depression"],
        "disgust": ["bullying"]
    }
    
    @staticmethod
    def detect_risks(text: str, dominant_emotion: str, top_emotions: List[tuple]) -> Dict[str, Any]:
        """Détecte les risques via mots-clés ET émotions"""
        text_lower = text.lower()
        detected_risks = {}
        
        # 1. Détection par mots-clés
        for category, keywords in RiskDetector.RISK_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                detected_risks[category] = {
                    "detected": True,
                    "keywords": matches,
                    "count": len(matches),
                    "source": "keywords"
                }
        
        # 2. Détection par émotion dominante
        if dominant_emotion in RiskDetector.EMOTION_RISK_MAPPING:
            for risk_cat in RiskDetector.EMOTION_RISK_MAPPING[dominant_emotion]:
                if risk_cat not in detected_risks:
                    detected_risks[risk_cat] = {
                        "detected": True,
                        "keywords": [],
                        "count": 1,
                        "source": "emotion",
                        "emotion_trigger": dominant_emotion
                    }
        
        # 3. Détection par top émotions (si score > 0.3)
        for emotion, score in top_emotions:
            if score > 0.3 and emotion in RiskDetector.EMOTION_RISK_MAPPING:
                for risk_cat in RiskDetector.EMOTION_RISK_MAPPING[emotion]:
                    if risk_cat not in detected_risks:
                        detected_risks[risk_cat] = {
                            "detected": True,
                            "keywords": [],
                            "count": 1,
                            "source": "secondary_emotion",
                            "emotion_trigger": emotion
                        }
        
        # Niveau de risque
        high_risk_cats = ["depression", "bullying"]
        high_risk_emotions = ["sadness", "grief", "fear", "anger"]
        
        high_risk_detected = any(cat in detected_risks for cat in high_risk_cats)
        high_risk_emotion = dominant_emotion in high_risk_emotions
        
        if high_risk_detected or high_risk_emotion:
            risk_level = "high"
        elif len(detected_risks) >= 3:
            risk_level = "medium"
        elif len(detected_risks) > 0:
            risk_level = "low"
        else:
            risk_level = "none"
        
        return {
            "risk_level": risk_level,
            "categories": detected_risks,
            "total_categories": len(detected_risks),
            "emotion_based": high_risk_emotion
        }


# ============================================================================
# RASA ACTIONS
# ============================================================================

class ActionAnalyzeSentiment(Action):
    """✅ CORRIGÉ : Analyse le sentiment AVANT detection de risque"""
    
    def name(self) -> Text:
        return "action_analyze_sentiment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text')
        
        # ✅ Analyser avec le modèle 28 émotions
        sentiment_model = SentimentModel()
        sentiment_result = sentiment_model.predict(user_message)
        
        # ✅ LOGS DÉTAILLÉS
        print(f"\n{'='*70}")
        print(f"[SENTIMENT ANALYSIS]")
        print(f"Message: '{user_message}'")
        print(f"Dominant Emotion: {sentiment_result['dominant_emotion']} (score: {sentiment_result['dominant_score']:.3f})")
        print(f"Top 3 Emotions: {[(e, f'{s:.3f}') for e, s in sentiment_result['top_emotions']]}")
        print(f"Global Sentiment: {sentiment_result['sentiment']}")
        print(f"{'='*70}\n")
        
        # Détecter négations/intensificateurs
        ling_features = NegationIntensifierDetector.detect(user_message)
        
        # ✅ Stocker dans l'historique IMMÉDIATEMENT
        conversation_history = tracker.get_slot("conversation_history") or []
        detected_emotions = tracker.get_slot("detected_emotions") or []
        
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": user_message,
            "sentiment": sentiment_result,  # ✅ Contient tout : dominant_emotion, top_emotions, etc.
            "linguistic_features": ling_features
        }
        
        conversation_history.append(conversation_entry)
        detected_emotions.append(sentiment_result["dominant_emotion"])
        
        # ✅ RETOURNER TOUS LES SLOTS
        return [
            SlotSet("conversation_history", conversation_history),
            SlotSet("detected_emotions", detected_emotions),
            SlotSet("dominant_emotion", sentiment_result["dominant_emotion"]),
            SlotSet("sentiment", sentiment_result["sentiment"])
        ]


class ActionDetectRisk(Action):
    """Détecte les risques SANS créer d'alerte immédiate"""
    
    def name(self) -> Text:
        return "action_detect_risk"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text')
        
        # Récupérer l'émotion depuis conversation_history
        conversation_history = tracker.get_slot("conversation_history") or []
        
        dominant_emotion = "neutral"
        top_emotions = []
        
        if conversation_history and len(conversation_history) > 0:
            last_entry = conversation_history[-1]
            sentiment_data = last_entry.get('sentiment', {})
            
            dominant_emotion = sentiment_data.get('dominant_emotion', 'neutral')
            top_emotions = sentiment_data.get('top_emotions', [])
            
            print(f"\n[RISK DETECTION]")
            print(f"Message: '{user_message}'")
            print(f"Dominant emotion: {dominant_emotion}")
        else:
            print(f"\n[WARNING] No conversation_history found!")
        
        # Détecter les risques
        risk_analysis = RiskDetector.detect_risks(user_message, dominant_emotion, top_emotions)
        
        print(f"Risk level: {risk_analysis['risk_level']}")
        print(f"Categories: {list(risk_analysis['categories'].keys())}\n")
        
        # ✅ STOCKER uniquement (pas d'alerte)
        risk_indicators = tracker.get_slot("risk_indicators") or []
        
        if risk_analysis["total_categories"] > 0:
            risk_entry = {
                "timestamp": datetime.now().isoformat(),
                "message": user_message,
                "risk_analysis": risk_analysis,
                "dominant_emotion": dominant_emotion,
                "student_id": tracker.sender_id,
                "detected_emotions": [dominant_emotion] + [e[0] for e in top_emotions[:2]]
            }
            risk_indicators.append(risk_entry)
            print(f"ℹ️ Risk recorded (total: {len(risk_indicators)}). Alert will be created at session end.\n")
        
        return [SlotSet("risk_indicators", risk_indicators)]


class ActionEmpathicResponse(Action):
    """✅ AMÉLIORÉ : Réponses contextuelles basées sur les 28 émotions"""
    
    def name(self) -> Text:
        return "action_empathic_response"
    
    EMOTION_RESPONSES = {
        "sadness": [
            "I can see you're feeling sad. That must be really hard. What's been weighing on your mind?",
            "It's okay to feel sad. Would you like to talk about what's making you feel this way?",
            "I hear that you're going through a tough time. I'm here to listen if you want to share more."
        ],
        "grief": [
            "I understand you're going through something very difficult. Loss is never easy. How are you coping?",
            "I'm so sorry you're experiencing this pain. Would it help to talk about it?",
            "Grief can feel overwhelming. I'm here with you. Take your time."
        ],
        "anger": [
            "I can sense your frustration. What happened that made you feel this way?",
            "It sounds like something really upset you. Do you want to tell me more about it?",
            "Your anger is valid. Let's talk about what's bothering you."
        ],
        "fear": [
            "I understand you're feeling scared. What are you worried about?",
            "Fear can be overwhelming. Can you tell me what's making you anxious?",
            "It's okay to be afraid. I'm here with you. What's on your mind?"
        ],
        "nervousness": [
            "I can tell you're feeling nervous. Is there something specific worrying you?",
            "Feeling anxious is normal. What's making you feel this way?",
            "Let's take this one step at a time. What's causing this nervousness?"
        ],
        "disappointment": [
            "I hear your disappointment. That can be really tough. What happened?",
            "It's understandable to feel let down. Would you like to share what disappointed you?",
            "Disappointment is hard. Tell me more about what you're going through."
        ],
        "joy": [
            "I'm so happy to hear you're feeling joyful! What's bringing you happiness?",
            "That's wonderful! Tell me more about what's making you so happy!",
            "Your joy is contagious! What happened that made you feel this way?"
        ],
        "excitement": [
            "Your excitement is amazing! What are you looking forward to?",
            "I love your enthusiasm! Tell me what's got you so excited!",
            "That sounds exciting! Share more details with me!"
        ],
        "gratitude": [
            "It's beautiful to see your gratitude. What are you thankful for?",
            "Gratitude is such a positive emotion. What's making you feel thankful?",
            "I'm glad you're feeling grateful. Tell me more!"
        ],
        "confusion": [
            "I can see this is confusing. Let's try to work through it together. What's unclear?",
            "Confusion is normal when things feel complicated. What part is most confusing?",
            "Let's clarify this step by step. What would you like to understand better?"
        ],
        "curiosity": [
            "Your curiosity is great! What would you like to know more about?",
            "I love that you're curious! What interests you?",
            "Curiosity is a wonderful thing. What are you wondering about?"
        ],
        "neutral": [
            "I'm listening. Please continue.",
            "Go on, I'm here to understand.",
            "Tell me more about what's on your mind."
        ]
    }
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        conversation_history = tracker.get_slot("conversation_history") or []
        
        if not conversation_history:
            dispatcher.utter_message(text="I'm here to listen. How are you feeling?")
            return []
        
        last_entry = conversation_history[-1]
        dominant_emotion = last_entry["sentiment"].get("dominant_emotion", "neutral")
        user_message = last_entry.get("message", "")
        
        # Sélectionner une réponse contextuelle
        responses = self.EMOTION_RESPONSES.get(dominant_emotion, self.EMOTION_RESPONSES["neutral"])
        response = random.choice(responses)
        
        # Ajouter contexte selon mots-clés
        keywords_context = {
            "school": "It sounds like something at school is affecting you. ",
            "friend": "Friendship issues can be really difficult. ",
            "family": "Family situations can be complex. ",
            "test": "Academic pressure can be stressful. ",
            "exam": "Exams can be really stressful. ",
            "alone": "Feeling alone is really hard. ",
            "sleep": "Sleep issues can affect everything. "
        }
        
        for keyword, context in keywords_context.items():
            if keyword in user_message.lower():
                response = context + response
                break
        
        dispatcher.utter_message(text=response)
        return []

class ActionCheckSessionEnd(Action):
    """✅ Analyse globale et création d'alerte à la fin de session"""
    
    def name(self) -> Text:
        return "action_check_session_end"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        latest_intent = tracker.latest_message.get('intent', {}).get('name')
        conversation_history = tracker.get_slot("conversation_history") or []
        risk_indicators = tracker.get_slot("risk_indicators") or []
        detected_emotions = tracker.get_slot("detected_emotions") or []
        
        session_ending_intents = ['goodbye', 'affirm', 'deny']
        
        should_generate_report = (
            latest_intent in session_ending_intents and 
            len(conversation_history) >= 3
        )
        
        if should_generate_report:
            print(f"\n{'='*70}")
            print(f"[SESSION END] Analyzing complete session for {tracker.sender_id}")
            print(f"{'='*70}")
            
            # ✅ ANALYSE GLOBALE DE LA SESSION
            from collections import Counter
            
            # 1. Analyser les émotions globales
            emotion_counts = Counter(detected_emotions)
            total_emotions = len(detected_emotions)
            
            print(f"\n📊 GLOBAL EMOTION ANALYSIS:")
            print(f"Total messages: {len(conversation_history)}")
            print(f"Emotions detected: {total_emotions}")
            
            # Calculer le ratio d'émotions négatives
            negative_emotions = ['sadness', 'grief', 'anger', 'fear', 'nervousness', 
                                'disappointment', 'disgust', 'embarrassment', 'remorse']
            
            negative_count = sum(emotion_counts.get(e, 0) for e in negative_emotions)
            negative_ratio = (negative_count / total_emotions * 100) if total_emotions > 0 else 0
            
            print(f"Negative emotions: {negative_count}/{total_emotions} ({negative_ratio:.1f}%)")
            print(f"Top 3 emotions: {emotion_counts.most_common(3)}")
            
            # 2. Analyser les risques globaux
            print(f"\n⚠️  RISK ANALYSIS:")
            print(f"Risk indicators: {len(risk_indicators)}")
            
            if risk_indicators:
                # Agréger toutes les catégories de risque
                all_risk_categories = {}
                high_risk_count = 0
                critical_risk_count = 0
                
                for risk in risk_indicators:
                    risk_level = risk.get('risk_analysis', {}).get('risk_level', 'none')
                    if risk_level == 'high':
                        high_risk_count += 1
                    elif risk_level == 'critical':
                        critical_risk_count += 1
                    
                    categories = risk.get('risk_analysis', {}).get('categories', {})
                    for category, details in categories.items():
                        if category not in all_risk_categories:
                            all_risk_categories[category] = {
                                'count': 0,
                                'keywords': set(),
                                'messages': []
                            }
                        all_risk_categories[category]['count'] += 1
                        all_risk_categories[category]['keywords'].update(details.get('keywords', []))
                        all_risk_categories[category]['messages'].append(risk.get('message', ''))
                
                print(f"High risk messages: {high_risk_count}")
                print(f"Critical risk messages: {critical_risk_count}")
                print(f"Risk categories: {list(all_risk_categories.keys())}")
                
                # ✅ DÉCISION : Créer alerte selon critères globaux
                should_create_alert = False
                alert_level = "low"
                
                # Critères pour créer une alerte
                if critical_risk_count > 0 or high_risk_count >= 2:
                    should_create_alert = True
                    alert_level = "critical"
                elif high_risk_count >= 1 and negative_ratio > 60:
                    should_create_alert = True
                    alert_level = "high"
                elif 'depression' in all_risk_categories or 'bullying' in all_risk_categories:
                    should_create_alert = True
                    alert_level = "high"
                elif negative_ratio > 70:
                    should_create_alert = True
                    alert_level = "medium"
                
                print(f"\n🎯 DECISION:")
                print(f"Create alert: {should_create_alert}")
                print(f"Alert level: {alert_level}")
                
                # ✅ CRÉER L'ALERTE si nécessaire
                if should_create_alert:
                    print(f"\n🚨 [CREATING CRITICAL ALERT FOR SESSION]")
                    
                    # Trouver le message le plus préoccupant
                    most_critical_message = ""
                    if 'depression' in all_risk_categories:
                        most_critical_message = all_risk_categories['depression']['messages'][0]
                    elif 'bullying' in all_risk_categories:
                        most_critical_message = all_risk_categories['bullying']['messages'][0]
                    elif risk_indicators:
                        most_critical_message = risk_indicators[0].get('message', '')
                    
                    alert_data = {
                        "alert_type": "SESSION_ANALYSIS",
                        "student_id": tracker.sender_id,
                        "timestamp": datetime.now().isoformat(),
                        "alert_level": alert_level,
                        
                        # Statistiques globales
                        "session_stats": {
                            "total_messages": len(conversation_history),
                            "total_emotions": total_emotions,
                            "negative_emotion_ratio": round(negative_ratio, 2),
                            "top_emotions": [
                                {"emotion": e, "count": c} 
                                for e, c in emotion_counts.most_common(5)
                            ]
                        },
                        
                        # Analyse des risques
                        "risk_summary": {
                            "total_risk_messages": len(risk_indicators),
                            "high_risk_count": high_risk_count,
                            "critical_risk_count": critical_risk_count,
                            "risk_categories": [
                                {
                                    "category": cat,
                                    "count": data['count'],
                                    "keywords": list(data['keywords'])[:5]
                                }
                                for cat, data in sorted(
                                    all_risk_categories.items(), 
                                    key=lambda x: x[1]['count'], 
                                    reverse=True
                                )
                            ]
                        },
                        
                        # Message le plus critique
                        "most_critical_message": most_critical_message,
                        
                        # Métadonnées
                        "requires_immediate_attention": alert_level in ["critical", "high"],
                        "session_completed": True
                    }
                    
                    try:
                        os.makedirs("alerts", exist_ok=True)
                        alert_filename = f"alerts/CRITICAL_{tracker.sender_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(alert_filename, 'w', encoding='utf-8') as f:
                            json.dump(alert_data, f, ensure_ascii=False, indent=2)
                        print(f"🚨 [ALERT SAVED] {alert_filename}")
                        print(f"📊 Risk categories: {list(all_risk_categories.keys())}")
                        print(f"📊 Negative emotions: {negative_ratio:.1f}%")
                    except Exception as e:
                        print(f"[ERROR] Failed to save alert: {e}")
                else:
                    print(f"\n✅ [NO ALERT NEEDED] Session analysis shows acceptable risk level")
            else:
                print(f"✅ No risk indicators detected in session")
            
            print(f"{'='*70}\n")
            
            # Sauvegarder conversation et générer PDF
            conversation_data = {
                "session_id": tracker.sender_id,
                "timestamp": datetime.now().isoformat(),
                "conversation_history": conversation_history,
                "detected_emotions": detected_emotions,
                "risk_indicators": risk_indicators,
                "session_ended": True
            }
            
            filename = f"conversations/conversation_{tracker.sender_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            try:
                os.makedirs("conversations", exist_ok=True)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(conversation_data, f, ensure_ascii=False, indent=2)
                print(f"[SAVE] Session saved: {filename}")
                
                # Générer PDF
                try:
                    from actions.pdf_generator import PDFReportGenerator
                    pdf_generator = PDFReportGenerator()
                    pdf_path = pdf_generator.generate_report(
                        session_id=tracker.sender_id,
                        conversation_history=conversation_history,
                        risk_indicators=risk_indicators
                    )
                    
                    if pdf_path:
                        print(f"[PDF] Auto-generated report: {pdf_path}")
                        dispatcher.utter_message(text="Thank you for sharing. Take care! 💙")
                except Exception as e:
                    print(f"[ERROR] PDF generation failed: {e}")
                
            except Exception as e:
                print(f"[ERROR] Failed to save session: {e}")
        
        return []

class ActionSaveConversation(Action):
    """Sauvegarde la conversation en JSON"""
    
    def name(self) -> Text:
        return "action_save_conversation"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        conversation_data = {
            "session_id": tracker.sender_id,
            "timestamp": datetime.now().isoformat(),
            "conversation_history": tracker.get_slot("conversation_history"),
            "detected_emotions": tracker.get_slot("detected_emotions"),
            "risk_indicators": tracker.get_slot("risk_indicators")
        }
        
        filename = f"conversations/conversation_{tracker.sender_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            os.makedirs("conversations", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            print(f"[SAVE] Conversation saved: {filename}")
        except Exception as e:
            print(f"[ERROR] Save error: {e}")
        
        return []


class ActionGeneratePDFReport(Action):
    """Génère un rapport PDF de la conversation"""
    
    def name(self) -> Text:
        return "action_generate_pdf_report"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            from actions.pdf_generator import PDFReportGenerator
        except ImportError:
            dispatcher.utter_message(text="Error: PDFReportGenerator not found.")
            return []
        
        conversation_history = tracker.get_slot("conversation_history") or []
        risk_indicators = tracker.get_slot("risk_indicators") or []
        
        if not conversation_history:
            dispatcher.utter_message(text="Not enough data to generate a report.")
            return []
        
        pdf_generator = PDFReportGenerator()
        pdf_path = pdf_generator.generate_report(
            session_id=tracker.sender_id,
            conversation_history=conversation_history,
            risk_indicators=risk_indicators
        )
        
        if pdf_path:
            dispatcher.utter_message(text=f"📄Report generated: {pdf_path}")
            print(f"[PDF] Report created: {pdf_path}")
        else:
            dispatcher.utter_message(text="Error while generating the report.")
        
        return []


# ============================================================================
# NEW ACTIONS: Name Extraction and Follow-Up
# ============================================================================

class ActionExtractStudentName(Action):
    """Extracts and saves the student's name from their message"""
    
    def name(self) -> Text:
        return "action_extract_student_name"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        import re
        
        # Check if we already have a name
        current_name = tracker.get_slot("student_name")
        
        if current_name:
            # Name already known
            return []
        
        # Extract name from message
        message = tracker.latest_message.get('text', '').strip()
        
        # Patterns to extract name
        # Ex: "My name is John", "I'm Sarah", "Call me Alex", or just "John"
        patterns = [
            r"(?:my name is|i'm|i am|call me|this is|name's)\s+([A-Z][a-z]+)",
            r"^([A-Z][a-z]+)$"  # Just a proper noun
        ]
        
        extracted_name = None
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted_name = match.group(1).capitalize()
                break
        
        if extracted_name:
            # Name found!
            greetings = [
                f"Nice to meet you, {extracted_name}! 😊 I'll remember your name for our conversations.",
                f"Hi {extracted_name}! 🌟 I'm glad to know your name. How can I help you today?",
                f"Thank you, {extracted_name}! 💙  I'm here to support you."
            ]
            dispatcher.utter_message(text=random.choice(greetings))
            return [SlotSet("student_name", extracted_name)]
        
        return []


class ActionFollowUp(Action):
    """Asks intelligent follow-up questions based on context"""
    
    def name(self) -> Text:
        return "action_follow_up"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get context
        dominant_emotion = tracker.get_slot("dominant_emotion") or "neutral"
        student_name = tracker.get_slot("student_name") or ""
        conversation_history = tracker.get_slot("conversation_history") or []
        previous_emotion = tracker.get_slot("previous_emotion")
        
        # Count messages
        num_messages = len(conversation_history)
        
        # Emotion categories
        negative_emotions = ["sadness", "anger", "fear", "disappointment", "grief", "nervousness"]
        positive_emotions = ["joy", "amusement", "love", "excitement", "gratitude", "pride"]
        
        name_prefix = f"{student_name}, " if student_name else ""
        
        # Question based on message number
        if num_messages == 1 and dominant_emotion in negative_emotions:
            # First negative message - explore duration
            questions = [
                f"I'm here to really understand what you're going through{', ' + student_name if student_name else ''}. How long have you been feeling this way?",
                f"{name_prefix}when did you start feeling like this?",
                f"Thank you for sharing{', ' + student_name if student_name else ''}. Is this a recent feeling or has it been building up?"
            ]
            dispatcher.utter_message(text=random.choice(questions))
        
        elif num_messages == 2:
            # Second message - explore cause
            questions = [
                f"Thank you for sharing more{', ' + student_name if student_name else ''}. Has something specific triggered this feeling, or has it been gradual?",
                f"{name_prefix}can you tell me if there's a particular event that made you feel this way?",
                f"I appreciate your openness{', ' + student_name if student_name else ''}. What do you think is the main cause of how you're feeling?"
            ]
            dispatcher.utter_message(text=random.choice(questions))
        
        elif num_messages >= 3 and dominant_emotion in negative_emotions:
            # Third message - suggest support
            questions = [
                f"{name_prefix}have you talked to anyone else about how you're feeling? Sometimes it helps to share with someone you trust.",
                f"I appreciate you opening up to me{', ' + student_name if student_name else ''}. Is there a trusted adult or friend you could talk to about this?",
                f"{name_prefix}you're being really brave. Would you consider talking to a school counselor or trusted teacher about this?"
            ]
            dispatcher.utter_message(text=random.choice(questions))
        
        # Track emotional changes
        elif previous_emotion in negative_emotions and dominant_emotion in positive_emotions:
            # Improvement detected!
            responses = [
                f"I'm really glad to see you're feeling better{', ' + student_name if student_name else ''}! 😊 What helped you feel this way?",
                f"{name_prefix}I can feel the positive change! What happened that made things better?",
                f"This is wonderful{', ' + student_name if student_name else ''}! 🌟 Something good must have happened - what was it?"
            ]
            dispatcher.utter_message(text=random.choice(responses))
        
        return []