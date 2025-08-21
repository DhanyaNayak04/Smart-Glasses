import pyttsx3
from voice_commands import listen_for_commands
from conversational_ai import gemini_conversation
from obstacle_detection import estimate_depth_cpu
from detect_objects import detect_objects

API_KEY = "AIzaSyC1yvPtTKHY3EQ23XCB06lZQEEPdR51euE"

def speak_response(message):
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)
    engine.say(message)
    engine.runAndWait()

def main():
    while True:
        user_input = listen_for_commands()
        if user_input.strip().lower() in ["exit", "quit"]:
            speak_response("Goodbye.")
            break
        # Command handling
        elif "start detection" in user_input:
            speak_response("Starting obstacle detection.")
            estimate_depth_cpu()
        elif "stop detection" in user_input:
            speak_response("Stopping obstacle detection.")
            # No persistent process, so just acknowledge
        elif "what is this" in user_input or "detect object" in user_input:
            speak_response("Identifying the object.")
            detect_objects()
        elif "read this" in user_input:
            speak_response("Reading the text. OCR module not implemented yet.")
        elif "who is this" in user_input:
            speak_response("Identifying the person. Face recognition module not implemented yet.")
        else:
            # Open-ended conversation with Gemini
            ai_response = gemini_conversation(user_input, api_key=API_KEY)
            print("Gemini:", ai_response)
            speak_response(ai_response)

if __name__ == "__main__":
    main()
