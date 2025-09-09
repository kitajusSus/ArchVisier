import sys
import os

# Ensure local imports work
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # type: ignore
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.append(base_path)
from training_engine import run_training_pipeline


def log(message: str) -> None:
    """Simple stdout logger used by the training worker."""
    print(message, flush=True)


def main() -> int:
    """Entry point for launching the training pipeline as a subprocess."""
    if len(sys.argv) < 3:
        print("Brak wymaganych argumentów", flush=True)
        return 1
    data_folder = sys.argv[1]
    output_model_dir = sys.argv[2]
    success = run_training_pipeline(data_folder, output_model_dir, log)
    print("RESULT:SUCCESS" if success else "RESULT:FAIL", flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

