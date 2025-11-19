"""
Setup script to pull a model in Ollama Docker container.
"""

import requests
import sys
import time

OLLAMA_URL = "http://localhost:11434"

def check_ollama_running():
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def pull_model(model_name: str = "llama2"):
    """Pull a model in Ollama."""
    print(f"Pulling model '{model_name}'...")
    print("This may take a few minutes depending on your internet connection...")
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=300
        )
        
        for line in response.iter_lines():
            if line:
                try:
                    data = line.decode('utf-8')
                    if data:
                        # Parse progress updates
                        import json
                        try:
                            progress = json.loads(data)
                            if 'status' in progress:
                                print(f"  {progress['status']}")
                        except:
                            pass
                except:
                    pass
        
        print(f"\n✅ Model '{model_name}' pulled successfully!")
        return True
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout pulling model. Try again.")
        return False
    except Exception as e:
        print(f"\n❌ Error pulling model: {e}")
        return False

def list_models():
    """List available models."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                print("\nAvailable models:")
                for model in models:
                    print(f"  - {model['name']}")
            else:
                print("\nNo models installed. Pull a model first.")
        else:
            print("Failed to list models.")
    except Exception as e:
        print(f"Error listing models: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Ollama models')
    parser.add_argument(
        '--model',
        default='llama2',
        help='Model name to pull (default: llama2). Options: llama2, mistral, codellama, etc.'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List installed models'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Ollama Setup")
    print("=" * 60)
    
    # Check if Ollama is running
    print("\n1. Checking if Ollama is running...")
    if not check_ollama_running():
        print("❌ Ollama is not running!")
        print("\nStart it with:")
        print("  docker compose up -d ollama")
        print("\nOr if running locally:")
        print("  ollama serve")
        sys.exit(1)
    
    print("✅ Ollama is running!")
    
    # List models if requested
    if args.list:
        list_models()
        sys.exit(0)
    
    # Pull model
    print(f"\n2. Pulling model '{args.model}'...")
    if pull_model(args.model):
        print(f"\n✅ Setup complete!")
        print(f"\nYou can now use model '{args.model}' in your pipeline.")
        print(f"\nSet environment variable:")
        print(f"  export MODEL_NAME={args.model}")
        print(f"\nOr update your .env file:")
        print(f"  MODEL_NAME={args.model}")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()

