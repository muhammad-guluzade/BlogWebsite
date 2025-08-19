from PIL import Image
import random
import hashlib

# Function to resize the image to fit within the 1280x720 limits
def resize_image(image):
    max_width = 1280
    max_height = 720
    width, height = image.size

    # Only resize if the image exceeds the maximum width or height
    if width > max_width or height > max_height:
        # Calculate the scaling factor for width and height
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize the image using the LANCZOS resampling filter (high quality)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return image

# Function to generate a consistent shuffle order from the key
def generate_shuffle_order(key, image_size):
    # Use the key to generate a hash (SHA-256)
    hashed_key = hashlib.sha256(key.encode()).hexdigest()

    # Create a list of indices from 0 to image_size - 1
    indices = list(range(image_size))

    # Use the hashed key as a seed for the random shuffle
    random.seed(int(hashed_key, 16))

    # Shuffle the indices based on the key
    random.shuffle(indices)

    return indices

# Function to encrypt the image (shuffling the pixel data)
def encrypt_image(input_path, output_path, key):
    # Open the image
    image = Image.open(input_path)

    # Resize image if it exceeds 1280x720 pixels
    image = resize_image(image)

    # Convert image to RGB mode
    image = image.convert("RGB")

    # Get the pixels of the image
    pixels = list(image.getdata())

    # Generate the shuffle order using the key
    indices = generate_shuffle_order(key, len(pixels))

    # Shuffle the pixels using the indices
    shuffled_pixels = [pixels[i] for i in indices]

    # Create a new image with the shuffled pixel data
    encrypted_image = Image.new(image.mode, image.size)
    encrypted_image.putdata(shuffled_pixels)

    # Save the encrypted image as PNG
    encrypted_image.save(output_path, "PNG")

# Function to restore the shuffled pixels based on the key
def restore_pixels(image, key):
    # Get the pixels of the shuffled image
    pixels = list(image.getdata())

    # Generate the shuffle order using the key
    indices = generate_shuffle_order(key, len(pixels))

    # Create a new list to restore the pixels back to their original positions
    restored_pixels = [None] * len(pixels)
    for i, original_index in enumerate(indices):
        restored_pixels[original_index] = pixels[i]

    # Create a new image and set the restored pixels
    restored_image = Image.new(image.mode, image.size)
    restored_image.putdata(restored_pixels)
    return restored_image

# Function to process the image: resize and restore it
def decrypt_image(input_path, key, output_path):
    # Open the shuffled image
    image = Image.open(input_path)

    # Restore the shuffled pixels based on the provided key
    restored_image = restore_pixels(image, key)

    # Save the restored image as PNG
    restored_image.save(output_path, "PNG")

