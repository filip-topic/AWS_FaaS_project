#!/usr/bin/env python3
import os
import shutil
import zipfile

def build_lambda_packages():
    """Build Lambda packages with simplified dependencies."""
    
    lambda_dirs = [
        "src/lambdas/preprocessing",
        "src/lambdas/profanity_check", 
        "src/lambdas/sentiment_analysis"
    ]
    
    print("=== Building Lambda Packages (Simplified) ===")
    
    for lambda_dir in lambda_dirs:
        print(f"\nProcessing {lambda_dir}...")
        
        # Create zip file
        zip_path = os.path.join(lambda_dir, "lambda.zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add handler.py
            handler_path = os.path.join(lambda_dir, "handler.py")
            zipf.write(handler_path, "handler.py")
            print(f"  ✓ Added handler.py")
            
            # Add utils module
            utils_dir = "src/utils"
            for root, dirs, files in os.walk(utils_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join("utils", os.path.relpath(file_path, utils_dir))
                    zipf.write(file_path, arcname)
            print(f"  ✓ Added utils module")
        
        print(f"  ✓ Created {zip_path}")
    
    print("\n=== Lambda packages built successfully ===")

if __name__ == "__main__":
    build_lambda_packages() 