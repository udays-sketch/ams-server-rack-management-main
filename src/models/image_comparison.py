#!/usr/bin/env python3
"""
Image Comparison Module for Server Rack Change Detection Web App

This module provides functionality for comparing server rack images and detecting changes
between them using both pixel-based and structural similarity methods.
Adapted from the original POC for web application use.
"""

import os
import cv2
import numpy as np
# Set matplotlib to use non-GUI backend
import matplotlib
matplotlib.use('Agg')  # Use Agg backend (non-GUI) to avoid threading issues
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim
from PIL import Image
import pytesseract
import uuid
import json
from datetime import datetime

class ServerRackChangeDetector:
    """
    A class for detecting and visualizing changes between server rack images.
    """
    
    def __init__(self, upload_folder, results_folder, threshold=0.8, min_contour_area=100, 
                 compression_quality=85, max_dimension=1920):
        """
        Initialize the ServerRackChangeDetector.
        
        Args:
            upload_folder (str): Path to store uploaded images
            results_folder (str): Path to store results
            threshold (float): Threshold for SSIM comparison (0.0-1.0)
            min_contour_area (int): Minimum contour area to consider as a change
            compression_quality (int): JPEG compression quality (0-100)
            max_dimension (int): Maximum dimension for image resizing
        """
        self.upload_folder = upload_folder
        self.results_folder = results_folder
        self.threshold = threshold
        self.min_contour_area = min_contour_area
        self.compression_quality = compression_quality
        self.max_dimension = max_dimension
        self.results = {}
        
        # Create folders if they don't exist
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(results_folder, exist_ok=True)
    
    def compress_image(self, image_path):
        """
        Compress an image to reduce memory usage.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Path to the compressed image
        """
        # Open the image with PIL
        img = Image.open(image_path)
        
        # Determine if resizing is needed
        width, height = img.size
        if width > self.max_dimension or height > self.max_dimension:
            # Calculate new dimensions maintaining aspect ratio
            if width > height:
                new_width = self.max_dimension
                new_height = int(height * (self.max_dimension / width))
            else:
                new_height = self.max_dimension
                new_width = int(width * (self.max_dimension / height))
            
            # Resize the image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Generate compressed file path
        filename, ext = os.path.splitext(image_path)
        compressed_path = f"{filename}_compressed.jpg"
        
        # Save with compression
        img.save(compressed_path, 'JPEG', quality=self.compression_quality, optimize=True)
        img.close()
        
        print(f"Compressed image: {os.path.getsize(compressed_path) / 1024:.2f} KB " +
              f"(Original: {os.path.getsize(image_path) / 1024:.2f} KB)")
        
        return compressed_path
    
    def save_uploaded_image(self, file, prefix):
        """
        Save an uploaded image file.
        
        Args:
            file: Flask file object
            prefix (str): Prefix for the filename (e.g., 'before', 'after')
            
        Returns:
            str: Path to the saved file
        """
        # Generate a unique filename
        filename = f"{prefix}_{uuid.uuid4().hex}.png"
        filepath = os.path.join(self.upload_folder, filename)
        
        # Save the file
        if hasattr(file, 'save'):
            # Flask file object
            file.save(filepath)
        else:
            # PIL Image or other object with save method
            file.save(filepath)
        
        # Compress the image
        compressed_path = self.compress_image(filepath)
        
        return compressed_path
    
    def load_images(self, before_path, after_path):
        """
        Load before and after images and convert to grayscale.
        
        Args:
            before_path (str): Path to the 'before' image
            after_path (str): Path to the 'after' image
            
        Returns:
            tuple: (before_color, after_color, before_gray, after_gray)
        """
        # Load images
        before_color = cv2.imread(before_path)
        after_color = cv2.imread(after_path)
        
        # Check if images were loaded successfully
        if before_color is None or after_color is None:
            raise ValueError(f"Failed to load images: {before_path} or {after_path}")
        
        # Convert to grayscale
        before_gray = cv2.cvtColor(before_color, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after_color, cv2.COLOR_BGR2GRAY)
        
        # Resize images if they have different dimensions
        if before_gray.shape != after_gray.shape:
            after_gray = cv2.resize(after_gray, (before_gray.shape[1], before_gray.shape[0]))
            after_color = cv2.resize(after_color, (before_color.shape[1], before_color.shape[0]))
        
        return before_color, after_color, before_gray, after_gray
    
    def compare_images(self, before_path, after_path):
        """Compare two images and detect changes"""
        try:
            # Read images with limited size to prevent memory issues
            before_img = self._read_and_resize_image(before_path)
            after_img = self._read_and_resize_image(after_path)
            
            # Store paths
            self.results['before_path'] = before_path
            self.results['after_path'] = after_path
            
            # Calculate SSIM
            self.results['ssim_score'] = self._calculate_ssim(before_img, after_img)
            
            # Create comparison
            self._create_comparison_image(before_img, after_img)
            
            # Detect changes
            self._detect_changes(before_img, after_img)
            
            # Clean up memory
            del before_img
            del after_img
            import gc
            gc.collect()
            
            return self.results
        except Exception as e:
            import traceback
            print(f"Error in compare_images: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def _read_and_resize_image(self, path):
        """Read image and resize if too large to prevent memory issues"""
        try:
            img = cv2.imread(path)
            if img is None:
                raise ValueError(f"Failed to read image at {path}")
            
            # Check size and resize if very large
            MAX_DIMENSION = 1600
            height, width = img.shape[:2]
            
            if height > MAX_DIMENSION or width > MAX_DIMENSION:
                # Calculate new dimensions
                if height > width:
                    new_height = MAX_DIMENSION
                    new_width = int(width * (MAX_DIMENSION / height))
                else:
                    new_width = MAX_DIMENSION
                    new_height = int(height * (MAX_DIMENSION / width))
                
                # Resize image
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return img
        except Exception as e:
            import traceback
            print(f"Error reading image {path}: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def _calculate_ssim(self, img1, img2):
        """Calculate SSIM between two images"""
        return ssim(img1, img2, full=True)[0]
    
    def _create_comparison_image(self, img1, img2):
        """Create a side-by-side comparison image"""
        # Create a side-by-side comparison
        height, width = img1.shape[:2]
        comparison = np.zeros((height, width * 3, 3), dtype=np.uint8)
        comparison[:, :width] = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
        comparison[:, width:width*2] = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
        comparison[:, width*2:] = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
        
        # Store comparison image
        self.results['comparison'] = comparison
    
    def _detect_changes(self, img1, img2):
        """Detect changes between two images"""
        # Calculate SSIM
        (score, diff) = ssim(img1, img2, full=True)
        
        # Convert the SSIM difference map to uint8 range [0, 255]
        diff = (diff * 255).astype("uint8")
        
        # Threshold the difference map to create a binary mask
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Find contours in the thresholded difference map
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        significant_contours = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
        
        # Create a mask for the significant changes
        mask = np.zeros_like(img1)
        for contour in significant_contours:
            cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Create a visual diff highlighting the changes
        visual_diff = img2.copy()
        visual_diff[mask == 255] = [0, 0, 255]  # Highlight changes in red
        
        # Store results
        self.results['ssim_score'] = score
        self.results['diff_map'] = diff
        self.results['change_mask'] = mask
        self.results['visual_diff'] = visual_diff
        self.results['contours'] = significant_contours
        self.results['num_changes'] = len(significant_contours)
    
    def extract_change_details(self):
        """
        Extract detailed information about the detected changes.
        
        Returns:
            list: List of dictionaries containing details about each change
        """
        if not self.results:
            raise ValueError("No comparison results available. Run compare_images first.")
        
        changes = []
        for i, contour in enumerate(self.results['contours']):
            # Calculate bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate area and center
            area = cv2.contourArea(contour)
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Determine rack unit position (assuming standard rack)
            # This is a simplified estimation - would need calibration for real-world use
            image_height = self.results['before_image'].shape[0]
            image_width = self.results['before_image'].shape[1]
            rack_units = 42  # Standard 42U rack
            approx_ru = int((y / image_height) * rack_units)
            
            # Calculate confidence based on contour area and SSIM score
            # Scale divisor based on image resolution (approximately 1% of total image area)
            total_image_area = image_width * image_height
            area_divisor = total_image_area * 0.01  # 1% of total image area
            confidence = min(1.0, (area / area_divisor) * (1.0 - self.results['ssim_score']))
            
            # Determine change type based on pixel intensity comparison
            before_roi = self.results['before_image'][y:y+h, x:x+w]
            after_roi = self.results['after_image'][y:y+h, x:x+w]
            
            before_mean = np.mean(before_roi)
            after_mean = np.mean(after_roi)
            
            if after_mean > before_mean * 1.2:
                change_type = "Addition"
            elif before_mean > after_mean * 1.2:
                change_type = "Removal"
            else:
                change_type = "Modification"
            
            # Extract any visible text using OCR (for asset tags, serial numbers, etc.)
            # This would need refinement for real-world use
            extracted_text = None
            try:
                # Convert ROI to grayscale and apply thresholding for better OCR
                roi_gray = cv2.cvtColor(after_roi, cv2.COLOR_BGR2GRAY)
                _, roi_thresh = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Use pytesseract for OCR
                extracted_text = pytesseract.image_to_string(roi_thresh).strip()
                
                # If no text was found, try the before image
                if not extracted_text:
                    roi_gray = cv2.cvtColor(before_roi, cv2.COLOR_BGR2GRAY)
                    _, roi_thresh = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    extracted_text = pytesseract.image_to_string(roi_thresh).strip()
            except:
                extracted_text = None
            
            change = {
                'id': i + 1,
                'type': change_type,
                'location': {
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'center_x': center_x,
                    'center_y': center_y,
                    'estimated_ru': approx_ru
                },
                'area': area,
                'confidence': confidence,
                'extracted_text': extracted_text if extracted_text else None
            }
            
            changes.append(change)
        
        return changes
    
    def save_results(self, session_id=None):
        """
        Save the comparison results to files.
        
        Args:
            session_id (str, optional): Session ID for the results. If None, a new UUID is generated.
            
        Returns:
            dict: Paths to the saved files and session ID
        """
        if not self.results:
            raise ValueError("No comparison results available. Run compare_images first.")
        
        # Generate session ID if not provided
        if session_id is None:
            session_id = uuid.uuid4().hex
        
        # Create session directory
        session_dir = os.path.join(self.results_folder, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Save the comparison image
        comparison_path = os.path.join(session_dir, "comparison.png")
        plt.figure(figsize=(15, 5))
        plt.imshow(self.results['comparison'])
        plt.title(f"Before | After | Changes (SSIM: {self.results['ssim_score']:.4f})")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(comparison_path)
        plt.close()
        
        # Save the visual diff
        visual_diff_path = os.path.join(session_dir, "visual_diff.png")
        cv2.imwrite(visual_diff_path, self.results['visual_diff'])
        
        # Save the change mask
        mask_path = os.path.join(session_dir, "mask.png")
        cv2.imwrite(mask_path, self.results['change_mask'])
        
        # Extract and save change details
        changes = self.extract_change_details()
        changes_path = os.path.join(session_dir, "changes.txt")
        
        with open(changes_path, 'w') as f:
            f.write(f"SSIM Score: {self.results['ssim_score']:.4f}\n")
            f.write(f"Number of Changes: {len(changes)}\n\n")
            
            for change in changes:
                f.write(f"Change #{change['id']}:\n")
                f.write(f"  Type: {change['type']}\n")
                f.write(f"  Location: (x={change['location']['x']}, y={change['location']['y']}, " +
                        f"w={change['location']['width']}, h={change['location']['height']})\n")
                f.write(f"  Estimated Rack Unit: {change['location']['estimated_ru']}\n")
                f.write(f"  Confidence: {change['confidence']:.2f}\n")
                
                if change['extracted_text']:
                    f.write(f"  Extracted Text: {change['extracted_text']}\n")
                
                f.write("\n")
        
        # Create a JSON file with the change details for AMS integration
        json_path = os.path.join(session_dir, "changes.json")
        with open(json_path, 'w') as f:
            json.dump(changes, f, indent=2)
        
        # Create a metadata file
        metadata = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'ssim_score': self.results['ssim_score'],
            'num_changes': len(changes),
            'changes': changes
        }
        
        metadata_path = os.path.join(session_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'session_id': session_id,
            'comparison': comparison_path,
            'visual_diff': visual_diff_path,
            'mask': mask_path,
            'changes_txt': changes_path,
            'changes_json': json_path,
            'metadata': metadata_path,
            'changes': changes
        }
    
    def get_web_paths(self, session_id):
        """
        Get web-accessible paths for the results.
        
        Args:
            session_id (str): Session ID for the results
            
        Returns:
            dict: Web paths to the result files
        """
        return {
            'comparison': f"/results/{session_id}/comparison.png",
            'visual_diff': f"/results/{session_id}/visual_diff.png",
            'mask': f"/results/{session_id}/mask.png",
            'changes_json': f"/results/{session_id}/changes.json",
            'metadata': f"/results/{session_id}/metadata.json"
        }
