#!/usr/bin/env python3
import os
import shutil

# Target directory extensions mapping
EXT_MAPPING = {
    'Images': ['.jpg', '.jpeg', '.gif'],
    'Documents': ['.txt'],
    'Videos': ['.mp4']
}

def organize_folder(source_dir):
    """
    Scans the source_dir for files matching the specified extensions
    and moves them to their respective folders.
    """
    print(f"Starting organization in: {source_dir}\n")
    
    # Track files moved for reporting
    moved_count = {folder: [] for folder in EXT_MAPPING}
    ignored_count = 0

    # Ensure target directories exist in the source directory
    for folder in EXT_MAPPING:
        dest_path = os.path.join(source_dir, folder)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
            print(f"Created folder: {folder}/")

    # Read the files in the directory
    try:
        items = os.listdir(source_dir)
    except Exception as e:
        print(f"Error reading directory: {e}")
        return

    for item in items:
        item_path = os.path.join(source_dir, item)
        
        # Only organize files (skip directories)
        if os.path.isfile(item_path):
            # Skip the organization script itself
            if item == os.path.basename(__file__):
                continue
                
            _, ext = os.path.splitext(item.lower())
            
            moved = False
            for folder, extensions in EXT_MAPPING.items():
                if ext in extensions:
                    dest_file_path = os.path.join(source_dir, folder, item)
                    
                    # Resolve naming conflicts if file already exists in destination
                    if os.path.exists(dest_file_path):
                        base, extension = os.path.splitext(item)
                        counter = 1
                        while os.path.exists(os.path.join(source_dir, folder, f"{base}_{counter}{extension}")):
                            counter += 1
                        dest_file_path = os.path.join(source_dir, folder, f"{base}_{counter}{extension}")
                    
                    try:
                        shutil.move(item_path, dest_file_path)
                        moved_count[folder].append(item)
                        moved = True
                        print(f"Moved: '{item}' -> '{folder}/'")
                    except Exception as e:
                        print(f"Error moving '{item}': {e}")
                    break
            
            if not moved:
                ignored_count += 1

    # Print summary
    print("\n--- Organization Summary ---")
    total_moved = 0
    for folder, files in moved_count.items():
        count = len(files)
        total_moved += count
        print(f"{folder}: {count} file(s) moved")
    print(f"Ignored/other files: {ignored_count}")
    print(f"Total files organized: {total_moved}")

if __name__ == "__main__":
    # Use current working directory where the script is run
    cwd = os.getcwd()
    organize_folder(cwd)
