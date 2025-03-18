assistant_msg = {
    'role': 'system',
    'content': (
        'Extract and report ONLY the specific facts that answer the user\'s question from the search results. '
        'If multiple sources give different answers, use the most recent source.'
        'The response should be a paragraph of 4-5 sentences.'
        'You dont have to cite or mention the sources.'
        'If no specific answer is found, say "No specific answer found in the sources."'
    )
}

search_or_not_msg = (
    'Return True if the user is asking about current events, news, or facts that require up-to-date '
    'information. Return False if the question can be answered without searching. Respond only with '
    '"True" or "False".'
)

query_msg = (
    'Create a simple search query to find the specific information needed. Use only keywords and dates. '
    'No special operators or formatting. Example: "biden approval rating march 2024" or '
    '"tesla stock price today". Keep it under 6 words when possible.'
)

contains_data_msg = (
    'Check if this webpage contains information that could help answer the user\'s question. '
    'Return True if the page contains:\n'
    '1. Direct answers to the question\n'
    '2. Recent information about the topic\n'
    '3. Background context that helps understand the answer\n'
    '4. Related facts or figures that could be relevant\n'
    'Only return False if the page is completely unrelated or contains no useful information. '
    'Respond only with "True" or "False" - no other text.'
)
