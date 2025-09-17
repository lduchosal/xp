# Event Telegram

Event telegrams identifies an event in the system, e.g. user pressing a button on. Below is shown an
example of an event telegram
```
<E14L00I02MAK>
```
- The "E" identifies the telegram as being of the event type, the number following (14) is the module type
code (see more on module types). 
- The two digits after the "L" designates link number from 00 to 99, and
- the two digits after the "I" designates the input number. 
- Finally, the "M" indicates a button press (make), 
- and a "B" designates a button release (break). 
- The last two characters before the > is a checksum of the telegram.

The input numbers extends beyond push buttons. If the push button panel is equipped with an IR
receiver, IR remote channels is mapped into the input space from 10 to 89.
The proximity sensor ("Sesame") on the Conson push button panels also emits an event. Input number
90 is used for sesam events.