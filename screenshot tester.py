import pyautogui
from PIL import Image

def capture_screenshot(region):
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save('test_screenshot.png')
    print("Screenshot saved as 'test_screenshot.png'")

def main():
    
    #(x=1303, y=564, width=194, height=272)
    region = (1303, 564 ,194 ,272 )
    capture_screenshot(region)

if __name__ == "__main__":
    main()