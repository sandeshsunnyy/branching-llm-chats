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

trimmer = trim_messages(
    max_tokens=10000,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

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
      memory_state = memory.get(config=config)

      channel_value = memory_state["channel_values"]
      current_ts = datetime.now(timezone.utc).isoformat()

      config_new_branch = {"configurable": {"thread_id": "abc125", "checkpoint_ns": "branch1"}}

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
      memory.put(config=config_new_branch, checkpoint=checkpoint, metadata=metadata, new_versions=new_versions)

      memory_state_new_branch = memory.get(config=config_new_branch)
      new_branch_memory = memory_state_new_branch["channel_values"]["messages"]

      length_of_current_context = len(new_branch_memory)

      new_app = BranchGraph().buildGraph()
      branch_state = new_app.invoke({"messages": new_branch_memory, "current_config":config_new_branch}, config=config_new_branch)
      #it should return a summary of whatever the messages where typed. Here whatever was added after the current point must be summerized and sent-back.
      #Give the length of current context as context and the rest for summarization.

      print(branch_state)

      return {"messages": branch_state["messages"][length_of_current_context:]} # this is for testing, will find out what to do here later.

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