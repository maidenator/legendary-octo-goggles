import cv2
import numpy as np
import os

def create_test_image(filename="test_image.jpg", text="ABCD1234567"):
    # Create white image
    height = 400
    width = 800
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    # Center the text approximately
    text_size = cv2.getTextSize(text, font, 2, 3)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    
    cv2.putText(img, text, (text_x, text_y), font, 2, (0, 0, 0), 3, cv2.LINE_AA)
    
    # Save
    cv2.imwrite(filename, img)
    print(f"Created {filename}")

if __name__ == "__main__":
    create_test_image()
