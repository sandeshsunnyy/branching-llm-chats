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
from langgraph.graph import START, MessagesState, StateGraph

from typing import Sequence

from langchain_core.messages import BaseMessage, SystemMessage, trim_messages
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
    language : str    

workflow = StateGraph(state_schema=State)

def call_model(state: State):
    trimmed_messages = trimmer.invoke(state["messages"])
    prompt = prompt_template.invoke({"messages": trimmed_messages, "language": state["language"]})
    response = model.invoke(prompt)
    print(type(response))
    return {"messages" : response}

workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

config = {"configurable" : {"thread_id": "abc124"}}
query = input("What's your query?")
language = "English"

from langchain_core.messages import HumanMessage, AIMessage

input_messages = [HumanMessage(content=query)]

#streaming responses

for chunk, metadata in app.stream(
    {"messages": input_messages, "language": language},
    config,
    stream_mode="messages",
):
    if isinstance(chunk, AIMessage):
        print(chunk.content)

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


memory_state = memory.get(config=config)