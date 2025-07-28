# PDF Outline Extraction Solution

## Pre-built Image
Available on Docker Hub: `parzivl/pdf-outline-extractor:latest`

## Quick Start (Using Pre-built Image)
```bash
mkdir -p input output
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none parzivl/pdf-outline-extractor:latest
```

## Build from Source
If you want to build locally:
```bash
docker build --platform linux/amd64 -t pdf-outline-extractor:latest .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-outline-extractor:latest
```

## For Windows PowerShell
```powershell
mkdir -p input, output
docker run --rm -v "${PWD}/input:/app/input" -v "${PWD}/output:/app/output" --network none parzivl/pdf-outline-extractor:latest
```

## Approach

This solution extracts structured outlines from PDF documents using a hybrid approach:

1. **Form Detection**: Identifies form documents and returns empty outlines
2. **Built-in TOC**: Uses PDF's native table of contents when available
3. **Text Analysis**: Advanced heading detection using font size, formatting, and pattern matching
4. **Title Extraction**: Multi-line title reconstruction with intelligent merging

The system processes documents through multiple stages:
- Header/footer filtering using position analysis
- Adjacent text merging with similar formatting
- ML-inspired classification for heading levels (H1/H2/H3)
- Pattern-based recognition for common document structures

## Models and Libraries Used

### Core Libraries
- **PyMuPDF (fitz)**: PDF processing and text extraction
- **NumPy**: Numerical operations for text analysis
- **Python Standard Library**: JSON, regex, pathlib, logging

### No External Models
- No pre-trained ML models (stays under 200MB limit)
- No network dependencies (works offline)
- Custom pattern-based classification system

## Architecture

- `main.py`: Main orchestrator with PDFOutlineExtractor class
- `helper.py`: Advanced heading detection with PDFHeadingAnalyzer
- Supports AMD64 architecture explicitly
- Containerized for consistent execution

## How to Build and Run

### Build the Docker Image
```bash
docker build --platform linux/amd64 -t pdf-outline-extractor:latest .
```

### Run the Solution
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-outline-extractor:latest
```

### Expected Behavior
- Processes all PDF files from `/app/input` directory
- Generates corresponding `filename.json` files in `/app/output`
- Each JSON contains extracted title and hierarchical outline
- Works completely offline with no network calls

### Input/Output Format
**Input**: PDF files in `/app/input/`
**Output**: JSON files with structure:
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1",
      "page": 1
    }
  ]
}
```

