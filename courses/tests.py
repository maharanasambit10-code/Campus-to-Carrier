from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from companies.models import Company

from .models import Course, CourseApplication


class CourseApplicationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='course-student',
            password='test-password-123',
            role='STUDENT',
        )
        self.client.force_login(self.user)
        self.company = Company.objects.create(name='Campus Academy')
        self.course = Course.objects.create(
            title='Django Backend Engineering',
            provider=self.company,
            description='Learn backend engineering with Django.',
        )

    def test_course_list_and_detail_render(self):
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.title)

        response = self.client.get(reverse('course_detail', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apply to Course')

    def test_student_can_apply_once_and_track_application(self):
        response = self.client.post(reverse('apply_course', args=[self.course.id]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.id]))
        self.assertTrue(CourseApplication.objects.filter(
            student=self.user.student_profile,
            course=self.course,
        ).exists())

        self.client.post(reverse('apply_course', args=[self.course.id]))
        self.assertEqual(CourseApplication.objects.filter(course=self.course).count(), 1)

        response = self.client.get(reverse('course_applications'))
        self.assertContains(response, self.course.title)
