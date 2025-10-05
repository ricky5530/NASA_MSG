"""
채팅 서비스
OpenAI API와 RAG 시스템을 결합한 대화형 AI 서비스
"""

import logging
import re
from typing import Dict, Any, Optional, List
from openai import OpenAI
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드 (chat_service가 독립적으로 실행될 수 있도록)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class ChatService:
    """RAG 기반 채팅 서비스"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
        self.conversations = {}  # 대화 히스토리 저장
        
        # OpenAI 클라이언트 초기화
        api_key = os.getenv("OPENAI_API_KEY")
        logger.info(f"🔑 API 키 존재 여부: {api_key is not None}, 길이: {len(api_key) if api_key else 0}")
        
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                logger.info("✅ ChatService OpenAI 클라이언트 초기화 완료")
            except Exception as e:
                logger.error(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
                self.client = None
        else:
            logger.error("❌ OPENAI_API_KEY 환경변수가 없습니다!")
            self.client = None
        
        # 기본 시스템 프롬프트 (한국어)
        self.base_system_prompt = """
        당신은 NASA의 우주 생물학 전문 AI 어시스턴트입니다. 
        
        역할:
        - 우주 생물학, 미세중력 실험, 우주 환경에서의 생명체 연구에 대한 전문적인 답변 제공
        - NASA OSDR (Open Science Data Repository)의 실험 데이터를 기반으로 정확한 정보 제공
        - 복잡한 과학적 개념을 이해하기 쉽게 설명
        
        답변 가이드라인:
        1. 제공된 컨텍스트를 우선적으로 활용하여 답변
        2. 과학적으로 정확하고 객관적인 정보 제공
        3. 출처가 명확한 정보만 사용
        4. 모르는 내용은 솔직히 모른다고 답변
        5. 사용자의 언어로 친근하고 전문적인 톤으로 답변
        
        답변 형식:
        - 핵심 답변을 먼저 제시
        - 관련 실험이나 연구 결과 인용
        - 추가 궁금한 점이나 관련 주제 제안
        """
    
    def get_system_prompt_for_language(self, language: str) -> str:
        """언어별 시스템 프롬프트 생성"""
        language_prompts = {
            "korean": """
당신은 NASA의 우주 생물학 전문 AI 어시스턴트입니다. 

역할:
- 우주 생물학, 미세중력 실험, 우주 환경에서의 생명체 연구에 대한 전문적인 답변 제공
- NASA OSDR (Open Science Data Repository)의 실험 데이터를 기반으로 정확한 정보 제공
- 복잡한 과학적 개념을 이해하기 쉽게 설명

답변 가이드라인:
1. 제공된 컨텍스트를 우선적으로 활용하여 답변
2. 과학적으로 정확하고 객관적인 정보 제공
3. 출처가 명확한 정보만 사용
4. 모르는 내용은 솔직히 모른다고 답변
5. 한국어로 친근하고 전문적인 톤으로 답변

답변 형식 (Markdown 사용):
- **제목**: # 또는 ## 사용하여 구조화
- **강조**: **굵게**, *기울임* 적극 활용
- **목록**: - 또는 1. 사용
- **인용**: > 블록 사용하여 중요한 인용문 표시
- **이미지**: 관련 NASA 이미지가 있다면 ![설명](https://images.nasa.gov/관련이미지.jpg) 형식으로 포함
- **링크**: [텍스트](URL) 형식으로 추가 자료 연결
- 시각적으로 풍부하고 구조화된 답변 작성

답변 구조:
1. 핵심 답변을 제목과 함께 먼저 제시
2. 상세 설명을 부제목과 목록으로 구조화
3. 관련 실험이나 연구 결과를 인용문으로 강조
4. 가능하다면 관련 NASA 이미지 포함
5. 추가 궁금한 점이나 관련 주제를 링크와 함께 제안
""",
            "english": """
You are a NASA Space Biology expert AI assistant.

Role:
- Provide expert answers on space biology, microgravity experiments, and life research in space environments
- Provide accurate information based on NASA OSDR (Open Science Data Repository) experimental data
- Explain complex scientific concepts in an understandable way

Response Guidelines:
1. Prioritize using the provided context in your answers
2. Provide scientifically accurate and objective information
3. Only use information with clear sources
4. Honestly admit when you don't know something
5. Respond in a friendly and professional tone in English

Response Format (Use Markdown):
- **Headings**: Use # or ## to structure your response
- **Emphasis**: Use **bold**, *italic* extensively
- **Lists**: Use - or 1. for clear organization
- **Quotes**: Use > blocks for important citations
- **Images**: Include relevant NASA images using ![description](https://images.nasa.gov/relevant-image.jpg) format when applicable
- **Links**: Use [text](URL) format for additional resources
- Create visually rich and well-structured responses

Response Structure:
1. Present the core answer with appropriate heading first
2. Organize detailed explanations with subheadings and lists
3. Highlight relevant experiments or research results with quote blocks
4. Include relevant NASA images when possible
5. Suggest additional questions or related topics with links
""",
            "japanese": """
あなたはNASAの宇宙生物学専門AIアシスタントです。

役割:
- 宇宙生物学、微小重力実験、宇宙環境での生命研究について専門的な回答を提供
- NASA OSDR (Open Science Data Repository) の実験データに基づいて正確な情報を提供
- 複雑な科学的概念を分かりやすく説明

回答ガイドライン:
1. 提供されたコンテキストを優先的に活用して回答
2. 科学的に正確で客観的な情報を提供
3. 出典が明確な情報のみを使用
4. 知らない内容は正直に知らないと答える
5. 日本語で親しみやすく専門的なトーンで回答

**必須: 回答形式はMarkdownを使用すること**:
- **見出し**: # または ## を使用して構造化
- **強調**: **太字**、*斜体* を積極的に活用
- **リスト**: - または 1. を使用
- **引用**: > ブロックを使用して重要な引用を表示
- **画像**: 関連するNASA画像があれば ![説明](https://images.nasa.gov/関連画像.jpg) 形式で含める
- **リンク**: [テキスト](URL) 形式で追加資料を接続
- 視覚的に豊かで構造化された回答を作成

回答構造:
1. コアな回答を見出しと共に最初に提示
2. 詳細説明をサブ見出しとリストで構造化
3. 関連する実験や研究結果を引用ブロックで強調
4. 可能であれば関連NASA画像を含める
5. 追加の質問や関連トピックをリンク付きで提案
""",
            "chinese": """
您是NASA空间生物学专家AI助手。

角色:
- 提供空间生物学、微重力实验、太空环境中生命研究的专业答案
- 基于NASA OSDR (开放科学数据存储库) 实验数据提供准确信息
- 以易懂的方式解释复杂的科学概念

回答指南:
1. 优先使用提供的上下文进行回答
2. 提供科学准确和客观的信息
3. 只使用来源明确的信息
4. 诚实承认不知道的内容
5. 用中文以友好和专业的语调回答

**必须: 使用Markdown格式回答**:
- 标题: 使用 # 或 ## 构建结构
- 强调: 使用 **粗体**, *斜体*
- 列表: 使用 - 或 1.
- 引用: 使用 > 块
- 图片: ![说明](URL)
- 链接: [文本](URL)

回答格式:
- 首先提出核心答案
- 引用相关实验或研究结果
- 建议额外问题或相关主题
""",
            "spanish": """
Eres un asistente de IA experto en Biología Espacial de la NASA.

Rol:
- Proporcionar respuestas expertas sobre biología espacial, experimentos de microgravedad e investigación de vida en entornos espaciales
- Proporcionar información precisa basada en datos experimentales de NASA OSDR (Repositorio de Datos de Ciencia Abierta)
- Explicar conceptos científicos complejos de manera comprensible

Pautas de Respuesta:
1. Priorizar el uso del contexto proporcionado en tus respuestas
2. Proporcionar información científica precisa y objetiva
3. Solo usar información con fuentes claras
4. Admitir honestamente cuando no sepas algo
5. Responder en español con un tono amigable y profesional

**Obligatorio: Usar formato Markdown**:
- Encabezados: # o ##
- Énfasis: **negrita**, *cursiva*
- Listas: - o 1.
- Citas: > bloque
- Imágenes: ![descripción](URL)
- Enlaces: [texto](URL)

Formato de Respuesta:
- Presentar la respuesta principal primero
- Citar experimentos o resultados de investigación relevantes
- Sugerir preguntas adicionales o temas relacionados
""",
            "french": """
Vous êtes un assistant IA expert en Biologie Spatiale de la NASA.

Rôle:
- Fournir des réponses expertes sur la biologie spatiale, les expériences de microgravité et la recherche sur la vie dans les environnements spatiaux
- Fournir des informations précises basées sur les données expérimentales de NASA OSDR (Dépôt de Données de Science Ouverte)
- Expliquer des concepts scientifiques complexes de manière compréhensible

Directives de Réponse:
1. Prioriser l'utilisation du contexte fourni dans vos réponses
2. Fournir des informations scientifiques précises et objectives
3. N'utiliser que des informations avec des sources claires
4. Admettre honnêtement quand vous ne savez pas quelque chose
5. Répondre en français avec un ton amical et professionnel

Format de Réponse:
- Présenter la réponse principale en premier
- Citer des expériences ou résultats de recherche pertinents
- Suggérer des questions supplémentaires ou des sujets connexes
""",
            "german": """
Sie sind ein NASA Weltraum-Biologie Experte KI-Assistent.

Rolle:
- Experte Antworten zu Weltraum-Biologie, Mikrogravitations-Experimenten und Lebensforschung in Weltraum-Umgebungen bereitstellen
- Präzise Informationen basierend auf NASA OSDR (Open Science Data Repository) experimentellen Daten bereitstellen
- Komplexe wissenschaftliche Konzepte verständlich erklären

Antwort-Richtlinien:
1. Priorisieren Sie die Verwendung des bereitgestellten Kontexts in Ihren Antworten
2. Wissenschaftlich genaue und objektive Informationen bereitstellen
3. Nur Informationen mit klaren Quellen verwenden
4. Ehrlich zugeben, wenn Sie etwas nicht wissen
5. Auf Deutsch in freundlichem und professionellem Ton antworten

Antwort-Format:
- Hauptantwort zuerst präsentieren
- Relevante Experimente oder Forschungsergebnisse zitieren
- Zusätzliche Fragen oder verwandte Themen vorschlagen
""",
            "portuguese": """
Você é um assistente de IA especialista em Biologia Espacial da NASA.

Função:
- Fornecer respostas especializadas sobre biologia espacial, experimentos de microgravidade e pesquisa de vida em ambientes espaciais
- Fornecer informações precisas baseadas em dados experimentais do NASA OSDR (Repositório de Dados de Ciência Aberta)
- Explicar conceitos científicos complexos de maneira compreensível

Diretrizes de Resposta:
1. Priorizar o uso do contexto fornecido em suas respostas
2. Fornecer informações científicas precisas e objetivas
3. Usar apenas informações com fontes claras
4. Admitir honestamente quando não souber algo
5. Responder em português com tom amigável e profissional

Formato de Resposta:
- Apresentar a resposta principal primeiro
- Citar experimentos ou resultados de pesquisa relevantes
- Sugerir perguntas adicionais ou tópicos relacionados
""",
            "russian": """
Вы экспертный ИИ-помощник NASA по космической биологии.

Роль:
- Предоставлять экспертные ответы по космической биологии, экспериментам в условиях микрогравитации и исследованиям жизни в космических условиях
- Предоставлять точную информацию на основе экспериментальных данных NASA OSDR (Открытое хранилище научных данных)
- Объяснять сложные научные концепции понятным способом

Руководство по ответам:
1. Приоритетно использовать предоставленный контекст в ваших ответах
2. Предоставлять научно точную и объективную информацию
3. Использовать только информацию с четкими источниками
4. Честно признавать, когда вы чего-то не знаете
5. Отвечать на русском языке дружелюбным и профессиональным тоном

Формат ответа:
- Сначала представить основной ответ
- Цитировать релевантные эксперименты или результаты исследований
- Предлагать дополнительные вопросы или связанные темы
""",
            "hindi": """
आप NASA के अंतरिक्ष जीव विज्ञान विशेषज्ञ AI सहायक हैं।

भूमिका:
- अंतरिक्ष जीव विज्ञान, सूक्ष्म गुरुत्वाकर्षण प्रयोगों, और अंतरिक्ष वातावरण में जीवन अनुसंधान पर विशेषज्ञ उत्तर प्रदान करना
- NASA OSDR (ओपन साइंस डेटा रिपॉजिटरी) के प्रयोगात्मक डेटा के आधार पर सटीक जानकारी प्रदान करना
- जटिल वैज्ञानिक अवधारणाओं को समझने योग्य तरीके से समझाना

उत्तर दिशानिर्देश:
1. अपने उत्तरों में प्रदान किए गए संदर्भ का प्राथमिकता से उपयोग करना
2. वैज्ञानिक रूप से सटीक और उद्देश्यपूर्ण जानकारी प्रदान करना
3. केवल स्पष्ट स्रोतों वाली जानकारी का उपयोग करना
4. ईमानदारी से स्वीकार करना जब आप कुछ नहीं जानते
5. हिंदी में मित्रतापूर्ण और पेशेवर स्वर में उत्तर देना

उत्तर प्रारूप:
- पहले मुख्य उत्तर प्रस्तुत करना
- प्रासंगिक प्रयोगों या शोध परिणामों का उद्धरण देना
- अतिरिक्त प्रश्न या संबंधित विषय सुझाना
""",
            "arabic": """
أنت مساعد ذكي متخصص في علم الأحياء الفضائي في وكالة ناسا.

الدور:
- تقديم إجابات خبير حول علم الأحياء الفضائي وتجارب الجاذبية الصغرى وأبحاث الحياة في البيئات الفضائية
- تقديم معلومات دقيقة بناءً على البيانات التجريبية لـ NASA OSDR (مستودع البيانات العلمية المفتوحة)
- شرح المفاهيم العلمية المعقدة بطريقة مفهومة

إرشادات الإجابة:
1. إعطاء الأولوية لاستخدام السياق المقدم في إجاباتك
2. تقديم معلومات علمية دقيقة وموضوعية
3. استخدام المعلومات ذات المصادر الواضحة فقط
4. الاعتراف بصدق عندما لا تعرف شيئاً
5. الإجابة باللغة العربية بنبرة ودية ومهنية

تنسيق الإجابة:
- تقديم الإجابة الأساسية أولاً
- الاستشهاد بالتجارب ذات الصلة أو نتائج البحث
- اقتراح أسئلة إضافية أو مواضيع ذات صلة
"""
        }
        
        # 기본값을 english로 변경 (unknown 언어가 들어와도 한국어로 고정되지 않도록)
        return language_prompts.get(language, language_prompts["english"])

    async def get_response(self, message: str, conversation_id: Optional[str] = None, language: str = "english") -> Dict[str, Any]:
        """사용자 메시지에 대한 AI 응답 생성"""
        logger.info(f"🌍 Language received from main: {language}")
        
        try:
            # 대화 ID 생성 또는 기존 대화 로드
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                self.conversations[conversation_id] = []
            
            # RAG 전체 응답 가져오기 (answer, sources, figures 포함)
            try:
                rag_response = self.rag_service.get_detailed_response(message)
                
                # RAG가 이미 완벽한 답변을 만들었으면 그대로 사용
                if rag_response and rag_response.get("answer"):
                    answer = rag_response["answer"]
                    sources = rag_response.get("sources", [])
                    
                    # 대화 히스토리 저장
                    if conversation_id not in self.conversations:
                        self.conversations[conversation_id] = []
                    self.conversations[conversation_id].append({
                        "user": message,
                        "assistant": answer
                    })
                    
                    logger.info(f"✅ RAG response used directly")
                    return {
                        "answer": answer,
                        "sources": sources,
                        "conversation_id": conversation_id
                    }
                else:
                    # RAG 실패시 빈 컨텍스트
                    context = ""
                    sources = []
            except Exception as e:
                logger.error(f"❌ RAG search failed: {e}")
                context = ""
                sources = []
            
            # OpenAI API 사용 불가능한 경우 기본 응답
            if not self.client:
                error_messages = {
                    "korean": "안녕하세요! 저는 NASA 우주 생물학 전문 AI 어시스턴트입니다. 현재 AI 응답 생성 서비스가 일시적으로 제한되어 있지만, 여전히 도움을 드릴 수 있습니다. 궁금한 것이 있으시면 언제든 질문해주세요!",
                    "english": "Hello! I'm a NASA space biology AI assistant. While the AI response generation service is temporarily limited, I'm still here to help. Feel free to ask me anything!",
                    "japanese": "こんにちは！私はNASA宇宙生物学の専門AIアシスタントです。AI応答生成サービスが一時的に制限されていますが、まだお手伝いできます。何でもお気軽にお聞きください！",
                    "chinese": "您好！我是NASA太空生物学专业AI助手。虽然AI响应生成服务暂时受限，但我仍可以为您提供帮助。有任何问题请随时询问！",
                    "spanish": "¡Hola! Soy un asistente de IA especializado en biología espacial de la NASA. Aunque el servicio de generación de respuestas de IA está temporalmente limitado, aún puedo ayudarte. ¡No dudes en preguntar!",
                    "french": "Bonjour ! Je suis un assistant IA spécialisé en biologie spatiale de la NASA. Bien que le service de génération de réponses IA soit temporairement limité, je peux encore vous aider. N'hésitez pas à poser des questions !",
                    "german": "Hallo! Ich bin ein KI-Assistent für Weltraumbiologie der NASA. Obwohl der KI-Antwortgenerierungsdienst vorübergehend eingeschränkt ist, kann ich Ihnen trotzdem helfen. Fragen Sie gerne!",
                    "portuguese": "Olá! Sou um assistente de IA especializado em biologia espacial da NASA. Embora o serviço de geração de respostas de IA esteja temporariamente limitado, ainda posso ajudá-lo. Sinta-se à vontade para perguntar!",
                    "russian": "Здравствуйте! Я ИИ-помощник по космической биологии NASA. Хотя сервис генерации ответов ИИ временно ограничен, я все еще могу помочь. Задавайте вопросы!",
                    "hindi": "नमस्ते! मैं NASA स्पेस बायोलॉजी का एक विशेषज्ञ AI सहायक हूँ। हालांकि AI प्रतिक्रिया सेवा अस्थायी रूप से सीमित है, मैं अभी भी आपकी सहायता कर सकता हूँ। कोई भी प्रश्न पूछने में संकोच न करें!",
                    "arabic": "مرحباً! أنا مساعد ذكي متخصص في علم الأحياء الفضائي في ناسا. رغم أن خدمة توليد الاستجابات الذكية محدودة مؤقتاً، ما زال بإمكاني مساعدتك. لا تتردد في طرح أي سؤال!"
                }
                error_msg = error_messages.get(language, error_messages["korean"])
                return {
                    "answer": error_msg,
                    "sources": sources,
                    "conversation_id": conversation_id
                }
            
            # 언어별 시스템 프롬프트 가져오기
            system_prompt = self.get_system_prompt_for_language(language)
            
            # 대화 히스토리 구성
            messages = [{"role": "system", "content": system_prompt}]
            
            # 기존 대화 히스토리 추가 (최근 5개만)
            if conversation_id in self.conversations:
                recent_history = self.conversations[conversation_id][-5:]
                for hist in recent_history:
                    messages.append({"role": "user", "content": hist["user"]})
                    messages.append({"role": "assistant", "content": hist["assistant"]})
            
            # 언어별 컨텍스트 메시지 생성
            context_templates = {
                "korean": "다음은 관련된 NASA 우주 생물학 실험 데이터입니다:\n\n{context}\n\n사용자 질문: {message}",
                "english": "The following is relevant NASA space biology experimental data:\n\n{context}\n\nUser question: {message}",
                "japanese": "以下は関連するNASA宇宙生物学実験データです：\n\n{context}\n\nユーザーの質問：{message}",
                "chinese": "以下是相关的NASA空间生物学实验数据：\n\n{context}\n\n用户问题：{message}",
                "spanish": "Los siguientes son datos experimentales relevantes de biología espacial de la NASA:\n\n{context}\n\nPregunta del usuario: {message}",
                "french": "Voici les données expérimentales pertinentes de biologie spatiale de la NASA :\n\n{context}\n\nQuestion de l'utilisateur : {message}",
                "german": "Folgendes sind relevante NASA-Weltraum-Biologie-Experimentaldaten:\n\n{context}\n\nBenutzerfrage: {message}",
                "portuguese": "Os seguintes são dados experimentais relevantes de biologia espacial da NASA:\n\n{context}\n\nPergunta do usuário: {message}",
                "russian": "Следующие данные являются релевантными экспериментальными данными NASA по космической биологии:\n\n{context}\n\nВопрос пользователя: {message}",
                "hindi": "निम्नलिखित प्रासंगिक NASA अंतरिक्ष जीव विज्ञान प्रयोगात्मक डेटा है:\n\n{context}\n\nउपयोगकर्ता का प्रश्न: {message}",
                "arabic": "البيانات التجريبية ذات الصلة في علم الأحياء الفضائي لوكالة ناسا هي كما يلي:\n\n{context}\n\nسؤال المستخدم: {message}"
            }
            
            # 컨텍스트가 있는 경우 추가
            if context:
                context_template = context_templates.get(language, context_templates["english"])
                context_message = context_template.format(context=context, message=message)
            else:
                # 컨텍스트가 없는 경우의 언어별 메시지
                no_context_templates = {
                    "korean": f"사용자 질문: {message}",
                    "english": f"User question: {message}",
                    "japanese": f"ユーザーの質問：{message}",
                    "chinese": f"用户问题：{message}",
                    "spanish": f"Pregunta del usuario: {message}",
                    "french": f"Question de l'utilisateur : {message}",
                    "german": f"Benutzerfrage: {message}",
                    "portuguese": f"Pergunta do usuário: {message}",
                    "russian": f"Вопрос пользователя: {message}",
                    "hindi": f"उपयोगकर्ता का प्रश्न: {message}",
                    "arabic": f"سؤال المستخدم: {message}"
                }
                context_message = no_context_templates.get(language, no_context_templates["english"])
            
            messages.append({"role": "user", "content": context_message})
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # 대화 히스토리 저장 (conversation_id가 없으면 초기화)
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
                
            self.conversations[conversation_id].append({
                "user": message,
                "assistant": ai_response,
                "timestamp": datetime.now().isoformat(),
                "sources_used": len(sources)
            })
            
            # 대화 히스토리 길이 제한 (최대 20개)
            if len(self.conversations[conversation_id]) > 20:
                self.conversations[conversation_id] = self.conversations[conversation_id][-20:]
            
            return {
                "answer": ai_response,
                "sources": sources,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"❌ 채팅 응답 생성 실패: {e}", exc_info=True)
            
            # 오류 발생시 간단한 기본 응답 생성
            error_templates = {
                "korean": "죄송합니다. 현재 AI 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "english": "Sorry, there's a temporary issue with the AI service. Please try again in a moment.",
                "japanese": "申し訳ありません。AIサービスに一時的な問題が発生しています。しばらくしてからもう一度お試しください。",
                "chinese": "抱歉，AI服务暂时出现问题。请稍后再试。",
                "spanish": "Lo siento, hay un problema temporal con el servicio de IA. Inténtelo de nuevo en un momento.",
                "french": "Désolé, il y a un problème temporaire avec le service IA. Veuillez réessayer dans un moment.",
                "german": "Entschuldigung, es gibt ein temporäres Problem mit dem KI-Service. Bitte versuchen Sie es in einem Moment erneut.",
                "portuguese": "Desculpe, há um problema temporário com o serviço de IA. Tente novamente em um momento.",
                "russian": "Извините, возникла временная проблема с ИИ-сервисом. Попробуйте еще раз через некоторое время.",
                "hindi": "क्षमा करें, AI सेवा में अस्थायी समस्या है। कृपया एक पल बाद पुनः प्रयास करें।",
                "arabic": "عذراً، هناك مشكلة مؤقتة في خدمة الذكاء الاصطناعي. يرجى المحاولة مرة أخرى بعد قليل."
            }
            
            no_context_error_templates = {
                "korean": "죄송합니다. 현재 답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
                "english": "Sorry, I cannot generate a response at the moment. Please try again later.",
                "japanese": "申し訳ありません。現在応答を生成できません。後でもう一度お試しください。",
                "chinese": "抱歉，目前无法生成响应。请稍后再试。",
                "spanish": "Lo siento, no puedo generar una respuesta en este momento. Inténtelo más tarde.",
                "french": "Désolé, je ne peux pas générer de réponse pour le moment. Veuillez réessayer plus tard.",
                "german": "Entschuldigung, ich kann derzeit keine Antwort generieren. Bitte versuchen Sie es später erneut.",
                "portuguese": "Desculpe, não posso gerar uma resposta no momento. Tente novamente mais tarde.",
                "russian": "Извините, я не могу сгенерировать ответ в данный момент. Попробуйте позже.",
                "hindi": "क्षमा करें, मैं इस समय प्रतिक्रिया उत्पन्न नहीं कर सकता। कृपया बाद में पुनः प्रयास करें।",
                "arabic": "عذراً، لا يمكنني توليد استجابة في الوقت الحالي. يرجى المحاولة مرة أخرى لاحقاً."
            }
            
            # 항상 간단한 에러 메시지만 반환 (디버그 정보 제거)
            fallback_response = error_templates.get(language, error_templates["korean"])
            
            return {
                "answer": fallback_response,
                "sources": [],
                "conversation_id": conversation_id or str(uuid.uuid4())
            }
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """대화 히스토리 조회"""
        return self.conversations.get(conversation_id, [])
    
    def clear_conversation(self, conversation_id: str):
        """대화 히스토리 삭제"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """대화 통계"""
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv) for conv in self.conversations.values())
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "active_conversations": len([conv for conv in self.conversations.values() if conv])
        }





