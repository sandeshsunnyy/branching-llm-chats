try: 
  from dotenv import load_dotenv

  load_dotenv()

except ImportError:
  pass


from langchain.chat_models import init_chat_model

model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You talk like a 15th century man. Answer questions accordingly in {language}"
    ),
    MessagesPlaceholder(variable_name="messages"),
])

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph

from typing import Sequence

from langchain_core.messages import BaseMessage, SystemMessage, trim_messages
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

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

workflow = StateGraph(state_schema=State)

def ask_user_to_branch(state: State):
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
       result = ask_user_to_branch(state=state)
       return result
    
def brancher(state: State):
   if state["branch"] == True:
      return "branch"
   else:
      return "no branch"
   
def call_model(state: State):
    trimmed_messages = trimmer.invoke(state["messages"])
    chain = prompt_template | model | StrOutputParser()
    chunks = []
    for chunk in chain.stream({"messages": trimmed_messages, "language": "English"}):
       chunks.append(chunk)
       print(chunk, end="", flush=True)
    print("\n\n")
    response = ''.join(chunks)
    return {"messages" : [AIMessage(content=response)]}

def branch_chat(state: State):
   print("In branch chat.")

def query(state: State):
   user_input = input("Ask away: ")
   query = [HumanMessage(content=user_input)]
   return {"messages" : query}


workflow.add_node("ask_to_branch", ask_user_to_branch)
workflow.add_edge(START, "ask_to_branch")
workflow.add_node("model", call_model)
workflow.add_node("branch_chat", branch_chat)
workflow.add_node("query", query)
workflow.add_edge("query", "model")
workflow.add_edge("model", "ask_to_branch")
workflow.add_edge("branch_chat", END)
workflow.add_conditional_edges(
   source="ask_to_branch",
   path=brancher,
   path_map={
      "branch": "branch_chat",
      "no branch": "query"
   }
)


memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

config = {"configurable" : {"thread_id": "abc124"}}

from langchain_core.messages import HumanMessage, AIMessage

app.invoke({"messages": []}, config)
'''
from datetime import datetime, timezone
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata


memory_state = memory.get(config=config)

channel_value = memory_state["channel_values"] # This contains the list of messages in dict format
current_ts = datetime.now(timezone.utc).isoformat()

config_new_branch = {"configurable": {"thread_id": "abc124", "checkpoint_ns": "branch1"}}

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


memory_state = memory.get(config=config)'''