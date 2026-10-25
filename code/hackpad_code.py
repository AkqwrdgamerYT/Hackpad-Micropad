import time

import board
import digitalio
import usb_hid
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS


# Connect each two-pin switch between its pin and GND.
# Connect the rotary encoder's CLK, DT, and SW pins to D7, D8, and D9;
# connect its common pin to GND.
SWITCH_PINS = (board.D1, board.D2, board.D3, board.D4, board.D5, board.D6)
ENCODER_A_PIN = board.D7
ENCODER_B_PIN = board.D8
ENCODER_SWITCH_PIN = board.D9

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer = ConsumerControl(usb_hid.devices)

encoder_a = digitalio.DigitalInOut(ENCODER_A_PIN)
encoder_a.direction = digitalio.Direction.INPUT
encoder_a.pull = digitalio.Pull.UP

encoder_b = digitalio.DigitalInOut(ENCODER_B_PIN)
encoder_b.direction = digitalio.Direction.INPUT
encoder_b.pull = digitalio.Pull.UP

encoder_switch = digitalio.DigitalInOut(ENCODER_SWITCH_PIN)
encoder_switch.direction = digitalio.Direction.INPUT
encoder_switch.pull = digitalio.Pull.UP


def open_from_start_menu(search_text):
	# Windows Start search finds installed desktop apps such as Discord and Opera.
	keyboard.send(Keycode.WINDOWS)
	time.sleep(0.4)
	layout.write(search_text)
	time.sleep(0.6)
	keyboard.send(Keycode.ENTER)


def open_youtube():
	# Use Windows Run so the URL opens in the computer's default browser.
	keyboard.send(Keycode.WINDOWS, Keycode.R)
	time.sleep(0.4)
	layout.write("https://www.youtube.com")
	keyboard.send(Keycode.ENTER)


switches = []
for pin in SWITCH_PINS:
	switch = digitalio.DigitalInOut(pin)
	switch.direction = digitalio.Direction.INPUT
	switch.pull = digitalio.Pull.UP
	switches.append(switch)

previous_pressed = [False] * len(switches)
previous_encoder_state = (int(encoder_a.value) << 1) | int(encoder_b.value)
encoder_steps = 0
encoder_button_candidate = encoder_switch.value
encoder_button_pressed = encoder_button_candidate
encoder_button_changed_at = time.monotonic()

ENCODER_TRANSITIONS = (
	(0, 1, -1, 0),
	(-1, 0, 0, 1),
	(1, 0, 0, -1),
	(0, -1, 1, 0),
)
ENCODER_DEBOUNCE = 0.03

while True:
	# Internal pull-ups make a pressed switch read as False.
	for index, switch in enumerate(switches):
		pressed = not switch.value
		if pressed and not previous_pressed[index]:
			if index == 0:
				open_from_start_menu("Discord")
			elif index == 1:
				open_youtube()
			elif index == 2:
				open_from_start_menu("Opera")
			elif index == 3:
				open_from_start_menu("Opera GX")
			elif index == 4:
				consumer.send(ConsumerControlCode.SCAN_NEXT_TRACK)
			else:
				consumer.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
		previous_pressed[index] = pressed

	# Decode the rotary encoder's quadrature signal; one detent is four transitions.
	encoder_state = (int(encoder_a.value) << 1) | int(encoder_b.value)
	encoder_steps += ENCODER_TRANSITIONS[previous_encoder_state][encoder_state]
	previous_encoder_state = encoder_state
	if encoder_steps >= 4:
		consumer.send(ConsumerControlCode.VOLUME_INCREMENT)
		encoder_steps = 0
	elif encoder_steps <= -4:
		consumer.send(ConsumerControlCode.VOLUME_DECREMENT)
		encoder_steps = 0

	# Debounce the encoder's push switch and send media play/pause on press.
	now = time.monotonic()
	raw_button_state = encoder_switch.value
	if raw_button_state != encoder_button_candidate:
		encoder_button_candidate = raw_button_state
		encoder_button_changed_at = now
	elif (raw_button_state != encoder_button_pressed
			and now - encoder_button_changed_at >= ENCODER_DEBOUNCE):
		encoder_button_pressed = raw_button_state
		if not encoder_button_pressed:
			consumer.send(ConsumerControlCode.PLAY_PAUSE)

	time.sleep(0.01)
