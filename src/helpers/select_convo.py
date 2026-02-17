#TODO: We have to work on updating the one-liner
from src.helpers.db_handler import retrieve_data_for_resuming_chat
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from src.main import Graph
from src.helpers.auxiliaries import print_conversations

def continue_chat(chat_data : tuple):
   
    messages = list(chat_data[1].values())
    thread_id, checkpoint_ns = chat_data[0], str(chat_data[0]) + '_ns'
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
        elif message['role'] == 'system':
            msg = SystemMessage(content=content, id=msg_id, additional_kwargs=additional_kwargs, response_metadata=response_metadata)
            langchain_msgs.append(msg)
    
    
    app = Graph().buildGraph()

    print("\n")
    for msg in langchain_msgs:
        if isinstance(msg, AIMessage):
            print(f"Sir. llm : {msg.content}\n")
        elif isinstance(msg, HumanMessage):
            print(f"human : {msg.content}\n")

    app.invoke({"messages": langchain_msgs, "current_config": config, "parent": None}, config=config)

if __name__ == "__main__":

    all_chats = retrieve_data_for_resuming_chat()
    viable_chats = [chat for chat in all_chats if chat[2] is not None]
    summaries = [chat[2] for chat in all_chats if chat[2] is not None]

    print_conversations(summaries)

    choice = int(input("\nWhich conversation do you wish to continue? Enter the idx: ")) - 1

    continue_chat(chat_data = viable_chats[choice])
    

