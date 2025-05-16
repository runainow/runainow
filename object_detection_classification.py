import argparse
import os
import cv2
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

# Define command-line arguments
parser = argparse.ArgumentParser(description='Object Detection and Classification in Images')
parser.add_argument('--input-folder', type=str, default='input_images', 
                    help='Path to the folder containing input images')
parser.add_argument('--output-folder', type=str, default='output_cropped', 
                    help='Path to the folder to save cropped and classified images')
parser.add_argument('--model-path', type=str, default='cifar10_model.pth', 
                    help='Path to the trained model file')
args = parser.parse_args()

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Define the CNN model (must match the trained model architecture)
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, 3)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, 3)
        self.fc1 = nn.Linear(32 * 6 * 6, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.view(-1, 32 * 6 * 6)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Load the trained model
model = SimpleCNN().to(device)
if os.path.exists(args.model_path):
    model.load_state_dict(torch.load(args.model_path))
    model.eval()
    print(f"Loaded model from {args.model_path}")
else:
    print(f"Model file {args.model_path} not found. Please train the model first.")
    exit(1)

# CIFAR-10 class names
classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

# Transform for input images
transform = transforms.Compose([
    transforms.Resize((32, 32)),  # CIFAR-10 images are 32x32
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

# Create output folder if it doesn't exist
if not os.path.exists(args.output_folder):
    os.makedirs(args.output_folder)

# Function to detect and crop object (simplified approach)
def detect_and_crop(image):
    # Convert PIL image to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Use a simple contour detection (this is a basic approach)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Crop the image to the bounding box
        cropped = opencv_image[y:y+h, x:x+w]
        cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        return Image.fromarray(cropped), (x, y, w, h)
    else:
        # If no object detected, return the center 80% of the image as a fallback
        h, w = opencv_image.shape[:2]
        center_crop_size = int(min(h, w) * 0.8)
        start_x = (w - center_crop_size) // 2
        start_y = (h - center_crop_size) // 2
        cropped = opencv_image[start_y:start_y+center_crop_size, start_x:start_x+center_crop_size]
        cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        return Image.fromarray(cropped), (start_x, start_y, center_crop_size, center_crop_size)

# Function to classify image
def classify_image(image):
    image = transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output.data, 1)
        return classes[predicted[0]]

# Process images in input folder
input_folder = args.input_folder
if not os.path.exists(input_folder):
    print(f"Input folder {input_folder} does not exist. Please provide images to classify.")
    exit(1)

image_files = [f for f in os.listdir(input_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
if not image_files:
    print(f"No images found in {input_folder}.")
    exit(1)

print(f"Processing {len(image_files)} images from {input_folder}...")
for img_file in image_files:
    img_path = os.path.join(input_folder, img_file)
    try:
        # Load image
        image = Image.open(img_path).convert('RGB')
        print(f"Processing {img_file}...")
        
        # Detect and crop object
        cropped_image, bbox = detect_and_crop(image)
        print(f"  - Object detected at {bbox}")
        
        # Classify the cropped image
        label = classify_image(cropped_image)
        print(f"  - Classified as: {label}")
        
        # Save cropped image with classification in filename
        output_filename = f"{os.path.splitext(img_file)[0]}_{label}.png"
        output_path = os.path.join(args.output_folder, output_filename)
        cropped_image.save(output_path)
        print(f"  - Saved cropped image to {output_path}")
    except Exception as e:
        print(f"Error processing {img_file}: {e}")

print("Processing complete.")
