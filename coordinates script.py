import pyautogui

print("Move the mouse to the top-left corner of the region and press Enter.")
input()  # Wait for user to press Enter
x, y = pyautogui.position()
print(f"Top-left corner: ({x}, {y})")

print("Move the mouse to the bottom-right corner of the region and press Enter.")
input()  # Wait for user to press Enter
x2, y2 = pyautogui.position()
print(f"Bottom-right corner: ({x2}, {y2})")

width = x2 - x
height = y2 - y
print(f"Region: (x={x}, y={y}, width={width}, height={height})")
