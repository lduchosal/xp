# 🔌 XP Protocol Communication Tool

[![PyPI version](https://badge.fury.io/py/conson-xp.svg)](https://badge.fury.io/py/conson-xp)
[![Python package](https://github.com/lduchosal/xp/actions/workflows/python-package.yml/badge.svg)](https://github.com/lduchosal/xp/actions/workflows/python-package.yml)
[![codecov](https://codecov.io/gh/lduchosal/xp/branch/main/graph/badge.svg)](https://codecov.io/gh/lduchosal/xp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

> **A powerful Python CLI toolkit for CONSON XP Protocol operations**

Control and communicate with XP devices through console bus (Conbus), parse telegrams in real-time, and integrate with smart home systems like Apple HomeKit.

---

## ✨ Key Features

🚀 **Real-time Communication**
Connect directly to XP130/XP230 servers with bidirectional TCP communication

📡 **Smart Telegram Processing**
Parse and validate event, system, and reply telegrams with built-in checksum verification

🏠 **HomeKit Integration**
Bridge XP devices to Apple HomeKit for seamless smart home control

🔍 **Device Discovery**
Automatically discover XP servers and scan connected modules on your network

⚡ **Modern Architecture**
Comprehensive type safety and robust error handling

---

## 🚀 Quick Start

```bash
# Install with PIP (recommended)
pip install conson-xp

# Parse a telegram
xp telegram parse "<E14L00I02MAK>"

# Discover XP servers on your network
xp conbus discover
```

## 📦 Installation

### Using PIP (Recommended)
```bash
pip install conson-xp
```

### Development Installation
```bash
# Using PDM

git clone <repository-url>

pip install pdm

pdm install -G scripts

```

## 📚 Usage

### 🎯 Core Operations

**Telegram Processing**
```bash
# Parse any telegram (auto-detect type)
xp telegram parse "<E14L00I02MAK>"
xp telegram parse "<S0020012521F02D18FN>"
xp telegram parse "<R0020012521F02D18+26,0§CIL>"

# Validate telegram integrity
xp telegram validate "<E14L00I02MAK>"
```

**Device Communication**
```bash
# Discover XP servers on your network
xp conbus discover

# Connect and scan for modules
xp conbus scan <serial_number> <function_code>
xp conbus scan 0123450001 02

# Control device outputs
xp conbus output <action> <serial_number> <ouput_number>
xp conbus output off 0123450001 00
xp conbus output on 0123450001 01
xp conbus output status 0123450001

# Blink device for identification
xp conbus blink <action> <serial_number>
xp conbus blink on 0123450001
xp conbus blink all on
xp conbus blink all off
```

**Module Information**
```bash
# Get module details
xp module info 14
xp module search "push button"

# List available modules
xp module list --group-by-category
```

### 🖥️ Terminal UI (TUI)

**Real-time Protocol Monitor**

Launch an interactive terminal interface for live protocol monitoring and control:

```bash
# Start the protocol monitor TUI
xp term protocol
```

**Features:**
- 📊 **Live Telegram Stream**: Real-time RX/TX telegram monitoring from Conbus server
- ⌨️ **Keyboard Shortcuts**: Quick access controls for common operations
  - `Q` - Quit application
  - `C` - Toggle connection (connect/disconnect)
  - `R` - Reset and clear log
  - `0-9, a-q` - Send predefined protocol telegrams
- 🎨 **Visual Status Indicators**: Color-coded connection states
  - 🟢 Green - Connected
  - 🟡 Yellow - Connecting/Disconnecting
  - 🔴 Red - Failed
  - ⚪ White - Disconnected
- 📝 **Interactive Display**: Scrollable telegram log with detailed parsing information

The TUI provides a convenient way to monitor and interact with XP devices without juggling multiple terminal commands.

### 🔧 Advanced Features

<details>
<summary><b>Real-time Operations</b></summary>

```bash
# Listen for event telegrams
xp conbus receive

# Send custom telegrams
xp conbus custom <serial_number> <function_code> <action_code>
xp conbus custom 01234500001 02 02

# Read/write datapoints
xp conbus datapoint <datapoint> <serial_number>
xp conbus datapoint hw_version 01234500001
xp conbus datapoint auto_report_status 01234500001
xp conbus datapoint voltage 01234500001
 ```
</details>

<details>
<summary><b>Checksum Operations</b></summary>

```bash
# Calculate and validate checksums
xp checksum calculate "E14L00I02M"
xp checksum validate "E14L00I02M" "AK"
xp checksum calculate "E14L00I02M" --algorithm crc32
```
</details>

### 🌐 Integration

**HomeKit Smart Home Bridge**
```bash
# Set up HomeKit integration
xp homekit config validate
xp homekit start
```

<details>
<summary><b>Module emulators</b></summary>

```bash
# Start XP protocol servers
xp server start
xp reverse-proxy start
```
</details>

---

## 🏗️ Architecture

**Layered Design**
```
CLI Layer → Services → Models → Connection Layer
```

**Key Components**: Telegram processing • Real-time Conbus communication • HomeKit bridge • Multiple XP server support • Configuration management

---

## 🛠️ Development

**Quick Development Setup**
```bash
# Run tests with coverage
pdm run test

# Code quality checks
pdm run lint && pdm run format && pdm run typecheck

# All quality checks at once
pdm run check
```

<details>
<summary><b>Project Structure</b></summary>

```
src/xp/
├── cli/           # Command-line interface
├── models/        # Core data models
├── services/      # Business logic
└── utils/         # Utility functions
```
</details>

<details>
<summary><b>Functionalities</b></summary>

```
<!-- BEGIN CLI HELP -->

xp

xp conbus

xp conbus actiontable
xp conbus actiontable download
xp conbus actiontable list
xp conbus actiontable show
xp conbus actiontable upload


xp conbus autoreport
xp conbus autoreport get
xp conbus autoreport set


xp conbus blink

xp conbus blink all
xp conbus blink all off
xp conbus blink all on

xp conbus blink off
xp conbus blink on

xp conbus config
xp conbus custom

xp conbus datapoint
xp conbus datapoint all
xp conbus datapoint query

xp conbus discover

xp conbus event
xp conbus event list
xp conbus event raw


xp conbus lightlevel
xp conbus lightlevel get
xp conbus lightlevel off
xp conbus lightlevel on
xp conbus lightlevel set


xp conbus linknumber
xp conbus linknumber get
xp conbus linknumber set


xp conbus modulenumber
xp conbus modulenumber get
xp conbus modulenumber set


xp conbus msactiontable
xp conbus msactiontable download


xp conbus output
xp conbus output off
xp conbus output on
xp conbus output state
xp conbus output status

xp conbus raw
xp conbus receive
xp conbus scan


xp file
xp file analyze
xp file decode
xp file validate

xp help

xp homekit

xp homekit config
xp homekit config show
xp homekit config validate

xp homekit start


xp module
xp module categories
xp module info
xp module list
xp module search


xp rp
xp rp start
xp rp status
xp rp stop


xp server
xp server start
xp server status
xp server stop


xp telegram

xp telegram blink
xp telegram blink off
xp telegram blink on


xp telegram checksum
xp telegram checksum calculate
xp telegram checksum validate

xp telegram discover

xp telegram linknumber
xp telegram linknumber read
xp telegram linknumber write

xp telegram parse
xp telegram validate
xp telegram version


xp term
xp term protocol

<!-- END CLI HELP -->
```
</details>

**Requirements**: Python 3.10+ • Pydantic • Click • HAP-python

## License

MIT License - see LICENSE file for details.

## Notice

This software is developed for **interoperability purposes only** under fair use provisions and EU Software Directive Article 6. See NOTICE.md for full details on intellectual property compliance.