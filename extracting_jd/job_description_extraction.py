from datasets import load_dataset  # type: ignore
import json
import re

try:
    # Load the dataset from HuggingFace
    print("Loading dataset from HuggingFace...")
    dataset = load_dataset("jacob-hugging-face/job-descriptions")
    
    # Select only the required columns: job_description, position_title, and model_response
    print(f"Original columns: {dataset['train'].column_names}")
    print("Filtering to keep only 'job_description', 'position_title', and 'model_response'...")
    
    # Check if required columns exist
    required_cols = ["job_description", "position_title", "model_response"]
    available_cols = dataset["train"].column_names
    missing_cols = [col for col in required_cols if col not in available_cols]
    
    if missing_cols:
        print(f"Warning: Missing columns: {missing_cols}")
        print(f"Available columns: {available_cols}")
        # Use only available columns
        required_cols = [col for col in required_cols if col in available_cols]
    
    if not required_cols:
        raise ValueError("None of the required columns are available in the dataset")
    
    # Keep only the required columns
    filtered = dataset["train"].select_columns(required_cols)
    
    print(f"Filtered columns: {filtered.column_names}")
    print(f"Total records: {len(filtered)}")
    
    # Save to JSON file in extracted_data folder
    from pathlib import Path
    output_dir = Path("extracted_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "job_descriptions_filtered.json"
    print(f"Saving filtered data to {output_file}...")    
    
    def clean_text(text):
        """Clean text by removing excessive newlines and whitespace"""
        if not text:
            return ""
        # Replace escaped newlines with actual newlines, then clean
        text = str(text).replace('\\n', '\n')
        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        # Remove empty lines at start and end
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        # Join back with single newlines
        text = '\n'.join(lines)
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    filtered_data = []
    total = len(filtered)
    print(f"Processing {total} records...")
    for idx, item in enumerate(filtered, 1):
        if idx % 100 == 0:
            print(f"  Processed {idx}/{total} records...")
        record = {}
        for col in required_cols:
            value = item.get(col, "")
            # Clean the value
            if col == "model_response":
                # Special handling for model_response - keep as JSON object (dict)
                try:
                    cleaned = str(value).strip()
                    # Remove outer quotes if present
                    if cleaned.startswith('"') and cleaned.endswith('"'):
                        cleaned = cleaned[1:-1]
                    # Parse JSON string
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        # Clean each value in the dict but keep as dict (not string)
                        cleaned_dict = {}
                        for key, val in parsed.items():
                            if isinstance(val, str):
                                cleaned_dict[key] = clean_text(val)
                            elif isinstance(val, list):
                                cleaned_dict[key] = [clean_text(str(v)) if isinstance(v, str) else v for v in val]
                            else:
                                cleaned_dict[key] = val
                        record[col] = cleaned_dict  # Keep as dict, not string
                    else:
                        record[col] = parsed
                except json.JSONDecodeError:
                    # If it's not valid JSON, try to clean as text
                    record[col] = clean_text(str(value))
                except Exception as e:
                    print(f"Warning: Could not parse model_response for record {len(filtered_data)}: {e}")
                    record[col] = clean_text(str(value))
            else:
                record[col] = clean_text(str(value))
        filtered_data.append(record)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully saved {len(filtered_data)} records to {output_file}")
    if filtered_data:
        print(f"Columns: {list(filtered_data[0].keys())}")
        print(f"\n Sample record:")
        sample = filtered_data[0]
        print(f"  Position Title: {sample.get('position_title', 'N/A')[:50]}...")
        print(f"  Job Description length: {len(sample.get('job_description', ''))} chars")
        print(f"  Model Response keys: {list(sample.get('model_response', {}).keys()) if isinstance(sample.get('model_response'), dict) else 'N/A'}")
    
except ImportError:
    print("Error: 'datasets' library not found. Please install it with: pip install datasets")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

