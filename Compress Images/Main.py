import os
from PIL import Image

def compress_image(relative_input_path, reduction_percentage=50):
    """
    Compresses an image by reducing its dimensions and optimizing its file size.
    
    :param relative_input_path: The path to the image relative to where this script is located.
    :param reduction_percentage: How much to reduce the image dimensions (0-99). 
                                 e.g., 50 means it scales down by 50%.
    """
    # 1. Resolve the absolute path based on the script's current directory
    input_path = os.path.abspath(relative_input_path)
    
    if not os.path.exists(input_path):
        print(f"Error: Could not find the file at '{input_path}'")
        print("Make sure the file name is correct and relative to the script.")
        return

    # 2. Setup Input and Output paths
    directory, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    
    # Get the parent directory (one level up from the 'Images' folder)
    parent_dir = os.path.dirname(directory)
    
    # Define the new 'Compressed' folder path
    compressed_folder = os.path.join(parent_dir, "Compressed")
    
    # CRITICAL: Create the 'Compressed' folder if it doesn't already exist
    os.makedirs(compressed_folder, exist_ok=True)
    
    # Build the final output path safely
    output_path = os.path.join(compressed_folder, f"{name}_compressed{ext}")

    # 3. Get the original file size in Kilobytes (KB)
    original_size_kb = os.path.getsize(input_path) / 1024

    try:
        # 4. Open and process the image
        with Image.open(input_path) as img:
            # Calculate new dimensions based on the reduction percentage
            scale_factor = (100 - reduction_percentage) / 100.0
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)

            # Resize the image using a high-quality downsampling filter
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save the image. 
            resized_img.save(output_path, optimize=True, quality=80)

        # 5. Get the new file size in KB
        compressed_size_kb = os.path.getsize(output_path) / 1024

        # 6. Print the comparison
        print("-" * 40)
        print("📸 COMPRESSION RESULTS")
        print("-" * 40)
        print(f"Original file : {filename}")
        print(f"Original size : {original_size_kb:.2f} KB")
        print(f"Reduced size  : {compressed_size_kb:.2f} KB")
        
        saved_kb = original_size_kb - compressed_size_kb
        if saved_kb > 0:
            print(f"Space saved   : {saved_kb:.2f} KB ({(saved_kb/original_size_kb)*100:.1f}%)")
        else:
            print("Space saved   : 0 KB (File is already highly optimized)")
        print(f"Output saved to: {output_path}")
        print("-" * 40)

        # 7. Open the final compressed image in the OS's default viewer
        with Image.open(output_path) as final_img:
            final_img.show()

    except Exception as e:
        print(f"An error occurred while processing the image: {e}")

# ==========================================
# How to use the script
# ==========================================
if __name__ == "__main__":
    image_file = "shutter.png" 
    compression_amount = 50 
    
    # Use os.path.join to safely combine the folder and file name
    input_relative_path = os.path.join("Images", image_file)
    
    compress_image(input_relative_path, reduction_percentage=compression_amount)