# Steps based on the Nvidia documentation
#pip install cuda-python
#cuda toolkit 12.5: https://developer.download.nvidia.com/compute/cuda/12.5.0/local_installers/cuda_12.5.0_555.85_windows.exe
#python3 -m pip install --upgrade pip
#python3 -m pip install wheel
#python3 -m pip install --upgrade tensorrt

import os
import sys
import subprocess
import time
import os.path

error_occurred = False
error_count = 0

def err(message):
    global error_occurred
    global error_count
    error_count += 1
    error_occurred = True
    file = open('output.txt', 'a')
    file.write(message + '\n')
    file.close()
    print(message)

def restart_cmd():
    os.system('py main.py --bat-launch')
    print('restarting command prompt...')
    quit()

if "--bat-launch" not in sys.argv:
    print('Please run the script using start.bat')
    sys.exit(1)

restart = False

try:
    import cuda
except:
    print('Installing cuda-python module')
    os.system('pip install cuda-python')
    restart = True

try:
    import requests
except:
    print('Installing requests module')
    os.system('pip install requests')
    restart = True

try:
    from tqdm import tqdm
except:
    os.system('pip install tqdm')
    restart = True

if restart:
    restart_cmd()


def check_python_version(target_version="3.10.5"):
    current_version = ".".join(map(str, sys.version_info[:3]))
    if current_version != target_version:
        err(f"ERROR: Expected Python {target_version}, but found Python {current_version}.")
        return False
    print(f"Python {target_version} detected.")
    return True

def isCudaInstalled(target_version="12.6"):
    try:
        result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True, check=True)
        if f"release {target_version}" in result.stdout:
            print(f"CUDA {target_version} is already installed.")
            return True
        else:
            print(f"CUDA version found, but not {target_version}. Installing CUDA {target_version}...")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("CUDA is not installed. Installing CUDA 12.6...")
        return False

def installCudaToolkit():
    global restart
    print('Downloading Cuda Toolkit...')
    f = open("output.txt", "w")
    download_link = 'https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe' # 'https://developer.download.nvidia.com/compute/cuda/12.5.0/local_installers/cuda_12.5.0_555.85_windows.exe'
    file_path = 'cuda_12.6.0_560.76_windows.exe' #"cuda_12.5.0_555.85_windows.exe"

    
    try:
        response = requests.get(download_link, stream=True, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        err(f"Failed to download CUDA Toolkit: {e}")
        return
    
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            progress_bar.update(len(chunk))
            if chunk:
                file.write(chunk)
                
    progress_bar.close()

    print(f'Cuda Toolkit downloaded. Attempting to install..')
    f.write('Cuda Tooklkit downloaded')

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        err('Error downloading file.')
        return
    
    try:
        subprocess.run([file_path, '/silent', '/noreboot'], check=True)
        print('Cuda Toolkit installed')
        f.write('Cuda Toolkit installed successfully')

        restart = True
    except subprocess.CalledProcessError as e:
        f.write(f'Failed to install Cuda Toolkit due to: {e}')
        err(f'Failed to install Cuda Toolkit due to: {e}')


if not check_python_version("3.10.5"):
    err('You do not have Python 3.10.5, which is the only supported version. https://www.python.org/ftp/python/3.10.5/python-3.10.5-amd64.exe')
else:
    if not isCudaInstalled():
        installCudaToolkit()

try:
    command = '''
    Get-AppExecutionAlias | Where-Object { $_.PackageFamilyName -like "*Python*" } | ForEach-Object { Disable-AppExecutionAlias -PackageFamilyName $_.PackageFamilyName -Executable $_.Executable }
    '''

    subprocess.run(["powershell", "-Command", command], shell=True)
except:
    err('Failed to disable python app execution aliases')

if restart:
    restart_cmd()

try:
    print('Updating pip...')
    os.system('python -m pip install --upgrade pip')
except:
    err('Failed to upgrade pip')

try:
    print('Installing Python wheel...')
    os.system('python -m pip install wheel')
except:
    err('Failed to install Python wheel')

try:
    print('Uinstalling possible torch versions...')
    os.system('pip uninstall -y torch torchvision torchaudio')
except:
    err('Failed to uninstall torch')

try:
    print('Installing torch. This may take some time..')
    os.system('pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126 --timeout=0')
except:
    err('Failed to install torch')

try:
    print('Installing TensorRT Python wheel...')
    os.system('python -m pip install --upgrade tensorrt')
except:
    err('Failed to install TensorRT Python wheel')

try:
    print('Installing TensorRT...')
    os.system('pip install tensorrt')
except:
    err('Failed to install TensorRT')

try:
    print('Installing Lunar Requirements...')
    os.system('pip install -r requirements.txt --no-cache-dir')
except:
    err('Failed to install requirements')

if not error_occurred:
    print('done!')
else:
    print(f'Atleast {error_count} errors occurred.')

time.sleep(5)
quit()