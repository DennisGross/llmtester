# LLMTESTER
LLMTESTER is a modular framework for generating, storing, and analyzing responses from Ollama-powered language models.

Use `generate_responses()` to produce and save model outputs.  
Then use `process_outputs()` to apply a custom `test_function` to each response and aggregate results using a `summary_function`.

`pip install git+https://github.com/DennisGross/llmtester.git`

Check out the example in the `examples/` folder.  
First, run `python test_executions.py` to generate responses, then run `python test_analysis.py` to analyze them.
