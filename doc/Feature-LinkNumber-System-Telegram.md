# LinkNumber system telegram

generate a linknumber telegram to get a module linknumber given its serial

```java
public String getLinkNumberTelegram(String serial) {
  Checksum cc = new Checksum();

  
  String strLinkNo = (this.linkNo < 10) ? ("0" + this.linkNo) : ("" + this.linkNo);
  String data = "S" + serial + "F04D04" + strLinkNo;
  String tg = "<" + data + cc.calculateChecksum(data) + ">";
  
  return tg;
}
```

Set the LinkNumber (action F04D04) to value 25 on module serial 0020044974 : <S0020044974F04D0425FO>
Module with serial 0020044974 Acknowledge (ACK : F18D) : <R0020044974F18DFB>
Module with serial 0020044974 Not Acknowledge (NAK : F19D) : <R0020044974F19DFA>


Parse the following
<S0020044974F04D0409FA>
<R0020044974F18DFB>
<R0020044974F19DFA>
<S0020044974F04D0425FO>
<R0020044974F18DFB>
<R0020044974F19DFA>

