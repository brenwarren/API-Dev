from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    return questions[start:end]

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    with app.app_context():
        db.create_all()

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        if not categories:
            abort(404)
        return jsonify({
            'success': True,
            'categories': {cat.id: cat.type for cat in categories}
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.id).all()
        if not current_questions:
            abort(404)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': {cat.id: cat.type for cat in categories},
            'current_category': None
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(question_id)
        if not question:
            abort(404)
        try:
            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    """
    @app.route('/questions', methods=['POST'])
    def add_question():
        data = request.get_json()
        question_text = data.get('question')
        answer = data.get('answer')
        category = data.get('category')
        difficulty = data.get('difficulty')
        if not (question_text and answer and category and difficulty):
            abort(422)
        try:
            question = Question(question=question_text, answer=answer, category=category, difficulty=difficulty)
            question.insert()
            return jsonify({
                'success': True,
                'created': question.id
            })
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        data = request.get_json()
        search_term = data.get('searchTerm', '')
        selection = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
        current_questions = [question.format() for question in selection]
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': None
        })

    """
    @TODO:
    Create a GET endpoint to get questions based on category.
    """
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        selection = Question.query.filter(Question.category == str(category_id)).all()
        current_questions = [question.format() for question in selection]
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': category_id
        })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        data = request.get_json()
        previous_questions = data.get('previous_questions', [])
        quiz_category = data.get('quiz_category', {})
        category_id = quiz_category.get('id', 0)
        if category_id == 0:
            questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
        else:
            questions = Question.query.filter(Question.category == str(category_id), Question.id.notin_(previous_questions)).all()
        if questions:
            question = random.choice(questions).format()
        else:
            question = None
        return jsonify({
            'success': True,
            'question': question
        })

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable entity'
        }), 422

    return app