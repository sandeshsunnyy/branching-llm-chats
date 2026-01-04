from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from typing import Sequence
from langchain_core.messages import BaseMessage, SystemMessage, trim_messages, AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from datetime import datetime, timezone
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
from utilities import prompt_template, summarizer_prompt_template, summarizer_prompt_template_oneliner
from db_handler import check_for_branch_entry, insert_chat, retrieve_messages, updata_chat, initiate_chat
from helpers import build_children_list
import uuid
import sys

try: 
  from dotenv import load_dotenv

  load_dotenv()

except ImportError:
  print("Could not load dotenv. The environment variables are not accessible.")
  sys.exit(1)

model = init_chat_model("gpt-4o-mini",temperature=0.7)
memory = MemorySaver()

trimmer = trim_messages(
    max_tokens=10000,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

def prepare_message(branch_id: uuid.UUID, new_message: BaseMessage, role: str = 'user') -> bool | None:
      
      if role in ["ai", "system", "human"]:
         try:
            template = {
                           "role" : role,
                           "content" : new_message.content,
                           "additional_kwargs" : new_message.additional_kwargs,
                           "response_metadata" : new_message.response_metadata,
                           "id" : datetime.now(timezone.utc).isoformat() + str(branch_id)
                        }
            return template   
         except Exception as e:
            print("The following exception occured with creating the database object of new message."
                  f"{e}")
            return None
      else:
         print("Role is not defined currectly")
         return None

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
    parent: uuid.UUID | None# Really comes into play when we have branches within branches. Along with the parent the current state messages length has to be mentioned. So we don't waste storage. Each child's state is saved as it goes, but as the child branch merges back, only the messages from the child branch (no history) are saved. The length has to be saved along with the parent beacuse that becomes the point of history we provide the child with.
    children: list[dict] #for retireval

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
      ai_msg = AIMessage(content=response)

      branch_id = state["current_config"]["configurable"]["thread_id"]

      entry_exists = check_for_branch_entry(branch_id=branch_id)

      if entry_exists is None:
         print('Database error.. exiting')
         sys.exit(1)

      if entry_exists:
         fetched_messages = retrieve_messages(branch_id=branch_id)

         summary = None

         if len(fetched_messages) == 10:
            onliner_chain = summarizer_prompt_template_oneliner | model | StrOutputParser()
            messages_to_summarize = state["messages"] + [ai_msg]
            summary = onliner_chain.invoke({"messages": messages_to_summarize})
         
         last_idx = list(fetched_messages.keys())[-1]
         new_idx = int(last_idx) + 1
         message = {
            new_idx: prepare_message(branch_id=branch_id, new_message=ai_msg, role="ai")
         }
         all_messages = {**fetched_messages, **message}

         if summary is not None:
            is_success = updata_chat(branch_id=branch_id, messages=all_messages, summary=summary)
         else:
            is_success = updata_chat(branch_id=branch_id, messages=all_messages)

         if not is_success:
            print("Update failed for AI message")
         return {"messages" : [ai_msg]}
      
      else:
         new_idx = 0
         message = {
            new_idx: prepare_message(branch_id=branch_id, new_message=ai_msg, role="ai")
         }
         is_success = updata_chat(branch_id=branch_id, messages=message)
         if not is_success:
            print("Update failed for AI message")
         return {"messages" : [ai_msg]}


   def branch_chat(self, state:State):

      length_of_current_context = len(state["messages"]) - 1 #for idx

      parent_id = state["current_config"]["configurable"]["thread_id"]
      branch_thread_id = uuid.uuid4()
      checkpoint_ns = str(branch_thread_id) + "_ns"
      config_new_branch = {"configurable": {"thread_id": branch_thread_id, "checkpoint_ns": checkpoint_ns}}
      is_success = initiate_chat(branch_id=branch_thread_id, parent_id=parent_id, parent_message_count_at_branch=length_of_current_context) # Remember this is idx
      if not is_success:
         print("Failed to add branch entry..exiting..")
         sys.exit(1)

      new_app = BranchGraph().buildGraph()

      branch_state = new_app.invoke({"messages": state["messages"], "current_config":config_new_branch, "parent": parent_id}, config=config_new_branch)
      
      putMemory(config=config_new_branch, channel_values=branch_state, memory=memory)

      summary_chain = summarizer_prompt_template | model | StrOutputParser()
      text_to_summarize = "\n".join(message.content for message in branch_state["messages"][length_of_current_context:])
      summary = summary_chain.invoke({"context": state["messages"], "messages_to_summarize" : text_to_summarize})
      summary = SystemMessage(content=summary)

      """
      1. Update with system message
      2. for child or branch add parent id and parent_message_count_at_branch
      """
      if state.get("children") is None:
         children = build_children_list(parent_id=parent_id, point_of_branching=length_of_current_context)
      else:
         children = build_children_list(parent_id=parent_id, point_of_branching=length_of_current_context, children=state["children"])

      prepare_message(branch_id=parent_id, new_message=summary, role='system') 
      

      return {"messages": [summary], "children": children}

   @staticmethod
   def query(state:State):
      user_input = HumanMessage(content=input("Ask away: "))
      index = len(state["messages"])
      query = [user_input]

      # Check if an entry for branch_id exists
      branch_id = state["current_config"]["configurable"]["thread_id"]
      entry_exists = check_for_branch_entry(branch_id=branch_id)


      if entry_exists is None:
         print('Database error.. exiting')
         sys.exit(1)

      if not entry_exists:
         parent_id = state["parent"]
         message = {
                     index : prepare_message(branch_id=branch_id, new_message=user_input, role="human")
                  }
         parent_count_at_branch = None

         # Creating summary
         onliner_chain = summarizer_prompt_template_oneliner | model | StrOutputParser()
         messages_to_summarize = state["messages"] + query
         oneliner = onliner_chain.invoke({"messages": messages_to_summarize})

         #timestamp is added by default

         insert_success = insert_chat(branch_id=branch_id, parent_id=parent_id, new_messages=message, parent_message_count_at_branch=parent_count_at_branch, summary=oneliner)
         if not insert_success:
            print("Some error occured during inserting")
      
      else:
         fetched_messages = retrieve_messages(branch_id=branch_id)
         if fetched_messages:

            summary = None

            if len(fetched_messages) == 10:
               onliner_chain = summarizer_prompt_template_oneliner | model | StrOutputParser()
               messages_to_summarize = state["messages"] + query
               summary = onliner_chain.invoke({"messages": messages_to_summarize})
            
            last_idx = list(fetched_messages.keys())[-1]
            new_idx = int(last_idx) + 1
            message = {
               new_idx: prepare_message(branch_id=branch_id, new_message=user_input, role="human")
            }
            all_messages = {**fetched_messages, **message}
            
            if summary is not None:
               is_success = updata_chat(branch_id=branch_id, messages=all_messages, summary=summary)   
            else:
               is_success = updata_chat(branch_id=branch_id, messages=all_messages)
               
            if not is_success:
               print("Update failed")
         else:
            new_idx = 0
            message = {
               new_idx : prepare_message(branch_id=branch_id, new_message=user_input, role="human")
            }

            # Creating summary
            onliner_chain = summarizer_prompt_template_oneliner | model | StrOutputParser()
            messages_to_summarize = state["messages"] + query
            oneliner = onliner_chain.invoke({"messages": messages_to_summarize})

            is_success = updata_chat(branch_id=branch_id, messages=message, summary=oneliner)
            if not is_success:
               print("Update failed")

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
   
if __name__ == "__main__":

   app = Graph().buildGraph()

   thread_id = uuid.uuid4()
   checkpoint_ns = str(thread_id) + "_ns"

   config = {"configurable" : {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns}}

   #initial branch has no parent and has not branched yet
   parent_id = None
   is_success = initiate_chat(branch_id=thread_id)

   app.invoke({"messages": [], "current_config": config, "parent": parent_id}, config=config)



"""
When you create a new thread:
1. Generate the thread_id: thread_id = str(uuid.uuid4())
2. Get other info: user_id = "user_12345" and created_at = datetime.utcnow()
3. Store it: Save all three pieces of info in your database table (e.g., a "Conversations" table).
4. Maybe store a one-liner as well for visualisations.
"""

#TODO: We'll set up a database to store all these conversations. That will be the next step. 