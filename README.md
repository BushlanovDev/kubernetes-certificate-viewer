<div align="center">
<h1>☸ Kubernetes Certificate Viewer</h1>
<p>Cross-platform desktop application for monitoring the status of kubernetes certificates</p>

[![Actions status](https://github.com/BushlanovDev/kubernetes-certificate-viewer/actions/workflows/check.yml/badge.svg)](https://github.com/BushlanovDev/kubernetes-certificate-viewer/actions)
[![Python](https://img.shields.io/badge/Python-3.12%2B-brightgreen)](https://www.python.org/downloads/)
[![PyQt](https://img.shields.io/badge/PyQt-5.15.11-brightgreen)](https://pypi.org/project/PyQt5/)
[![Platform Win32 | Linux | macOS](https://img.shields.io/badge/Platform-Win32%20|%20Linux%20|%20macOS-brightgreen)]()
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT)
</div>

## 🌟 Description

A simple desktop console utility for monitoring current Kubernetes cluster certificates.
<div align="center">
  <img src="https://github.com/BushlanovDev/kubernetes-certificate-viewer/blob/main/resources/screenshot.png?raw=true" alt="Kubernetes Certificate Viewer" width="800" />
</div>

## 🚀 Quick Start

Download the executable file for your platform from
the [release page](https://github.com/BushlanovDev/kubernetes-certificate-viewer/releases) and enjoy =)

## 💻 Run from source code

```bash
# Clone project 
git clone https://github.com/BushlanovDev/kubernetes-certificate-viewer.git

# Create and activate virtual venv 
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run app
python main.py

# Run app with parameters
python main.py --path=/home/user/.kube --days=3
```

## 🛠️ Building an executable file

```bash
pip install pyinstaller # or pip install auto-py-to-exe for use gui

pyinstaller --noconfirm --onedir --windowed --icon "./resources/icon32.ico" --hidden-import "zeroconf._utils.ipaddress" --hidden-import "zeroconf._handlers.answers"  "./main.py"
```

## 📄 License

This repository's source code is available under the [MIT License](LICENSE).
