"""DETOPlus Invoice Renamer — Application entry point.

Launches the Tkinter GUI for the PDF Watcher.
For headless/CI use: import from detoplus.invoice_renamer directly.
"""

import sys
import os

# Ensure src/ is on the path when run as __main__
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))


def main():
    """Entry point — launches the GUI."""
    from detoplus.invoice_renamer.ui.app import PDFWatcherApp

    app = PDFWatcherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
