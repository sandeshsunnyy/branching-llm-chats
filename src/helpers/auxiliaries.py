import uuid 
from db_handler import retrieve_messages

def build_children_list(parent_id: uuid.UUID, point_of_branching: int, children: list[dict] | None = None) -> list[dict] | None:
    if children is None or not children:
        return [{"parent": parent_id, "parent_message_count_at_branch": point_of_branching}]
    else:
        child = {"parent": parent_id, "parent_message_count_at_branch": point_of_branching}
        children.append(child)
        return children
    
def print_conversations(convos: list[str]) -> None:

    print("-" * 107)
    middle_part = "|" + " idx " + "|" + " " * 45 + "conversations"
    remaining_part = 106 - len(middle_part)
    print(middle_part + " " * remaining_part + "|") 
    
    for item_id, item in enumerate(convos, 1):
    
        print("-" * 107)
        #number_part 
        number_part_center_point = int(len(str(item_id)) / 2)
        number_part_start_point = int(7/2) - number_part_center_point - 1
        number_part_remaining = 5 - number_part_start_point - len(str(item_id))

        #string part
        center_point = int(len(item) / 2)
        start_point = 49 - center_point

        middle_part_first_half = "|" + " " * number_part_start_point + str(item_id) + " " * number_part_remaining + "|" + " " * start_point + item
        remaining_part = 106 - len(middle_part_first_half)
        middle_part_second_half = " " * remaining_part + "|"
        full_block = middle_part_first_half + middle_part_second_half
        print(full_block)
    print("-" * 107 + "\n")
        

def display_last_two_threads():

    retrieved_msgs = [msg[0] for msg in retrieve_messages()][-2:]
    
    for convo_no, msg in enumerate(retrieved_msgs, 1):
        actual_msgs = list(msg.values())
        if convo_no == 1:
            print("BRANCH")
        else:
            print("MAIN THREAD")
        print("*" * 20 + "\n")
        for actual_msg in actual_msgs:
            print(f"{actual_msg['role'].upper()} : {actual_msg["content"]}\n")
    

if __name__ == "__main__":
    display_last_two_threads()