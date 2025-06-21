#!/usr/bin/env python3
import shutil
import os
import zipfile
import subprocess

def fix_lambda_packages():
    """Fix Lambda packages by copying utils module and recreating zip files."""
    
    lambda_dirs = [
        "src/lambdas/preprocessing",
        "src/lambdas/profanity_check", 
        "src/lambdas/sentiment_analysis"
    ]
    
    print("=== Fixing Lambda Packages ===")
    
    for lambda_dir in lambda_dirs:
        print(f"Processing {lambda_dir}...")
        
        # Copy utils module to Lambda directory
        utils_dest = os.path.join(lambda_dir, "utils")
        if os.path.exists(utils_dest):
            shutil.rmtree(utils_dest)
        
        shutil.copytree("src/utils", utils_dest)
        print(f"  ✓ Copied utils to {lambda_dir}")
        
        # Recreate zip file
        zip_path = os.path.join(lambda_dir, "lambda.zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(lambda_dir):
                for file in files:
                    if file != "lambda.zip":  # Don't include the zip file itself
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, lambda_dir)
                        zipf.write(file_path, arcname)
        
        print(f"  ✓ Recreated {zip_path}")
        
        # Clean up copied utils directory
        shutil.rmtree(utils_dest)
        print(f"  ✓ Cleaned up utils directory")
    
    print("=== Lambda packages fixed ===")

if __name__ == "__main__":
    fix_lambda_packages() 