import os
from PIL import Image

def optimize_images_in_directory(base_path, max_size=1280, quality=100):
    """
    Recursively processes all images in a directory:
    - Converts to JPG
    - Resizes to max_size
    - Compresses with given quality
    """

    supported_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if not file.lower().endswith(supported_extensions):
                continue

            input_path = os.path.join(root, file)

            try:
                img = Image.open(input_path)

                # Convert to RGB (required for JPG)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize (keeping aspect ratio)
                img.thumbnail((max_size, max_size))

                # Build output path (force .jpg)
                output_filename = os.path.splitext(file)[0] + ".jpg"
                output_path = os.path.join(root, output_filename)

                # Save optimized image
                img.save(output_path, "JPEG", quality=quality, optimize=True)

                # Remove original file if different extension
                if input_path != output_path:
                    os.remove(input_path)

                print(f"Processed: {output_path}")

            except Exception as e:
                print(f"Failed: {input_path} -> {e}")

folder_path = "sites/18799_Fort_Street/spots"
optimize_images_in_directory(folder_path)