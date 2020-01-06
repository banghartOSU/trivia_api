import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def get_categories():
  categories = Category.query.order_by(Category.id).all()
  format_categories = [category.format() for category in categories]
  res = {}
  for category in format_categories:
    res.update({ category.get('id'):category.get('type') }) #needed to return single dict after formatting list
  return res

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]
  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={"/*" : {"origins": "*"}} )
  
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authroization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

  @app.route('/categories')
  def get_categories_path():
    if len(Category.query.all()) < 1:
      abort(404)
    try:
      categories = get_categories()
      return jsonify({
        'success':True, 
        'categories': categories
        })
    except:
      abort(500)

  @app.route('/questions')
  def get_questions():
    #@TODO: Make sure the condition should be here -- or elsewhere
    if len(Question.query.all()) < 1:
      abort(404)

    try:
      selection = Question.query.order_by(Question.id).all()
      current_selection = paginate_questions(request, selection)
      categories = get_categories()
      return jsonify({
        'success':True, 
        'questions': current_selection,
        'total_questions' : len(selection),
        'categories' : categories,
        'current_category' : 0
        })
    except:
      abort(500)


  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()
      question.delete()
      return jsonify({'success' : True})
    except:
      abort(422)

  @app.route('/questions', methods=['POST'])
  def add_new_question():
    req = request.get_json()
    try:
      if req.get('searchTerm'): #If the POST request includes a serach key from the serach submit button then it is a search
        search_term = req.get('searchTerm')
        selection = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
        formatted_questions = paginate_questions(request, selection)
        return jsonify({
          'success' : True,
          'questions' : formatted_questions,
          'total_questions' : len(selection),
          'current_category' : ''
        })
      else:
        question = Question(
          question=req.get('question'),
          answer=req.get('answer'),
          category=req.get('category'),
          difficulty=req.get('difficulty')
        )
        question.insert()
        return jsonify({
          'success':True
          })
    except:
      abort(422)
  

  @app.route('/categories/<int:category_id>/questions')
  def get_category_questions(category_id):
    try:
      selection = Question.query.filter(Question.category == category_id).all()
      current_category = Category.query.get(category_id).type
      current_questions = paginate_questions(request, selection)
      return jsonify({
        'success' : True,
        'questions' : current_questions,
        'total_questions' : len(current_questions),
        'current_category' : current_category
      })
    except:
      abort(422)

  @app.route('/quizzes', methods=['POST', 'GET'])
  def play_quiz():
    try:
      req = request.get_json()
      print(req)
      previous_questions = req.get('previous_questions')
      quiz_category = req.get('quiz_category')['id']
      print(quiz_category)

      if quiz_category :
        selection = Question.query.filter(~Question.id.in_(previous_questions), Question.category == quiz_category).all()
      else:
        selection = Question.query.filter(~Question.id.in_(previous_questions)).all()

      if selection:
        question = random.choice(selection).format()
      else: 
        question = False

      return jsonify({
        'success' : True,
        'question' : question
      })
    except:
      abort(422)

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success' : False,
      'error' : 404,
      'message' : 'resource not found'
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success' : False,
      'error' : 422,
      'message' : 'unprocessable'
    }), 422

  @app.errorhandler(500)
  def internal_server_error(error):
    return jsonify({
      'success' : False,
      'error' : 500,
      'message' : 'internal server error'
    }) , 500

  return app

    