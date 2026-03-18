import os
from PIL import Image
import sys

def split_image_3x3(image_path, output_dir="output"):
    """
    Splits an image into 9 equal parts (3x3 grid).
    """
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found.")
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Calculate dimensions for each tile
        tile_width = width // 3
        tile_height = height // 3
        
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        ext = os.path.splitext(image_path)[1]
        
        count = 1
        for row in range(3):
            for col in range(3):
                # Calculate coordinates (left, upper, right, lower)
                left = col * tile_width
                upper = row * tile_height
                right = (col + 1) * tile_width if col < 2 else width
                lower = (row + 1) * tile_height if row < 2 else height
                
                # Crop and save
                tile = img.crop((left, upper, right, lower))
                output_name = f"{base_name}_{count}{ext}"
                tile_path = os.path.join(output_dir, output_name)
                tile.save(tile_path)
                print(f"Saved: {tile_path}")
                count += 1
                
        print(f"\nDone! 9 images saved to: {output_dir}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grid_splitter.py <image_path>")
    else:
        split_image_3x3(sys.argv[1])
