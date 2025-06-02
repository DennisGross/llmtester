# Import everything from your module that contains `process_outputs`.
# This assumes you have a file structure like:
#    otest/
#      process_data.py  (which defines process_outputs, etc.)
from llmtester.process_data import *

# ------------------------------
# 1. Define the test_function
# ------------------------------
# This function will be called once per "response" file set.
# It receives:
#   - metadata: a dictionary loaded from meta_<n>.json
#   - raw_output: the contents of raw_output_<n>.txt as a string
#   - thinking: the contents of thinking_<n>.txt as a string
#   - response: the contents of response_<n>.txt as a string
#
# It must return a dictionary with whatever values you want to collect
# from each response. Here, we just pick:
#   - "response_num" from the metadata (so we know which response it is)
#   - "response_length" = the number of characters in the `response` text
def test_function(
    metadata: Dict[str, Any],
    raw_output: str,
    thinking: str,
    response: str
) -> Dict[str, Any]:
    # metadata["response_num"] is expected to be set by process_outputs if not already present
    return {
        "response_num": metadata["response_num"],
        "response_length": len(response)  # count how many characters in the response text
    }

# ------------------------------
# 2. Define the summary_function
# ------------------------------
# After processing all responses, process_outputs collects a list of the
# dictionaries returned by test_function. That list is passed to this function
# as `results`.
#
# Here, we compute:
#   - total = sum of all response lengths
#   - count = how many results we saw
#   - average response length = total / count   (or 0 if there were no results)
def summary_function(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(r["response_length"] for r in results)  # sum up response_length for each result
    count = len(results)                                 # how many responses were processed
    return {
        "avg_response_length": total / count if count else 0
    }

# ------------------------------
# 3. Main script execution
# ------------------------------
# This `if` block ensures that the code inside only runs when you execute
# this file directly (e.g. `python example.py`). It won’t run if you import
# this file from somewhere else.
if __name__ == "__main__":
    # Call process_outputs with:
    #   1) The path to your folder containing files like response_1.txt, raw_output_1.txt, etc.
    #      In this example, we assume there's a folder named "hello" in the current directory.
    #   2) test_function: our function that inspects each individual response
    #   3) summary_function: our function that summarizes all results
    summary = process_outputs("hello", test_function, summary_function)

    # Print out the summary dictionary to the console.
    # For instance, you might see something like: {"avg_response_length": 123.45}
    print(summary)
