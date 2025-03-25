import os
import sys
import subprocess
import time
from pathlib import Path

ERROR_LOG = Path("output.txt")
RESTARTED = "--restarted" in sys.argv
RESTART = False
ERROR_COUNT = 0


def log_error(message):
    global ERROR_COUNT
    ERROR_COUNT += 1
    with ERROR_LOG.open("a") as f:
        f.write(message + "\n")
    print(message)

def restart_script():
    print("Restarting script...")
    subprocess.Popen(["start", "", "py", "main.py", "--bat-launch", "--restarted"], shell=True)
    sys.exit()

def check_and_install(package):
    global RESTART
    try:
        __import__(package)
    except ImportError:
        print(f"Installing missing module: {package}")
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        RESTART = True

def ensure_required_modules():
    for module in ["cuda", "requests", "tqdm", "tkinter"]:
        check_and_install(module)

def check_python_version(expected="3.10.5"):
    actual = ".".join(map(str, sys.version_info[:3]))
    if actual != expected:
        log_error(f"ERROR: Expected Python {expected}, but found Python {actual}.")
        return False
    print(f"Python {expected} detected.")
    return True

def is_cuda_installed(required_version="12.6"):
    installed_versions = []
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    cuda_root = Path(program_files) / "NVIDIA GPU Computing Toolkit" / "CUDA"
    
    if cuda_root.exists():
        for subdir in cuda_root.iterdir():
            if subdir.name.startswith("v"):
                version = subdir.name.lstrip("v")
                installed_versions.append(version)

    if required_version in installed_versions:
        print(f"CUDA {required_version} is installed (among: {', '.join(installed_versions)}).")
        return True
    else:
        print(f"CUDA {required_version} not found. Installed versions: {', '.join(installed_versions) or 'None'}")
        return False

def install_cuda():
    global RESTART
    cuda_url = "https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe"
    installer = Path("cuda_12.6.0_560.76_windows.exe")

    if installer.exists():
        print("CUDA installer already exists. Skipping download.")
    else:
        print("Downloading CUDA Toolkit...")
        try:
            import requests
            from tqdm import tqdm
            response = requests.get(cuda_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            bar = tqdm(total=total_size, unit="iB", unit_scale=True)

            with installer.open("wb") as f:
                for chunk in response.iter_content(1024):
                    bar.update(len(chunk))
                    f.write(chunk)
            bar.close()

            if total_size != 0 and bar.n != total_size:
                log_error("Incomplete CUDA download.")
                return

        except Exception as e:
            log_error(f"CUDA download failed: {e}")
            return

    try:
        print("Installing CUDA Toolkit...")
        subprocess.run([str(installer), "/silent", "/noreboot"], check=True)
        print("CUDA Toolkit installed.")
        RESTART = True
    except subprocess.CalledProcessError as e:
        log_error(f"CUDA installation failed: {e}")

def convert_model():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select YOLO model", filetypes=[("YOLO Model Files", "*.pt;*.onnx")])

    if not path:
        log_error("No model selected.")
        return

    ext = Path(path).suffix
    if ext not in [".pt", ".onnx"]:
        log_error("Invalid model format. Only .pt and .onnx are supported.")
        return

    try:
        print("Converting model to TensorRT engine...")
        subprocess.run(["yolo", "export", f"model={path}", "format=engine", "imgsz=640"], check=True)
        print("Model conversion successful!")
    except subprocess.CalledProcessError:
        log_error("Model conversion failed.")

def try_disable_execution_aliases():
    try:
        subprocess.run([
            "powershell",
            "-Command",
            "Get-Command Disable-AppExecutionAlias"
        ], capture_output=True, check=True)
        
        subprocess.run([
            "powershell", "-Command",
            "Get-AppExecutionAlias | Where-Object { $_.PackageFamilyName -like '*Python*' } | " +
            "ForEach-Object { Disable-AppExecutionAlias -PackageFamilyName $_.PackageFamilyName -Executable $_.Executable }"
        ], shell=True)
        print("Disabled Python App Execution Aliases.")
    except subprocess.CalledProcessError:
        print("Could not disable App Execution Aliases (not supported on this system). Skipping.")

def main():
    global RESTART

    if "--bat-launch" not in sys.argv:
        print("Please launch the script via start.bat")
        sys.exit(1)

    ensure_required_modules()

    if RESTART and not RESTARTED:
        restart_script()

    if not check_python_version("3.10.5"):
        log_error("Only Python 3.10.5 is supported.")
        print("Download: https://www.python.org/ftp/python/3.10.5/python-3.10.5-amd64.exe")
        return

    if not is_cuda_installed("12.6"):
        install_cuda()

    if RESTART and not RESTARTED:
        restart_script()

    try_disable_execution_aliases()

    tools = [
        ["pip", "install", "--upgrade", "pip"],
        ["pip", "install", "wheel"],
        ["pip", "uninstall", "-y", "torch", "torchvision", "torchaudio"],
        ["pip", "install", "torch", "torchvision", "torchaudio", "--index-url=https://download.pytorch.org/whl/cu126"],
        ["pip", "install", "--upgrade", "tensorrt"],
        ["pip", "install", "-r", "requirements.txt", "--no-cache-dir"],
    ]

    for command in tools:
        try:
            print(f"Running: {' '.join(command)}")
            subprocess.run([sys.executable, "-m"] + command, check=True)
        except subprocess.CalledProcessError:
            log_error(f"Failed to run: {' '.join(command)}")

    choice = input("Convert your model to TensorRT engine format? (y/n): ").strip().lower()
    if choice == 'y':
        convert_model()
    else:
        print("Skipping model conversion.")

    if ERROR_COUNT == 0:
        print("All steps completed successfully!")
    else:
        print(f"{ERROR_COUNT} error(s) occurred. See {ERROR_LOG} for details.")

    time.sleep(5)

if __name__ == "__main__":
    main()
