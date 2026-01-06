import pyautogui
import keyboard

speed = 20

while True:
    if keyboard.is_pressed('up'):
        pyautogui.move(0, -speed)
    elif keyboard.is_pressed('down'):
        pyautogui.move(0, speed)
    elif keyboard.is_pressed('left'):
        pyautogui.move(-speed, 0)
    elif keyboard.is_pressed('right'):
        pyautogui.move(speed, 0)
    elif keyboard.is_pressed('space'):
        pyautogui.click()
    elif keyboard.is_pressed('esc'):
        break