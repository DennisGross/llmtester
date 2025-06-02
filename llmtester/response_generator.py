#!/usr/bin/env python3
import argparse
import os
import re
import time
import json
import glob
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple, TypedDict, cast

import ollama  # Direct Ollama package import

# Define custom types
class ResponseData(TypedDict):
    """Type definition for the response data dictionary."""
    raw_text: str            # Complete unmodified output
    text: str                # Processed response with thinking removed
    thinking: str            # Extracted thinking content
    has_thinking: bool
    generation_time: float
    length_chars: int
    word_count: int
    thinking_length_chars: int
    thinking_word_count: int
    raw_length: int          # Length of complete raw response
    raw_word_count: int      # Word count of complete raw response

class GenerationStats(TypedDict):
    """Type definition for generation statistics."""
    output_directory: str
    success_count: int
    thinking_count: int
    responses_requested: int
    time_taken_seconds: float
    start_response_num: int
    end_response_num: int
    temperature: float

def sanitize_filename(name: str) -> str:
    """Convert a string to a valid filename by removing invalid characters.
    
    Args:
        name: The input string to sanitize
        
    Returns:
        A sanitized string usable as a filename
    """
    if not name or name.strip() == "":
        return "empty_prompt"
    sanitized = re.sub(r'[^\w\-\s]', '_', name)
    sanitized = sanitized.replace(' ', '_')
    return sanitized[:30]  # Limit length

def ensure_directory_exists(directory: str) -> bool:
    """Create directory if it doesn't exist.
    
    Args:
        directory: The directory path to check/create
        
    Returns:
        True if directory already existed, False if it was created
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
        return False
    else:
        print(f"Using existing directory: {directory}")
        return True

def get_next_response_number(directory: str) -> int:
    """Find the highest response number in the directory and return the next one.
    
    Args:
        directory: Directory to search for existing response files
        
    Returns:
        The next available response number
    """
    # Use glob pattern matching for more efficient file searching
    response_files = glob.glob(os.path.join(directory, "response_*.txt"))
    
    highest = 0
    if response_files:
        for filepath in response_files:
            filename = os.path.basename(filepath)
            try:
                # Extract the number more efficiently with a regex pattern
                match = re.match(r'response_(\d+)\.txt', filename)
                if match:
                    num = int(match.group(1))
                    highest = max(highest, num)
            except (ValueError, IndexError, AttributeError) as e:
                print(f"Warning: Could not parse number from filename {filename}: {e}")
    
    next_num = highest + 1
    print(f"Found highest existing response number: {highest}, next number will be: {next_num}")
    return next_num

def generate_ollama_response(
    model_name: str, 
    prompt: str, 
    request_timeout: float = 1000.0, 
    temperature: float = 0.7
) -> Optional[ResponseData]:
    """Generate a response using the Ollama package directly.
    
    Args:
        model_name: Name of the Ollama model to use
        prompt: Prompt to send to the model
        request_timeout: Request timeout in seconds
        temperature: Sampling temperature, higher values make output more random
        
    Returns:
        Response data including text, thinking text, generation time, and length metrics
        or None if generation failed
    """
    try:
        # Configure the client options
        client = ollama.Client(timeout=request_timeout)
        
        # Track generation start time
        start_time: float = time.time()
        
        # Generate the response with temperature parameter
        response: Dict[str, Any] = client.generate(
            model=model_name,
            prompt=prompt,
            options={"temperature": temperature}  # Add temperature parameter
        )
        
        # Calculate generation time
        generation_time: float = time.time() - start_time
        
        # Save the raw, unprocessed response text
        raw_response_text: str = response.get('response', '')
        
        # Make a copy of the raw response for processing
        response_text: str = raw_response_text
        
        # Extract thinking content if present (content between <think> and </think> tags)
        thinking_content: str = ""
        has_thinking: bool = False

        print(raw_response_text)
        
        # Find all thinking content
        thinking_matches: List[str] = re.findall(r'<think>(.*?)</think>', response_text, re.DOTALL)
        if thinking_matches:
            has_thinking = True
            thinking_content = "\n\n".join(thinking_matches)
        
        # Remove thinking tags and content from the main response
        clean_response_text: str = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
        
        # Remove any leading/trailing whitespace
        clean_response_text = clean_response_text.strip()
        thinking_content = thinking_content.strip()
        
        # Calculate response length metrics
        response_length: int = len(clean_response_text)
        response_word_count: int = len(clean_response_text.split())
        thinking_length: int = len(thinking_content)
        thinking_word_count: int = len(thinking_content.split()) if thinking_content else 0
        
        # Calculate raw text metrics
        raw_length: int = len(raw_response_text)
        raw_word_count: int = len(raw_response_text.split())
        
        return {
            'raw_text': raw_response_text,            # Complete unmodified output
            'text': clean_response_text,              # Processed response with thinking removed
            'thinking': thinking_content,             # Extracted thinking content
            'has_thinking': has_thinking,
            'generation_time': generation_time,
            'length_chars': response_length,
            'word_count': response_word_count,
            'thinking_length_chars': thinking_length,
            'thinking_word_count': thinking_word_count,
            'raw_length': raw_length,                 # Length of complete raw response
            'raw_word_count': raw_word_count          # Word count of complete raw response
        }
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

def save_response(
    response_data: ResponseData, 
    directory: str, 
    response_num: int, 
    model_name: str, 
    temperature: float,
    prompt: str  # Added prompt parameter
) -> bool:
    """Save a response, its thinking content, metadata, and full output to disk.
    
    Args:
        response_data: Response data from generate_ollama_response
        directory: Directory to save the response
        response_num: Response number for file naming
        model_name: Name of the model used
        temperature: Temperature value used for generation
        prompt: Original prompt used for generation
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Save response text to file
        filename: str = os.path.join(directory, f"response_{response_num}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response_data['text'])
        
        # Save thinking content if it exists (in the same folder)
        thinking_filename: str = os.path.join(directory, f"thinking_{response_num}.txt")
        with open(thinking_filename, "w", encoding="utf-8") as f:
            f.write(response_data['thinking'])
        
        # Save the completely raw, unprocessed LLM output
        raw_output_filename: str = os.path.join(directory, f"raw_output_{response_num}.txt")
        with open(raw_output_filename, "w", encoding="utf-8") as f:
            f.write(response_data['raw_text'])
        
        # Save enhanced metadata about this generation
        meta_filename: str = os.path.join(directory, f"meta_{response_num}.json")
        with open(meta_filename, "w", encoding="utf-8") as f:
            json.dump({
                "model": model_name,
                "temperature": temperature,  # Add temperature to metadata
                "prompt": prompt,  # Include the original prompt in metadata
                "timestamp": datetime.now().isoformat(),
                "generation_time_seconds": round(response_data['generation_time'], 3),
                "response": {
                    "length_characters": response_data['length_chars'],
                    "word_count": response_data['word_count'],
                },
                "thinking": {
                    "present": response_data['has_thinking'],
                    "length_characters": response_data['thinking_length_chars'],
                    "word_count": response_data['thinking_word_count']
                },
                "total": {
                    "length_characters": response_data['raw_length'],
                    "word_count": response_data['raw_word_count'],
                    "characters_per_second": round(response_data['raw_length'] / response_data['generation_time'], 2) if response_data['generation_time'] > 0 else 0,
                    "tokens_per_second_estimate": round(response_data['raw_word_count'] * 1.3 / response_data['generation_time'], 2) if response_data['generation_time'] > 0 else 0
                }
            }, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving response: {e}")
        return False

def save_prompt(directory: str, prompt: str) -> None:
    """Save the original prompt to a file if it doesn't exist.
    
    Args:
        directory: Directory to save the prompt file
        prompt: Content of the prompt to save
    """
    # This function is kept for backward compatibility
    # but we no longer need to call it since the prompt
    # is now saved in each meta file.
    pass

def generate_responses(
    model_name: str, 
    prompt: str, 
    num_responses: int = 1, 
    output_dir: Optional[str] = None, 
    request_timeout: float = 1000.0, 
    verbose: bool = True, 
    delay_between_calls: float = 0.1, 
    temperature: float = 0.7
) -> GenerationStats:
    """Generate multiple responses using Ollama and save them to disk.
    
    Args:
        model_name: Name of the Ollama model to use
        prompt: Prompt to send to the model
        num_responses: Number of responses to generate
        output_dir: Directory to save responses (auto-generated if None)
        request_timeout: Request timeout in seconds
        verbose: Whether to print progress messages
        delay_between_calls: Delay between API calls in seconds
        temperature: Sampling temperature, higher values make output more random
        
    Returns:
        Generation stats including directory, success count, time taken, and response range
    """
    start_time: float = time.time()
    
    # Setup output directory
    if output_dir:
        dir_name: str = output_dir
        ensure_directory_exists(dir_name)
    else:
        # Create data directory if it doesn't exist
        ensure_directory_exists("data")
        
        # Create a directory name from the model, prompt, and temperature
        model_part: str = sanitize_filename(model_name)
        prompt_part: str = sanitize_filename(prompt) if prompt.strip() else "empty_prompt"
        temp_part: str = f"temp{temperature:.1f}".replace('.', '_')  # Format temperature for filename
        
        # Add timestamp to directory name to avoid overwriting
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Store output in a subfolder of "data" directory including temperature info
        dir_name: str = os.path.join("data", f"output_{model_part}_{prompt_part}_{temp_part}_{timestamp}")
        
        # Create the output directory
        ensure_directory_exists(dir_name)
    
    # We no longer need to call save_prompt() since we'll save the prompt in each meta file
    # save_prompt(dir_name, prompt)
    
    # Find the next response number if the directory already has responses
    start_response_num: int = get_next_response_number(dir_name)
    
    if verbose:
        print(f"Generating {num_responses} responses using model '{model_name}' with temperature {temperature}")
        print(f"Output will be saved to: {dir_name}")
        print(f"Starting with response number {start_response_num}")
    
    # Generate n responses
    success_count: int = 0
    thinking_count: int = 0
    
    for i in range(num_responses):
        response_num: int = start_response_num + i
        
        if verbose:
            print(f"Generating response {i+1}/{num_responses} (file #{response_num})...")
        
        # Generate response using direct Ollama package with temperature
        response_data: Optional[ResponseData] = generate_ollama_response(
            model_name=model_name,
            prompt=prompt,
            request_timeout=request_timeout,
            temperature=temperature
        )
        
        if response_data:
            # Save the response with temperature metadata and original prompt
            save_success: bool = save_response(
                response_data=response_data,
                directory=dir_name,
                response_num=response_num,
                model_name=model_name,
                temperature=temperature,
                prompt=prompt  # Pass the prompt to save in metadata
            )
            
            if save_success:
                if verbose:
                    thinking_info: str = ""
                    if response_data['has_thinking']:
                        thinking_count += 1
                        thinking_info = f", thinking: {response_data['thinking_word_count']} words"
                    
                    print(f"Saved response {i+1}/{num_responses} (#{response_num}: {response_data['word_count']} words{thinking_info}, {response_data['generation_time']:.2f}s)")
                success_count += 1
            
            # Add a small delay to ensure different random seeds
            if delay_between_calls > 0 and i < num_responses - 1:
                time.sleep(delay_between_calls)
        else:
            if verbose:
                print(f"Failed to generate response {i+1}/{num_responses} (#{response_num})")
    
    elapsed_time: float = time.time() - start_time
    
    if verbose:
        print(f"\nGeneration complete: {success_count}/{num_responses} responses")
        print(f"Responses with thinking content: {thinking_count}/{success_count}")
        print(f"Time taken: {elapsed_time:.2f} seconds")
        print(f"All responses saved to directory: {dir_name}")
        print(f"Response numbers: {start_response_num} to {start_response_num + success_count - 1}")
    
    # Return stats about the generation
    return {
        "output_directory": dir_name,
        "success_count": success_count,
        "thinking_count": thinking_count,
        "responses_requested": num_responses,
        "time_taken_seconds": round(elapsed_time, 3),
        "start_response_num": start_response_num,
        "end_response_num": start_response_num + success_count - 1,
        "temperature": temperature
    }

def main() -> GenerationStats:
    """Main function for command-line usage.
    
    Returns:
        Statistics about the generation run
    """
    parser = argparse.ArgumentParser(description="Generate responses using Ollama with thinking content preserved.")
    parser.add_argument("--model", default="deepseek-r1:8b", help="Name of the Ollama model to use (default: deepseek-r1:8b)")
    parser.add_argument("--prompt", default="Hello, my name is", help="Initial prompt to send to the model (default: 'Hello, my name is')")
    parser.add_argument("--n", type=int, default=25, help="Number of responses to generate (default: 25)")
    parser.add_argument("--timeout", type=float, default=1000.0, help="Request timeout in seconds (default: 1000.0)")
    parser.add_argument("--output", help="Target folder path for saving outputs (default: auto-generated in 'data' directory)")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between API calls in seconds (default: 0.1)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature, higher values make output more random (default: 0.7)")
    parser.add_argument("--continue-from", action="store_true", help="Continue numbering from last response in output directory")
    args = parser.parse_args()
    
    # Call the main function with temperature parameter
    result: GenerationStats = generate_responses(
        model_name=args.model,
        prompt=args.prompt,
        num_responses=args.n,
        output_dir=args.output,
        request_timeout=args.timeout,
        verbose=not args.quiet,
        delay_between_calls=args.delay,
        temperature=args.temperature
    )
    
    return result

if __name__ == "__main__":
    main()