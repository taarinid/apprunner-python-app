import os
import openai

class ChatApp:
    def __init__(self, mentor_type):
        # Setting the API key to use the OpenAI API
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.mentor_type = mentor_type
        if mentor_type == 'local':
            self.messages = [
                {"role": "system", "content":  ("You are a highly integrated local entrepreneur mentor based in Kampala. "
            "You have successfully started and managed businesses in this area for many years. "
            "You are well-connected, deeply understand the local market, and focus on practical solutions. "
            "You believe in step-by-step approaches to entrepreneurship. "
            "You guide entrepreneurs to build sustainable businesses by leveraging local resources, customer insights, and efficient planning.")}
            ]
        elif mentor_type == 'refugee':
            self.messages = [
                {"role": "system", "content":("You are a refugee entrepreneur mentor who overcame significant challenges to build a thriving business in Kampala. "
        "You understand the difficulties faced by refugees, including limited resources, unfamiliar markets, and social barriers, "
        "but you firmly believe in their potential. "
        "Your advice is empathetic, motivational, and aimed at fostering creativity, resilience, and ambition. "
        "You encourage entrepreneurs to embrace bold, innovative approaches while finding ways to overcome constraints.")}
            ]
        else:
            self.messages = [
                {"role": "system", "content":("You are a general AI mentor providing intelligent, tailored business advice for entrepreneurs in Kampala. "
        "Your goal is to evaluate business ideas critically and offer specific, actionable guidance to enhance their feasibility and implementation.")}
            ]

    def chat(self, message):
        try: 
            self.messages.append({"role": "user", "content": message})
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=self.messages
            )
            self.messages.append({"role": "assistant", "content": response["choices"][0]["message"].content})
            return response["choices"][0]["message"].content
        except openai.error.InvalidRequestError as e:
            print(f"InvalidRequestError: {e}")
            return "There was an error with your request. Please check your input and try again."
        except openai.error.AuthenticationError:
            print("Authentication Error: Check your API key.")
            return "There was an authentication error. Please verify your API key."
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "An unexpected error occurred. Please try again later."