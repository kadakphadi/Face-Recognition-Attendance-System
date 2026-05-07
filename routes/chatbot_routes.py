# routes/chatbot_routes.py
from flask import Blueprint, request, jsonify
from utils.decorators import login_required
from utils.chatbot import AttendanceChatbot
import logging

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot', __name__)
bot = AttendanceChatbot()


@chatbot_bp.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    """Chatbot API endpoint"""
    try:
        data = request.get_json()

        if not data or not data.get('message'):
            return jsonify({
                "status": "error",
                "message": "No message provided."
            }), 400

        user_message = data['message'].strip()

        if len(user_message) > 200:
            return jsonify({
                "status": "error",
                "message": "Message too long."
            }), 400

        response = bot.get_response(user_message)

        return jsonify({
            "status": "success",
            "message": response['message'],
            "type": response['type']
        })

    except Exception as e:
        logger.error(f"Chatbot API error: {e}")
        return jsonify({
            "status": "error",
            "message": "Server error. Please try again."
        }), 500