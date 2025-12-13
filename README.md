# CV Analysis Project - AI-Powered Resume Matching System

An intelligent resume analysis and job matching system that uses semantic embeddings and LLM-based analysis to match candidates with job descriptions.

## 🚀 Features

- **PDF Resume Extraction**: Extract and parse text from PDF resumes using `pdfplumber`
- **Semantic Search**: Vector-based similarity search using ChromaDB with HNSW indexing and cosine similarity
- **LLM-Powered Analysis**: AI recruiter analysis using Gemini or local Ollama models
- **Job Description Matching**: Two-stage search (JD → Resume) for accurate candidate matching
- **ATS Scoring**: Deterministic scoring system (skills, experience, education, similarity)
- **CLI Interface**: Interactive command-line interface for recruiters

## 📋 Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://gitlab.com/summer_intern25/omar.git
cd cv_analysis_project
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📁 Project Structure

```
cv_analysis_project/
├── extracting_resumes/          # Resume PDF extraction and parsing
│   ├── extract_text.py         # PDF text extraction
│   ├── resume_parser.py        # Resume parsing logic
│   ├── work_history_parser.py  # Work history extraction
│   ├── run_extraction.py       # Batch extraction script
│   └── debug_test.py           # Debug/testing utilities
│
├── query_structuring_resumes/   # Resume normalization
│   ├── cleaning_resumes.py     # Clean job descriptions
│   ├── create_master_resume.py # Create master resume database
│   └── final_clean.py           # Final cleaning pass
│
├── extracting_JD/              # Job description extraction
│   └── job_description_extraction.py
│
├── query_structuring_JD/       # Job description normalization
│   ├── clean_and_structure_jds.py
│   └── match_resumes_to_jd.py
│
├── embeddings/                 # Vector embeddings
│   ├── embed_resumes.py        # Embed resumes into ChromaDB
│   └── embed_job_descriptions.py # Embed job descriptions
│
├── shared/                     # Shared utilities
│   ├── core_search.py          # Semantic search engine
│   └── candidate_filters.py   # Query parsing and filtering
│
├── comparison_llm/             # LLM analysis layer
│   ├── main.py                 # CLI entry point
│   ├── llm_client.py           # LLM client (Gemini/Ollama)
│   ├── scoring.py              # ATS scoring system
│   ├── prompts.py              # LLM prompts
│   ├── formatters.py           # Output formatting
│   └── response_cleaner.py     # Response cleaning
│
├── data/                       # Resume PDFs (by category)
├── extracted_data/             # Intermediate JSON files
├── extracted_data_final/       # Final cleaned data
├── chroma_db/                  # ChromaDB vector database
└── exports/                    # Recruiter report exports
```

## 🎯 Usage

### 1. Extract Resumes from PDFs

```bash
python extracting_resumes/run_extraction.py
```

### 2. Create Master Resume Database

```bash
python query_structuring_resumes/create_master_resume.py
python query_structuring_resumes/cleaning_resumes.py
```

### 3. Generate Embeddings

```bash
python embeddings/embed_resumes.py
python embeddings/embed_job_descriptions.py
```

### 4. Run the Recruiter CLI

```bash
python comparison_llm/main.py
```

Enter your job query when prompted, and the system will:
- Search for matching candidates using semantic similarity
- Score candidates (skills, experience, education, similarity)
- Display top candidates in tables
- Provide AI-powered recommendations for top 3 candidates
- Export results as JSON

## 🔍 How It Works

### Similarity Calculation

The system uses **semantic embeddings** (not keyword matching):

1. **HNSW Index**: Hierarchical Navigable Small World graph for fast approximate nearest neighbor search
2. **Cosine Similarity**: Distance metric for vector comparison
3. **Two-Stage Search**:
   - Stage 1: Find closest job description by semantic similarity
   - Stage 2: Use that JD to search resume embeddings
4. **Top-K Retrieval**: Returns top 20 candidates, displays top 10

### Extraction Pipeline

- **PDF Extraction**: Uses `pdfplumber` for text extraction
- **Keyword Parsing**: Section detection (summary, experience, education, skills)
- **Work History Parsing**: Intelligent date parsing and job extraction
- **Normalization**: Clean and structure extracted data

### Scoring System

- **Skills Score**: Based on skill overlap
- **Experience Score**: Years of experience matching
- **Education Score**: Education level matching
- **Similarity Score**: Vector similarity (0-100%)

## 📊 Example Output

```
SIMILARITY TO JOB DESCRIPTION
========================================================================================
#   ID               SIM% CATEGORY
----------------------------------------------------------------------------------------
1   21338490        74.9%  Accountant
2   23139819        74.8%  Accountant
3   59403481        74.7%  Accountant
...

FINAL AI RECRUITER RECOMMENDATION
============================================================================================================================================

#1 → ID: 21338490 | AI ATS SCORE: 99/100 | Level: Senior
   Summary       → An exceptional match for an Accountant role...
   Why hire      → Possesses the ideal combination of education...
   Recommendation→ Strong Hire — Priority interview
```

## 🔧 Configuration

- **Embedding Model**: `BAAI/bge-small-en-v1.5` (configurable in `embeddings/` scripts)
- **ChromaDB**: Persistent storage at `chroma_db/`
- **LLM Backend**: Gemini 1.5 Flash or Ollama qwen2.5:1.5b (selectable in CLI)

## 📝 License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

**Note**: This project uses semantic embeddings for similarity calculation, not keyword matching. The extraction phase uses PDF parsing and keyword detection, while the matching phase uses vector semantic similarity.

