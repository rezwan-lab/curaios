"""
Simple web dashboard for CurAIos.

This module provides a basic Flask-based web interface for the Curaios.
To run the dashboard:

python -m ui.web_dashboard

Then open a web browser and navigate to http://localhost:5000

CurAIos - Biological Data Curator Project Setup Script
CurAIos is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
except ImportError:
    print("Flask is required for the web dashboard. Install with: pip install flask")
    sys.exit(1)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import get_settings, init_settings
from core.validation import validate_input
from core.normalization import normalize_input
from core.search_query import build_search_query
from utils.file_operations import save_metadata
from utils.logging_utils import setup_logging, get_audit_logger
from config.constants import InputType, OutputFormat

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'))

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()

init_settings()
settings = get_settings()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/normalize')
def normalize():
    try:
        organism = request.args.get('organism')
        disease = request.args.get('disease')
        data_type = request.args.get('data_type')
        min_samples = request.args.get('min_samples')
        date_range = request.args.get('date_range')
        output_format = request.args.get('output_format', 'json')
        
        if min_samples:
            try:
                min_samples = int(min_samples)
            except ValueError:
                return jsonify({"error": f"Invalid min_samples value: {min_samples}"})
        
        normalized_data = {}
        
        if organism:
            try:
                validated_organism = validate_input(organism, InputType.ORGANISM.value)
                normalized_organism = normalize_input(validated_organism, InputType.ORGANISM.value)
                normalized_data["organism"] = normalized_organism
            except Exception as e:
                logger.error(f"Error normalizing organism: {e}", exc_info=True)
                return jsonify({"error": f"Error normalizing organism: {str(e)}"})
        
        if disease:
            try:
                validated_disease = validate_input(disease, InputType.DISEASE.value)
                normalized_disease = normalize_input(validated_disease, InputType.DISEASE.value)
                normalized_data["disease"] = normalized_disease
            except Exception as e:
                logger.error(f"Error normalizing disease: {e}", exc_info=True)
                return jsonify({"error": f"Error normalizing disease: {str(e)}"})
        
        if data_type:
            try:
                validated_data_type = validate_input(data_type, InputType.DATA_TYPE.value)
                normalized_data_type = normalize_input(validated_data_type, InputType.DATA_TYPE.value)
                normalized_data["data_type"] = normalized_data_type
            except Exception as e:
                logger.error(f"Error normalizing data type: {e}", exc_info=True)
                return jsonify({"error": f"Error normalizing data type: {str(e)}"})
        
        try:
            query = build_search_query(
                organism=normalized_data.get("organism"),
                disease=normalized_data.get("disease"),
                data_type=normalized_data.get("data_type"),
                min_samples=min_samples,
                date_range=date_range
            )
            normalized_data["query"] = query
        except Exception as e:
            logger.error(f"Error building search query: {e}", exc_info=True)
            return jsonify({"error": f"Error building search query: {str(e)}"})
        
        placeholder_results = [
            {"title": "Sample Dataset 1", "samples": 42, "publication_date": "2022-03-15"},
            {"title": "Sample Dataset 2", "samples": 128, "publication_date": "2021-11-30"},
            {"title": "Sample Dataset 3", "samples": 76, "publication_date": "2023-01-22"}
        ]
        
        # Save results to file
        metadata = {
            "query": query,
            "results": placeholder_results,
            "normalized_inputs": {
                "organism": normalized_data.get("organism", {}).get("canonical_name"),
                "disease": normalized_data.get("disease", {}).get("canonical_name"),
                "data_type": normalized_data.get("data_type", {}).get("canonical_name")
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            output_file = save_metadata(
                metadata,
                os.path.join(settings.output_dir, f"web_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                output_format
            )
            normalized_data["outputFile"] = output_file
        except Exception as e:
            logger.error(f"Error saving metadata: {e}", exc_info=True)
            # Continue without saving
            normalized_data["outputFile"] = None
        
        # Log the activity
        audit_logger.log_activity(
            action="web_search",
            details={
                "organism": normalized_data.get("organism", {}).get("canonical_name"),
                "disease": normalized_data.get("disease", {}).get("canonical_name"),
                "data_type": normalized_data.get("data_type", {}).get("canonical_name"),
                "query": query
            }
        )
        
        return jsonify(normalized_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in normalize API: {e}", exc_info=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(settings.output_dir, filename)

@app.route('/api/history')
def get_history():
    try:
        output_files = []
        for file in os.listdir(settings.output_dir):
            if file.startswith('web_results_') and os.path.isfile(os.path.join(settings.output_dir, file)):
                file_path = os.path.join(settings.output_dir, file)
                timestamp = os.path.getmtime(file_path)
                size = os.path.getsize(file_path)
                
                format = file.split('.')[-1] if '.' in file else 'unknown'
                
                output_files.append({
                    "filename": file,
                    "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                    "size": size,
                    "format": format
                })

        output_files.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return jsonify({"history": output_files})
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving history: {str(e)}"})

@app.route('/api/stats')
def get_stats():
    try:
        stats = {
            "total_searches": 42,
            "top_organisms": [
                {"name": "Homo sapiens", "count": 18},
                {"name": "Mus musculus", "count": 12},
                {"name": "Escherichia coli", "count": 5}
            ],
            "top_diseases": [
                {"name": "Alzheimer's Disease", "count": 10},
                {"name": "Diabetes Mellitus", "count": 8},
                {"name": "Breast Neoplasms", "count": 7}
            ],
            "top_data_types": [
                {"name": "RNAseq", "count": 20},
                {"name": "scRNAseq", "count": 15},
                {"name": "WGS", "count": 7}
            ]
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving stats: {str(e)}"})

@app.route('/api/config')
def get_config():
    try:
        config = {
            "default_output_format": settings.default_output_format,
            "cache_enabled": settings.cache_enabled,
            "fuzzy_threshold": settings.fuzzy_threshold,
            "semantic_threshold": settings.semantic_threshold,
            "plugins_enabled": settings.plugins_enabled
        }
        
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error retrieving config: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving config: {str(e)}"})


def run_web_dashboard(host='127.0.0.1', port=5000, debug=False):
    print(f"Starting CurAIos Curator web dashboard at http://{host}:{port}")
    print("Press Ctrl+C to stop")

    setup_logging(log_level="DEBUG" if debug else "INFO")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nStopping web dashboard")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run CurAIos Curator web dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    run_web_dashboard(host=args.host, port=args.port, debug=args.debug)

os.makedirs(app.template_folder, exist_ok=True)
os.makedirs(app.static_folder, exist_ok=True)

template_path = os.path.join(app.template_folder, 'index.html')
if not os.path.exists(template_path):
    with open(template_path, 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>CurAIos Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <header>
        <h1>CurAIos Dashboard</h1>
    </header>
    
    <main>
        <section class="input-section">
            <h2>Input Parameters</h2>
            <form id="normalization-form">
                <div class="form-group">
                    <label for="organism">Organism:</label>
                    <input type="text" id="organism" name="organism" placeholder="e.g., human, mouse, e. coli">
                </div>
                
                <div class="form-group">
                    <label for="disease">Disease:</label>
                    <input type="text" id="disease" name="disease" placeholder="e.g., alzheimer's, diabetes, cancer">
                </div>
                
                <div class="form-group">
                    <label for="data_type">Data Type:</label>
                    <input type="text" id="data_type" name="data_type" placeholder="e.g., RNAseq, microarray, proteomics">
                </div>
                
                <div class="form-group">
                    <label for="min_samples">Minimum Samples:</label>
                    <input type="number" id="min_samples" name="min_samples" placeholder="e.g., 10">
                </div>
                
                <div class="form-group">
                    <label for="date_range">Date Range:</label>
                    <input type="text" id="date_range" name="date_range" placeholder="e.g., 2020-2023">
                </div>
                
                <div class="form-group">
                    <label for="output_format">Output Format:</label>
                    <select id="output_format" name="output_format">
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                        <option value="xlsx">Excel</option>
                    </select>
                </div>
                
                <button type="submit" id="normalize-btn">Normalize & Search</button>
            </form>
        </section>
        
        <section class="results-section">
            <h2>Normalization Results</h2>
            <div id="normalization-results">
                <div class="placeholder">Enter parameters and click "Normalize & Search" to see results.</div>
            </div>
            
            <h2>Search Query</h2>
            <div id="search-query">
                <div class="placeholder">Enter parameters and click "Normalize & Search" to generate a query.</div>
            </div>
            
            <h2>Search Results</h2>
            <div id="search-results">
                <div class="placeholder">Enter parameters and click "Normalize & Search" to see results.</div>
            </div>
            
            <div class="download-section">
                <h3>Download Results</h3>
                <div id="download-links"></div>
            </div>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2023 CurAIos Curator</p>
    </footer>
    
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
""")

css_path = os.path.join(app.static_folder, 'style.css')
if not os.path.exists(css_path):
    with open(css_path, 'w') as f:
        f.write("""/* Basic styles for CurAIos Curator Dashboard */

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f7fa;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem;
    text-align: center;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 2rem;
}

section {
    background: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
}

.input-section {
    flex: 1;
    min-width: 300px;
}

.results-section {
    flex: 2;
    min-width: 500px;
}

h2 {
    margin-bottom: 1rem;
    color: #2c3e50;
}

.form-group {
    margin-bottom: 1rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
}

input, select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 0.75rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    margin-top: 1rem;
}

button:hover {
    background-color: #2980b9;
}

.placeholder {
    color: #7f8c8d;
    font-style: italic;
}

#normalization-results, #search-query, #search-results {
    background-color: #f9f9f9;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1.5rem;
    overflow-x: auto;
}

.download-section {
    margin-top: 2rem;
}

.download-link {
    display: inline-block;
    margin-right: 1rem;
    margin-top: 0.5rem;
    padding: 0.5rem 1rem;
    background-color: #2ecc71;
    color: white;
    text-decoration: none;
    border-radius: 4px;
}

.download-link:hover {
    background-color: #27ae60;
}

pre {
    white-space: pre-wrap;
    word-wrap: break-word;
}

.normalized-item {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;
}

.normalized-item:last-child {
    border-bottom: none;
}

.property {
    display: flex;
    margin-bottom: 0.25rem;
}

.property-name {
    font-weight: bold;
    min-width: 150px;
}

.confidence-high {
    color: #27ae60;
}

.confidence-medium {
    color: #f39c12;
}

.confidence-low {
    color: #e74c3c;
}

footer {
    text-align: center;
    padding: 1rem;
    margin-top: 2rem;
    color: #7f8c8d;
}

@media (max-width: 768px) {
    main {
        flex-direction: column;
    }
}
""")

js_path = os.path.join(app.static_folder, 'script.js')
if not os.path.exists(js_path):
    with open(js_path, 'w') as f:
        f.write("""// CurAIos Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('normalization-form');
    const normalizationResults = document.getElementById('normalization-results');
    const searchQuery = document.getElementById('search-query');
    const searchResults = document.getElementById('search-results');
    const downloadLinks = document.getElementById('download-links');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        normalizationResults.innerHTML = '<div class="loading">Processing...</div>';
        searchQuery.innerHTML = '<div class="loading">Generating query...</div>';
        searchResults.innerHTML = '<div class="loading">Searching...</div>';
        downloadLinks.innerHTML = '';
        
        // Get form data
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        // Add non-empty form values to params
        for (const [key, value] of formData.entries()) {
            if (value.trim()) {
                params.append(key, value);
            }
        }
        
        try {
            // Call API to normalize inputs
            const response = await fetch('/api/normalize?' + params.toString());
            const data = await response.json();
            
            if (data.error) {
                normalizationResults.innerHTML = `<div class="error">${data.error}</div>`;
                searchQuery.innerHTML = '<div class="placeholder">Error occurred during normalization.</div>';
                searchResults.innerHTML = '<div class="placeholder">Error occurred during normalization.</div>';
                return;
            }
            
            // Display normalization results
            displayNormalizationResults(data);
            
            // Display search query
            searchQuery.innerHTML = `<pre>${data.query || 'No query generated'}</pre>`;
            
            // Display sample results (in a real application, this would be actual results)
            searchResults.innerHTML = '<div class="placeholder">Sample search results would appear here.</div>';
            
            // Display download links
            if (data.outputFile) {
                const filename = data.outputFile.split('/').pop();
                const format = formData.get('output_format') || 'json';
                
                downloadLinks.innerHTML = `
                    <a href="/download/${filename}" class="download-link">${format.toUpperCase()} Results</a>
                `;
            }
            
        } catch (error) {
            console.error('Error:', error);
            normalizationResults.innerHTML = `<div class="error">An error occurred: ${error.message}</div>`;
            searchQuery.innerHTML = '<div class="placeholder">Error occurred during processing.</div>';
            searchResults.innerHTML = '<div class="placeholder">Error occurred during processing.</div>';
        }
    });
    
    function displayNormalizationResults(data) {
        let html = '';
        
        // Organism results
        if (data.organism) {
            html += '<div class="normalized-item">';
            html += '<h3>Organism</h3>';
            html += displayEntity(data.organism);
            html += '</div>';
        }
        
        // Disease results
        if (data.disease) {
            html += '<div class="normalized-item">';
            html += '<h3>Disease</h3>';
            html += displayEntity(data.disease);
            html += '</div>';
        }
        
        // Data type results
        if (data.data_type) {
            html += '<div class="normalized-item">';
            html += '<h3>Data Type</h3>';
            html += displayEntity(data.data_type);
            html += '</div>';
        }
        
        if (!html) {
            html = '<div class="placeholder">No inputs provided for normalization.</div>';
        }
        
        normalizationResults.innerHTML = html;
    }
    
    function displayEntity(entity) {
        let html = '<div class="entity-details">';
        
        // Original input
        if (entity.original_input) {
            html += `<div class="property">
                <span class="property-name">Original input:</span>
                <span>${entity.original_input}</span>
            </div>`;
        }
        
        // Canonical name
        if (entity.canonical_name) {
            html += `<div class="property">
                <span class="property-name">Normalized to:</span>
                <span><strong>${entity.canonical_name}</strong></span>
            </div>`;
        }
        
        // ID (NCBI Taxonomy or MeSH)
        if (entity.ncbi_taxonomy_id) {
            html += `<div class="property">
                <span class="property-name">NCBI Taxonomy ID:</span>
                <span>${entity.ncbi_taxonomy_id}</span>
            </div>`;
        }
        
        if (entity.mesh_id) {
            html += `<div class="property">
                <span class="property-name">MeSH ID:</span>
                <span>${entity.mesh_id}</span>
            </div>`;
        }
        
        // Confidence score
        if (entity.confidence) {
            const confidenceValue = entity.confidence;
            let confidenceClass = '';
            
            if (confidenceValue >= 0.9) {
                confidenceClass = 'confidence-high';
            } else if (confidenceValue >= 0.7) {
                confidenceClass = 'confidence-medium';
            } else {
                confidenceClass = 'confidence-low';
            }
            
            html += `<div class="property">
                <span class="property-name">Confidence:</span>
                <span class="${confidenceClass}">${(confidenceValue * 100).toFixed(1)}%</span>
            </div>`;
        }
        
        // Alternatives
        if (entity.alternatives && entity.alternatives.length > 0) {
            html += `<div class="property">
                <span class="property-name">Alternatives:</span>
                <span>${entity.alternatives.join(', ')}</span>
            </div>`;
        }
        
        // Source
        if (entity.source) {
            html += `<div class="property">
                <span class="property-name">Source:</span>
                <span>${entity.source}</span>
            </div>`;
        }
        
        html += '</div>';
        return html;
    }
});