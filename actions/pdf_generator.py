from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
from typing import List, Dict, Any
from collections import Counter

class PDFReportGenerator:
    """Générateur de rapport PDF pour 28 émotions XLM-RoBERTa"""
    
    # Mapping des 28 émotions vers catégories pour l'affichage
    EMOTION_CATEGORIES = {
        # Positives
        'admiration': 'positive', 'amusement': 'positive', 'approval': 'positive',
        'caring': 'positive', 'desire': 'positive', 'excitement': 'positive',
        'gratitude': 'positive', 'joy': 'positive', 'love': 'positive',
        'optimism': 'positive', 'pride': 'positive', 'relief': 'positive',
        
        # Négatives
        'anger': 'negative', 'annoyance': 'negative', 'disappointment': 'negative',
        'disapproval': 'negative', 'disgust': 'negative', 'embarrassment': 'negative',
        'fear': 'negative', 'grief': 'negative', 'nervousness': 'negative',
        'remorse': 'negative', 'sadness': 'negative',
        
        # Neutres
        'confusion': 'neutral', 'curiosity': 'neutral', 'neutral': 'neutral',
        'realization': 'neutral', 'surprise': 'neutral'
    }
    
    # Émojis pour les émotions
    EMOTION_EMOJIS = {
        'admiration': '👏', 'amusement': '😄', 'anger': '😠', 'annoyance': '😒',
        'approval': '👍', 'caring': '🤗', 'confusion': '😕', 'curiosity': '🤔',
        'desire': '😍', 'disappointment': '😞', 'disapproval': '👎', 'disgust': '🤢',
        'embarrassment': '😳', 'excitement': '🎉', 'fear': '😨', 'gratitude': '🙏',
        'grief': '😢', 'joy': '😊', 'love': '❤️', 'nervousness': '😰',
        'neutral': '😐', 'optimism': '🌟', 'pride': '😌', 'realization': '💡',
        'relief': '😌', 'remorse': '😔', 'sadness': '😭', 'surprise': '😲'
    }
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name="CustomBody",
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY
        ))
        
        self.styles.add(ParagraphStyle(
            name='AlertText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.red,
            fontName='Helvetica-Bold'
        ))
    
    def generate_report(self, session_id: str, 
                       conversation_history: List[Dict], 
                       risk_indicators: List[Dict]) -> str:
        """Génère le rapport PDF complet"""
        
        os.makedirs("reports", exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reports/psychological_report_{session_id}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        story = []
        
        # Construire le rapport
        story.extend(self._create_header(session_id))
        story.extend(self._create_executive_summary(conversation_history, risk_indicators))
        story.extend(self._create_emotion_analysis(conversation_history))
        story.extend(self._create_risk_analysis(risk_indicators))
        story.extend(self._create_conversation_excerpts(conversation_history, risk_indicators))
        story.extend(self._create_recommendations(risk_indicators))
        story.extend(self._create_footer())
        
        try:
            doc.build(story)
            return filename
        except Exception as e:
            print(f"Erreur génération PDF: {e}")
            return None
    
    def _create_header(self, session_id: str) -> List:
        """Crée l'en-tête du rapport"""
        elements = []
        
        title = Paragraph("Rapport d'Analyse Psychologique<br/>(Détection 28 Émotions)", 
                         self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        info_data = [
            ['Session ID:', session_id],
            ['Date:', datetime.now().strftime('%d/%m/%Y')],
            ['Heure:', datetime.now().strftime('%H:%M:%S')],
            ['Modèle:', 'XLM-RoBERTa (28 émotions GoEmotions)'],
            ['Type:', 'Analyse conversationnelle avec détection multi-émotions']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_executive_summary(self, conversation_history: List[Dict], 
                                 risk_indicators: List[Dict]) -> List:
        """Crée le résumé exécutif"""
        elements = []
        
        elements.append(Paragraph("Résumé Exécutif", self.styles['SectionHeader']))
        
        # Statistiques
        total_messages = len(conversation_history)
        
        # Émotions dominantes
        dominant_emotions = [
            entry['sentiment']['dominant_emotion'] 
            for entry in conversation_history
        ]
        emotion_counts = Counter(dominant_emotions)
        top_emotion = emotion_counts.most_common(1)[0][0] if dominant_emotions else "N/A"
        
        # Sentiment global (positif/négatif/neutre)
        sentiments = [
            self.EMOTION_CATEGORIES.get(emotion, 'neutral')
            for emotion in dominant_emotions
        ]
        sentiment_counts = Counter(sentiments)
        
        positive_pct = (sentiment_counts.get('positive', 0) / total_messages * 100) if total_messages > 0 else 0
        negative_pct = (sentiment_counts.get('negative', 0) / total_messages * 100) if total_messages > 0 else 0
        neutral_pct = (sentiment_counts.get('neutral', 0) / total_messages * 100) if total_messages > 0 else 0
        
        # Niveau de risque
        risk_level = "Faible"
        if risk_indicators:
            risk_levels = [risk['risk_analysis']['risk_level'] for risk in risk_indicators]
            if "high" in risk_levels:
                risk_level = "Élevé"
            elif "medium" in risk_levels:
                risk_level = "Moyen"
        
        emoji_top = self.EMOTION_EMOJIS.get(top_emotion, '😐')
        
        summary_text = f"""
        Cette analyse couvre une conversation de <b>{total_messages} messages</b>. 
        L'émotion dominante détectée est <b>"{top_emotion}" {emoji_top}</b>.
        
        <br/><br/>
        <b>Distribution des sentiments:</b><br/>
        • Positif: {positive_pct:.1f}%<br/>
        • Négatif: {negative_pct:.1f}%<br/>
        • Neutre: {neutral_pct:.1f}%
        
        <br/><br/>
        Le niveau de risque global évalué est <b>{risk_level}</b>.
        """
        
        if risk_level in ["Élevé", "Moyen"]:
            summary_text += """<br/><br/>
            <font color="red"><b>⚠ ATTENTION:</b> Des indicateurs de risque psychologique 
            ont été détectés. Un suivi professionnel est recommandé.</font>
            """
        
        elements.append(Paragraph(summary_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_emotion_analysis(self, conversation_history: List[Dict]) -> List:
        """Crée l'analyse détaillée des émotions"""
        elements = []
        
        elements.append(Paragraph("Analyse des Émotions Détectées (28 émotions)", 
                                 self.styles['SectionHeader']))
        
        # Compter les émotions dominantes
        dominant_emotions = [
            entry['sentiment']['dominant_emotion'] 
            for entry in conversation_history
        ]
        emotion_counts = Counter(dominant_emotions)
        
        # Top 10 émotions
        emotion_data = [['Émotion', 'Occurrences', 'Pourcentage', 'Catégorie']]
        total = len(dominant_emotions)
        
        for emotion, count in emotion_counts.most_common(10):
            percentage = (count / total) * 100
            category = self.EMOTION_CATEGORIES.get(emotion, 'neutral')
            emoji = self.EMOTION_EMOJIS.get(emotion, '')
            
            # Couleur selon catégorie
            if category == 'positive':
                cat_text = '✅ Positive'
            elif category == 'negative':
                cat_text = '⚠️ Négative'
            else:
                cat_text = '⚪ Neutre'
            
            emotion_data.append([
                f"{emoji} {emotion.capitalize()}",
                str(count),
                f"{percentage:.1f}%",
                cat_text
            ])
        
        emotion_table = Table(emotion_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
        emotion_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        elements.append(emotion_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Évolution émotionnelle
        evolution_text = "<b>Évolution émotionnelle:</b> "
        if len(dominant_emotions) >= 3:
            first_third = dominant_emotions[:len(dominant_emotions)//3]
            last_third = dominant_emotions[-len(dominant_emotions)//3:]
            
            first_emotion = Counter(first_third).most_common(1)[0][0]
            last_emotion = Counter(last_third).most_common(1)[0][0]
            
            emoji_first = self.EMOTION_EMOJIS.get(first_emotion, '')
            emoji_last = self.EMOTION_EMOJIS.get(last_emotion, '')
            
            evolution_text += f"La conversation a débuté avec '{first_emotion}' {emoji_first} "
            evolution_text += f"et s'est terminée avec '{last_emotion}' {emoji_last}."
        else:
            evolution_text += "Données insuffisantes pour analyser l'évolution."
        
        elements.append(Paragraph(evolution_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_risk_analysis(self, risk_indicators: List[Dict]) -> List:
        """Crée l'analyse des risques"""
        elements = []
        
        elements.append(Paragraph("Analyse des Indicateurs de Risque", 
                                 self.styles['SectionHeader']))
        
        if not risk_indicators:
            elements.append(Paragraph(
                "✓ Aucun indicateur de risque significatif détecté.",
                self.styles['CustomBody']
            ))
            elements.append(Spacer(1, 0.3*inch))
            return elements
        
        # Agréger les catégories de risque
        all_categories = {}
        for risk in risk_indicators:
            for category, details in risk['risk_analysis']['categories'].items():
                if category not in all_categories:
                    all_categories[category] = {
                        'count': 0,
                        'keywords': set(),
                        'emotions': set()
                    }
                all_categories[category]['count'] += details['count']
                if details.get('keywords'):
                    all_categories[category]['keywords'].update(details['keywords'])
                if details.get('emotion_trigger'):
                    all_categories[category]['emotions'].add(details['emotion_trigger'])
        
        # Tableau des risques
        risk_data = [['Catégorie de Risque', 'Occurrences', 'Mots-clés / Émotions']]
        
        category_labels = {
            'bullying': '🔴 Harcèlement',
            'sleep': '🟡 Troubles du sommeil',
            'depression': '🔴 Dépression',
            'anxiety': '🟠 Anxiété',
            'isolation': '🟠 Isolement social',
            'academic': '🟡 Difficultés scolaires'
        }
        
        for category, data in sorted(all_categories.items(), 
                                     key=lambda x: x[1]['count'], reverse=True):
            label = category_labels.get(category, category.capitalize())
            
            triggers = []
            if data['keywords']:
                triggers.extend(list(data['keywords'])[:3])
            if data['emotions']:
                emotions_str = ', '.join([f"{e}" for e in list(data['emotions'])[:2]])
                triggers.append(f"[émotions: {emotions_str}]")
            
            triggers_text = ', '.join(triggers[:4])
            
            risk_data.append([
                label,
                str(data['count']),
                triggers_text
            ])
        
        risk_table = Table(risk_data, colWidths=[2*inch, 1*inch, 3*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FADBD8')])
        ]))
        
        elements.append(risk_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Alerte risque élevé
        high_risk_categories = ['bullying', 'depression']
        has_high_risk = any(cat in all_categories for cat in high_risk_categories)
        
        if has_high_risk:
            alert_text = """
            <font color="red"><b>⚠ ALERTE - RISQUE ÉLEVÉ DÉTECTÉ</b></font><br/>
            Des indicateurs de risque psychologique sérieux ont été identifiés. 
            Il est <b>fortement recommandé</b> de consulter un professionnel de la santé mentale 
            (psychologue, conseiller, ou infirmière scolaire) dans les plus brefs délais.
            """
            elements.append(Paragraph(alert_text, self.styles['AlertText']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_conversation_excerpts(self, conversation_history: List[Dict],
                                     risk_indicators: List[Dict]) -> List:
        """Crée les extraits significatifs"""
        elements = []
        
        elements.append(Paragraph("Extraits Significatifs de la Conversation", 
                                 self.styles['SectionHeader']))
        
        significant_messages = []
        
        # Messages avec émotions négatives fortes
        negative_emotions = ['sadness', 'grief', 'fear', 'anger', 'disgust']
        for entry in conversation_history:
            emotion = entry['sentiment']['dominant_emotion']
            score = entry['sentiment']['dominant_score']
            
            if emotion in negative_emotions and score > 0.6:
                significant_messages.append({
                    'message': entry['message'],
                    'emotion': emotion,
                    'score': score,
                    'timestamp': entry['timestamp'],
                    'type': 'negative_emotion'
                })
        
        # Messages avec risques
        for risk in risk_indicators:
            significant_messages.append({
                'message': risk['message'],
                'categories': list(risk['risk_analysis']['categories'].keys()),
                'emotion': risk.get('dominant_emotion', 'unknown'),
                'timestamp': risk['timestamp'],
                'type': 'risk'
            })
        
        # Limiter à 10 extraits
        significant_messages = significant_messages[:10]
        
        if not significant_messages:
            elements.append(Paragraph(
                "Aucun extrait particulièrement préoccupant identifié.",
                self.styles['CustomBody']
            ))
        else:
            for i, msg in enumerate(significant_messages, 1):
                time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M:%S')
                message_text = msg['message'][:200]
                if len(msg['message']) > 200:
                    message_text += "..."
                
                if msg['type'] == 'risk':
                    categories = ', '.join(msg['categories'])
                    emotion = msg.get('emotion', 'unknown')
                    emoji = self.EMOTION_EMOJIS.get(emotion, '')
                    
                    excerpt_text = f"""
                    <b>[{time}] Extrait {i}:</b><br/>
                    "{message_text}"<br/>
                    <font color="red"><b>⚠ Risques:</b> {categories}</font><br/>
                    <b>Émotion:</b> {emotion} {emoji}
                    """
                else:
                    emotion = msg['emotion']
                    score = msg['score']
                    emoji = self.EMOTION_EMOJIS.get(emotion, '')
                    
                    excerpt_text = f"""
                    <b>[{time}] Extrait {i}:</b><br/>
                    "{message_text}"<br/>
                    <b>Émotion forte:</b> {emotion} {emoji} (confiance: {score:.1%})
                    """
                
                elements.append(Paragraph(excerpt_text, self.styles['CustomBody']))
                elements.append(Spacer(1, 0.15*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_recommendations(self, risk_indicators: List[Dict]) -> List:
        """Crée les recommandations"""
        elements = []
        
        elements.append(Paragraph("Recommandations", self.styles['SectionHeader']))
        
        recommendations = []
        
        if risk_indicators:
            all_categories = set()
            for risk in risk_indicators:
                all_categories.update(risk['risk_analysis']['categories'].keys())
            
            if 'bullying' in all_categories:
                recommendations.append(
                    "• <b>Harcèlement:</b> Signalement immédiat aux autorités scolaires. "
                    "Contact des parents. Envisager un dépôt de plainte si nécessaire."
                )
            
            if 'depression' in all_categories:
                recommendations.append(
                    "• <b>Dépression:</b> Consultation urgente avec le psychologue scolaire "
                    "ou un professionnel de santé mentale. Informer les parents."
                )
            
            if 'sleep' in all_categories:
                recommendations.append(
                    "• <b>Troubles du sommeil:</b> Consulter un médecin. "
                    "Établir une routine de sommeil. Réduire l'exposition aux écrans."
                )
            
            if 'anxiety' in all_categories:
                recommendations.append(
                    "• <b>Anxiété:</b> Techniques de relaxation, méditation. "
                    "Suivi psychologique si symptômes persistants."
                )
            
            if 'isolation' in all_categories:
                recommendations.append(
                    "• <b>Isolement social:</b> Encourager la participation à des activités de groupe. "
                    "Soutien du conseiller d'orientation."
                )
            
            if 'academic' in all_categories:
                recommendations.append(
                    "• <b>Difficultés scolaires:</b> Soutien scolaire personnalisé. "
                    "Rencontre avec les enseignants pour adapter l'accompagnement."
                )
        
        # Recommandations générales
        recommendations.extend([
            "• <b>Suivi régulier:</b> Maintenir un contact régulier avec l'élève.",
            "• <b>Communication:</b> Encourager l'élève à exprimer ses émotions.",
            "• <b>Réseau de soutien:</b> Impliquer famille, amis et professionnels."
        ])
        
        for rec in recommendations:
            elements.append(Paragraph(rec, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_footer(self) -> List:
        """Crée le pied de page"""
        elements = []
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_text = """
        <i>Ce rapport a été généré automatiquement par un système d'analyse conversationnelle 
        utilisant l'intelligence artificielle (modèle XLM-RoBERTa pour la détection de 28 émotions). 
        Les informations présentées sont à titre indicatif et ne remplacent pas un diagnostic 
        professionnel. Pour toute situation préoccupante, veuillez consulter un professionnel 
        de la santé mentale qualifié.</i><br/><br/>
        
        <b>Confidentialité:</b> Ce document contient des informations sensibles et doit être 
        traité avec la plus stricte confidentialité conformément aux réglementations en vigueur 
        (RGPD, secret professionnel).<br/><br/>
        
        <b>Contacts d'urgence:</b> En cas de crise, contacter le numéro national de prévention 
        du suicide: 3114 (France) ou vos services d'urgence locaux.
        """
        
        elements.append(Paragraph(footer_text, self.styles['CustomBody']))
        
        return elements