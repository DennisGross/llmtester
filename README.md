# LLMTESTER
LLMTESTER is a modular framework for generating, storing, and analyzing responses from Ollama-powered language models.

Use `generate_responses()` to produce and save model outputs.  
Then use `process_outputs()` to apply a custom `test_function` to each response and aggregate results using a `summary_function`.

This tool follows a **MapReduce-style pattern**:
- The `test_function` acts as the **map step**, processing each individual LLM response.
- The `summary_function` acts as the **reduce step**, combining those results into a final summary.


## Install
```
pip install git+https://github.com/DennisGross/llmtester.git
```

## Example
Copy, paste and run the following dummy example:
```
from llmtester.response_generator import *
from llmtester.process_data import *
stats = generate_responses(
        model_name="gemma3:1b",
        prompt="Hello!",
        num_responses=3,
        output_dir="hello_folder",
        request_timeout=120,
        verbose=True,            
        delay_between_calls=0.2,
        temperature=0.8
    )
results = process_outputs(
        folder_path="hello_folder",
        test_function=analyze_output, # custom function to analyze each response
        summary_function=summarize_results # custom function to summarize results
    )
```
Browse available Ollama models at: [https://ollama.com/library](https://ollama.com/library).

When using custom functions (test_function and summary_function), ensure to have the same function signatures:

```
def analyze_output(metadata: Dict[str, Any], raw_output: str, thinking: str, response: str) -> Dict[str, Any]
def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]
```
