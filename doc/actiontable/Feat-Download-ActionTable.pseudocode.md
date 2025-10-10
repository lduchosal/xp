
class ActionTableParser:

    int UPPER4 = 240
    int LOWER4 = 15

    int LOWER3 = 7
    int UPPER5 = 248
      
    byte[] actionTable
    list[ActionTableEntry] actions
      
    boolean debug = true
      
    list parse(String moduleType, String serial, byte[] data):
        actionTable = data
        actions = list[]
            
        parseActionTable
        return actions
      
    list[ActionTableEntry] getActions:
    return actions
      
    void parseActionTable:
        int type = 0
        int link = 0
        int input = 0
        int output = 0
        int command = 0
        int parameter = 0
            
        for (int i = 0 i < actionTable.length i += 5):
            type = deBCD(actionTable[i])
            link = deBCD(actionTable[i + 1])
            input = deBCD(actionTable[i + 2])
            output = lower3(actionTable[i + 3])
            command = upper5(actionTable[i + 3])
            parameter = actionTable[i + 4]

            table = ActionTableEntry(type, link, input, output, command, parameter)
            actions.add(table)
         
        
    int lower3(byte b):
        return b & LOWER3
      
    int upper5(byte b):
        return (b & UPPER5) >> 3
    
    int deBCD(byte b):
        return ((UPPER4 & b) >> 4) * 10 + (LOWER4 & b)

