import json
# -----------------------------------------------
# Simple example: Using `generate_responses`
# (from otest.response_generator)
# -----------------------------------------------

# 1. Import the function that does text generation for you.
#    - `generate_responses` will handle calling Ollama, extracting "thinking", 
#      saving files, and returning some stats.
from llmtester.response_generator import generate_responses

# 2. Optionally import the type for readability (not strictly needed).
#    - This helps a “noob” understand what kind of data comes back.
from llmtester.response_generator import GenerationStats

# -----------------------------------------------
# 3. Define your main logic below
# -----------------------------------------------
if __name__ == "__main__":
    # 3.a. Choose which Ollama model to use.
    #      You can change this string to any model name that Ollama recognizes.
    model_name = "deepseek-r1:8b"
    
    # 3.b. Write your prompt. This is what the model will see as input.
    prompt = "Once upon a time in a magical forest,"
    
    # 3.c. Decide how many separate responses (completions) you want.
    #      Each response will be saved to its own set of files.
    num_responses = 3
    
    # 3.d. (Optional) If you want to specify a custom output folder, set it here.
    output_folder = "hello"
    
    # 3.e. (Optional) Lowering the timeout and adjusting temperature.
    #      - timeout: how long (in seconds) to wait for Ollama before giving up.
    #      - temperature: controls randomness (0.0 = deterministic, 1.0 = very random).
    timeout_seconds = 60.0
    temperature = 0.5

    # 3.f. Call the generation function.
    #      This will:
    #        1. Create (or reuse) an output directory
    #        2. Loop `num_responses` times and ask Ollama for text completions
    #        3. Extract any <think>...</think> sections and save them separately
    #        4. Save the cleaned response, raw response, thinking, and metadata JSON
    #        5. Return a stats dictionary about what happened
    stats: GenerationStats = generate_responses(
        model_name=model_name,
        prompt=prompt,
        num_responses=num_responses,
        output_dir=output_folder,
        request_timeout=timeout_seconds,
        verbose=True,            # Print progress messages
        delay_between_calls=0.2, # Small delay so each call has a different seed
        temperature=temperature   # Set randomness level
    )

    print("Generation complete.")

