import os
import unittest

from flaskr import create_app
from models import db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.database_name = "trivia_test"
        self.database_user = "postgres"
        self.database_password = "password"
        self.database_host = "localhost:5432"
        self.database_path = f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}/{self.database_name}"

        # Create app with the test configuration
        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": self.database_path,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "TESTING": True
        })
        self.client = self.app.test_client()

        # Bind the app to the current context and create all tables
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Executed after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
        # GET /categories
        def test_get_categories_success(self):
            res = self.client.get('/categories')
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertIn('categories', data)

        def test_get_categories_404(self):
            # Remove all categories to force 404
            with self.app.app_context():
                Category.query.delete()
                db.session.commit()
            res = self.client.get('/categories')
            data = res.get_json()
            self.assertEqual(res.status_code, 404)
            self.assertFalse(data['success'])

        # GET /questions
        def test_get_questions_success(self):
            res = self.client.get('/questions')
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertIn('questions', data)

        def test_get_questions_404(self):
            # Remove all questions to force 404
            with self.app.app_context():
                Question.query.delete()
                db.session.commit()
            res = self.client.get('/questions')
            data = res.get_json()
            self.assertEqual(res.status_code, 404)
            self.assertFalse(data['success'])

        # POST /questions (Create)
        def test_add_question_success(self):
            new_question = {
                'question': 'What is the capital of France?',
                'answer': 'Paris',
                'category': 1,
                'difficulty': 2
            }
            res = self.client.post('/questions', json=new_question)
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertIn('created', data)
            # Check persistence
            with self.app.app_context():
                q = Question.query.get(data['created'])
                self.assertIsNotNone(q)
                self.assertEqual(q.question, new_question['question'])

        def test_add_question_422(self):
            incomplete_question = {
                'question': 'Incomplete',
                'answer': '',
                'category': 1,
                'difficulty': 2
            }
            res = self.client.post('/questions', json=incomplete_question)
            data = res.get_json()
            self.assertEqual(res.status_code, 422)
            self.assertFalse(data['success'])

        # DELETE /questions/<id>
        def test_delete_question_success(self):
            with self.app.app_context():
                q = Question(question='Delete me', answer='A', category=1, difficulty=1)
                q.insert()
                qid = q.id
            res = self.client.delete(f'/questions/{qid}')
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertEqual(data['deleted'], qid)
            # Check persistence
            with self.app.app_context():
                self.assertIsNone(Question.query.get(qid))

        def test_delete_question_404(self):
            res = self.client.delete('/questions/99999')
            data = res.get_json()
            self.assertEqual(res.status_code, 404)
            self.assertFalse(data['success'])

        # POST /questions/search
        def test_search_questions_success(self):
            with self.app.app_context():
                q = Question(question='Find me', answer='A', category=1, difficulty=1)
                q.insert()
            res = self.client.post('/questions/search', json={'searchTerm': 'Find'})
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertGreaterEqual(data['total_questions'], 1)

        # GET /categories/<id>/questions
        def test_get_questions_by_category_success(self):
            with self.app.app_context():
                cat = Category(type='Science')
                db.session.add(cat)
                db.session.commit()
                q = Question(question='Science Q', answer='A', category=cat.id, difficulty=1)
                q.insert()
            res = self.client.get(f'/categories/{cat.id}/questions')
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertEqual(data['current_category'], cat.id)

        # POST /quizzes
        def test_play_quiz_success(self):
            with self.app.app_context():
                cat = Category(type='History')
                db.session.add(cat)
                db.session.commit()
                q = Question(question='History Q', answer='A', category=cat.id, difficulty=1)
                q.insert()
            quiz_payload = {
                'previous_questions': [],
                'quiz_category': {'id': cat.id}
            }
            res = self.client.post('/quizzes', json=quiz_payload)
            data = res.get_json()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertIsNotNone(data['question'])

        # Error handler tests
        def test_404_error_handler(self):
            res = self.client.get('/nonexistent')
            data = res.get_json()
            self.assertEqual(res.status_code, 404)
            self.assertFalse(data['success'])
            self.assertEqual(data['error'], 404)

        def test_422_error_handler(self):
            # Force 422 by sending bad POST to /questions
            res = self.client.post('/questions', json={})
            data = res.get_json()
            self.assertEqual(res.status_code, 422)
            self.assertFalse(data['success'])
            self.assertEqual(data['error'], 422)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
