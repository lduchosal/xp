# System and Reply telegrams
System telegrams are used to system related information like updateing firmware
and reading the temperature from a module.
The system telegram shown below is used to request the temperature from a module.
<S0020012521F02D18FN>
System telegrams are identified by the "S", and followed by the receiver serial number. The
two digtits after "F" designates the system function (here "Read Data point"), and the two digits
afte "D" is the data point ID (here temperature).
The system telegram above is answered using a reply telegram like shown below.
<R0020012521F02D18+26,0§CIL>
The "R" is for reply telegram, and is followed by the serial number of the sender of the
telegram.