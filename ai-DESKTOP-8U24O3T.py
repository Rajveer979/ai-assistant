import os
import threading
import webbrowser
import datetime
import speech_recognition as sr
from tkinter import Tk, Label, Entry, Button, Frame, Scrollbar, Text, END, messagebox
from concurrent.futures import ThreadPoolExecutor

try:
    from google import genai
except ImportError as e:
    raise ImportError(
        "Cannot import 'genai' from 'google'.\n"
        "Fixes:\n"
        "  1) Remove/rename any local 'google.py' or 'google' folder in your project.\n"
        "  2) Install the official client: pip install --upgrade google-genai\n"
        f"Original error: {e}"
    ) from e


class PersonalAssistant:
    """A personal AI assistant with GUI and voice input capabilities."""
    
    MODEL_NAME = "gemini-2.0-flash"
    WINDOW_SIZE = "1000x600"
    
    COMMANDS = {
        "hello": lambda: "Hello! How can I assist you today?",
        "open youtube": lambda: (webbrowser.open("https://www.youtube.com"), "Opening YouTube...")[1],
        "open google": lambda: (webbrowser.open("https://www.google.com"), "Opening Google...")[1],
        "time": lambda: f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}",
        "open notepad": lambda: (os.system("notepad"), "Opening Notepad...")[1],
        "bye": lambda: ("Goodbye! Have a great day!", True),
        "wiki": lambda: (webbrowser.open("https://www.wikipedia.org/"), "Opening Wikipedia...")[1],
        "open spotify": lambda: (webbrowser.open("https://open.spotify.com/"), "Opening Spotify...")[1],
    }

    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Personal Assistant")
        self.root.geometry(self.WINDOW_SIZE)
        self.root.config(bg="#121212")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.api_key = os.environ.get("GENAI_API_KEY")
        if not self.api_key:
            raise ValueError("GENAI_API_KEY environment variable not set. Please set it before running.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        self._setup_gui()

    def _setup_gui(self):
        """Initialize and layout all GUI widgets."""
        Label(
            self.root, 
            text="Ask me something:", 
            font=("Poppins", 18, "bold"), 
            bg="#121212", 
            fg="#E0E0E0"
        ).pack(pady=20)
        
        self.entry = Entry(
            self.root, 
            width=50, 
            font=("Poppins", 14), 
            bg="#1E1E1E", 
            fg="#E0E0E0", 
            insertbackground="#E0E0E0",
            bd=2, 
            relief="flat", 
            highlightbackground="#3C8DAD", 
            highlightthickness=2
        )
        self.entry.pack(pady=10)
        
        self.send_button = Button(
            self.root, 
            text="Send", 
            width=20, 
            height=2, 
            font=("Poppins", 14, "bold"), 
            bg="#3C8DAD", 
            fg="#FFFFFF", 
            relief="flat", 
            activebackground="#1DB954", 
            activeforeground="#121212", 
            command=self._on_send
        )
        self.send_button.pack(pady=20)
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(bg="#1DB954"))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(bg="#3C8DAD"))
        
        self.speech_button = Button(
            self.root, 
            text="🎤 Speak", 
            width=20, 
            height=2, 
            font=("Poppins", 14, "bold"), 
            bg="#FF5733", 
            fg="#FFFFFF", 
            relief="flat", 
            activebackground="#C70039", 
            activeforeground="#121212", 
            command=self._on_speech
        )
        self.speech_button.pack(pady=10)
        
        response_frame = Frame(self.root, bg="#1E1E1E", bd=2, relief="solid", width=900, height=400)
        response_frame.pack(pady=20)
        
        scrollbar = Scrollbar(response_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.result_text = Text(
            response_frame, 
            wrap="word", 
            font=("Poppins", 14), 
            height=15, 
            width=90, 
            bg="#1E1E1E", 
            fg="#E0E0E0", 
            insertbackground="#E0E0E0", 
            bd=0, 
            yscrollcommand=scrollbar.set
        )
        self.result_text.pack(padx=20, pady=20)
        scrollbar.config(command=self.result_text.yview)
        
        self.root.bind('<Return>', lambda e: self._on_send())

    def _on_send(self):
        """Handle send button click or Enter key press."""
        user_input = self.entry.get().strip()
        if not user_input:
            return
        
        self._set_ui_state(processing=True)
        self.executor.submit(self._process_input, user_input)

    def _on_speech(self):
        """Handle speech button click."""
        self._set_ui_state(processing=True)
        self.result_text.insert(END, "Listening...\n")
        self.result_text.yview(END)
        self.executor.submit(self._recognize_speech)

    def _process_input(self, user_input: str):
        """Process user input and return response."""
        user_input = user_input.lower()
        response = self._get_response(user_input)
        self.root.after(0, self._display_response, response)

    def _get_response(self, user_input: str) -> str:
        """Get response for user input, checking commands first, then LLM."""
        for cmd, action in self.COMMANDS.items():
            if cmd in user_input:
                result = action()
                if isinstance(result, tuple) and result[1] is True:
                    self.root.after(0, self.root.quit)
                return result if isinstance(result, str) else result[0] if isinstance(result, tuple) else ""
        
        return self._query_llm(user_input)

    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with appropriate error handling."""
        try:
            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Sorry, I'm having trouble connecting. Error: {type(e).__name__}"

    def _recognize_speech(self):
        """Recognize speech from microphone in a background thread."""
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio)
                self.root.after(0, self.entry.delete, 0, END)
                self.root.after(0, self.entry.insert, 0, text)
                self.root.after(0, self._on_send)
        except sr.UnknownValueError:
            self.root.after(0, self._display_response, "Sorry, I could not understand the audio.")
        except sr.WaitTimeoutError:
            self.root.after(0, self._display_response, "Listening timed out. Please try again.")
        except sr.RequestError:
            self.root.after(0, self._display_response, "Could not request results. Check your internet connection.")
        except Exception as e:
            self.root.after(0, self._display_response, f"Speech error: {type(e).__name__}")
        finally:
            self.root.after(0, self._set_ui_state, processing=False)

    def _display_response(self, response: str):
        """Display response in the GUI (must be called from main thread)."""
        self.result_text.delete(1.0, END)
        self.result_text.insert(END, response)
        self._set_ui_state(processing=False)

    def _set_ui_state(self, processing: bool):
        """Enable/disable UI elements during processing."""
        state = "disabled" if processing else "normal"
        self.entry.config(state=state)
        self.send_button.config(state=state)
        self.speech_button.config(state=state)

    def _on_closing(self):
        """Handle window close event."""
        self.executor.shutdown(wait=False)
        self.root.destroy()


def main():
    root = Tk()
    app = PersonalAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()