# AI Servo Optimization Platform

A PyQt-based platform for servo system parameter identification and optimization, integrated with MATLAB/Simulink workflows.

This project provides a graphical interface for engineers to perform system identification and optimization of servo control systems using advanced algorithms such as PSO and GA.

---

## 🚀 Features

- PyQt5-based graphical user interface (GUI)
- MATLAB Engine integration for simulation
- Parameter identification module
- Optimization algorithms (PSO, GA, etc.)
- Multi-tab interface (Login, Optimization, Schneider control)

---

## 🧠 Architecture

- **Frontend**: PyQt GUI  
- **Backend**: Python + MATLAB Engine  
- **Simulation**: Simulink models  

---

## 📂 Project Structure

```text
ai-servo-optimization-platform/
├─ src/                  # PyQt GUI and core logic
├─ matlab_scripts/       # MATLAB and Simulink scripts
│  ├─ identification/
│  └─ optimization/
├─ README.md
├─ requirements.txt
└─ .gitignore
```

---

## ⚙️ Requirements

- Python 3.9+
- PyQt5
- numpy
- MATLAB (with Engine API for Python)

---

## ▶️ How to Run

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Start MATLAB engine


3. Run the application:
```
python src/login.py
```

---

## 📌 Notes

MATLAB must be installed and configured properly

Simulink models are required for simulation tasks

---

## 🔧 MATLAB Engine Setup

Install MATLAB Engine manually:
```
cd "MATLAB_ROOT/extern/engines/python"
python setup.py install
```