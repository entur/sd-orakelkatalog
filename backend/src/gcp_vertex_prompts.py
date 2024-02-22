combine_prompt_template_v2 = """
    You will be given a detailed description of different datasets in norwegian
    enclosed in triple backticks (```) and a question enclosed in
    double backticks(``).
    Select the datasets that are most relevant to answer the question, with a maximum of 5 datasets.
    If there are more more than 5 relevant datasets, try to vary them in your answer.
    Create a markdown link on the format [DATASET_TITLE](DATA_NORGE_LINK) for each relevant dataset.
    Using those dataset descriptions, answer the following
    question in as much detail as possible.
    You should only use the information in the descriptions.
    Your answer should include the title links and why each dataset match the question posed by the user.
    If no datasets are given, explain that the data may not exist.
    Double check to make sure the markdown link format is correct and that the dataset title is the link text.
    Give the answer in Norwegian.

    Description:
    ```{text}```


    Question:
    ``{user_query}``


    Answer:
"""

combine_prompt_template_v1 = """
    You will be given a detailed description of different datasets in norwegian
    enclosed in triple backticks (```) and a question enclosed in
    double backticks(``).
    Select the datasets that is most relevant to answer the question.
    Using those dataset descriptions, answer the following
    question in as much detail as possible.
    You should only use the information in the descriptions.
    Your answer should include the title of each relevant dataset, and why they match the question posed by the user.
    Structure your answer to be easily readable by a human person.
    If no datasets are given, assume there are no datasets matching the
    question, and explain that the data might not exist.
    Refer to the user directly, but never sign off your answer.
    Give the answer in Markdown and mark the dataset title as bold text.
    Give the answer in Norwegian.

    Description:
    ```{text}```


    Question:
    ``{user_query}``


    Answer:
"""

keyword_generation_prompt = """
    For the following query in Norwegian, generate 3 related keywords that might give better results in a keyword search.
    The keywords should also be given in Norwegian.
    Your answer should only include the keywords in plaintext.

    Query:
    {query}
"""
