from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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

summarizer_prompt_template_oneliner = ChatPromptTemplate.from_messages([
   (
      "system",
      """
         Persona:
         You are a summarizer. Your job is to summarize the messages given to you and produce a one-liner. A context will also be given so that you understand the whole picture. So summarize the text given under 'Messages to summarize' into a one-liner.

         Actual Workflow:
         I am building a project where people can branch from current chats to have different threads of conversations so that the main branch is not subjected to context decay. The branches thus formed need to accessed seperately and so these one-liners would act as the necessary UI element

         Output Format:
         The result should be just the summary one-liner as a string. If the conversation is not worth having a summary one-liner, just reply what you thought his/her intention was, that too as a one-liner.

         Final Instructions:
         1. Stick strictly to the output format.
         2. In the context provided, the AIMessage might have a persona. So it would be good if you could summarize based on that persona itself. I might have to deduct what the persona is yourself. If you are not able to, then it's fine just return a normal string.
         3. KEEP THE ONE-LINER SHORT.

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