map_prompt_template = """
    You will be given a detailed description of a published dataset in norwegian.
    This description is enclosed in triple backticks (```).
    Using this description only, extract the title of the dataset,
    the category and its most useful features.
    
    ```{text}```
    SUMMARY:
    """

combine_prompt_template = """
    You will be given a detailed description of different datasets in norwegian
    enclosed in triple backticks (```) and a question enclosed in
    double backticks(``).
    Select the datasets that is most relevant to answer the question.
    Using those dataset descriptions, answer the following
    question in as much detail as possible.
    You should only use the information in the descriptions.
    Your answer should include the title of the dataset, and why it matches the question posed by the user.
    Structure your answer to be easily readable by a human person.
    If no datasets are given, assume there are no datasets matching the
    question, and explain that the data might not exist.
    Try to refer to the user directly, but never sign off your answer.
    Give the answer in Markdown and mark the dataset title as bold text.
    Give the answer in Norwegian.

    Description:
    ```{text}```


    Question:
    ``{user_query}``


    Answer:
    """
