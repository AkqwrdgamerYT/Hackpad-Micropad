import os
import re
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk


APP_SHORTCUTS = {
	"Discord": ("Discord",),
	"Opera": ("Opera", "Opera Browser"),
	"Opera GX": ("Opera GX", "Opera GX Browser"),
}


def find_start_menu_shortcut(app_names):
	"""Find an installed app's shortcut in the Windows Start Menu."""
	roots = tuple(
		Path(os.environ[environment_variable])
		/ "Microsoft" / "Windows" / "Start Menu" / "Programs"
		for environment_variable in ("APPDATA", "PROGRAMDATA")
		if environment_variable in os.environ
	)
	normalized_names = {
		re.sub(r"[^a-z0-9]", "", name.casefold())
		for name in app_names
	}

	for root in roots:
		if not root.is_dir():
			continue
		for shortcut in root.rglob("*.lnk"):
			normalized_stem = re.sub(r"[^a-z0-9]", "", shortcut.stem.casefold())
			if normalized_stem in normalized_names:
				return shortcut
	return None


def launch_app(app_name, shortcut_names):
	shortcut = find_start_menu_shortcut(shortcut_names)
	if shortcut is None:
		raise FileNotFoundError(
			f"Could not find {app_name} in the Windows Start Menu. "
			"Make sure it is installed and has a Start Menu shortcut."
		)
	os.startfile(str(shortcut))


class MacropadApp:
	def __init__(self, root):
		self.root = root
		root.title("Macropad")
		root.geometry("380x390")
		root.resizable(False, False)

		style = ttk.Style(root)
		style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
		style.configure("Action.TButton", font=("Segoe UI", 12), padding=12)

		container = ttk.Frame(root, padding=24)
		container.pack(fill="both", expand=True)

		ttk.Label(container, text="Macropad", style="Title.TLabel").pack(pady=(4, 4))
		ttk.Label(container, text="Open an app or website").pack(pady=(0, 18))

		actions = (
			("Discord", lambda: launch_app("Discord", APP_SHORTCUTS["Discord"])),
			("YouTube", self.open_youtube),
			("Opera", lambda: launch_app("Opera", APP_SHORTCUTS["Opera"])),
			("Opera GX", lambda: launch_app("Opera GX", APP_SHORTCUTS["Opera GX"])),
		)
		for label, action in actions:
			ttk.Button(
				container,
				text=label,
				style="Action.TButton",
				command=lambda name=label, callback=action: self.run_action(name, callback),
			).pack(fill="x", pady=5)

		self.status = ttk.Label(container, text="Ready", anchor="center")
		self.status.pack(fill="x", pady=(14, 0))

	def run_action(self, name, action):
		try:
			action()
		except OSError as error:
			self.status.configure(text=f"Couldn't open {name}")
			messagebox.showerror(f"Couldn't open {name}", str(error), parent=self.root)
		else:
			self.status.configure(text=f"Opened {name}")

	def open_youtube(self):
		if not webbrowser.open("https://www.youtube.com"):
			raise OSError("Windows could not open YouTube in the default browser.")


if __name__ == "__main__":
	window = tk.Tk()
	MacropadApp(window)
	window.mainloop()
