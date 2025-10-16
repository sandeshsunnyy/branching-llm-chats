from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from typing import Sequence
from langchain_core.messages import BaseMessage, SystemMessage, trim_messages, AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from datetime import datetime, timezone
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
import langchain

try: 
  from dotenv import load_dotenv

  load_dotenv()

except ImportError:
  pass


model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
memory = MemorySaver()

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You talk like a 15th century man. Answer questions accordingly in {language}"
    ),
    MessagesPlaceholder(variable_name="messages"),
])

summarizer_prompt_template = ChatPromptTemplate.from_messages([
   (
      "system",
      """
         Persona:
         You are a summarizer. Your job is to summarize the messages given to you. A context will also be given so that you understand the whole picture. So summarize the text given under 'Messages to summarize'.

         Actual Workflow:
         I am building a project where people can branch from current chats to have different threads of conversations so that the main branch is not subjected to context decay. But if i want to return to the main branch, the summary of the branch must also be included so as to make the main context less oblivious. So your job is to give me that summary.

         Output Format:
         The result should be just the summary as a string. If the conversation is not worth having a summary, just reply what you thought his/her intention was.

         Final Instructions:
         1. Stick strictly to the output format.
         2. In the context provided, the AIMessage might have a persona. So it would be good if you could summarize based on that persona itself. I might have to deduct what the persona is yourself. If you are not able to, then it's fine just return a normal string.

         Context is given below:
      """
   ),
   MessagesPlaceholder(variable_name="context"),
   (
      "human",
      """
         Messages to summarize:

         {messages_to_summarize}
      """
   ),
])

trimmer = trim_messages(
    max_tokens=10000,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

def putMemory(config: dict, channel_values: dict, memory: MemorySaver) -> None:
   channel_value = channel_values
   current_ts = datetime.now(timezone.utc).isoformat()

   checkpoint = Checkpoint(
      v=1,
      id=current_ts,
      ts=current_ts,
      channel_values=channel_value,
      channel_versions={"messages":current_ts},
      versions_seen={"messages":current_ts}
   )

   metadata = CheckpointMetadata(
      source='input',
      step=0,
      parents={},
   )

   new_versions = {"messages":current_ts}
   memory.put(config=config, checkpoint=checkpoint, metadata=metadata, new_versions=new_versions)

class State(TypedDict):
    messages : Annotated[Sequence[BaseMessage], add_messages]
    branch: bool
    stop_chat: bool
    current_config: dict
    parent: list
    children: list

class Graph:

   def ask_user_to_branch(self, state:State):
         if not state["messages"]:
            return {"branch": False}
         # This is a step that could be completely avoided by a button in the UI
         query = input("Do you want to open a new branch? (y/n)").lower()
         if query == "y":
            return {"branch": True}
         elif query == "n":
            return {"branch": False}
         else:
            print("Invalid entry.. try again..")
            result = self.ask_user_to_branch(state=state)
            return result
   
   @staticmethod
   def brancher(state:State):
      if state["branch"] == True:
         return "branch"
      else:
         return "no branch"
   
   @staticmethod
   def call_model(state:State):
      trimmed_messages = trimmer.invoke(state["messages"])
      chain = prompt_template | model | StrOutputParser()
      chunks = []
      for chunk in chain.stream({"messages": trimmed_messages, "language": "English"}):
         chunks.append(chunk)
         print(chunk, end="", flush=True)
      print("\n\n")
      response = ''.join(chunks)
      return {"messages" : [AIMessage(content=response)]}


   def branch_chat(self, state:State):

      length_of_current_context = len(state["messages"])

      config_new_branch = {"configurable": {"thread_id": "abc125", "checkpoint_ns": "branch1"}}

      new_app = BranchGraph().buildGraph()

      branch_state = new_app.invoke({"messages": state["messages"], "current_config":config_new_branch}, config=config_new_branch)
      
      putMemory(config=config_new_branch, channel_values=branch_state, memory=memory)

      summary_chain = summarizer_prompt_template | model | StrOutputParser()
      text_to_summarize = "\n".join(message.content for message in branch_state["messages"][length_of_current_context:])
      summary = summary_chain.invoke({"context": state["messages"], "messages_to_summarize" : text_to_summarize})
      summary = SystemMessage(content=summary)

      return {"messages": [summary]}

   @staticmethod
   def query(state:State):
      user_input = input("Ask away: ")
      query = [HumanMessage(content=user_input)]
      return {"messages" : query}

   def stop(self, state: State):
      decision = input("Do you want to end the conversation? (y/n): ").strip().lower()
      if decision == 'y':
         return {"stop_chat": True }
      elif decision == 'n':
         return {"stop_chat": False}
      else:
         print("Invalid entry!")
         decision = self.stop(state)
         return decision

   @staticmethod
   def should_stop(state:State):
      if state["stop_chat"]:
         return "stop"
      else:
         return "continue"

   def buildGraph(self):
      workflow = StateGraph(state_schema=State)
      workflow.add_node("ask_to_branch", self.ask_user_to_branch)
      workflow.add_edge(START, "ask_to_branch")
      workflow.add_node("model", self.call_model)
      workflow.add_node("branch_chat", self.branch_chat)
      workflow.add_node("query", self.query)
      workflow.add_edge("query", "model")
      workflow.add_node("stop", self.stop)
      workflow.add_edge("model", "stop")
      workflow.add_edge("branch_chat", "stop")
      workflow.add_conditional_edges(
         source="ask_to_branch",
         path=self.brancher,
         path_map={
            "branch": "branch_chat",
            "no branch": "query"
         }
      )
      workflow.add_conditional_edges(
         source="stop",
         path=self.should_stop,
         path_map={
            "stop": END,
            "continue": "ask_to_branch"
         }
      )
      app = workflow.compile(memory)
      return app

class BranchGraph(Graph):

   def stop(self, state):
      decision = input("Do you want to return to main branch? (y/n): ").strip().lower()
      if decision == 'y':
         return {"stop_chat": True }
      elif decision == 'n':
         return {"stop_chat": False}
      else:
         print("Invalid entry!")
         decision = self.stop(state)
         return decision
      
   def buildGraph(self):
      workflow = StateGraph(state_schema=State)
      workflow.add_node("ask_to_branch", self.ask_user_to_branch)
      workflow.add_edge(START, "ask_to_branch")
      workflow.add_node("model", self.call_model)
      workflow.add_node("branch_chat", self.branch_chat)
      workflow.add_node("query", self.query)
      workflow.add_edge("query", "model")
      workflow.add_node("stop", self.stop)
      workflow.add_edge("model", "stop")
      workflow.add_edge("branch_chat", "stop")
      workflow.add_conditional_edges(
         source="ask_to_branch",
         path=self.brancher,
         path_map={
            "branch": "branch_chat",
            "no branch": "query"
         }
      )
      workflow.add_conditional_edges(
         source="stop",
         path=self.should_stop,
         path_map={
            "stop": END,
            "continue": "ask_to_branch"
         }
      )
      app = workflow.compile(memory)
      return app

app = Graph().buildGraph()

config = {"configurable" : {"thread_id": "abc124"}}

from langchain_core.messages import HumanMessage, AIMessage

app.invoke({"messages": [], "current_config": config}, config=config)


config_new_branch = {"configurable": {"thread_id": "abc125", "checkpoint_ns": "branch1"}}

memory_state = memory.get(config=config)
new_memory_state = memory.get(config=config_new_branch)

old_messages = memory_state["channel_values"]["messages"]
new_messages = new_memory_state["channel_values"]["messages"]

print("Old Messages")
print("-"*20)
print(old_messages)
print("\n")
print("New Messages")
print("-"*20)
print(new_messages)
print("\n")