import json
from decimal import Decimal
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()

from accounts.models import Membership
from companies.models import Company
from jobs.models import Job
from students.models import StudentProfile, Skill
from interviews.models import MockInterviewSession
from interviews.services import (
    get_aria_greeting,
    get_interview_questions,
    generate_aria_follow_up,
    generate_priya_interviewer_turn,
    evaluate_star_feedback,
    normalize_speech_metrics,
    synthesize_neural_tts,
    create_avatar_streaming_session,
    generate_mock_interview_report,
    identify_job_domain,
)


class MockInterviewSessionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rohit_sharma',
            email='rohit@campuslink.edu',
            password='Password@123',
            first_name='Rohit',
            last_name='Sharma',
        )

    def test_create_mock_interview_session(self):
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Software Engineer Intern',
            company_type='Tech Startup',
            interview_type='TECHNICAL',
            difficulty='INTERMEDIATE',
            duration_minutes=20,
            overall_score=8.5,
            communication_score=8.0,
            content_score=9.0,
            confidence_score=8.5,
            body_language_score=8.5,
            strengths=['Great structure', 'Clear speech', 'Relevant project examples'],
            areas_for_improvement=['Reduce filler words', 'Add more metrics', 'Maintain eye contact'],
            sample_answer={'question': 'Tell me about yourself', 'better_star_answer': 'STAR example'},
            practice_plan=[{'day': 1, 'task': 'Practice STAR framework'}],
            transcript=[{'speaker': 'Aria', 'text': 'Hello Rohit!'}],
            observations={'filler_count': 2, 'speaking_pace_wpm': 130},
            status='COMPLETED',
        )
        self.assertEqual(session.user.first_name, 'Rohit')
        self.assertEqual(session.overall_score, 8.5)
        self.assertEqual(len(session.strengths), 3)
        self.assertEqual(session.status, 'COMPLETED')
        self.assertIn('rohit_sharma', str(session))


class AriaMockInterviewViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='ananya_sen',
            email='ananya@campuslink.edu',
            password='Password@123',
            first_name='Ananya',
            last_name='Sen',
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            department='Computer Science',
            degree='B.Tech',
            cgpa=9.1,
            graduation_year=2026,
        )
        self.membership = Membership.objects.create(
            user=self.user,
            plan='PRO_MONTHLY',
            status='ACTIVE',
        )

    def test_anonymous_user_redirected_from_mock_room(self):
        response = self.client.get(reverse('ai_mock_interview'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_student_can_access_mock_room(self):
        self.client.login(username='ananya_sen', password='Password@123')
        response = self.client.get(reverse('ai_mock_interview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Priya')
        self.assertContains(response, 'Ananya')
        self.assertContains(response, 'CampusLink')
        self.assertContains(response, 'PRIYA AI · SENIOR TECHNICAL HR PARTNER')
        self.assertContains(response, 'aria_interviewer.jpg')
        self.assertContains(response, 'btnTestVoice')
        self.assertIn("Test Priya's Voice", response.content.decode('utf-8'))
        self.assertNotContains(response, 'NEXUS AI · ROBOTIC MOCK INTERVIEWER')
        self.assertNotContains(response, 'ai_robot_interviewer.jpg')
        self.assertTemplateUsed(response, 'interviews/mock_room.html')

    def test_non_pro_user_cannot_access_mock_interview_or_tts(self):
        free_user = User.objects.create_user(
            username='free_student',
            email='free@campuslink.edu',
            password='Password@123',
        )
        self.client.force_login(free_user)

        room_response = self.client.get(reverse('ai_mock_interview'))
        self.assertEqual(room_response.status_code, 302)
        self.assertIn(reverse('pro_checkout'), room_response.url)

        start_response = self.client.post(
            reverse('api_start_mock_interview'),
            data=json.dumps({'role_target': 'Software Intern'}),
            content_type='application/json',
        )
        self.assertEqual(start_response.status_code, 403)
        self.assertEqual(start_response.json()['error'], 'PRO_REQUIRED')

        tts_response = self.client.get(reverse('api_synthesize_tts'), {'text': 'Hello'})
        self.assertEqual(tts_response.status_code, 403)
        self.assertEqual(tts_response.json()['error'], 'PRO_REQUIRED')

        list_response = self.client.get(reverse('interview_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Unlock with PRO')
        self.assertNotContains(list_response, 'Start with Priya')

    def test_api_start_mock_interview(self):
        self.client.login(username='ananya_sen', password='Password@123')
        payload = {
            'role_target': 'Full Stack Developer Intern',
            'company_type': 'FinTech Leader',
            'interview_type': 'TECHNICAL',
            'difficulty': 'INTERMEDIATE',
            'duration_minutes': 20,
        }
        response = self.client.post(
            reverse('api_start_mock_interview'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('session_id', data)
        self.assertIn('Ananya', data['greeting'])
        self.assertIn('Full Stack Developer Intern', data['greeting'])
        self.assertTrue(len(data['questions']) > 0)

        # Verify DB session created
        session = MockInterviewSession.objects.get(pk=data['session_id'])
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.interview_type, 'TECHNICAL')
        self.assertEqual(session.status, 'IN_PROGRESS')

    def test_api_aria_turn_regular_answer(self):
        self.client.login(username='ananya_sen', password='Password@123')
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Software Engineer Intern',
            company_type='Tech Firm',
            interview_type='HR',
            difficulty='BEGINNER',
            status='IN_PROGRESS',
        )
        payload = {
            'session_id': session.pk,
            'current_index': 0,
            'student_answer': 'I am a final-year CS student passionate about building scalable web applications. Recently I built a real-time collaboration tool using Django and WebSockets.',
            'questions': ['Tell me about yourself.', 'What is your greatest technical strength?'],
            'transcript': [{'speaker': 'Aria', 'text': 'Tell me about yourself.'}],
            'speech_metrics': {'filler_count': 5, 'eye_contact_percent': 50, 'pause_count': 3},
            'speechx_active': True,
            'speech_end': True,
            'action': 'answer',
        }
        response = self.client.post(
            reverse('api_aria_turn'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('aria_speech', data)
        self.assertEqual(data['next_question'], 'What is your greatest technical strength?')
        self.assertFalse(data['is_last'])
        self.assertEqual(data['star_feedback']['metrics']['filler_count'], 5)
        self.assertEqual(data['star_feedback']['metrics']['eye_contact_percent'], 50)
        self.assertTrue(data['star_feedback']['metrics_feedback'])

    def test_api_aria_turn_adapts_up_when_star_answer_is_complete(self):
        self.client.force_login(self.user)
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Software Engineer Intern',
            company_type='Tech Firm',
            interview_type='BEHAVIORAL',
            difficulty='INTERMEDIATE',
            status='IN_PROGRESS',
        )
        response = self.client.post(
            reverse('api_aria_turn'),
            data=json.dumps({
                'session_id': session.pk,
                'current_index': 0,
                'student_answer': 'During our capstone project, I was responsible for meeting the release goal. I organized testing and fixed the deployment checks. The result was a 20% reduction in failed builds.',
                'questions': ['Tell me about a time you solved a challenge.', 'Describe how you work with a team.'],
                'transcript': [],
                'action': 'answer',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['star_feedback']['score'], 4)
        self.assertEqual(data['difficulty'], 'ADVANCED')
        self.assertEqual(data['next_question'], data['questions'][data['next_index']])
        session.refresh_from_db()
        self.assertEqual(session.difficulty, 'ADVANCED')

    def test_api_aria_turn_rejects_empty_answer(self):
        self.client.login(username='ananya_sen', password='Password@123')
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Software Engineer Intern',
            company_type='Tech Firm',
            interview_type='HR',
            difficulty='BEGINNER',
            status='IN_PROGRESS',
        )
        response = self.client.post(
            reverse('api_aria_turn'),
            data=json.dumps({
                'session_id': session.pk,
                'student_answer': '',
                'action': 'answer',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_api_aria_turn_waits_for_speech_end(self):
        self.client.force_login(self.user)
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Software Engineer Intern',
            company_type='Tech Firm',
            interview_type='HR',
            difficulty='BEGINNER',
            status='IN_PROGRESS',
        )
        response = self.client.post(
            reverse('api_aria_turn'),
            data=json.dumps({
                'session_id': session.pk,
                'student_answer': 'This is an interim transcription that should not be answered yet.',
                'speechx_active': True,
                'speech_end': False,
                'action': 'answer',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error'], 'WAIT_FOR_SPEECH_END')

    def test_api_aria_turn_repeat_question(self):
        self.client.login(username='ananya_sen', password='Password@123')
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Data Analyst Intern',
            company_type='Analytics Firm',
            interview_type='BEHAVIORAL',
            difficulty='INTERMEDIATE',
        )
        payload = {
            'session_id': session.pk,
            'current_index': 1,
            'student_answer': '',
            'questions': ['Tell me about yourself.', 'Describe a challenging project you solved with data.'],
            'transcript': [],
            'action': 'repeat',
        }
        response = self.client.post(
            reverse('api_aria_turn'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('repeat the question', data['aria_speech'])
        self.assertEqual(data['next_question'], 'Describe a challenging project you solved with data.')

    def test_api_aria_turn_skip_question(self):
        self.client.login(username='ananya_sen', password='Password@123')
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Product Intern',
            company_type='Startup',
            interview_type='CASE',
            difficulty='ADVANCED',
        )
        payload = {
            'session_id': session.pk,
            'current_index': 0,
            'student_answer': '',
            'questions': ['Question 1', 'Question 2'],
            'transcript': [],
            'action': 'skip',
        }
        response = self.client.post(
            reverse('api_aria_turn'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['next_question'], 'Question 2')

    def test_api_finish_mock_interview_and_report_view(self):
        self.client.login(username='ananya_sen', password='Password@123')
        session = MockInterviewSession.objects.create(
            user=self.user,
            role_target='Software Engineer Intern',
            company_type='Enterprise Tech',
            interview_type='TECHNICAL',
            difficulty='INTERMEDIATE',
            status='IN_PROGRESS',
        )
        transcript = [
            {'speaker': 'Aria', 'text': 'Tell me about yourself.'},
            {
                'speaker': 'Student',
                'text': 'I am a CS student at BPUT. In my last internship, I created an automated test pipeline that cut release cycle times by 30 percent. My main technologies are Python, Django, and PostgreSQL.',
            },
            {'speaker': 'Aria', 'text': 'What was your biggest technical challenge?'},
            {
                'speaker': 'Student',
                'text': 'We faced severe database lockups during concurrent batch updates. I restructured the queries to use chunked transactions with Redis caching, which resolved the latency spikes.',
            },
        ]
        payload = {
            'session_id': session.pk,
            'transcript': transcript,
            'observed_metrics': {
                'filler_count': 1,
                'words_spoken': 75,
                'duration_seconds': 60,
                'eye_contact_ratio': 85,
                'posture_rating': 'Solid',
                'confidence_rating': 'High',
            },
        }
        response = self.client.post(
            reverse('api_finish_mock_interview'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        report = data['report']

        self.assertGreaterEqual(report['overall_score'], 1.0)
        self.assertLessEqual(report['overall_score'], 10.0)
        self.assertEqual(len(report['strengths']), 3)
        self.assertEqual(len(report['areas_for_improvement']), 3)
        self.assertIn('STAR', report['sample_answer'])
        self.assertIn('Situation', report['sample_answer'])

        # Now test the report view renders
        report_url = data['report_url']
        report_response = self.client.get(report_url)
        self.assertEqual(report_response.status_code, 200)
        self.assertContains(report_response, 'Interview Performance Report')
        self.assertContains(report_response, '7-Day Practice Plan')
        self.assertContains(report_response, 'Priya')

    @patch('interviews.views.synthesize_neural_tts', return_value=(b'RIFFtest', 'audio/wav'))
    def test_api_synthesize_tts_fallback_or_content(self, mock_synthesize):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('api_synthesize_tts'), {'text': 'Hello world'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'audio/wav')
        mock_synthesize.assert_called_once_with('Hello world')

    def test_api_avatar_session_endpoint(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('api_avatar_session'), {'provider': 'heygen'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('provider', data)
        self.assertTrue('fallback' in data or 'success' in data)

    def test_api_start_mock_interview_job_wise(self):
        """Verify that starting an interview for a specific Job tailors questions and returns job_info."""
        self.client.force_login(self.user)
        company = Company.objects.create(name='Tech Innovations Inc.', industry='Technology')
        from django.utils import timezone
        import datetime
        job = Job.objects.create(
            title='Python Backend Developer',
            company=company,
            description='Build scalable REST APIs using Python, Django, and PostgreSQL.',
            location='Bengaluru, India',
            application_deadline=timezone.now() + datetime.timedelta(days=30),
            is_verified=True
        )
        skill_py, _ = Skill.objects.get_or_create(name='Python')
        skill_dj, _ = Skill.objects.get_or_create(name='Django')
        job.required_skills.add(skill_py, skill_dj)

        payload = {
            'job_id': job.id,
            'interview_type': 'TECHNICAL',
            'difficulty': 'INTERMEDIATE',
            'duration_minutes': 15,
        }
        response = self.client.post(
            reverse('api_start_mock_interview'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('job_info', data)
        self.assertEqual(data['job_info']['title'], 'Python Backend Developer')
        self.assertEqual(data['job_info']['company'], 'Tech Innovations Inc.')
        self.assertTrue(len(data['questions']) >= 4)
        
        # Verify questions specifically mention backend concepts or the company
        all_q_text = " ".join(data['questions']).lower()
        self.assertTrue('python' in all_q_text or 'backend' in all_q_text or 'tech innovations' in all_q_text or 'database' in all_q_text or 'api' in all_q_text)

    def test_mock_room_with_selected_job(self):
        """Verify mock room renders with available jobs and preselected job_id."""
        self.client.force_login(self.user)
        company = Company.objects.create(name='Alpha Labs', industry='Cloud')
        from django.utils import timezone
        import datetime
        job = Job.objects.create(
            title='Cloud SRE Engineer',
            company=company,
            description='Manage Kubernetes and AWS infrastructure.',
            location='Remote',
            application_deadline=timezone.now() + datetime.timedelta(days=30),
            is_verified=True
        )
        resp = self.client.get(f"{reverse('ai_mock_interview')}?job_id={job.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Alpha Labs')
        self.assertContains(resp, 'Cloud SRE Engineer')
        self.assertIn('available_jobs', resp.context)
        self.assertEqual(resp.context['selected_job_id'], job.id)


class AriaServicesTest(TestCase):
    def test_star_feedback_uses_observed_metrics_only(self):
        feedback = evaluate_star_feedback(
            'During the group project, my task was to meet the launch goal. I built a test plan. The result improved reliability by 20%.',
            {'filler_count': 5, 'eye_contact_percent': 50, 'pause_count': 4, 'untrusted': 'ignore'},
        )
        self.assertEqual(feedback['score'], 4)
        self.assertEqual(feedback['metrics'], {
            'filler_count': 5,
            'eye_contact_percent': 50,
            'pause_count': 4,
        })
        self.assertEqual(len(feedback['metrics_feedback']), 3)

    def test_speech_metrics_are_bounded_and_invalid_values_omitted(self):
        self.assertEqual(
            normalize_speech_metrics({
                'filler_count': -5,
                'eye_contact_ratio': 145,
                'speaking_pace_wpm': 'not-a-number',
            }),
            {'filler_count': 0, 'eye_contact_percent': 100},
        )

    def test_greeting_format(self):
        greeting = get_aria_greeting('Rahul', 'Data Science Intern', 'AI Labs', 'TECHNICAL', 'Intermediate')
        self.assertIn('Priya', greeting)
        self.assertIn('Rahul', greeting)
        self.assertIn('Data Science Intern', greeting)
        self.assertIn('AI Labs', greeting)
        self.assertIn('TECHNICAL', greeting)

    def test_kokoro_is_used_when_cloud_tts_is_unconfigured(self):
        expected_audio = (b'RIFFkokoro-audio', 'audio/wav')
        with patch.dict('os.environ', {'AZURE_SPEECH_KEY': '', 'ELEVENLABS_API_KEY': ''}), \
             patch('interviews.services._synthesize_kokoro', return_value=expected_audio) as synthesize:
            result = synthesize_neural_tts('Welcome to your interview.')

        self.assertEqual(result, expected_audio)
        synthesize.assert_called_once_with('Welcome to your interview.')

    def test_question_banks_return_questions(self):
        for itype in ['HR', 'TECHNICAL', 'BEHAVIORAL', 'CASE']:
            for diff in ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']:
                questions = get_interview_questions('Software Engineer', 'Big Tech', itype, diff)
                self.assertGreaterEqual(len(questions), 8)
                for q in questions:
                    self.assertIsInstance(q, str)
                    self.assertGreater(len(q), 10)

    def test_generate_aria_follow_up_length_and_professionalism(self):
        follow_up = generate_aria_follow_up(
            transcript=[],
            current_question='Tell me about yourself.',
            student_answer='I love programming in Python and built a full stack app for campus event registrations.',
            role_target='Backend Intern',
            interview_type='HR',
            difficulty='BEGINNER',
        )
        self.assertIsInstance(follow_up, str)
        self.assertTrue(len(follow_up) > 20)
        # Verify it doesn't lecture (under 30s speaking time ~ 60-80 words)
        words = follow_up.split()
        self.assertLess(len(words), 80)

    def test_priya_interviewer_structured_turn(self):
        turn = generate_priya_interviewer_turn(
            user_name='Rohit',
            role_target='Software Engineer Intern',
            interview_type='TECHNICAL',
            difficulty='BEGINNER',
            transcript=[],
            current_question='Tell me about yourself.',
            student_answer='I built a full-stack Django and React application with Redis caching and Docker.'
        )
        self.assertIn('speech_text', turn)
        self.assertIn('emotion', turn)
        self.assertIn('gesture', turn)
        self.assertIn('internal_score_note', turn)
        self.assertIn(turn['emotion'], ['neutral', 'smile', 'curious', 'serious', 'encouraging'])
        self.assertIn(turn['gesture'], ['none', 'nod', 'explain', 'emphasize'])
        self.assertTrue(len(turn['speech_text']) > 15)

    def test_big_tech_greetings(self):
        """Test tailored greetings for Google, Amazon Bar Raiser, and Microsoft."""
        google_greet = get_aria_greeting('Aarav', 'Software Engineer', 'Google', 'HR', 'Beginner')
        self.assertIn('Google', google_greet)
        self.assertIn('Hiring Committee', google_greet)
        self.assertIn('ambiguity', google_greet.lower())

        amazon_greet = get_aria_greeting('Neha', 'SDE I', 'Amazon', 'BEHAVIORAL', 'Intermediate')
        self.assertIn('Amazon', amazon_greet)
        self.assertIn('Bar Raiser', amazon_greet)
        self.assertIn('16 Leadership Principles', amazon_greet)

        msft_greet = get_aria_greeting('Rohan', 'Cloud Engineer', 'Microsoft', 'TECHNICAL', 'Advanced')
        self.assertIn('Microsoft', msft_greet)
        self.assertIn('Growth Mindset', msft_greet)

    def test_big_tech_question_banks(self):
        """Verify authentic Big Tech questions returned for Google, Amazon, and Microsoft."""
        # Google
        google_qs = get_interview_questions('Software Engineer', 'Google', 'HR', 'BEGINNER')
        google_text = " ".join(google_qs).lower()
        self.assertTrue('google' in google_text or 'ambiguity' in google_text or 'humility' in google_text)

        # Amazon
        amazon_qs = get_interview_questions('Software Development Engineer', 'Amazon', 'HR', 'BEGINNER')
        amazon_text = " ".join(amazon_qs).lower()
        self.assertTrue('amazon' in amazon_text or 'leadership principles' in amazon_text or 'customer obsession' in amazon_text)

        # Microsoft
        msft_qs = get_interview_questions('Software Engineer', 'Microsoft', 'HR', 'BEGINNER')
        msft_text = " ".join(msft_qs).lower()
        self.assertTrue('microsoft' in msft_text or 'growth mindset' in msft_text or 'others' in msft_text)

    def test_big_tech_interviewer_probing(self):
        """Verify authentic interviewer follow-ups (Amazon Bar Raiser ownership/metrics, Google ambiguity, Microsoft growth mindset)."""
        # Amazon: probes individual ownership when candidate says 'we' without 'i'
        amazon_turn = generate_priya_interviewer_turn(
            user_name='Candidate',
            role_target='SDE',
            interview_type='HR',
            difficulty='BEGINNER',
            transcript=[],
            current_question='Tell me about a challenging project.',
            student_answer='We launched a large data service and we managed all the customer deployments together.',
            company_type='Amazon'
        )
        self.assertIn('personal ownership', amazon_turn['speech_text'].lower())
        self.assertIn('individual contribution', amazon_turn['speech_text'].lower())

        # Google: probes 10x scalability or collaborative consensus
        google_turn = generate_priya_interviewer_turn(
            user_name='Candidate',
            role_target='Software Engineer',
            interview_type='TECHNICAL',
            difficulty='INTERMEDIATE',
            transcript=[],
            current_question='Design a distributed storage cache.',
            student_answer='I designed a distributed cache architecture with sharded redis database clusters.',
            company_type='Google'
        )
        self.assertIn('scale', google_turn['speech_text'].lower())

        # Microsoft: probes learning from failure
        msft_turn = generate_priya_interviewer_turn(
            user_name='Candidate',
            role_target='Software Engineer',
            interview_type='BEHAVIORAL',
            difficulty='BEGINNER',
            transcript=[],
            current_question='Tell me about a failure.',
            student_answer='We had a critical bug that caused a database fail and service outage during release.',
            company_type='Microsoft'
        )
        self.assertIn('lesson', msft_turn['speech_text'].lower())

    def test_big_tech_report_generation(self):
        """Verify performance report includes Big Tech evaluations for Google, Amazon, and Microsoft."""
        session_amazon = MockInterviewSession(company_type='Amazon', role_target='SDE')
        transcript = [
            {'speaker': 'Nexus', 'text': 'Tell me about yourself.'},
            {'speaker': 'Student', 'text': 'I built a high-throughput payment processor that reduced latency by 35% and handled 1000 transactions per second.'}
        ]
        report_amazon = generate_mock_interview_report(session_amazon, transcript)
        self.assertIsNotNone(report_amazon['big_tech_evaluation'])
        self.assertEqual(report_amazon['big_tech_evaluation']['company'], 'Amazon')
        self.assertIn('Bar Raiser', report_amazon['big_tech_evaluation']['track'])
        self.assertIn('Amazon', report_amazon['sample_answer'])

        session_google = MockInterviewSession(company_type='Google', role_target='Software Engineer')
        report_google = generate_mock_interview_report(session_google, transcript)
        self.assertIsNotNone(report_google['big_tech_evaluation'])
        self.assertEqual(report_google['big_tech_evaluation']['company'], 'Google')
        self.assertIn('Googleyness', report_google['big_tech_evaluation']['track'])

        session_msft = MockInterviewSession(company_type='Microsoft', role_target='Software Engineer')
        report_msft = generate_mock_interview_report(session_msft, transcript)
        self.assertIsNotNone(report_msft['big_tech_evaluation'])
        self.assertEqual(report_msft['big_tech_evaluation']['company'], 'Microsoft')
        self.assertIn('Growth Mindset', report_msft['big_tech_evaluation']['track'])

    def test_silent_interview_yields_minimum_rating_and_warning(self):
        """Verify that when a candidate stays silent or provides no answers, rating is strictly 1.0/10 and flagged as No Verbal Participation."""
        session_google = MockInterviewSession(company_type='Google', role_target='Software Engineer Intern')
        # Candidate was silent - no Student turns or empty text
        empty_transcript = [
            {'speaker': 'Priya', 'text': 'Tell me about yourself.'},
            {'speaker': 'Priya', 'text': 'Are you ready to begin?'}
        ]
        report = generate_mock_interview_report(session_google, empty_transcript)
        self.assertEqual(report['overall_score'], Decimal('1.0'))
        self.assertEqual(report['communication_score'], Decimal('1.0'))
        self.assertEqual(report['content_score'], Decimal('1.0'))
        self.assertEqual(report['confidence_score'], Decimal('1.0'))
        self.assertEqual(report['body_language_score'], Decimal('1.0'))
        self.assertEqual(report['tier_label'], 'No Verbal Participation')
        self.assertEqual(report['tier_class'], 'danger')
        self.assertIn('Zero Verbal Participation', report['areas_for_improvement'][0])

        # Check Big tech principles are marked with No Signal
        self.assertIsNotNone(report['big_tech_evaluation'])
        for principle in report['big_tech_evaluation']['principles_evaluated']:
            self.assertEqual(principle['status'], 'No Signal')

    def test_comprehensive_interview_yields_high_rating(self):
        """Verify that when a candidate answers substantively with STAR details and metrics, rating reflects strong competence (>= 7.5/10)."""
        session_amazon = MockInterviewSession(company_type='Amazon', role_target='Software Development Engineer')
        detailed_transcript = [
            {'speaker': 'Priya', 'text': 'Tell me about a complex project you designed and delivered.'},
            {
                'speaker': 'Student',
                'text': 'During my previous software internship, I took ownership of our microservice payment processing gateway that suffered from severe latency bottlenecks during flash sale traffic spikes. As lead backend engineer, my task was to bring 99th percentile transaction response times below 250 milliseconds while handling 6000 concurrent requests per second. I designed and implemented an asynchronous event-driven architecture using Python Django, Celery, and Redis caching. I decoupled synchronous database transactions using an Amazon SQS queue, optimized relational PostgreSQL indexes, and architected automated circuit breakers with retry backoff. As a result, our checkout latency dropped by 85 percent from 2.8 seconds to 190 milliseconds, zero transactions were lost, and customer cart completion improved by 28 percent across 2 million orders.'
            }
        ]
        report = generate_mock_interview_report(session_amazon, detailed_transcript)
        self.assertGreaterEqual(float(report['overall_score']), 7.5)
        self.assertIn(report['tier_label'], ['Strong Candidate', 'Exceptional Candidate'])
        self.assertIsNotNone(report['big_tech_evaluation'])
        self.assertIn('Amazon', report['big_tech_evaluation']['company'])

    def test_candidate_answer_is_sent_once_to_gemini(self):
        answer = 'I built a campus scheduling app and improved booking completion by twenty percent.'
        api_response = Mock(status_code=200)
        api_response.json.return_value = {
            'candidates': [{
                'content': {'parts': [{
                    'text': json.dumps({
                        'speech_text': 'You improved completion. How did you measure that change?',
                        'emotion': 'curious',
                        'gesture': 'nod',
                        'internal_score_note': 'Included a measurable outcome'
                    })
                }]}
            }]
        }
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test-key',
            'GOOGLE_API_KEY': '',
            'ANTHROPIC_API_KEY': ''
        }), patch('interviews.services.requests.post', return_value=api_response) as post:
            generate_priya_interviewer_turn(
                user_name='Ananya',
                role_target='Product Intern',
                interview_type='HR',
                difficulty='BEGINNER',
                transcript=[
                    {'speaker': 'Aria', 'text': 'Tell me about a project.'},
                    {'speaker': 'Student', 'text': answer}
                ],
                current_question='Tell me about a project.',
                student_answer=answer,
                speech_metrics={'filler_count': 2, 'eye_contact_percent': 72}
            )

        contents = post.call_args.kwargs['json']['contents']
        system_instruction = post.call_args.kwargs['json']['systemInstruction']['parts'][0]['text']
        self.assertEqual([item['role'] for item in contents], ['model', 'user'])
        self.assertEqual(contents[-1]['parts'][0]['text'].count(answer), 1)
        self.assertIn('"eye_contact_percent": 72', contents[-1]['parts'][0]['text'])
        self.assertIn('Do not reveal APIs', system_instruction)

    def test_fallback_gives_behavioral_guidance_for_candidate_question(self):
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': '',
            'GOOGLE_API_KEY': '',
            'ANTHROPIC_API_KEY': ''
        }):
            turn = generate_priya_interviewer_turn(
                user_name='Ananya',
                role_target='Product Intern',
                interview_type='BEHAVIORAL',
                difficulty='BEGINNER',
                transcript=[],
                current_question='Tell me about a time you handled a challenge.',
                student_answer='Can you explain what I should include in this answer?'
            )

        self.assertIn('STAR', turn['speech_text'])
        self.assertIn('situation', turn['speech_text'].lower())


class DomainSpecificQuestionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='domain_tester',
            email='tester@campuslink.edu',
            password='Password@123',
            first_name='Ananya',
            last_name='Das',
        )
        Membership.objects.create(user=self.user, plan='PRO_MONTHLY', status='ACTIVE')

    def test_identify_job_domain_mappings(self):
        self.assertEqual(identify_job_domain('Mobile App Developer', ['Flutter', 'Android']), 'MOBILE')
        self.assertEqual(identify_job_domain('QA & Automation Engineer', ['PyTest', 'Selenium']), 'QA')
        self.assertEqual(identify_job_domain('Software Engineer Intern', ['DSA', 'Algorithms']), 'SWE_INTERN')
        self.assertEqual(identify_job_domain('Frontend Developer', ['React', 'CSS']), 'FRONTEND')
        self.assertEqual(identify_job_domain('Python Backend Developer', ['Django', 'FastAPI']), 'BACKEND')
        self.assertEqual(identify_job_domain('Data Analyst', ['SQL', 'Pandas']), 'DATA')
        self.assertEqual(identify_job_domain('DevOps Engineer', ['Docker', 'AWS']), 'DEVOPS')
        self.assertEqual(identify_job_domain('Full Stack Web Developer', ['MERN', 'React']), 'FULLSTACK')

    def test_mobile_domain_questions_tailoring(self):
        questions = get_interview_questions(
            role_target='Mobile App Developer',
            company_type='Consumer Apps Corp',
            interview_type='TECHNICAL',
            difficulty='BEGINNER',
            custom_skills=['Flutter', 'Android']
        )
        self.assertTrue(len(questions) >= 4)
        combined = " ".join(questions).lower()
        self.assertTrue('mobile' in combined or 'flutter' in combined or 'lifecycle' in combined)

    def test_qa_domain_questions_tailoring(self):
        questions = get_interview_questions(
            role_target='QA & Automation Engineer',
            company_type='Enterprise Quality Inc',
            interview_type='TECHNICAL',
            difficulty='BEGINNER',
            custom_skills=['PyTest', 'Selenium']
        )
        self.assertTrue(len(questions) >= 4)
        combined = " ".join(questions).lower()
        self.assertTrue('test' in combined or 'pyramid' in combined or 'qa' in combined)

    def test_swe_intern_domain_questions_tailoring(self):
        questions = get_interview_questions(
            role_target='Software Engineer Intern',
            company_type='Tech Innovations',
            interview_type='TECHNICAL',
            difficulty='BEGINNER',
            custom_skills=['DSA', 'Data Structures']
        )
        self.assertTrue(len(questions) >= 4)
        combined = " ".join(questions).lower()
        self.assertTrue('array' in combined or 'hash' in combined or 'data structures' in combined)

    def test_api_start_mock_interview_returns_domain_and_skills(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse('api_start_mock_interview'),
            data=json.dumps({
                'role_target': 'Mobile App Developer',
                'company_type': 'Consumer Apps Corp',
                'interview_type': 'TECHNICAL',
                'difficulty': 'BEGINNER',
                'duration_minutes': 15,
                'skills': ['Flutter', 'Dart', 'Android']
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['domain'], 'MOBILE')
        self.assertIn('Flutter', data['job_info']['skills'])
        self.assertTrue(len(data['questions']) >= 4)

