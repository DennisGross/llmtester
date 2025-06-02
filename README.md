# LLMTESTER
LLMTESTER is a modular framework for generating, storing, and analyzing responses from Ollama-powered language models.

Use `generate_responses()` to produce and save model outputs.  
Then use `process_outputs()` to apply a custom `test_function` to each response and aggregate results using a `summary_function`.

This tool follows a **MapReduce-style pattern**:
- The `test_function` acts as the **map step**, processing each individual LLM response.
- The `summary_function` acts as the **reduce step**, combining those results into a final summary.

```
pip install git+https://github.com/DennisGross/llmtester.git
```

Run dummy example:
```
from llmtester.response_generator import *
from llmtester.process_data import *
stats = generate_responses(
        model_name="deepseek-r1:8b",
        prompt="Hello!",
        num_responses=3,
        output_dir="hello_folder",
        request_timeout=120,
        verbose=True,            
        delay_between_calls=0.2,
        temperature=0.8   # Set randomness level
    )
results = process_outputs(
        folder_path="hello_folder",
        test_function=analyze_output,
        summary_function=summarize_results
    )
```

Check out more examples in the `examples/` folder.  
First, run `python test_executions.py` to generate responses, then run `python test_analysis.py` to analyze them.
