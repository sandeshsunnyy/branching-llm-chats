import uuid 

def build_children_list(children: list[dict] | None, parent_id: uuid.UUID, point_of_branching: int) -> list[dict] | None:
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
        

