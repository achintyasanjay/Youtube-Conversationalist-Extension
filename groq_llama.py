from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

api_key = "enter key here"

chat = ChatGroq(temperature=0, model_name="llama3-70b-8192", groq_api_key=api_key)

system = "You are a helpful assistant. "
human = "{text}"
prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

chain = prompt | chat
print(chain.invoke({"text": "Explain the importance of low latency LLMs."}))

# from groq.llmcloud import ChatCompletion

# with ChatCompletion("llama2-70b-4096") as chat:
#   prompt = "Who won the world series in 2020?"
#   response, id, stats =  chat.send_chat(prompt)
#   print(f"Question : {prompt}\nResponse : {response}\n")
#   prompt = "The Los Angeles Dodgers won the World Series in 2020."
#   response, id, stats =  chat.send_chat(prompt)
#   print(f"Question : {prompt}\nResponse : {response}\n")
#   prompt = "Where was it played?"
#   response, id, stats =  chat.send_chat(prompt)
#   print(f"Question : {prompt}\nResponse : {response}\n")
