#TODO: We have to work on updating the one-liner
from db_handler import retrieve_data_for_resuming_chat
from langchain.messages import HumanMessage, AIMessage
from branching_llm import Graph
import uuid

if __name__ == "__main__":
    all_chats = retrieve_data_for_resuming_chat()
    viable_chats = [chat for chat in all_chats if chat[2] is not None][0]
    messages = list(viable_chats[1].values())
    thread_id, checkpoint_ns = viable_chats[0], str(viable_chats[0]) + '_ns'
    config = {"configurable" : {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns}}

    langchain_msgs = []
    for message in messages:
        content = message["content"]
        msg_id = message["id"]
        additional_kwargs = message["additional_kwargs"]
        response_metadata = message["response_metadata"]
        if message['role'] == 'ai':
            msg = AIMessage(content=content, id=msg_id, additional_kwargs=additional_kwargs, response_metadata=response_metadata)
            langchain_msgs.append(msg)
        elif message['role'] == 'human':
            msg = HumanMessage(content=content, id=msg_id, additional_kwargs=additional_kwargs, response_metadata=response_metadata)
            langchain_msgs.append(msg)
    
    
    app = Graph().buildGraph()

    print(f"{langchain_msgs[-1].content}")

    app.invoke({"messages": langchain_msgs, "current_config": config, "parent": None}, config=config)

