import os
from dotenv import load_dotenv
import gradio as gr
from google import genai
from google.genai.types import HttpOptions

# 1. Env-Variablen laden
load_dotenv()  # Liest die Datei .env ein und setzt os.environ 
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Bitte setze die Environment-Variable GEMINI_API_KEY!")  # Sicherheit: Key muss vorhanden sein

# 2. Gen AI Client initialisieren
#    Wir nutzen explizit die HTTP-Optionen für API-Version v1
client = genai.Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1"))  # Gemini über Vertex AI API v1 :contentReference[oaicite:4]{index=4}

def respond_fn(user_message, history):
    """
    - user_message: aktuelle Eingabe des Nutzers
    - history: bisherige Chat-Paare als Liste von Tuple(str, str)
    """
    # 3. Anfrage an Gemini schicken
    response = client.models.generate_content(
        model="gemini-2.5-flash",    # Nutze das gewünschte Modell :contentReference[oaicite:5]{index=5}
        contents=user_message        # Prompt-Text
    )
    bot_message = response.text     # Antworttext extrahieren :contentReference[oaicite:6]{index=6}

    # 4. Chat-History aktualisieren
    history = history or []
    history.append((user_message, bot_message))
    return "", history               # leerer Text im Eingabefeld, aktualisierte History

# 5. Gradio-Interface definieren
with gr.Blocks() as demo:
    gr.Markdown("## MealPlanner Bot mit Gemini-Integration")
    chatbot = gr.Chatbot()          # Zeigt User- und Bot-Nachrichten an :contentReference[oaicite:7]{index=7}
    with gr.Row():
        inp = gr.Textbox(placeholder="Gib deine Frage ein...", show_label=False)
        btn = gr.Button("Senden")
    # Button-Klick und Enter-Taste triggern respond_fn
    btn.click(respond_fn, [inp, chatbot], [inp, chatbot])
    inp.submit(respond_fn, [inp, chatbot], [inp, chatbot])

if __name__ == "__main__":
    demo.launch()

