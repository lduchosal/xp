# Actions

Listed below are the possible output actions in an action table.

 | Action name    | Code | Description                                                                           |
 |----------------|-----:|---------------------------------------------------------------------------------------|
 | VOID           |    0 | No (empty) actions                                                                    |
 | TURNON         |    1 | Turn output on. Can be given a time parameter to limit the on period                  | 
 | TURNOFF        |    2 | Turn output off. Can be given a time parameter to limit the off period                | 
 | TOGGLE         |    3 | Toggle function (and regulate for dimmers)                                            |
 | BLOCK          |    4 | Block further actions on output. The block is active between the make and break event |
 | AUXRELAY       |    5 | Turns on the output between a make and a break event                                  |
 | MUTUALEX       |    6 | Mutual exclusion between outputs                                                      |
 | LEVELUP        |    7 | Regulate lightlevel up between make and break                                         |
 | LEVELDOWN      |    8 | Regulate lightlevel down between make and break event                                 |
 | LEVELINC       |    9 | Increment lightlevel                                                                  |
 | LEVELDEC       |   10 | Decrement lightlevel                                                                  |
 | LEVELSET       |   11 | Set lightlevel                                                                        |
 | FADETIME       |   12 | Set fadetime                                                                          |
 | SCENESET       |   13 | Set light scene                                                                       |
 | SCENENEXT      |   14 | Change to next lighe scene                                                            |
 | SCENEPREV      |   15 | Change to previous light scene                                                        |
 | CTRLMETHOD     |   16 | Reserved                                                                              |
 | RETURNDATA     |   17 | Read Data point from module                                                               |
 | DELEAYEDON     |   18 | Delay on action with time as parameter                                                |
 | EVENTTIMER1    |   19 | Event timers, that will send out an event message after the time specified            |
 | EVENTTIMER2    |   20 | in the parameter. The event will use the host module type (if the function is used    |
 | EVENTTIMER3    |   21 | in a XP24 module, the event type will be XP24), the host module link number, and      |
 | EVENTTIMER4    |   22 | Four inputs" 70 to 73 for EVENTTIMER1 to EVENTTIMER4 respectively                     | 
 | STEPCTRL       |   23 | Used for controlling multispeed ceiling fans. The STEPCTRL command will use releay 1 and 2 or 3 and 4 in pairs, and will cycle through 4 states (off-off, on-on, on-off, off-on)  | 
 | STEPCTRLUP     |   24 | Like STEPCTRL, except that it stops at the on-on state                                |
 | STEPCTRLDOWN   |   25 | Like STEPCTRLUP, except that it walks the states in the opposite direction and stops at off-off           |
 | LEVELSETINTERN |   29 |                                                                                       |
 | FADE           |   30 | Fade light                                                                            |
 | LEARN          |   31 | Enter learn state                                                                     |
