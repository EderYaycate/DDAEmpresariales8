from django.contrib.auth.models import User
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Exam, Option, Question


class ApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_quiz', verbosity=0)
        cls.user = User.objects.get(username='admin')
        cls.exam = Exam.objects.get(title='Fundamentos de Python')

    def login(self):
        self.client.force_authenticate(self.user)

    @staticmethod
    def question_payload(exam_id, **overrides):
        payload = {
            'exam': exam_id,
            'text': '¿Cuál es la capital de Perú?',
            'options': [
                {'text': 'Lima', 'is_correct': True},
                {'text': 'Cusco', 'is_correct': False},
            ],
        }
        payload.update(overrides)
        return payload


class ReadTests(ApiTestCase):
    def test_root_lists_the_three_resources(self):
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for name in ('exams', 'questions', 'options'):
            self.assertIn(name, response.data)

    def test_browsable_api_renders_html_and_login_page_exists(self):
        page = self.client.get('/api/', HTTP_ACCEPT='text/html')
        self.assertEqual(page.status_code, 200)
        self.assertIn('text/html', page['Content-Type'])
        self.assertEqual(self.client.get('/api-auth/login/').status_code, 200)

    def test_created_exam_also_reports_its_question_count(self):
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/exams/', {'title': 'Vacío'}, format='json')
        self.assertEqual(response.data['question_count'], 0)

    def test_exam_list_is_paginated_and_counts_questions(self):
        response = self.client.get('/api/exams/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['question_count'], 7)

    def test_question_detail_nests_options_and_refers_exam_by_id(self):
        question = Question.objects.first()
        response = self.client.get(f'/api/questions/{question.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['exam'], question.exam_id)
        self.assertEqual(len(response.data['options']), 3)

    def test_pagination_has_a_second_page_and_the_last_page_is_short(self):
        first = self.client.get('/api/questions/')
        self.assertEqual(first.data['count'], 13)
        self.assertEqual(len(first.data['results']), 5)
        self.assertIsNotNone(first.data['next'])
        last = self.client.get('/api/questions/?page=3')
        self.assertEqual(len(last.data['results']), 3)
        self.assertIsNone(last.data['next'])

    def test_page_out_of_range_returns_404(self):
        self.assertEqual(self.client.get('/api/questions/?page=99').status_code, 404)

    def test_filter_questions_by_exam(self):
        response = self.client.get(f'/api/questions/?exam={self.exam.pk}')
        self.assertEqual(response.data['count'], 7)
        for item in response.data['results']:
            self.assertEqual(item['exam'], self.exam.pk)

    def test_filter_with_a_non_numeric_exam_returns_400(self):
        response = self.client.get('/api/questions/?exam=abc')
        self.assertEqual(response.status_code, 400)
        self.assertIn('exam', response.data)

    def test_search_questions_by_text(self):
        response = self.client.get('/api/questions/?search=lista')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['count'], 1)
        for item in response.data['results']:
            self.assertIn('lista', item['text'].lower())

    def test_search_and_exam_filter_combine(self):
        other = Exam.objects.exclude(pk=self.exam.pk).get()
        response = self.client.get(f'/api/questions/?exam={other.pk}&search=lista')
        self.assertEqual(response.data['count'], 1)  # the Django template-tag question

    def test_unknown_id_returns_404(self):
        self.assertEqual(self.client.get('/api/questions/9999/').status_code, 404)


class PermissionTests(ApiTestCase):
    def test_anonymous_cannot_write(self):
        response = self.client.post('/api/exams/', {'title': 'Nuevo'}, format='json')
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(Exam.objects.count(), 2)

    def test_anonymous_cannot_delete(self):
        response = self.client.delete(f'/api/exams/{self.exam.pk}/')
        self.assertIn(response.status_code, (401, 403))
        self.assertTrue(Exam.objects.filter(pk=self.exam.pk).exists())


class WriteTests(ApiTestCase):
    def setUp(self):
        self.login()

    def test_create_exam_returns_201(self):
        response = self.client.post(
            '/api/exams/', {'title': 'Bases de datos', 'description': 'SQL'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Exam.objects.filter(title='Bases de datos').exists())

    def test_create_question_with_nested_options(self):
        response = self.client.post(
            '/api/questions/', self.question_payload(self.exam.pk), format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data['options']), 2)
        self.assertEqual(Question.objects.get(pk=response.data['id']).options.count(), 2)

    def test_partial_update_changes_only_the_sent_field(self):
        question = Question.objects.first()
        before = question.options.count()
        response = self.client.patch(
            f'/api/questions/{question.pk}/', {'text': 'Texto nuevo'}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        question.refresh_from_db()
        self.assertEqual(question.text, 'Texto nuevo')
        self.assertEqual(question.options.count(), before)

    def test_patch_with_options_replaces_them(self):
        question = Question.objects.first()
        response = self.client.patch(
            f'/api/questions/{question.pk}/',
            {'options': [{'text': 'A', 'is_correct': True}, {'text': 'B', 'is_correct': False}]},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(o.text for o in question.options.all()), ['A', 'B'])

    def test_delete_question_returns_204_and_removes_its_options(self):
        question = Question.objects.first()
        option_ids = list(question.options.values_list('pk', flat=True))
        response = self.client.delete(f'/api/questions/{question.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Option.objects.filter(pk__in=option_ids).exists())

    def test_missing_required_field_returns_400(self):
        payload = self.question_payload(self.exam.pk)
        del payload['text']
        response = self.client.post('/api/questions/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('text', response.data)

    def test_wrong_type_returns_400(self):
        response = self.client.post(
            '/api/questions/', self.question_payload('no-es-un-numero'), format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('exam', response.data)

    def test_exam_that_does_not_exist_returns_400(self):
        response = self.client.post(
            '/api/questions/', self.question_payload(9999), format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('exam', response.data)

    def test_question_without_a_correct_option_is_rejected(self):
        payload = self.question_payload(
            self.exam.pk,
            options=[{'text': 'A', 'is_correct': False}, {'text': 'B', 'is_correct': False}],
        )
        response = self.client.post('/api/questions/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('options', response.data)

    def test_question_with_two_correct_options_is_rejected(self):
        payload = self.question_payload(
            self.exam.pk,
            options=[{'text': 'A', 'is_correct': True}, {'text': 'B', 'is_correct': True}],
        )
        response = self.client.post('/api/questions/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('exactamente una', str(response.data['options']))

    def test_rejected_question_leaves_nothing_behind(self):
        total = Question.objects.count()
        payload = self.question_payload(self.exam.pk, options=[])
        self.client.post('/api/questions/', payload, format='json')
        self.assertEqual(Question.objects.count(), total)

    def test_patch_options_without_correct_one_is_rejected_and_keeps_old_options(self):
        question = Question.objects.first()
        before = list(question.options.values_list('text', flat=True))
        response = self.client.patch(
            f'/api/questions/{question.pk}/',
            {'options': [{'text': 'X', 'is_correct': False}]},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(list(question.options.values_list('text', flat=True)), before)


class OptionRuleTests(ApiTestCase):
    def setUp(self):
        self.login()
        self.question = Question.objects.first()

    def test_add_a_wrong_option(self):
        response = self.client.post(
            '/api/options/',
            {'question': self.question.pk, 'text': 'Otra', 'is_correct': False},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_second_correct_option_is_rejected(self):
        response = self.client.post(
            '/api/options/',
            {'question': self.question.pk, 'text': 'Otra', 'is_correct': True},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_unmark_the_only_correct_option(self):
        correct = self.question.options.get(is_correct=True)
        response = self.client.patch(
            f'/api/options/{correct.pk}/', {'is_correct': False}, format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_delete_the_correct_option(self):
        correct = self.question.options.get(is_correct=True)
        response = self.client.delete(f'/api/options/{correct.pk}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Option.objects.filter(pk=correct.pk).exists())

    def test_can_delete_a_wrong_option(self):
        wrong = self.question.options.filter(is_correct=False).first()
        response = self.client.delete(f'/api/options/{wrong.pk}/')
        self.assertEqual(response.status_code, 204)

    def test_filter_options_by_question(self):
        response = self.client.get(f'/api/options/?question={self.question.pk}')
        self.assertEqual(response.data['count'], 3)
