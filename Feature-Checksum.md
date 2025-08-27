# Checksum

The following java implementation of the telegram checksum

```java

public class Checksum
{
  public String calculateChecksum(String buffer) {
    char cc = Character.MIN_VALUE;
    for (int i = 0; i < buffer.length(); i++) {
      cc = (char)(cc ^ buffer.charAt(i));
    }
    return nibble((byte)cc);
  }

  public static String nibble(byte byteVal) {
    char lowNibble = 'A';
    int lowcc = ((byteVal & 0xF0) >> 4) + 65;
    int highcc = (byteVal & 0xF) + 65;
    return new String("" + (char)lowcc + (char)highcc);
  }
  
  public static byte[] deNibble(String strVal) {
    char lowNibble = 'A';
    byte[] result = new byte[strVal.length() / 2];
    for (int i = 0; i < strVal.length(); i += 2) {
      int lowcc = strVal.charAt(i) - 65 << 4;
      int highcc = strVal.charAt(i + 1) - 65;
      result[i / 2] = (byte)(lowcc + highcc);
    } 
    return result;
  }
  
  public static int unBcd(byte bcd) {
    int iBcd = byteToIntNoSign(bcd);
    return (iBcd >> 4) * 10 + (iBcd & 0xF);
  }
  
  public static int byteToIntNoSign(byte in) {
    if (in < 0)
      return in + 256; 
    return in;
  }

  public String calculateChecksum32(byte[] buffer) {
    String nibbleResult = "";
    int crc = -1;
    
    short s;
    
    for (s = 0; s < buffer.length; s = (short)(s + 1)) {
      byte bite = buffer[s];
      crc ^= bite;
      short j;
      for (j = 7; j >= 0; j = (short)(j - 1)) {
        int mask = -(crc & 0x1);
        crc = crc >>> 1 ^ 0xEDB88320 & mask;
      } 
    } 
    crc ^= 0xFFFFFFFF;
    
    for (int i = 0; i < 4; i++) {
      nibbleResult = nibble((byte)crc) + nibbleResult;
      crc >>>= 8;
    } 
    return nibbleResult;
  }
}


```
