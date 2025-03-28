#!/usr/bin/env python3
"""
CurAIos - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab

This script helps set up the project by:
1. Creating necessary directories
2. Copying the correct versions of fixed modules
3. Generating a default configuration
4. Installing dependencies
5. Creating essential files (.gitignore, etc.)
6. Validating the installation
"""

import os
import sys
import shutil
import subprocess
import json
import argparse
from pathlib import Path


def create_directories(base_path):
    print("\n[1/6] Creating directories...")
    
    directories = [
        "data/cache",
        "data/output",
        "config",
        "core",
        "external",
        "utils",
        "ui",
        "plugins",
        "tests"
    ]
    
    for directory in directories:
        dir_path = os.path.join(base_path, directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"  Created directory: {dir_path}")

    gitkeep_paths = [
        "data/cache/.gitkeep",
        "data/output/.gitkeep",
        "plugins/.gitkeep",
        "tests/.gitkeep"
    ]
    
    for path in gitkeep_paths:
        full_path = os.path.join(base_path, path)
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                pass
            print(f"  Created empty file: {full_path}")
    
    print("Directories created successfully")


def copy_fixed_modules(base_path):
    print("\n[2/6] Installing fixed modules...")
    module_pairs = [
        ("fixed_data_retrieval.py", "external/data_retrieval.py"),
        ("fixed_llm_service.py", "core/llm_service.py"),
        ("integration_test_script.py", "test_integration.py")
    ]
    
    for source, destination in module_pairs:
        source_path = os.path.join(base_path, source)
        dest_path = os.path.join(base_path, destination)
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"  Copied {source} to {destination}")
        else:
            print(f"  WARNING: Could not find {source}")
    
    print("Fixed modules installed")


def generate_config(base_path):
    print("\n[3/6] Generating configuration...")
    config = {
        "llm": {
            "api_key": "",
            "model": "deepseek/deepseek-chat",
            "embedding_model": "DeepSeek-V1",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "ncbi": {
            "api_key": "",
            "email": "",
            "tool": "curaios",
            "rate_limit": 3
        },
        "logging": {
            "level": "INFO",
            "file": "curaios.log",
            "audit_file": "audit.log"
        },
        "repositories": {
            "enabled": ["geo", "figshare", "zenodo", "osf", "sciencedb"],
            "max_results_per_source": 100
        },
        "cache": {
            "enabled": True,
            "ttl": 86400
        },
        "fuzzy_matching": {
            "threshold": 0.85
        },
        "semantic_matching": {
            "threshold": 0.75
        },
        "plugins": {
            "enabled": True,
            "dirs": ["plugins"]
        }
    }
    
    config_path = os.path.join(base_path, "config/config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    template_path = os.path.join(base_path, "config/config.json.template")
    with open(template_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"  Created {config_path}")
    print(f"  Created {template_path}")
    print("Configuration generated")


def install_dependencies(base_path):
    print("\n[4/6] Installing dependencies...")
    
    requirements = [
        "requests>=2.28.0",
        "numpy>=1.22.0",
        "python-Levenshtein>=0.12.2",
        "rapidfuzz>=2.0.0",
        "pandas>=1.4.0",
        "biopython>=1.79",
        "tqdm>=4.64.0",
        "pyyaml>=6.0",
        "scikit-learn>=1.0.2",
        "deepseek-ai>=0.0.1",
        "loguru>=0.6.0"
    ]
    
    req_path = os.path.join(base_path, "requirements.txt")
    with open(req_path, 'w') as f:
        f.write("\n".join(requirements))
    
    print(f"  Created {req_path}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("Error installing dependencies. Please run: pip install -r requirements.txt")


def create_gitignore(base_path):
    print("\n[5/6] Creating additional files...")
    
    gitignore_path = os.path.join(base_path, ".gitignore")
    
    gitignore_content = """
# Python bytecode
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Virtual environments
venv/
env/
ENV/

# IDEs and editors
.idea/
.vscode/
*.swp
*.swo

# OS specific files
.DS_Store
Thumbs.db

# Environment variables
.env

# Log files
*.log

# Cache files
data/cache/*
!data/cache/.gitkeep

# Output files
data/output/*
!data/output/.gitkeep

# Config with API keys
config/config.json
"""
    
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content.strip())
    
    print(f"  Created {gitignore_path}")
    
    readme_path = os.path.join(base_path, "README.md")
    
    readme_content = """
# Curaios - Biological Data Curator

A tool for normalizing, validating, and retrieving biological data using LLMs and external databases.

## Features

- Dynamic input normalization with semantic validation
- Organism name validation using NCBI Taxonomy
- Disease term validation using NCBI MeSH
- Advanced data type normalization
- Autonomous search query construction
- Comprehensive logging and error handling

## Setup

1. Run the setup script: `python setup_project.py`
2. Edit the configuration in `config/config.json`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the integration test: `python test_integration.py`

## Usage

```
python main.py --organism "human" --disease "diabetes" --data-type "rna-seq" --output "results.json"
```

For interactive mode:

```
python main.py --interactive
```

## Directory Structure

- `config/`: Configuration files
- `core/`: Core normalization and validation logic
- `data/`: Cache and output directories
- `external/`: External API integrations
- `plugins/`: User-defined extensions
- `tests/`: Test scripts
- `ui/`: User interface components
- `utils/`: Utility functions
"""
    
    with open(readme_path, 'w') as f:
        f.write(readme_content.strip())
    
    print(f"  Created {readme_path}")
    print("✓ Additional files created")


def validate_setup(base_path):
    print("\n[6/6] Validating setup...")
    
    critical_files = [
        "main.py",
        "core/normalization.py",
        "core/validation.py",
        "core/search_query.py",
        "core/llm_service.py", 
        "external/data_retrieval.py",
        "config/config.json"
    ]
    
    missing_files = []
    for file in critical_files:
        file_path = os.path.join(base_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print("Warning: The following critical files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        
        for file in missing_files:
            if file.startswith("core/") or file.startswith("external/"):
                dir_path = os.path.dirname(os.path.join(base_path, file))
                os.makedirs(dir_path, exist_ok=True)
                with open(os.path.join(base_path, file), 'w') as f:
                    f.write(f'"""\n{file} - Stub file created by setup script\n"""\n\n# TODO: Implement this module\n')
                print(f"  Created stub file for: {file}")
            elif file == "main.py":
                with open(os.path.join(base_path, file), 'w') as f:
                    f.write('#!/usr/bin/env python3\n"""\nCuraios - Biological Data Curator\n\nMain entry point for the application.\n"""\n\nimport argparse\nimport sys\n\ndef main():\n    """Main entry point."""\n    parser = argparse.ArgumentParser(description="Curaios - Biological Data Curator")\n    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")\n    parser.add_argument("--organism", type=str, help="Organism name")\n    parser.add_argument("--disease", type=str, help="Disease name")\n    parser.add_argument("--data-type", type=str, help="Data type")\n    parser.add_argument("--output", type=str, default="results.json", help="Output file")\n    args = parser.parse_args()\n    \n    print("Curaios - Biological Data Curator")\n    print("TODO: Implement main functionality")\n\nif __name__ == "__main__":\n    main()\n')
                print(f"  Created stub file for: {file}")
    else:
        print("All critical files are present")
    
    required_imports = ["requests", "numpy", "rapidfuzz"]
    missing_imports = []
    
    for module in required_imports:
        try:
            __import__(module)
        except ImportError:
            missing_imports.append(module)
    
    if missing_imports:
        print(f"Warning: Missing required imports: {', '.join(missing_imports)}")
        print("  Please run: pip install -r requirements.txt")
    else:
        print("Essential dependencies are installed")
    
    print("\nSetup completed. You may now need to:")
    print("1. Edit config/config.json to add your API keys")
    print("2. Run test_integration.py to verify everything works")
    print("3. Use main.py for normal operation")


def main():
    parser = argparse.ArgumentParser(description="Curaios - Biological Data Curator Project Setup")
    parser.add_argument("--path", type=str, default=".", help="Base path for the project")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    args = parser.parse_args()
    
    base_path = os.path.abspath(args.path)
    print(f"CurAIos - Biological Data Curator Project Setup")
    print(f"Setting up project in: {base_path}")
    print("===============================")
    
    create_directories(base_path)
    copy_fixed_modules(base_path)
    generate_config(base_path)
    
    if not args.skip_deps:
        install_dependencies(base_path)
    else:
        print("\n[4/6] Skipping dependency installation (--skip-deps flag used)")
    
    create_gitignore(base_path)
    validate_setup(base_path)
    
    print("\n✓ Setup complete!")


if __name__ == "__main__":
    main()