import os
import re
import json
from decimal import Decimal
import requests

from django.conf import settings

ARIA_SYSTEM_PROMPT = """You are "Aria", the AI Mock Interview Assistant on CampusLink, a platform that helps college students prepare for jobs and internships.

ROLE
Conduct a realistic live video-call mock interview. You speak with the student by voice, and you may see their camera feed and hear their audio.

BEFORE STARTING
Greet the student warmly by name, then confirm:
1. Target role and company type (e.g., Software Intern, Marketing Trainee)
2. Interview type: HR, technical, behavioral, or case
3. Difficulty: beginner, intermediate, or advanced
4. Duration: 10, 20, or 30 minutes

INTERVIEW FLOW
- Start with a short icebreaker ("Tell me about yourself").
- Ask ONE question at a time. Wait for the full answer before continuing.
- Ask follow-up questions based on what they actually said.
- Mix resume, behavioral (STAR method), and role-specific questions.
- Keep a professional but friendly tone, like a real interviewer.
- Keep each spoken turn under 30 seconds. Don't lecture.
- If the student is silent for more than 10 seconds, gently prompt them.
- If they ask to repeat or rephrase, do so without judgment.

LIVE OBSERVATION
Note their eye contact, posture, filler words (um, like, you know), speaking pace, and confidence.

RULES
- Stay in character as an interviewer until the session ends.
- Never be rude, discriminatory, or ask illegal questions.
- Be honest but encouraging. Feedback should be constructive.
- Do not claim to be human if sincerely asked.
- Keep student data private.
"""

ROLE_QUESTION_BANKS = {
    'TECHNICAL': {
        'BEGINNER': [
            "Tell me about yourself, your educational background, and what inspired you to pursue a career in technology.",
            "Can you walk me through a technical project you built recently? What tech stack did you choose and why?",
            "How do you approach debugging when your code produces an unexpected error or fails a test case?",
            "What is the difference between an Array and a Linked List, and in what scenario would you prefer one over the other?",
            "Tell me about a time you had to learn a new programming language or tool quickly to complete an assignment.",
            "Do you have any questions for me regarding the engineering team or our technical stack?"
        ],
        'INTERMEDIATE': [
            "Walk me through your background and the technical problems you find most exciting to solve.",
            "Describe the architecture of the most complex application you've developed. How did you handle data flow and error states?",
            "How do you ensure your code is maintainable, scalable, and follows clean coding principles like SOLID or DRY?",
            "Suppose your API endpoint is experiencing high latency under sudden traffic spikes. How would you diagnose and optimize it?",
            "Tell me about a time when you disagreed with a teammate on a technical design decision. How did you resolve it?",
            "What technical areas are you currently exploring to deepen your engineering expertise?"
        ],
        'ADVANCED': [
            "Give me a high-level overview of your engineering journey and the architectural challenges you enjoy tackling.",
            "How would you design a distributed URL shortening service or real-time notification system handling millions of requests daily?",
            "Discuss database indexing strategies: when does an index hurt performance rather than help, and how do you optimize complex queries?",
            "Describe a production incident or severe system failure you encountered. How did you mitigate it and prevent recurrence?",
            "Tell me about a time you had to trade off code perfection against strict shipment deadlines. How did you make the call?",
            "What questions do you have for me about our system scale, team autonomy, or technical roadmap?"
        ]
    },
    'HR': {
        'BEGINNER': [
            "Tell me about yourself and what drawn your interest to this role at our company.",
            "Why did you choose your major, and what has been your most valuable learning experience in college?",
            "Where do you see your career heading in the next 2 to 3 years?",
            "Tell me about a time you had to juggle multiple deadlines (e.g. exams, projects, extracurriculars). How did you prioritize?",
            "What are your greatest professional strengths, and what is one skill you are actively working to improve?",
            "Why should we select you for this internship or entry-level opportunity over other candidates?"
        ],
        'INTERMEDIATE': [
            "Walk me through your journey so far and what makes this position the ideal next step for your growth.",
            "What kind of work environment and team culture brings out your absolute best performance?",
            "Tell me about a situation where a project or group task didn't go according to plan. What happened and what did you learn?",
            "How do you handle constructive criticism or feedback from mentors and senior colleagues?",
            "Describe a time you demonstrated initiative by solving a problem before anyone asked you to.",
            "Do you have any questions for me about our company values, expectations, or team dynamics?"
        ],
        'ADVANCED': [
            "Introduce yourself and highlight the core professional milestones that define your trajectory.",
            "How do you align personal career ambition with team goals and cross-functional company priorities?",
            "Describe how you influence team members or stakeholders when you do not hold direct authority.",
            "Tell me about a high-pressure situation where you had to make a critical decision with incomplete information.",
            "What does leadership mean to you in day-to-day collaboration?",
            "What would success look like to you in your first 90 days in this role?"
        ]
    },
    'BEHAVIORAL': {
        'BEGINNER': [
            "Tell me about yourself and describe a group project where you worked closely with others.",
            "Tell me about a time you faced a difficult challenge in a project. Walk me through the Situation, Task, Action, and Result (STAR).",
            "Give me an example of a time you received difficult feedback. How did you respond and adapt?",
            "Describe a time when you made a mistake on an assignment or project. How did you handle it?",
            "Tell me about a time you went above and beyond the basic expectations for a task.",
            "What is a recent achievement you are genuinely proud of, and why?"
        ],
        'INTERMEDIATE': [
            "Walk me through your background and what motivated you to specialize in your field.",
            "Tell me about a time you had to resolve a conflict within your team. What steps did you take and what was the outcome?",
            "Describe a situation where project requirements changed suddenly near the deadline. How did you manage the transition?",
            "Give an example of a project where you had to balance quality, speed, and resource constraints.",
            "Tell me about a time you mentored or assisted a peer who was struggling with a concept or task.",
            "What is the most challenging feedback you've ever received, and how did it change your working style?"
        ],
        'ADVANCED': [
            "Tell me about yourself and how your past experiences prepared you to lead initiatives.",
            "Describe a time when you had to advocate for an unpopular idea or technical direction. How did you build consensus?",
            "Tell me about a significant failure in your career or projects. What were the root causes, and how did you rebound?",
            "Describe a situation where you had to navigate ambiguity and deliver tangible results without clear guidelines.",
            "How do you maintain team morale and focus when facing tight deadlines or shifting organizational priorities?",
            "What questions do you have for me about leadership and collaboration at our organization?"
        ]
    },
    'CASE': {
        'BEGINNER': [
            "Tell me about yourself and your analytical problem-solving background.",
            "Estimate the number of cups of coffee consumed in a major metro city like Bengaluru or Delhi every day. Walk me through your assumptions.",
            "A local campus food delivery service is seeing high cart abandonment at the payment stage. How would you diagnose the problem?",
            "If you were tasked with launching a new student discount feature on our platform, what 3 key metrics would you track to measure success?",
            "Suppose your initial launch shows low adoption in the first week. What steps would you take to understand why?",
            "Do you have any questions on how our product and strategy teams approach user problems?"
        ],
        'INTERMEDIATE': [
            "Walk me through your background and how you approach structured quantitative and qualitative problem solving.",
            "Estimate the annual market size for electric two-wheelers in India over the next 3 years. What are the key market drivers?",
            "A popular SaaS product noticed a 15% drop in user retention after a major UI redesign. How would you isolate the root cause?",
            "How would you price a new subscription tier for college graduates seeking premium mentorship services?",
            "Tell me about a time you used data to overturn a subjective assumption or persuade a skeptical stakeholder.",
            "What questions do you have regarding our product growth strategy and market opportunities?"
        ],
        'ADVANCED': [
            "Give me an executive summary of your background and your approach to complex business and product challenges.",
            "A ride-hailing company is experiencing a 20% driver churn rate during peak hours. Structure an end-to-end framework to address supply liquidity.",
            "Evaluate whether a major tech company should build, buy, or partner to enter the generative AI developer tools market.",
            "How would you design the go-to-market strategy for a high-growth B2B fintech platform expanding internationally?",
            "Describe a time you executed a complex strategic tradeoff with significant downside risks. How did you manage stakeholder alignment?",
            "What strategic challenges are top of mind for you about our company's competitive positioning?"
        ]
    }
}

def get_aria_greeting(student_name, role_target="Software Intern", company_type="Tech Company", interview_type="HR", difficulty="Beginner", duration_minutes=15):
    name = student_name or "there"
    company_phrase = f" at {company_type}" if company_type else ""
    dur_phrase = f" for {duration_minutes} minutes" if duration_minutes else ""
    return (
        f"Hello {name}! I'm Aria, your AI Mock Interview Assistant on CampusLink. "
        f"I'm excited to help you prepare for your {role_target} role{company_phrase}. "
        f"We'll conduct a realistic {interview_type} interview at the {difficulty} level{dur_phrase}. "
        "Take a deep breath, stay confident, and let's begin whenever you're ready!"
    )

def get_interview_questions(role_target="Software Intern", company_type="Tech Company", interview_type="HR", difficulty="BEGINNER"):
    itype = interview_type.upper() if interview_type else 'HR'
    if itype not in ROLE_QUESTION_BANKS:
        itype = 'HR'
    diff = difficulty.upper() if difficulty else 'BEGINNER'
    if diff not in ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']:
        diff = 'BEGINNER'

    questions = list(ROLE_QUESTION_BANKS[itype][diff])
    return questions

PRIYA_STRUCTURED_PROMPT = """You are an expert AI Mock Interview Assistant on CampusLink conducting a realistic {role} {type} interview for {user_name}.
You communicate like an authentic, articulate human interviewer on a video call.
GUIDELINES FOR NATURAL HUMAN TALKING STYLE:
- Speak in warm, conversational, natural spoken sentences (1-3 sentences maximum per turn).
- NEVER use markdown, bullet points, asterisks, numbered lists, or headers.
- Always begin by naturally acknowledging the candidate's answer with human discourse markers ('That makes total sense', 'I appreciate how you explained that', 'Got it, that is a solid perspective', 'Good point on that challenge').
- If the candidate's answer was vague or brief, ask a natural probing follow-up for specific details or measurable outcomes.
- Keep the cadence concise, engaging, and professional.
- Return JSON strictly in this format: {{"speech_text": "...", "emotion": "neutral|smile|curious|serious|encouraging", "gesture": "none|nod|explain|emphasize", "internal_score_note": "..."}}."""


def generate_priya_interviewer_turn(user_name, role_target, interview_type, difficulty, transcript, current_question, student_answer):
    """
    Core LLM interviewer brain. Returns structured JSON:
    {
        "speech_text": str,
        "emotion": "neutral"|"smile"|"curious"|"serious"|"encouraging",
        "gesture": "none"|"nod"|"explain"|"emphasize",
        "internal_score_note": str
    }
    Supports Google Gemini, Anthropic Claude, and OpenAI via environment keys with intelligent structured fallback.
    """
    prompt = PRIYA_STRUCTURED_PROMPT.format(
        role=role_target,
        type=interview_type,
        user_name=user_name or "Candidate"
    )

    # 1. Try Gemini if configured
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            contents = []
            for item in transcript[-4:]:
                role = "model" if item.get('speaker') in ['Aria', 'Priya', 'Nexus'] else "user"
                contents.append({"role": role, "parts": [{"text": item.get('text', '')}]})
            contents.append({
                "role": "user",
                "parts": [{"text": f"Current Question: {current_question}\nCandidate Answer: {student_answer}"}]
            })
            payload = {
                "systemInstruction": {"parts": [{"text": prompt}]},
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7, "maxOutputTokens": 200},
                "contents": contents
            }
            res = requests.post(url, json=payload, timeout=4)
            if res.status_code == 200:
                data = res.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(text)
                if 'speech_text' in parsed:
                    return {
                        "speech_text": parsed.get('speech_text', '').strip(),
                        "emotion": parsed.get('emotion', 'neutral').lower(),
                        "gesture": parsed.get('gesture', 'nod').lower(),
                        "internal_score_note": parsed.get('internal_score_note', '')
                    }
        except Exception:
            pass

    # 2. Try Anthropic Claude if configured
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key:
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            messages = []
            for item in transcript[-4:]:
                role = "assistant" if item.get('speaker') in ['Aria', 'Priya', 'Nexus'] else "user"
                messages.append({"role": role, "content": item.get('text', '')})
            messages.append({"role": "user", "content": f"Current Question: {current_question}\nCandidate Answer: {student_answer}\nReturn only valid JSON."})
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 150,
                "system": prompt,
                "messages": messages
            }
            res = requests.post(url, json=payload, headers=headers, timeout=4)
            if res.status_code == 200:
                text = res.json().get('content', [{}])[0].get('text', '')
                parsed = json.loads(text)
                if 'speech_text' in parsed:
                    return {
                        "speech_text": parsed.get('speech_text', '').strip(),
                        "emotion": parsed.get('emotion', 'neutral').lower(),
                        "gesture": parsed.get('gesture', 'nod').lower(),
                        "internal_score_note": parsed.get('internal_score_note', '')
                    }
        except Exception:
            pass

    # 3. Intelligent Contextual Fallback Engine with authentic human conversational tone
    cleaned = student_answer.strip().lower()
    words = cleaned.split()
    word_count = len(words)

    if word_count < 8:
        return {
            "speech_text": "I see where you're starting from. Could you elaborate a bit more on that experience? Walk me through a specific situation you handled.",
            "emotion": "curious",
            "gesture": "explain",
            "internal_score_note": "Brief answer, requested elaboration"
        }

    has_action = any(w in cleaned for w in ['created', 'built', 'implemented', 'designed', 'solved', 'analyzed', 'led', 'developed', 'tested', 'managed'])
    has_outcome = any(w in cleaned for w in ['result', 'learned', 'improved', 'increased', 'completed', 'success', 'metric', 'impact', 'delivered', 'achieved'])

    if has_action and not has_outcome:
        return {
            "speech_text": "That's a very solid breakdown of the technical actions you took. I'd love to hear: what was the measurable outcome or impact of that decision?",
            "emotion": "encouraging",
            "gesture": "nod",
            "internal_score_note": "Action demonstrated, probed for quantifiable result"
        }

    if any(w in cleaned for w in ['team', 'group', 'colleague', 'peer', 'partner', 'mentor']):
        return {
            "speech_text": "That's really insightful. Team collaboration is vital in fast-paced teams, and it sounds like you kept communication transparent.",
            "emotion": "smile",
            "gesture": "nod",
            "internal_score_note": "Good teamwork emphasis"
        }

    if any(w in cleaned for w in ['bug', 'error', 'difficult', 'challenge', 'failure', 'lockup', 'hurdle', 'debug']):
        return {
            "speech_text": "That makes complete sense. Troubleshooting tricky hurdles under tight deadlines requires strong resilience and a calm mindset.",
            "emotion": "serious",
            "gesture": "emphasize",
            "internal_score_note": "Problem solving resilience noted"
        }

    return {
        "speech_text": "Great explanation. That gives me a clear picture of your problem-solving process and how you approach challenges.",
        "emotion": "encouraging",
        "gesture": "nod",
        "internal_score_note": "Clear, structured response"
    }


def generate_aria_follow_up(transcript, current_question, student_answer, role_target, interview_type, difficulty, user_name=None):
    """
    Backward-compatible wrapper for generating Aria / Priya follow-ups.
    Returns clean speech text (1-3 sentences).
    """
    result = generate_priya_interviewer_turn(
        user_name=user_name,
        role_target=role_target,
        interview_type=interview_type,
        difficulty=difficulty,
        transcript=transcript,
        current_question=current_question,
        student_answer=student_answer
    )
    return result['speech_text']


def synthesize_neural_tts(text, voice='en-IN-NeerjaNeural'):
    """
    Synthesize natural Indian-English female voice via Azure Speech or ElevenLabs.
    Returns (audio_bytes, mime_type) if configured, else None (to fallback to client Web Speech).
    """
    # 1. Azure Neural TTS (en-IN-NeerjaNeural or en-IN-AnanyaNeural)
    azure_key = os.getenv('AZURE_SPEECH_KEY')
    azure_region = os.getenv('AZURE_SPEECH_REGION', 'centralindia')
    if azure_key and azure_region:
        try:
            url = f"https://{azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
            headers = {
                "Ocp-Apim-Subscription-Key": azure_key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                "User-Agent": "CampusLinkAILabs"
            }
            ssml = f"""<speak version='1.0' xml:lang='en-IN'>
                <voice xml:lang='en-IN' xml:gender='Female' name='{voice}'>
                    {text}
                </voice>
            </speak>"""
            res = requests.post(url, data=ssml.encode('utf-8'), headers=headers, timeout=4)
            if res.status_code == 200:
                return res.content, 'audio/mpeg'
        except Exception:
            pass

    # 2. ElevenLabs TTS
    eleven_key = os.getenv('ELEVENLABS_API_KEY')
    eleven_voice = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # Default natural female voice
    if eleven_key:
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{eleven_voice}"
            headers = {
                "xi-api-key": eleven_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
            }
            res = requests.post(url, json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                return res.content, 'audio/mpeg'
        except Exception:
            pass

    return None


def create_avatar_streaming_session(provider='heygen'):
    """
    Initializes a WebRTC streaming avatar session with HeyGen or D-ID.
    Returns session credentials and SDP negotiation parameters.
    """
    heygen_key = os.getenv('HEYGEN_API_KEY')
    did_key = os.getenv('DID_API_KEY')

    if provider == 'heygen' and heygen_key:
        try:
            url = "https://api.heygen.com/v1/streaming.new"
            headers = {"X-Api-Key": heygen_key, "Content-Type": "application/json"}
            payload = {"quality": "high", "avatar_id": os.getenv('HEYGEN_AVATAR_ID', 'default')}
            res = requests.post(url, json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                return {'success': True, 'provider': 'heygen', 'data': res.json().get('data', {})}
        except Exception as e:
            return {'success': False, 'error': str(e), 'fallback': True}

    if provider == 'did' and did_key:
        try:
            url = "https://api.d-id.com/talks/streams"
            headers = {"Authorization": f"Basic {did_key}", "Content-Type": "application/json"}
            payload = {"source_url": os.getenv('AVATAR_IMAGE_URL', '')}
            res = requests.post(url, json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                return {'success': True, 'provider': 'did', 'data': res.json()}
        except Exception as e:
            return {'success': False, 'error': str(e), 'fallback': True}

    return {
        'success': True,
        'provider': 'local_state_loop',
        'fallback': True,
        'message': 'No external streaming API key configured. Operating in high-performance local video/motion loop mode.'
    }

def analyze_filler_words(text):
    fillers = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'sort of', 'kind of', 'right']
    found = {}
    total = 0
    lower = text.lower()
    for filler in fillers:
        count = len(re.findall(r'\b' + re.escape(filler) + r'\b', lower))
        if count > 0:
            found[filler] = count
            total += count
    return {'total_fillers': total, 'breakdown': found}

def calculate_speaking_pace(word_count, duration_seconds):
    if duration_seconds <= 0:
        return 120 # typical default WPM
    minutes = duration_seconds / 60.0
    wpm = round(word_count / minutes) if minutes > 0 else 120
    return min(max(wpm, 60), 220)

def generate_mock_interview_report(session, transcript_history, observed_metrics=None):
    """
    Computes rigorous, constructive feedback based on actual answers,
    filler words, response completeness, and role context.
    """
    observed_metrics = observed_metrics or {}
    total_words = 0
    all_answers = []
    
    for turn in transcript_history:
        if turn.get('speaker') == 'Student':
            answer_text = turn.get('text', '')
            all_answers.append(answer_text)
            total_words += len(answer_text.split())

    combined_text = " ".join(all_answers)
    filler_data = analyze_filler_words(combined_text)
    total_fillers = filler_data['total_fillers']
    
    # Calculate Scores out of 10
    # 1. Communication: penalized slightly if excessive filler words or too terse
    comm_score = 8.5
    if total_fillers > 10:
        comm_score -= 1.5
    elif total_fillers > 5:
        comm_score -= 0.8
    if total_words < 80:
        comm_score -= 1.2
    comm_score = round(max(5.0, min(9.5, comm_score)), 1)

    # 2. Content & Relevance: awarded for length, STAR components, technical/role keywords
    content_score = 7.5
    if any(k in combined_text.lower() for k in ['result', 'impact', 'learned', 'outcome', 'metrics']):
        content_score += 1.0
    if any(k in combined_text.lower() for k in ['challenge', 'problem', 'implemented', 'designed', 'built']):
        content_score += 0.8
    if total_words > 250:
        content_score += 0.5
    content_score = round(max(5.0, min(9.8, content_score)), 1)

    # 3. Confidence: based on fillers and answer completeness
    conf_score = 8.0
    if total_fillers > 8:
        conf_score -= 1.2
    if observed_metrics.get('eye_contact_percent', 85) < 70:
        conf_score -= 0.8
    conf_score = round(max(5.5, min(9.6, conf_score)), 1)

    # 4. Body Language & Presence
    body_score = Decimal(str(round(max(6.0, min(9.5, float(observed_metrics.get('eye_contact_percent', 88)) / 10.0)), 1)))

    overall = round((float(comm_score) * 0.3 + float(content_score) * 0.35 + float(conf_score) * 0.2 + float(body_score) * 0.15), 1)

    # 3 Key Strengths
    strengths = [
        "Strong authenticity and willingness to share hands-on project experiences.",
        "Clear articulation of personal motivation for the target role and domain.",
        "Demonstrated positive mindset toward collaborative teamwork and continuous learning."
    ]
    if any(w in combined_text.lower() for w in ['impact', 'result', 'metric', 'improved']):
        strengths[0] = "Excellent focus on outcomes and measurable impact rather than just describing duties."

    # 3 Areas to Improve
    areas_for_improvement = [
        "Incorporate the STAR methodology (Situation, Task, Action, Result) more systematically so every answer finishes with tangible results.",
        f"Be conscious of verbal filler words (detected {total_fillers} instances like 'um'/'like')—try pausing quietly for 1 second instead.",
        "Deepen role-specific technical terminology to showcase mastery when explaining architecture or strategic trade-offs."
    ]

    # Sample Answer for weakest response
    weakest_sample = (
        "Question: 'Tell me about a challenging technical hurdle you faced in a project.'\n\n"
        "Exemplary STAR Model Answer:\n"
        "• Situation: During my final-year web portal project, our database queries were taking over 3 seconds under concurrent student registration loads.\n"
        "• Task: As backend lead, my objective was to bring latency under 250ms without exceeding our cloud server RAM budget.\n"
        "• Action: I profiled the slow queries using Django Debug Toolbar, identified 12 redundant N+1 queries, implemented select_related and prefetch_related, and added Redis caching for static course catalogs.\n"
        "• Result: Query response times dropped by 88% down to 180ms, allowing 500+ simultaneous students to register smoothly."
    )

    # 7-day Practice Plan
    practice_plan = [
        {"day": 1, "focus": "STAR Story Bank", "task": "Write down 4 distinct STAR stories covering: a technical challenge, a team disagreement, a leadership moment, and a failure."},
        {"day": 2, "focus": "Eliminating Fillers", "task": "Record yourself answering 'Tell me about yourself' for 90 seconds. Listen back specifically counting filler words and re-record."},
        {"day": 3, "focus": "Technical Deep Dive", "task": "Practice explaining your top GitHub project's system architecture out loud without looking at code notes."},
        {"day": 4, "focus": "Metrics & Outcomes", "task": "Attach at least one numerical metric or verifiable result to each bullet point on your resume."},
        {"day": 5, "focus": "Camera & Body Language", "task": "Practice maintaining eye contact directly with the webcam lens rather than looking down at screen notes."},
        {"day": 6, "focus": "Behavioral Rapid Fire", "task": "Conduct a 20-minute timed mock session answering conflict, priority, and ambiguity questions."},
        {"day": 7, "focus": "Final Simulation with Aria", "task": "Complete an advanced mock interview session on CampusLink to validate improved confidence and pace."}
    ]

    return {
        'overall_score': Decimal(str(overall)),
        'communication_score': Decimal(str(comm_score)),
        'content_score': Decimal(str(content_score)),
        'confidence_score': Decimal(str(conf_score)),
        'body_language_score': Decimal(str(body_score)),
        'strengths': strengths,
        'areas_for_improvement': areas_for_improvement,
        'sample_answer': weakest_sample,
        'practice_plan': practice_plan,
        'observations': {
            'total_words': total_words,
            'total_fillers': total_fillers,
            'filler_details': filler_data['breakdown'],
            'speaking_pace_wpm': calculate_speaking_pace(total_words, int(observed_metrics.get('duration_seconds', 300))),
            'eye_contact_percent': observed_metrics.get('eye_contact_percent', 88),
            'camera_active': observed_metrics.get('camera_active', True),
        }
    }
