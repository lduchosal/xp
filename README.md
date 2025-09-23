# 🔌 XP Protocol Communication Tool

> **A powerful Python CLI and API toolkit for CONSON XP Protocol operations**

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
FastAPI REST endpoints and comprehensive type safety

---

## 🚀 Quick Start

```bash
# Install with PIP (recommended)
pip install conson-xp

# Parse a telegram
xp telegram parse "<E14L00I02MAK>"

# Discover XP servers on your network
xp conbus discover

# Start the REST API server
xp api start
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

pdm install -G dev

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
xp conbus scan <host> <port>

# Control device outputs
xp conbus output <host> <port> <module_id> <datapoint> <value>

# Blink device for identification
xp conbus blink <host> <port> <module_id> <datapoint>
```

**Module Information**
```bash
# Get module details
xp module info 14
xp module search "push button"

# List available modules
xp module list --group-by-category
```

### 🔧 Advanced Features

<details>
<summary><b>Real-time Operations</b></summary>

```bash
# Listen for real-time telegrams
xp conbus receive <host> <port>

# Send custom telegrams
xp conbus custom <host> <port> <telegram>

# Read/write datapoints
xp conbus datapoint read <host> <port> <module_id> <datapoint>
xp conbus datapoint write <host> <port> <module_id> <datapoint> <value>
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

<details>
<summary><b>File Processing</b></summary>

```bash
# Process telegram files
xp file parse telegrams.txt
xp file extract-telegrams mixed-data.txt
```
</details>

### 🌐 API & Integration

**REST API Server**
```bash
# Start API server with interactive docs at /docs
xp api start
```

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
CLI Layer → API Layer → Services → Models → Connection Layer
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
├── api/           # FastAPI REST endpoints
├── cli/           # Command-line interface
├── models/        # Core data models
├── services/      # Business logic
└── utils/         # Utility functions
```
</details>

**Requirements**: Python 3.10+ • FastAPI • Pydantic • Click • HAP-python

## License

MIT License - see LICENSE file for details.

## Notice

This software is developed for **interoperability purposes only** under fair use provisions and EU Software Directive Article 6. See NOTICE.md for full details on intellectual property compliance.