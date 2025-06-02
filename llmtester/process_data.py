#!/usr/bin/env python3
import os
import json
import glob
import re
from typing import Dict, List, Callable, Any

# Type definitions for the function signatures
TestFunction = Callable[[Dict[str, Any], str, str, str], Dict[str, Any]]
SummaryFunction = Callable[[List[Dict[str, Any]]], Dict[str, Any]]

import os
import json
import glob
import re
import inspect
from typing import Dict, List, Callable, Any, get_origin, get_args

# Type definitions for the function signatures (for annotation checks)
TestFunction = Callable[[Dict[str, Any], str, str, str], Dict[str, Any]]
SummaryFunction = Callable[[List[Dict[str, Any]]], Dict[str, Any]]

def process_outputs(
    folder_path: str, 
    test_function: TestFunction,
    summary_function: SummaryFunction
) -> Dict[str, Any]:
    """
    Process all outputs in a folder using user-defined test and summary functions,
    with very strict signature and return-type checks.
    
    Args:
        folder_path: Path to the folder containing the outputs
        test_function: Function annotated as (metadata: Dict[str, Any], raw_output: str, thinking: str, response: str) -> Dict[str, Any]
        summary_function: Function annotated as (results: List[Dict[str, Any]]) -> Dict[str, Any>
        
    Returns:
        A dictionary with the summarized results
    """
    # -----------------------------
    # 1. Strict validation of test_function signature & annotations
    # -----------------------------
    if not callable(test_function):
        raise TypeError("test_function must be a callable")

    sig_test = inspect.signature(test_function)
    params_test = sig_test.parameters

    # 1.a. Must have exactly four parameters
    if len(params_test) != 4:
        raise TypeError(
            "test_function must accept exactly four parameters: "
            "(metadata: Dict[str, Any], raw_output: str, thinking: str, response: str)"
        )

    # 1.b. Verify parameter names, order, and annotations
    expected_test_params = [
        ("metadata", Dict[str, Any]),
        ("raw_output", str),
        ("thinking", str),
        ("response", str),
    ]
    for idx, ((param_name, param_obj), (exp_name, exp_type)) in enumerate(zip(params_test.items(), expected_test_params)):
        if param_name != exp_name:
            raise TypeError(
                f"test_function parameter #{idx + 1} should be named '{exp_name}', but got '{param_name}'"
            )
        ann = param_obj.annotation
        if ann is inspect._empty:
            raise TypeError(
                f"test_function parameter '{param_name}' must be annotated as '{exp_type}', but no annotation was found"
            )
        # Check that the annotation matches exactly
        if get_origin(ann) is dict or ann is dict:
            # normalize annotation
            origin = get_origin(ann) or ann
            args = get_args(ann) or ()
            if origin is not dict or args != (str, Any):
                raise TypeError(
                    f"test_function parameter '{param_name}' annotation must be 'Dict[str, Any]', but got '{ann}'"
                )
        else:
            if ann is not exp_type:
                raise TypeError(
                    f"test_function parameter '{param_name}' annotation must be '{exp_type.__name__}', but got '{ann}'"
                )

    # 1.c. Verify return annotation exactly Dict[str, Any]
    ret_ann_test = sig_test.return_annotation
    if ret_ann_test is inspect._empty:
        raise TypeError(
            "test_function must have a return annotation 'Dict[str, Any]', but none was found"
        )
    if get_origin(ret_ann_test) is dict or ret_ann_test is dict:
        origin = get_origin(ret_ann_test) or ret_ann_test
        args = get_args(ret_ann_test) or ()
        if origin is not dict or args != (str, Any):
            raise TypeError(
                f"test_function return annotation must be 'Dict[str, Any]', but got '{ret_ann_test}'"
            )
    else:
        raise TypeError(
            f"test_function return annotation must be 'Dict[str, Any]', but got '{ret_ann_test}'"
        )

    # -----------------------------
    # 2. Strict validation of summary_function signature & annotations
    # -----------------------------
    if not callable(summary_function):
        raise TypeError("summary_function must be a callable")

    sig_summary = inspect.signature(summary_function)
    params_summary = sig_summary.parameters

    # 2.a. Must have exactly one parameter
    if len(params_summary) != 1:
        raise TypeError(
            "summary_function must accept exactly one parameter: "
            "(results: List[Dict[str, Any]])"
        )

    # 2.b. Verify parameter name and annotation
    pname, pobj = next(iter(params_summary.items()))
    if pname != "results":
        raise TypeError(
            f"summary_function parameter should be named 'results', but got '{pname}'"
        )
    ann_summary_param = pobj.annotation
    if ann_summary_param is inspect._empty:
        raise TypeError(
            "summary_function parameter 'results' must be annotated as 'List[Dict[str, Any]]', but no annotation was found"
        )
    # Check annotation is exactly List[Dict[str, Any]]
    if get_origin(ann_summary_param) is list or get_origin(ann_summary_param) is list:
        origin = get_origin(ann_summary_param)
        args = get_args(ann_summary_param)
        if origin is not list or len(args) != 1:
            raise TypeError(
                f"summary_function parameter 'results' annotation must be 'List[Dict[str, Any]]', but got '{ann_summary_param}'"
            )
        inner = args[0]
        if get_origin(inner) is dict:
            inner_origin = get_origin(inner)
            inner_args = get_args(inner)
            if inner_origin is not dict or inner_args != (str, Any):
                raise TypeError(
                    f"summary_function parameter 'results' annotation must be 'List[Dict[str, Any]]', but got '{ann_summary_param}'"
                )
        else:
            raise TypeError(
                f"summary_function parameter 'results' annotation must be 'List[Dict[str, Any]]', but got '{ann_summary_param}'"
            )
    else:
        raise TypeError(
            f"summary_function parameter 'results' annotation must be 'List[Dict[str, Any]]', but got '{ann_summary_param}'"
        )

    # 2.c. Verify return annotation exactly Dict[str, Any]
    ret_ann_summary = sig_summary.return_annotation
    if ret_ann_summary is inspect._empty:
        raise TypeError(
            "summary_function must have a return annotation 'Dict[str, Any]', but none was found"
        )
    if get_origin(ret_ann_summary) is dict or ret_ann_summary is dict:
        origin = get_origin(ret_ann_summary) or ret_ann_summary
        args = get_args(ret_ann_summary) or ()
        if origin is not dict or args != (str, Any):
            raise TypeError(
                f"summary_function return annotation must be 'Dict[str, Any]', but got '{ret_ann_summary}'"
            )
    else:
        raise TypeError(
            f"summary_function return annotation must be 'Dict[str, Any]', but got '{ret_ann_summary}'"
        )

    # -----------------------------
    # 3. Ensure the folder path exists
    # -----------------------------
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder path does not exist: {folder_path}")
    
    # -----------------------------
    # 4. Find all the response files
    # -----------------------------
    response_files = sorted(glob.glob(os.path.join(folder_path, "response_*.txt")))
    if not response_files:
        raise ValueError(f"No response files found in: {folder_path}")
    
    # -----------------------------
    # 5. Process each output
    # -----------------------------
    results: List[Dict[str, Any]] = []
    
    for response_file in response_files:
        # Extract the response number from the filename
        base_name = os.path.basename(response_file)
        try:
            response_num = int(re.search(r'response_(\d+)\.txt', base_name).group(1))
        except (IndexError, ValueError, AttributeError) as e:
            print(f"Warning: Could not extract response number from {base_name}: {e}")
            continue
        
        # Construct paths for related files
        thinking_file = os.path.join(folder_path, f"thinking_{response_num}.txt")
        raw_file = os.path.join(folder_path, f"raw_output_{response_num}.txt")
        meta_file = os.path.join(folder_path, f"meta_{response_num}.json")
        
        # Check if all required files exist
        if not all(os.path.exists(f) for f in [response_file, thinking_file, raw_file, meta_file]):
            missing = []
            if not os.path.exists(response_file): missing.append(f"response_{response_num}.txt")
            if not os.path.exists(thinking_file): missing.append(f"thinking_{response_num}.txt")
            if not os.path.exists(raw_file): missing.append(f"raw_output_{response_num}.txt")
            if not os.path.exists(meta_file): missing.append(f"meta_{response_num}.json")
            print(f"Warning: Missing files for response #{response_num}: {', '.join(missing)}")
            continue
        
        try:
            # Read all the files
            with open(response_file, 'r', encoding='utf-8') as f:
                response_text = f.read()
            if not isinstance(response_text, str):
                raise TypeError(f"Content of {response_file} is not a string")

            with open(thinking_file, 'r', encoding='utf-8') as f:
                thinking_text = f.read()
            if not isinstance(thinking_text, str):
                raise TypeError(f"Content of {thinking_file} is not a string")

            with open(raw_file, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            if not isinstance(raw_text, str):
                raise TypeError(f"Content of {raw_file} is not a string")

            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            if not isinstance(metadata, dict):
                raise TypeError(f"Content of {meta_file} did not parse into a dict")

            # Add response number to metadata if not already there
            if 'response_num' not in metadata:
                metadata['response_num'] = response_num
            
            # -----------------------------
            # 5.a. Call test_function and strictly validate its return
            # -----------------------------
            test_result = test_function(metadata, raw_text, thinking_text, response_text)

            # Check that test_result is exactly a dict
            if not isinstance(test_result, dict):
                raise TypeError(
                    f"test_function returned {type(test_result).__name__}; expected Dict[str, Any]"
                )
            # Further: ensure all keys are strings
            for key in test_result.keys():
                if not isinstance(key, str):
                    raise TypeError(
                        f"test_function returned a dict with a non-string key: {repr(key)}"
                    )
            # (We do not enforce anything about values inside the dict beyond being Any)

            results.append(test_result)
            
        except Exception as e:
            print(f"Error processing response #{response_num}: {e}")
    
    # -----------------------------
    # 6. Apply summary_function and strictly validate its return
    # -----------------------------
    if not results:
        return {"error": "No results were generated"}
    
    summary = summary_function(results)
    if not isinstance(summary, dict):
        raise TypeError(
            f"summary_function returned {type(summary).__name__}; expected Dict[str, Any]"
        )
    for key in summary.keys():
        if not isinstance(key, str):
            raise TypeError(
                f"summary_function returned a dict with a non-string key: {repr(key)}"
            )
    
    return summary


# Example test function
def analyze_output(
    metadata: Dict[str, Any], 
    raw_output: str, 
    thinking: str, 
    response: str
) -> Dict[str, Any]:
    """
    Example test function that analyzes an LLM output.
    
    Args:
        metadata: Dictionary containing metadata about the generation
        raw_output: Raw output from the LLM
        thinking: Extracted thinking content
        response: Processed response with thinking removed
        
    Returns:
        Dictionary with analysis results
    """
    # Extract basic metadata
    prompt = metadata.get("prompt", "")
    result = {
        "response_num": metadata.get("response_num", 0),
        "model": metadata.get("model", "unknown"),
        "temperature": metadata.get("temperature", 0.0),
        "generation_time": metadata.get("generation_time_seconds", 0.0),
    }
    
    # Basic metrics
    result.update({
        "has_thinking": len(thinking) > 0,
        "thinking_length": len(thinking),
        "thinking_word_count": len(thinking.split()) if thinking else 0,
        "response_length": len(response),
        "response_word_count": len(response.split()),
    })
    
    # Calculate ratios
    if result["response_length"] > 0:
        result["thinking_response_ratio"] = result["thinking_length"] / result["response_length"]
    else:
        result["thinking_response_ratio"] = 0
        
    # Count question marks in response (as an example metric)
    result["question_count"] = response.count("?")
    
    # Look for reasoning markers in thinking
    reasoning_markers = ["because", "therefore", "thus", "since", "as a result"]
    if thinking:
        result["reasoning_marker_count"] = sum(thinking.lower().count(marker) for marker in reasoning_markers)
    else:
        result["reasoning_marker_count"] = 0
    
    return result

# Example summary function
def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Example summary function that aggregates analysis results.
    
    Args:
        results: List of dictionaries from the test function
        
    Returns:
        Dictionary with aggregated results
    """
    # Skip empty results
    if not results:
        return {"error": "No results to aggregate"}
    
    # Basic summary stats
    total_responses = len(results)
    thinking_responses = sum(1 for r in results if r.get("has_thinking", False))
    
    # Group by temperature
    temps = {}
    for r in results:
        temp = r.get("temperature", 0.0)
        if temp not in temps:
            temps[temp] = []
        temps[temp].append(r)
    
    # Calculate averages
    avg_response_length = sum(r.get("response_length", 0) for r in results) / total_responses
    avg_thinking_length = sum(r.get("thinking_length", 0) for r in results) / total_responses
    avg_generation_time = sum(r.get("generation_time", 0.0) for r in results) / total_responses
    avg_reasoning_markers = sum(r.get("reasoning_marker_count", 0) for r in results) / total_responses
    avg_thinking_ratio = sum(r.get("thinking_response_ratio", 0) for r in results) / total_responses
    
    # Temperature-specific analysis
    temp_analysis = {}
    for temp, temp_results in temps.items():
        temp_thinking = sum(1 for r in temp_results if r.get("has_thinking", False))
        temp_analysis[temp] = {
            "count": len(temp_results),
            "thinking_percentage": (temp_thinking / len(temp_results)) * 100,
            "avg_response_length": sum(r.get("response_length", 0) for r in temp_results) / len(temp_results),
            "avg_thinking_length": sum(r.get("thinking_length", 0) for r in temp_results) / len(temp_results),
            "avg_generation_time": sum(r.get("generation_time", 0.0) for r in temp_results) / len(temp_results),
        }
    
    return {
        "total_responses": total_responses,
        "thinking_responses": thinking_responses,
        "thinking_percentage": (thinking_responses / total_responses) * 100,
        "avg_response_length": avg_response_length,
        "avg_thinking_length": avg_thinking_length,
        "avg_generation_time": avg_generation_time,
        "avg_reasoning_markers": avg_reasoning_markers,
        "avg_thinking_ratio": avg_thinking_ratio,
        "temperature_analysis": temp_analysis,
    }

def main():
    """Example usage demonstration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process and analyze LLM outputs.")
    parser.add_argument("--folder", default="data/output_deepseek-r1_8b_Hello__my_name_is_temp0_7_20250602_125158", help="Path to the folder containing outputs")
    args = parser.parse_args()
    
    # Process the outputs with example functions
    results = process_outputs(
        folder_path=args.folder,
        test_function=analyze_output,
        summary_function=summarize_results
    )
    
    # Print the results
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()