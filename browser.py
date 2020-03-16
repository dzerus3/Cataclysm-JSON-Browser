import json
import glob
#import argparse TODO

version = "0.0 - In developemnt"

def main():
    print(getWelcome())
    #jsonDir = readJsonDir()

    jsonDir = "/home/sal/workspace/Cataclysm-DDA/data/json"
    # If no valid JSON dir has been found, set one
    if jsonDir == 1:
        jsonDir = getJsonDir()

    startPrompt(jsonDir)


# Get the Json directory from file
# Returns 1 on error, directory name on success
""" This function does not work and I fail to understand why; hardcoding it
def readJsonDir():
    # Creates the file if it does not exist already
    with open("jsondir.txt", "r") as jsonDirFile:
        directory = jsonDirFile.readline()

        if checkDirValidity(directory):
            return 1
    print("Directory: " + directory)
    return directory
"""

# Run when the program is started for the first time, or whenever the JSON dir is not found
def getJsonDir():
    print("Please enter the path to the game's JSON folder.")
    directory = str(input())

    # Recursive call to itself until a valid location is specified
    if checkDirValidity(directory):
        print("This path appears to be wrong.")
        directory = getJsonDir()

    # TODO: Write the directory down into the allocated file

    return directory


def checkDirValidity(directory):
        # Checks whether the directory exists, and whether there are any .json files inside
        try:
            if glob.glob(directory + "/*.json") == []:
                return 1
        except:
            return 1

        return 0


def printVersion():
    print("Version: {0}".format(version))


def getWelcome():
    return "Welcome to Dellon's CDDA json browser!"


def interpretCommand(command):
    fullCommand = command.split()
    cmd = expandAbbreviation(fullCommand[0])
    args = fullCommand[1:]

    return commands[cmd], args


def loadJson(jsonDir):
    loadedJson = {}

    # Items, vehicles, and vehicle parts loaded separately because they are across multiple files
    loadedJson["items"]    = loadJsonFiles(jsonDir, subDir="items")
    loadedJson["vehicles"] = loadJsonFiles(jsonDir, subDir="vehicles")
    loadedJson["recipes"]  = loadJsonFiles(jsonDir, subDir="recipes")
    loadedJson["parts"]    = loadJsonFiles(jsonDir, subDir="vehicleparts")

    loadedJson["bionics"]  = loadJsonFiles(jsonDir, jsonFile="bionics.json")
    loadedJson["materials"]= loadJsonFiles(jsonDir, jsonFile="materials.json")
    loadedJson["martialarts"]  = loadJsonFiles(jsonDir, jsonFile="martialarts.json")
    loadedJson["mutations"]    = loadJsonFiles(jsonDir, jsonFile="mutations/mutations.json")
    loadedJson["construction"] = loadJsonFiles(jsonDir, jsonFile="construction.json")

    return loadedJson


def loadJsonFiles(jsonDir, jsonFile=0, subDir=0):
    # If neither is specified or both are specified that's an error
    if jsonFile == subDir:
        raise TypeError("loadJsonFiles called with wrong number of args")

    result = []

    try:
        # TODO: Rewrite this without conditionals, ie using a list
        # If the json is contained in a single file
        if jsonFile:
            with open(jsonDir + "/" + jsonFile, "r") as openedJsonFile:
                result.append(json.load(openedJsonFile))

        # If there is a subdirectory with more files (or even with more subdirectories)
        if subDir:
            jsonFiles = glob.glob(jsonDir + "/" + subDir + "/**/*.json", recursive=True)
            for f in jsonFiles:
                with open(f, "r") as openedJsonFile:
                    result.append(json.load(openedJsonFile))

    # In the improbable event one of the files is missing, or wrong directory got through the checks
    except FileNotFoundError:
        if jsonFile:
            print("Failed to open file {0}. Some commands may be unavailable.".format(jsonFile))
            print("Are you sure " + jsonDir + jsonFile + " is the right location?")
        else:
            print("Failed to open file {0}. Some commands may be unavailable.".format(f))
            print("Are you sure " + jsonDir + f + " is the right location?")

    return result


# This is the command prompt the user interacts with
def startPrompt(jsonDir):
    loadedJson = loadJson(jsonDir)
    print("What would you like to do? Type 'help' for some options. ")

    while True:
        command = input("> ")

        try:
            doAction, args = interpretCommand(command)
        except (NameError, KeyError):
            incorrectCommand(command)
        doAction(args, loadedJson)



# Attempts to expand the abbreviation; if the abbreviation is not valid,
# assumes command has been typed out in full and returns whatever was passed
def expandAbbreviation(abbr):
    try:
        return abbreviations[abbr]
    except KeyError:
        return abbr


# This category attempts to imitate the item browser as much as possible in
# terms of ui
def findItem(args, loadedJson):
    if not checkArgsNumber(args, 2):
        # Required to make multi-word names work
        itemName = ' '.join(args[1:])

        if args[0] == "description":
            outputItemDesc(itemName, loadedJson)
        elif args[0] == "recipes":
            outputCraftingRecipes(itemName, loadedJson)
        elif args[0] == "craft":
            pass
        elif args[0] == "disassembly":
            pass
        else:
            print("Cannot find item's {0}".format(args[0]))


def outputItemDesc(itemName, loadedJson):
    item = findItemByName(itemName, loadedJson)

    readableItem = getItemDesc(item)
    for i in readableItem: #TODO: Make the ui prettier
        # If the value was not set
        if not readableItem[i]:
            continue
        print(prettifyString(i) + ": " + prettifyString(readableItem[i]))


# I really cannot find a way to print efficiently hundreds of recipes in a terminal
# URGENT TODO: As of right now, this does not output all crafting recipes
# I think it is because a.) Multi-word items and b.) replaceable components
def outputCraftingRecipes(itemName, loadedJson):
    item = findItemByName(itemName, loadedJson)
    if not item:
        return
    recipes = findRecipeEntries(item["id"], loadedJson)
    counter = 1

    # Items with more than 25 recipes (i.e. rag) become almost unreadable
    # This conditional tries to alleviate that
    # TODO: Make this prettier
    recipLen = len(recipes)
    if recipLen > 25:
        for r in recipes:
            item = findItemByID(r["result"], loadedJson)

            if item == None:
                # TODO: Investigate results of rock item
                # Without this conditional
                continue

            name = getItemName(item)
            name = setStringLength(name)

            counterStr = setStringLength(str(counter), 3) # TODO: Make this line work

            print(str(counter) + ". " + prettifyString(name))
            counter+=1
    else:
        for r in recipes:
            item = findItemByID(r["result"], loadedJson)

            if item == None:
                continue

            name = getItemName(item)
            print(str(counter) + ". " + prettifyString(name))
            counter+=1



# This json reading thing sure is something
# the name of the component is stored in a dictionary (json categories)
# of lists (json files) of dictionaries (the json itself) of lists of lists
# (the components) of lists (the number of components and name)
def findRecipeEntries(itemId, loadedJson):
    matchingRecipes = []

    for recipes in loadedJson["recipes"]:
        for recipe in recipes:
            if recipe.get("components"):
                for components in recipe["components"]:
                    componentName = components[0][0]
                    if componentName == itemId:
                        matchingRecipes.append(recipe)
    return matchingRecipes


# Removes any extra information, handles missing information,
# and returns it in a dictionary
def getItemDesc(item):
    values = {}
    # All the values we do not want to see
    ignoredValues = ["id", "color", "type", "//", "//2", "use_action"] # TODO Add option to display these; probably with arguments
    # Material is separate value because we have to get stuff from another file
    # itemMat = item["material"] # TODO

    for i in item:
        if i not in ignoredValues:
            values[i] = str(item[i])
    return values


def findItemByName(name, loadedJson):
    name = name.lower()
    for i in loadedJson["items"]:
        for sub in i:
            subName = getItemName(sub)
            if sub.get("type") == "ammunition_type":
                continue
            if subName == name:
                return sub


def findItemByID(iden, loadedJson):
    iden = iden.lower()
    for i in loadedJson["items"]:

        for sub in i:
            if sub.get("id"):
                subName = sub["id"]
            else:
                continue

            if subName == iden:
                return sub


# I don't understand why, but some items have a name defined as name:str:<item name>
# some have it defined as name:<item name> some only have an id,
# and some have no id at all so I have to handle all cases and it's ugly
def getItemName(item):
    # Note: this definition has to be here, else some entries cause a crash
    itemname = ""
    try:
        # If we have a name attribute...
        if item.get("name"):
            itemname = item["name"]

            # If that name has an str attribute...
            if itemname.get("str"):
                itemname = item["name"]["str"]
    except AttributeError:
        pass

    return itemname


def prettifyString(string):
    string = string.capitalize()
    string = string.replace("_", " ")
    return string


def setStringLength(string, length=20):
    changedString = shortenString(string, length)
    changedString = padString(changedString, length)

    return changedString


def shortenString(string, length=20):
    strlen = len(string)
    if strlen > length:
        string = string[:17]
        string+="..."

    return string


# Pads string with spaces so it is easier to pretty-print
def padString(string, length=20):
    strlen = len(string)
    if strlen < length:
        padNum = length - len(string)
        string += " " * padNum
    return string


def endPrompt(*argv):
    quit()


def printHelpMessage(*argv):
    print("A list of commands:\n")
    for e in commandHelp:
        print("{0}:  {1}".format(e, commandHelp[e]))


def incorrectCommand(command):
    a = command.split(" ")
    print("Command not found: {0}".format(a[0]))


def checkArgsNumber(args, necessary):
    try:
        a = args[necessary - 1]
        return 0
    except IndexError:
        print("Not enough arguments for command.", end=' ')
        print("You need at least {0}".format(necessary))
        return 1


commands = {
    "help" : printHelpMessage,
    "quit" : endPrompt,
    "item" : findItem
}
abbreviations = {
    "i" : "item",
    "v" : "vehicle",
    "p" : "part",
    "b" : "bionic",
    "m" : "materials",
    "ma": "martialart",
    "mu": "mutation",
    "c" : "construction",
    "j" : "json",
    "q" : "quit"
}
commandHelp = {
    "help"     : "  Prints out this help message.",
    "quit/q"   : "Exits the program.",
    "item/i"   : "Outputs selected value of an item.",
    "vehicle/v": "Outputs selected value of a vehicle.",
    "part/p"   : "Outputs selected value of a vehicle part.",
    "bionic/b" : "Outputs selected value of a bionic.",
    "materials/m"   : "Outputs selected value of a material.",
    "martialart/ma" : "Outputs selected value of a martial art.",
    "mutation/mu"   : "Outputs selected value of a mutation.",
    "construction/c": "Outputs selected value of a construction interaction.",
    "json/j"   : "Display the raw json value of all values with attribute equal to second attribute."
}


if __name__ == "__main__":
    main()
