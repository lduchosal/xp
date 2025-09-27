# Download XP24 Ms Action Table

XP module's action can be programme into the module flash memory

## cli

xp conbus msactiontable download <serial_number> [decode (default true)]

### output

Decoded msactiontable 

```
IN_1_COMMAND = TOGGLE;
IN_2_COMMAND = TOGGLE;
IN_3_COMMAND = TOGGLE;
IN_4_COMMAND = TOGGLE;
MUTUALX_12 = NO;
MUTUALX_34 = NO;
MUTUAL_DEADTIME = 300;
CURTAIN_12 = NO;
CURTAIN_34 = NO;
```

Encoded msactiontable

```
AAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
```

## Protocol

[TX] <S0123450001F13D00FK> DOWNLOAD MS ACTION TABLE
[RX] <R0123450001F18DFA> ACK
[RX] <R0123450001F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD> TABLE
[TX] <S0123450001F18D00FB> CONTINUE
[RX] <R0123450001F16DFO> EOF

## pseudo code implementation

class Xp24ActionTable(XPActionTable)
{
    MS300: int = 12
    MS500: int = 20
    AT_MAX_ROWS: int  = 4

    functions: list[ModuleFunction]
    parameters: list[ModuleParameter]
    mutex12: bool = false
    mutex34: bool = false
    lamella12: bool = false
    lamella34: bool = false
    ms: int 

  def generateMSTableTelegrams(String serial) -> list[str]{
    Vector<String> telegrams = new Vector();
    Checksum cc = new Checksum();
    
    String data = "";
    data = data + "S" + serial + "F17DAAAA";

    
    for (int i = 0; i < 4; i++) {
      data = data + encodeRow(i);
    }

    data = data + (this.mutex12 ? "AB" : "AA");
    data = data + (this.mutex34 ? "AB" : "AA");

    data = data + Checksum.nibble((byte)this.ms);

    
    data = data + (this.lamella12 ? "AB" : "AA");
    data = data + (this.lamella34 ? "AB" : "AA");

    
    data = data + "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
    
    data = "<" + data + cc.calculateChecksum(data) + ">";
    telegrams.add(data);
    
    return telegrams;
  }
  
  public void decodeMSTelegrams(Vector<String> msTelegrams) {
    String concat = "";
    for (String s : msTelegrams) {
      concat = concat + s.substring(20, 84);
    }
    
    byte[] raw = Checksum.deNibble(concat.substring(0, 64));

    Vector<ModuleParameter> timeParms = XPModuleFunctions.instance().getTimeParams();
    for (int n = 0; n < 4; n++) {
      this.functions[n] = XPModuleFunctions.instance().getModuleFunction(raw[2 * n]);
      this.parameters[n] = timeParms.get(raw[2 * n + 1]);
    } 
    
    this.mutex12 = (raw[8] != 0);
    this.mutex34 = (raw[9] != 0);
    this.ms = raw[10];
    this.lamella12 = (raw[11] != 0);
    this.lamella34 = (raw[12] != 0);
  }
  private String encodeRow(int row) {
    int parameterId;
    if (row < 0 || row > 4) return "";

    Checksum cc = new Checksum();
    String res = "";

    if (this.parameters[row] != null) {
      parameterId = this.parameters[row].getId();
    } else {
      
      parameterId = 0;
    } 
    
    res = res + Checksum.nibble((byte)this.functions[row].getId());
    res = res + Checksum.nibble((byte)parameterId);
    return res;
  }
  
  public void setFunctions(ModuleFunction[] functions) {
    this.functions = functions;
  }
  
  public ModuleFunction[] getFunctions() {
    return this.functions;
  }
  
  public void setParameters(ModuleParameter[] parameters) {
    this.parameters = parameters;
  }
  
  public ModuleParameter[] getParameters() {
    return this.parameters;
  }
  
  public void setMutex12(boolean mutex12) {
    this.mutex12 = mutex12;
  }
  
  public boolean isMutex12() {
    return this.mutex12;
  }
  
  public void setMutex34(boolean mutex34) {
    this.mutex34 = mutex34;
  }
  
  public boolean isMutex34() {
    return this.mutex34;
  }
  
  public void setLamella12(boolean lamella12) {
    this.lamella12 = lamella12;
  }
  
  public boolean isLamella12() {
    return this.lamella12;
  }
  
  public void setLamella34(boolean lamella34) {
    this.lamella34 = lamella34;
  }
  
  public boolean isLamella34() {
    return this.lamella34;
  }
  
  public void setMs(int ms) {
    this.ms = ms;
  }
  
  public int getMs() {
    return this.ms;
  }
  
  public XPActionTable deepCopy() {
    return new Xp24ActionTable(this);
  }
}
