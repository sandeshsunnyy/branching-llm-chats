import uuid 

def build_children_list(children: list[dict] | None, parent_id: uuid.UUID, point_of_branching: int) -> list[dict] | None:
    if children is None:
        return None
    else:
        child = {"parent": parent_id, "parent_message_count_at_branch": point_of_branching}
        children.append(child)
        return children
        

