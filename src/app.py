"""Web application launcher."""

import subprocess
from pathlib import Path


def launch():
    """Launch the Streamlit web interface."""
    app_path = Path(__file__).parent / "web" / "streamlit_app.py"
    subprocess.run(["streamlit", "run", str(app_path)], check=True)


if __name__ == "__main__":
    launch()
