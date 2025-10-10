File : reply_telegram.py
Method: _parse_module_output_state_value

Actual
"data_value": {
  "raw": "xxxx0000",
  "parsed": null
},

Expected
"data_value": {
  "raw": "xxxx0000",
  "parsed": {
    "output" : [
        "00": False,
        "01": True,
        "02": True,
        "03": True
    ]
  }
},

Case : xxxx1110
Output :
[
    "00": False,
    "01": True,
    "02": True,
    "03": True
]

Case : xxxx0001
Output :
[
    "00": True,
    "01": False,
    "02": False,
    "03": False
]

Example:

def _parse_voltage_value(self) -> dict:
    """Parse voltage value like '+12,5§V'"""
    try:
        # Remove unit indicator (§V)
        value_part = self.data_value.replace("§V", "")
        # Replace comma with dot for decimal
        value_str = value_part.replace(",", ".")
        voltage = float(value_str)

        return {
            "value": voltage,
            "unit": "V",
            "formatted": f"{voltage:.1f}V",
            "raw_value": self.data_value,
            "parsed": True,
        }
    except (ValueError, AttributeError):
        return {
            "raw_value": self.data_value,
            "parsed": False,
            "error": "Failed to parse voltage",
        }
