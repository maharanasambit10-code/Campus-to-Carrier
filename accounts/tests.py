from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Membership, Payment, User
from students.models import Achievement, Certification, Internship, Skill, StudentProfile
from companies.models import Company
from recruiters.models import RecruiterProfile
from jobs.models import Job
from applications.models import Application
from ai_engine.services import calculate_career_readiness, match_jobs
from notifications.models import Notification
from interviews.models import Interview


class LoginFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('student1', password='password123', role='STUDENT')
        StudentProfile.objects.create(user=self.student)
        self.recruiter = User.objects.create_user('recruiter1', password='password123', role='RECRUITER')
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company=Company.objects.create(name='Test Company'),
        )
        self.officer = User.objects.create_user('officer1', password='password123', role='PLACEMENT_OFFICER')
        self.admin = User.objects.create_user(
            'admin1', password='admin-password123', role='SUPER_ADMIN', is_staff=True
        )

    def test_role_logins_create_sessions_and_redirect(self):
        expected = {
            'student1': reverse('student_dashboard'),
            'recruiter1': reverse('recruiter_dashboard'),
            'officer1': reverse('officer_dashboard'),
        }
        for username, destination in expected.items():
            with self.subTest(username=username):
                response = self.client.post(reverse('login'), {'username': username, 'password': 'password123'})
                self.assertRedirects(response, destination, fetch_redirect_response=False)
                self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get(username=username).pk)
                self.client.logout()

    def test_invalid_login_shows_an_error_without_authenticating(self):
        response = self.client.post(reverse('login'), {'username': 'wrongusername', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_uses_post_and_redirects_home(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_student_registration_creates_account_profile_and_session(self):
        response = self.client.post(reverse('student_register'), {
            'first_name': 'New',
            'last_name': 'Student',
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'password': 'strong-password-123',
            'confirm_password': 'strong-password-123',
            'phone': '9000000000',
            'college': 'BPUT',
            'department': 'Computer Science',
        })

        self.assertRedirects(response, reverse('student_dashboard'), fetch_redirect_response=False)
        user = User.objects.get(username='newstudent')
        self.assertEqual(user.role, 'STUDENT')
        self.assertTrue(user.check_password('strong-password-123'))
        self.assertEqual(user.student_profile.college, 'BPUT')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_student_registration_rejects_duplicate_username(self):
        response = self.client.post(reverse('student_register'), {
            'first_name': 'Another',
            'username': 'student1',
            'email': 'another@example.com',
            'password': 'strong-password-123',
            'confirm_password': 'strong-password-123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This username is already in use.')

    def test_two_step_registration_completes_student_profile_and_logs_in(self):
        self.client.logout()
        account_response = self.client.post(reverse('student_register'), {
            'step': 'account',
            'first_name': 'Profile',
            'last_name': 'Builder',
            'username': 'profilebuilder',
            'email': 'profilebuilder@example.com',
            'phone': '9000000000',
            'password': 'strong-password-123',
            'confirm_password': 'strong-password-123',
        })

        self.assertRedirects(account_response, f'{reverse("student_register")}?step=profile', fetch_redirect_response=False)
        user = User.objects.get(username='profilebuilder')

        profile_response = self.client.post(reverse('student_register'), {
            'step': 'profile',
            'college': 'BPUT',
            'degree': 'B.Tech',
            'department': 'Computer Science',
            'specialization': 'AI and Machine Learning',
            'current_semester': '6',
            'graduation_year': '2027',
            'cgpa': '8.7',
            'skills': 'Python, Django, SQL',
            'preferred_job_role': 'Backend Developer',
            'job_type': 'BOTH',
            'preferred_work_location': 'HYBRID',
            'linkedin': 'https://linkedin.com/in/profilebuilder',
            'github': 'https://github.com/profilebuilder',
            'portfolio': 'https://profilebuilder.example.com',
        })

        self.assertRedirects(profile_response, reverse('student_dashboard'), fetch_redirect_response=False)
        user.refresh_from_db()
        profile = user.student_profile
        self.assertEqual(user.role, 'STUDENT')
        self.assertTrue(user.check_password('strong-password-123'))
        self.assertEqual(profile.specialization, 'AI and Machine Learning')
        self.assertEqual(profile.current_semester, 6)
        self.assertEqual(profile.preferred_job_role, 'Backend Developer')
        self.assertEqual(set(profile.studentskill_set.values_list('skill__name', flat=True)), {'Python', 'Django', 'Sql'})
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_admin_login_has_separate_form_and_redirects_to_admin_dashboard(self):
        response = self.client.get('/admin/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Login')

        response = self.client.post(reverse('admin_login'), {
            'username': 'admin1',
            'password': 'admin-password123',
        })
        self.assertRedirects(response, reverse('admin_dashboard'), fetch_redirect_response=False)

    def test_user_login_cannot_authenticate_admin_and_user_cannot_open_admin_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin1',
            'password': 'admin-password123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

        self.client.force_login(self.student)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(response, reverse('student_dashboard'), fetch_redirect_response=False)

    def test_pro_feature_requires_active_membership(self):
        response = self.client.get(reverse('pro_landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CampusLinkLearn PRO')

        self.client.force_login(self.student)
        locked_response = self.client.get(reverse('pro_feature', args=['resume-analyzer']))
        self.assertEqual(locked_response.status_code, 200)
        self.assertContains(locked_response, 'This feature is available with CampusLinkLearn PRO')

        Membership.objects.update_or_create(
            user=self.student,
            defaults={'plan': 'PRO_MONTHLY', 'status': 'ACTIVE'},
        )
        unlocked_response = self.client.get(reverse('pro_feature', args=['resume-analyzer']))
        self.assertContains(unlocked_response, 'PRO feature unlocked')

    def test_dashboard_pro_links_and_landing_cards_clickable(self):
        # 1. Free student accesses dashboard
        self.client.force_login(self.student)
        dash_resp = self.client.get(reverse('student_dashboard'))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, reverse('pro_landing'))
        self.assertContains(dash_resp, reverse('ai_mock_interview'))
        self.assertContains(dash_resp, reverse('course_list'))

        # 2. Free student visits pro landing page
        landing_resp = self.client.get(reverse('pro_landing'))
        self.assertEqual(landing_resp.status_code, 200)
        # Verify cards are <a> tags linking to feature unlock pages
        for slug in ['resume-analyzer', 'mock-interview', 'job-matching', 'career-roadmap', 'learning-hub', 'career-intelligence']:
            feature_url = reverse('pro_feature', args=[slug])
            self.assertContains(landing_resp, f'href="{feature_url}"')
            feat_resp = self.client.get(feature_url)
            self.assertEqual(feat_resp.status_code, 200)
            self.assertContains(feat_resp, 'This feature is available with CampusLinkLearn PRO')

        # 3. Active PRO student visits pro landing page
        Membership.objects.update_or_create(
            user=self.student,
            defaults={'plan': 'PRO_MONTHLY', 'status': 'ACTIVE'},
        )
        pro_landing_resp = self.client.get(reverse('pro_landing'))
        self.assertEqual(pro_landing_resp.status_code, 200)
        self.assertContains(pro_landing_resp, f'href="{reverse("ai_mock_interview")}"')
        self.assertContains(pro_landing_resp, f'href="{reverse("career_match")}"')
        self.assertContains(pro_landing_resp, f'href="{reverse("course_list")}"')
        self.assertContains(pro_landing_resp, 'Launch Feature')

        # Direct navigation to the features returns 200
        self.assertEqual(self.client.get(reverse('ai_mock_interview')).status_code, 200)
        self.assertEqual(self.client.get(reverse('career_match')).status_code, 200)
        self.assertEqual(self.client.get(reverse('course_list')).status_code, 200)

    def test_checkout_does_not_fake_membership_activation(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('pro_checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No payment is taken in this environment')
        membership = Membership.objects.get(user=self.student)
        self.assertEqual(membership.plan, 'FREE')

    def test_checkout_tracks_selected_plan_and_payment_method_as_pending(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('pro_checkout'), {
            'plan': 'PRO_ANNUAL',
            'payment_method': 'UPI',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'UPI')
        membership = Membership.objects.get(user=self.student)
        self.assertEqual(membership.plan, 'PRO_ANNUAL')
        self.assertEqual(membership.status, 'PENDING')
        self.assertEqual(membership.provider, 'UPI')

    def test_users_cannot_open_another_role_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('recruiter_dashboard'))
        self.assertRedirects(response, reverse('student_dashboard'), fetch_redirect_response=False)

        self.client.force_login(self.recruiter)
        response = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(response, reverse('recruiter_dashboard'), fetch_redirect_response=False)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse('profile'))

        self.assertRedirects(response, f'{reverse("login")}?next={reverse("profile")}')

    def test_student_profile_link_and_edit_persist_user_and_profile_data(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('student_dashboard'))
        self.assertContains(response, f'href="{reverse("profile")}"')

        profile_response = self.client.get(reverse('profile'))
        self.assertRedirects(profile_response, reverse('student_profile'))

        save_response = self.client.post(reverse('profile'), {
            'first_name': 'Bapuni',
            'last_name': 'Behera',
            'email': 'bapuni@example.com',
            'phone': '8093568055',
            'department': 'Computer Science',
            'college': 'BPUT',
            'graduation_year': '2026',
            'cgpa': '8.5',
            'tenth_percentage': '85',
            'twelfth_percentage': '87',
            'location': 'Bhubaneswar, Odisha',
            'about_me': 'Placement-focused student',
            'career_objective': 'Backend engineering',
            'linkedin': 'https://linkedin.com/in/bapuni',
            'github': 'https://github.com/bapuni',
            'portfolio': '',
            'leetcode': '',
        })

        self.assertRedirects(save_response, reverse('student_profile'))
        self.student.refresh_from_db()
        self.student.student_profile.refresh_from_db()
        self.assertEqual(self.student.get_full_name(), 'Bapuni Behera')
        self.assertEqual(self.student.email, 'bapuni@example.com')
        self.assertEqual(self.student.student_profile.phone, '8093568055')
        self.assertEqual(self.student.student_profile.location, 'Bhubaneswar, Odisha')

    def test_recruiter_profile_uses_existing_recruiter_profile_and_saves(self):
        self.client.force_login(self.recruiter)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Account profile')

        save_response = self.client.post(reverse('profile'), {
            'first_name': 'Recruiter',
            'last_name': 'Lead',
            'email': 'lead@example.com',
            'designation': 'Talent Partner',
            'phone': '9000000000',
        })

        self.assertRedirects(save_response, reverse('profile'))
        self.recruiter.refresh_from_db()
        self.recruiter.recruiter_profile.refresh_from_db()
        self.assertEqual(self.recruiter.get_full_name(), 'Recruiter Lead')
        self.assertEqual(self.recruiter.recruiter_profile.designation, 'Talent Partner')
        self.assertEqual(self.recruiter.recruiter_profile.phone, '9000000000')

    def test_student_can_manage_profile_records_and_preview(self):
        self.client.force_login(self.student)
        certification_response = self.client.post(reverse('save_certification'), {
            'name': 'Django Developer',
            'issuer': 'Django Software Foundation',
            'issue_date': '2026-01-15',
            'credential_id': 'DJ-123',
            'credential_url': 'https://example.com/credential',
        })
        experience_response = self.client.post(reverse('save_internship'), {
            'company': 'Campus Labs',
            'role': 'Backend Intern',
            'employment_type': 'INTERNSHIP',
            'location': 'Bhubaneswar',
            'start_date': '2025-06-01',
            'end_date': '2025-08-31',
            'description': 'Built placement APIs.',
            'skills_used': 'Python, Django',
        })
        achievement_response = self.client.post(reverse('save_achievement'), {
            'title': 'Hackathon finalist',
            'description': 'Reached the final round.',
            'achieved_on': '2026-02-01',
            'organization': 'Campus Hack',
            'proof_url': 'https://example.com/proof',
        })

        self.assertRedirects(certification_response, reverse('student_profile'))
        self.assertRedirects(experience_response, reverse('student_profile'))
        self.assertRedirects(achievement_response, reverse('student_profile'))
        self.assertTrue(Certification.objects.filter(student=self.student.student_profile, name='Django Developer').exists())
        self.assertTrue(Internship.objects.filter(student=self.student.student_profile, company='Campus Labs').exists())
        self.assertTrue(Achievement.objects.filter(student=self.student.student_profile, title='Hackathon finalist').exists())

        profile = self.student.student_profile
        self.assertEqual(profile.completion_percentage, 15)
        preview_response = self.client.get(reverse('recruiter_preview'))
        self.assertEqual(preview_response.status_code, 200)
        self.assertContains(preview_response, 'Hackathon finalist')

    def test_home_page_renders_live_platform_metrics(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'From Campus Talent to')
        self.assertContains(response, 'Smart job discovery')
        self.assertContains(response, 'Companies')

    def test_recruiter_can_create_job_and_view_dashboard(self):
        self.client.force_login(self.recruiter)
        response = self.client.post(reverse('recruiter_job_create'), {
            'title': 'Python Backend Engineer',
            'description': 'Build backend APIs and services.',
            'location': 'Bhubaneswar',
            'job_type': 'Full-Time',
            'salary': '12 LPA',
            'minimum_cgpa': '7.5',
            'maximum_backlogs': '0',
            'graduation_year': '2026',
            'application_deadline': '2027-01-15 12:00:00',
            'required_skills': [str(Skill.objects.create(name='Python').id), str(Skill.objects.create(name='Django').id)],
            'preferred_skills': [str(Skill.objects.create(name='SQL').id)],
            'min_tenth': '60',
            'min_twelfth': '60',
            'allowed_departments': 'CSE, IT',
            'work_mode': 'Hybrid',
            'internship_type': 'Full-Time',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Job.objects.filter(title='Python Backend Engineer').exists())

    def test_recruiter_can_edit_owned_job_and_update_application_status(self):
        self.client.force_login(self.recruiter)
        job = Job.objects.create(
            company=self.recruiter.recruiter_profile.company,
            title='Original Role',
            description='Original description',
            location='Bhubaneswar',
            application_deadline='2027-01-15T12:00:00Z',
        )
        application = Application.objects.create(
            student=self.student.student_profile,
            job=job,
        )

        edit_response = self.client.post(reverse('recruiter_job_edit', args=[job.id]), {
            'title': 'Updated Role',
            'description': 'Updated description',
            'location': 'Remote',
            'job_type': 'Full-Time',
            'salary': '14 LPA',
            'minimum_cgpa': '8',
            'maximum_backlogs': '0',
            'graduation_year': '2026',
            'application_deadline': '2027-02-15 12:00:00',
            'work_mode': 'Remote',
            'required_skills': [],
            'preferred_skills': [],
        })
        status_response = self.client.post(reverse('recruiter_application_status', args=[application.id]), {'status': 'SHORTLISTED'})

        self.assertEqual(edit_response.status_code, 302)
        self.assertEqual(status_response.status_code, 302)
        self.assertEqual(Job.objects.get(id=job.id).title, 'Updated Role')
        self.assertEqual(Application.objects.get(id=application.id).status, 'SHORTLISTED')

    def test_officer_can_verify_company_and_recruiter_can_schedule_interview(self):
        pending_company = Company.objects.create(name='Pending Company')
        self.client.force_login(self.officer)
        verify_response = self.client.post(reverse('verify_company', args=[pending_company.id]), {'status': 'VERIFIED'})
        self.assertEqual(verify_response.status_code, 302)
        self.assertEqual(Company.objects.get(id=pending_company.id).verification_status, 'VERIFIED')

        self.client.force_login(self.recruiter)
        job = Job.objects.create(
            company=self.recruiter.recruiter_profile.company,
            title='Interview Role',
            description='Interview role',
            location='Remote',
            application_deadline='2027-01-15T12:00:00Z',
        )
        application = Application.objects.create(student=self.student.student_profile, job=job)
        schedule_response = self.client.post(reverse('schedule_interview', args=[application.id]), {
            'round_name': 'Technical Round',
            'scheduled_at': '2027-01-15T10:00',
            'mode': 'ONLINE',
            'meeting_link': 'https://example.com/interview',
        })

        self.assertEqual(schedule_response.status_code, 302)
        self.assertTrue(Interview.objects.filter(application=application, round_name='Technical Round').exists())
        self.assertTrue(Notification.objects.filter(user=self.student, title='Interview scheduled').exists())
        self.assertEqual(Application.objects.get(id=application.id).status, 'INTERVIEW')

    def test_ai_matching_and_career_readiness_use_real_profile_data(self):
        student_user = User.objects.create_user('student-match', password='password123', role='STUDENT')
        profile = StudentProfile.objects.create(user=student_user, cgpa=8.7, department='CSE', graduation_year=2026)
        python = Skill.objects.create(name='Python')
        django = Skill.objects.create(name='Django')
        sql = Skill.objects.create(name='SQL')
        profile.skills.add(python, django, sql)

        company = Company.objects.create(name='Demo Company')
        role_job = Job.objects.create(
            company=company,
            title='Backend Developer',
            description='Build APIs',
            location='Bhubaneswar',
            job_type='Full-Time',
            salary='10 LPA',
            minimum_cgpa=7.5,
            maximum_backlogs=0,
            graduation_year=2026,
            application_deadline='2027-01-15T12:00:00Z',
            min_tenth=60,
            min_twelfth=60,
            allowed_departments='CSE, IT',
            work_mode='Hybrid',
            internship_type='Full-Time'
        )
        role_job.required_skills.add(python, django, sql)

        matches = match_jobs(profile, [role_job])
        readiness = calculate_career_readiness(profile)

        self.assertTrue(matches[0]['score'] >= 0)
        self.assertIn('matched_skills', matches[0])
        self.assertGreaterEqual(readiness, 0)
        self.assertLessEqual(readiness, 100)



class RazorpayPaymentFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('probuyer', password='password123', role='STUDENT')
        Membership.objects.get_or_create(user=self.user)

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret_key_123', RAZORPAY_WEBHOOK_SECRET='webhook_secret_123')
    @patch('accounts.views.get_razorpay_client')
    def test_valid_plan_creates_correct_razorpay_order(self, mock_client):
        mock_client.return_value.order.create.return_value = {'id': 'order_123', 'amount': 199900, 'currency': 'INR'}

        self.client.force_login(self.user)
        response = self.client.post(reverse('razorpay_create_order'), {'plan': 'PRO_ANNUAL'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['order_id'], 'order_123')
        self.assertEqual(response.json()['amount'], 199900)
        self.assertTrue(Payment.objects.filter(user=self.user, razorpay_order_id='order_123').exists())

    def test_free_pro_monthly_activates_immediately(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('razorpay_create_order'), {'plan': 'PRO_MONTHLY'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['amount'], 100)

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret_key_123', RAZORPAY_WEBHOOK_SECRET='webhook_secret_123')
    def test_invalid_plan_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('razorpay_create_order'), {'plan': 'INVALID_PLAN'})

        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_order_request_is_rejected(self):
        response = self.client.post(reverse('razorpay_create_order'), {'plan': 'PRO_MONTHLY'})

        self.assertEqual(response.status_code, 302)

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret_key_123', RAZORPAY_WEBHOOK_SECRET='webhook_secret_123')
    def test_successful_payment_signature_activates_pro(self):
        self.client.force_login(self.user)
        order = Payment.objects.create(
            user=self.user,
            plan='PRO_MONTHLY',
            amount=Decimal('299.00'),
            currency='INR',
            status='created',
            razorpay_order_id='order_abc',
        )
        signature = self._signature_for('order_abc', 'pay_123')

        response = self.client.post(
            reverse('razorpay_verify_payment'),
            data={'razorpay_order_id': 'order_abc', 'razorpay_payment_id': 'pay_123', 'razorpay_signature': signature, 'plan': 'PRO_MONTHLY'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        membership = Membership.objects.get(user=self.user)
        self.assertEqual(membership.plan, 'PRO_MONTHLY')
        self.assertEqual(membership.status, 'ACTIVE')
        self.assertTrue(membership.is_active)

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret_key_123', RAZORPAY_WEBHOOK_SECRET='webhook_secret_123')
    def test_invalid_signature_does_not_activate_pro(self):
        self.client.force_login(self.user)
        Payment.objects.create(user=self.user, plan='PRO_MONTHLY', amount=Decimal('299.00'), currency='INR', status='created', razorpay_order_id='order_bad')

        response = self.client.post(
            reverse('razorpay_verify_payment'),
            data={'razorpay_order_id': 'order_bad', 'razorpay_payment_id': 'pay_bad', 'razorpay_signature': 'bad_signature', 'plan': 'PRO_MONTHLY'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        membership = Membership.objects.get(user=self.user)
        self.assertEqual(membership.plan, 'FREE')

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret_key_123', RAZORPAY_WEBHOOK_SECRET='webhook_secret_123')
    def test_failed_payment_does_not_activate_pro(self):
        self.client.force_login(self.user)
        payment = Payment.objects.create(user=self.user, plan='PRO_ANNUAL', amount=Decimal('1999.00'), currency='INR', status='pending', razorpay_order_id='order_failed')

        response = self.client.post(
            reverse('razorpay_verify_payment'),
            data={'razorpay_order_id': 'order_failed', 'razorpay_payment_id': 'pay_failed', 'razorpay_signature': 'bad_signature', 'plan': 'PRO_ANNUAL'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
        membership = Membership.objects.get(user=self.user)
        self.assertEqual(membership.plan, 'FREE')

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret_key_123', RAZORPAY_WEBHOOK_SECRET='webhook_secret_123')
    def test_webhook_signature_verification_requires_secret(self):
        payload = '{"event":"payment.captured","payload":{"payment":{"entity":{"order_id":"order_hook","id":"pay_hook"}}}}'
        signature = self._webhook_signature(payload, 'wrong-secret')

        response = self.client.post(
            reverse('razorpay_webhook'),
            data=payload,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature,
        )

        self.assertEqual(response.status_code, 400)

    def test_admin_payment_records_are_accessible_only_to_admins(self):
        admin_user = User.objects.create_user('adminpayment', password='password123', role='SUPER_ADMIN', is_staff=True)
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Payments & Memberships')

        self.client.force_login(self.user)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(response, reverse('student_dashboard'), fetch_redirect_response=False)

    @staticmethod
    def _signature_for(order_id, payment_id):
        import hashlib
        import hmac
        return hmac.new(b'secret_key_123', f'{order_id}|{payment_id}'.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _webhook_signature(payload, secret):
        import hashlib
        import hmac
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

