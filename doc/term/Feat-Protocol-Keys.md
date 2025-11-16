# Protocol Monitor - Protocol Keys

| Key | Command      | Telegram                  |
|-----|--------------|---------------------------|
| 1   | Discover     | `S0000000000F01D00`       |
| 2   | Error Code   | `S0020044966F02D10`       |
| 3   | Module Type  | `S0020044966F02D00`       |
| 4   | Auto Report  | `S0020044966F02D21`       |
| 5   | Link Number  | `S0020044966F02D04`       |
| 6   | Blink On     | `S0020044966F01D01`       |
| 7   | Blink Off    | `S0020044966F01D00`       |
| 8   | Output 1 On  | `S0020044966F02101`       |
| 9   | Output 1 Off | `S0020044966F02100`       |
| 0   | Output State | `S0020044966F02D09`       |
| a   | Module State | `S0020044966F02D09`       |
| b   | All Off      | `E02L00I00M` `E02L00I00B` |
| c   | All On       | `E02L00I08M` `E02L00I08B` |
| d   |              | ``                        |
| e   |              | ``                        |
| f   |              | ``                        |
| g   |              | ``                        |

## Config file

File: protocol.yml
```
protocol:
    "1":
        name: "Discover"
        telegrams:
            - S0000000000F01D0
    
    "2":
        name: "Error Code"
        telegrams:
            - S0020044966F02D10
    
    "b":
        name: "All Off"
        telegrams:
            - E02L00I00M
            - E02L00I00B
```