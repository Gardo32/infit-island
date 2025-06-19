from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
import asyncio
import os
import logging

from engine.logic.game_loop import GameLoop
from storage.database import db_handler
from engine.ai.llm_handler import LLMHandler

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize but don't create the Flask app here
socketio = SocketIO(async_mode='threading')
llm_handler = LLMHandler()

# In-memory game state management
game_state = {
    "game_loop": None,
    "is_running": False,
    "status": "Idle"
}

# In-memory log storage
log_capture = []

class SocketIOHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_capture.append(log_entry)
        socketio.emit('log_update', {'log': log_entry})

# Add the custom handler to the root logger
logger = logging.getLogger()
logger.addHandler(SocketIOHandler())

def configure_web_routes(app):
    """Configure all web routes with the provided Flask app"""
    app.config['SECRET_KEY'] = 'secret!'  # Replace with a real secret key
    app.static_folder = os.path.join(os.path.dirname(__file__), 'static')
    app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
    
    @app.route("/")
    def index():
        # Ensure templates directory exists
        template_path = os.path.join(app.template_folder, 'index.html')
        if os.path.exists(template_path):
            return render_template("index.html")
        else:
            return jsonify({
                "error": "Dashboard template not found", 
                "message": "Create templates/index.html for the director interface"
            }), 404

    @app.route("/logs")
    def logs():
        return render_template("logs.html", logs=log_capture)
        
    @app.route("/api/characters")
    def list_characters():
        characters_collection = db_handler.get_collection("characters")
        characters = list(characters_collection.find({}))
        for char in characters:
            char["id"] = char["_id"]
            del char["_id"]
        return jsonify(characters)

    @app.route("/api/characters/create", methods=["POST"])
    def create_character_endpoint():
        if not game_state["is_running"] or not game_state["game_loop"]:
            return jsonify({"error": "Game is not running. Please start the game first."}), 400
        
        try:
            # create_character is synchronous
            new_char = game_state["game_loop"].character_engine.create_character()
            # The returned doc has _id, need to convert for JSON response
            new_char["id"] = new_char["_id"]
            del new_char["_id"]
            return jsonify(new_char), 201
        except Exception as e:
            logging.error(f"Error creating character: {e}")
            return jsonify({"message": f"An internal error occurred: {str(e)}"}), 500

    @app.route("/api/characters/create_batch", methods=["POST"])
    def create_character_batch_endpoint():
        if not game_state["is_running"] or not game_state["game_loop"]:
            return jsonify({"error": "No season running. Please start a new season first."}), 400
        
        data = request.get_json()
        count = data.get('count', 1)

        if not 3 <= count <= 8:
            return jsonify({"error": "Cast size must be between 3 and 8 contestants."}), 400

        try:
            new_chars = game_state["game_loop"].character_engine.create_characters(count)
            
            for char in new_chars:
                char["id"] = char["_id"]
                del char["_id"]
            
            logging.info(f"Cast of {count} contestants created successfully.")

            return jsonify(new_chars), 201
        except Exception as e:
            logging.error(f"Error creating cast: {e}")
            return jsonify({"message": f"Cast creation error: {str(e)}"}), 500

    @app.route("/api/status")
    def status():
        # Make sure we're using the correct db_handler that has a ping() method
        # If db_handler is still not working, we can try to reinitialize it
        try:
            db_ok = db_handler.ping()
        except AttributeError:
            # If the method doesn't exist, try to import the correct handler or create a new instance
            from storage.database import DatabaseClient
            temp_db = DatabaseClient()
            db_ok = temp_db.ping()
        
        try:
            llm_ok = asyncio.run(llm_handler.ping())
        except Exception:
            llm_ok = False

        characters_collection = db_handler.get_collection("characters")
        character_count = characters_collection.count_documents({})

        return jsonify({
            "status": "ok",
            "season_status": game_state["status"],
            "cast_size": character_count,
            "director_role": "external_observer",
            "dependencies": {
                "database": "ok" if db_ok else "error",
                "llm": "ok" if llm_ok else "error"
            }
        })

# Register socket handlers
@socketio.on('connect')
def handle_connect():
    logging.info('Director connected to control dashboard')
    emit('game_state', {"status": game_state["status"]})

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Director disconnected from control dashboard')

@socketio.on('start_game')
def handle_start_game():
    if not game_state["is_running"]:
        logging.info("Director starting new season...")
        game_state["game_loop"] = GameLoop()
        asyncio.run(game_state["game_loop"].start())
        game_state["is_running"] = True
        game_state["status"] = "Season in Progress"
        emit('game_state', {"status": game_state["status"], "message": "New season started. Ready for cast creation."}, broadcast=True)
        logging.info("New season started.")

@socketio.on('end_game')
def handle_end_game():
    if game_state["is_running"]:
        logging.info("Director ending current season...")
        try:
            if game_state.get("game_loop"):
                asyncio.run(game_state["game_loop"].end_game()) # This will clear data
        except Exception as e:
            logging.error(f"Error during game_loop.end_game(): {e}")
            emit('error', {'message': f'Error during season cleanup: {str(e)}'})
        
        # Reset server state regardless of cleanup success
        game_state["is_running"] = False
        game_state["status"] = "Idle"
        game_state["game_loop"] = None
        emit('game_state', {"status": "Idle", "message": "Season ended. All data archived and cleared."}, broadcast=True)
        logging.info("Season ended and data cleared.")

@socketio.on('director_choice')
def handle_director_choice(data):
    if not game_state["is_running"] or not game_state["game_loop"]:
        emit('error', {'message': 'No season currently running.'})
        return

    choice_text = data.get('choice')
    logging.info(f"Director selected choice: {choice_text}")
    
    if not choice_text:
        emit('error', {'message': 'Missing choice selection.'})
        return

    try:
        response = asyncio.run(
            game_state["game_loop"].progress_story(choice_text)
        )
        response['source'] = 'NARRATOR'
        emit('story_update', response, broadcast=True)
        logging.info("Story progressed successfully.")
    except Exception as e:
        logging.error(f"Error during story progression: {e}")
        emit('error', {'message': f'Director control error: {str(e)}'})

@socketio.on('observe_character')
def handle_observe_character(data):
    if not game_state["is_running"] or not game_state["game_loop"]:
        emit('error', {'message': 'No season currently running.'})
        return

    character_id = data.get('character_id')
    observation_type = data.get('observation_type', 'general')  # 'general', 'private_thoughts', 'interaction'
    context = data.get('context', '')

    if not character_id:
        emit('error', {'message': 'Missing character_id.'})
        return

    try:
        response = asyncio.run(
            game_state["game_loop"].character_engine.observe_character(character_id, observation_type, context)
        )

        if "error" in response:
            emit('error', {'message': response['error']})
        else:
            response['source'] = 'OBSERVATION'
            response['character_id'] = character_id
            emit('character_observation', response, broadcast=True)
    except Exception as e:
        logging.error(f"Error during character observation: {e}")
        emit('error', {'message': f'Observation error: {str(e)}'})


@socketio.on('start_story')
def handle_start_story():
    if not game_state["is_running"] or not game_state["game_loop"]:
        emit('error', {'message': 'No season currently running.'})
        return

    try:
        # Check if we have characters
        characters_collection = db_handler.get_collection("characters")
        character_count = characters_collection.count_documents({})
        
        if character_count == 0:
            emit('error', {'message': 'No cast created yet. Please create a cast first.'})
            return

        logging.info("Director starting story...")
        story_data = asyncio.run(game_state["game_loop"].start_story())
        story_data['source'] = 'NARRATOR'
        emit('story_update', story_data, broadcast=True)
        logging.info("Story started successfully.")
    except Exception as e:
        logging.error(f"Error starting story: {e}")
        emit('error', {'message': f'Failed to start story: {str(e)}'})

# To run this application, create a `run.py` file in the root of your workspace with:
#
# from web.app import app, socketio
#
# if __name__ == '__main__':
#     socketio.run(app, debug=True, port=5000, host='0.0.0.0')
#
# Then run `python run.py` in your terminal.
        
        for char in new_chars:
            char["id"] = char["_id"]
            del char["_id"]
        
        logging.info(f"Cast of {count} contestants created successfully.")

        return jsonify(new_chars), 201
    except Exception as e:
        logging.error(f"Error creating cast: {e}")
        return jsonify({"message": f"Cast creation error: {str(e)}"}), 500




@socketio.on('start_story')
def handle_start_story():
    if not game_state["is_running"] or not game_state["game_loop"]:
        emit('error', {'message': 'No season currently running.'})
        return

    try:
        # Check if we have characters
        characters_collection = db_handler.get_collection("characters")
        character_count = characters_collection.count_documents({})
        
        if character_count == 0:
            emit('error', {'message': 'No cast created yet. Please create a cast first.'})
            return

        logging.info("Director starting story...")
        story_data = asyncio.run(game_state["game_loop"].start_story())
        story_data['source'] = 'NARRATOR'
        emit('story_update', story_data, broadcast=True)
        logging.info("Story started successfully.")
    except Exception as e:
        logging.error(f"Error starting story: {e}")
        emit('error', {'message': f'Failed to start story: {str(e)}'})

# To run this application, create a `run.py` file in the root of your workspace with:
#
# from web.app import app, socketio
#
# if __name__ == '__main__':
#     socketio.run(app, debug=True, port=5000, host='0.0.0.0')
#
# Then run `python run.py` in your terminal.
