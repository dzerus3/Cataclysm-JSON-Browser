import json
import glob
import os

version = "0.0.3 - Alpha"


### STARTUP FUNCTIONS

def main():
    print(getWelcome())
    jsonDir = readJsonDir()
    startPrompt(jsonDir)


# Get the Json directory from file
def readJsonDir():
    configfile = os.path.join(
            os.environ.get('APPDATA') or
            os.environ.get('XDG_CONFIG_HOME') or
            os.path.join(os.environ['HOME'], '.config'),
            'cdda_json_browser'
    )
    try:
        with open(configfile, 'r') as configFile:
            directory = configFile.readline()

            if not os.path.isdir(directory):
                raise FileNotFoundError

    except FileNotFoundError:
        directory = getJsonDir()
        with open(configfile, 'w') as configFile:
            configFile.write(directory)

    finally:
        return directory


# Run when the program is started for the first time, or whenever the JSON dir is not found
def getJsonDir():
    print("Please enter the path to the game's JSON folder.")
    directory = input()

    # Recursive call to itself until a valid location is specified
    if not os.path.isdir(directory):
        print("This path appears to be wrong.")
        directory = getJsonDir()

    return directory


def getWelcome():
    return "Welcome to Dellon's CDDA json browser!"

def loadJson(jsonDir):
    loadedJson = {}

    # Items, vehicles, and vehicle parts loaded separately because they are across multiple files
    loadedJson["items"]    = loadJsonFiles(jsonDir, subDir="items")
    loadedJson["monsters"]    = loadJsonFiles(jsonDir, subDir="monsters")
    loadedJson["vehicles"] = loadJsonFiles(jsonDir, subDir="vehicles")
    loadedJson["recipes"]  = loadJsonFiles(jsonDir, subDir="recipes")
    loadedJson["parts"]    = loadJsonFiles(jsonDir, subDir="vehicleparts")

    loadedJson["bionics"]  = loadJsonFiles(jsonDir, jsonFile="bionics.json")
    loadedJson["materials"]= loadJsonFiles(jsonDir, jsonFile="materials.json")
    loadedJson["martialArts"]  = loadJsonFiles(jsonDir, jsonFile="martialarts.json")
    loadedJson["mutations"]    = loadJsonFiles(jsonDir, jsonFile="mutations/mutations.json")
    loadedJson["construction"] = loadJsonFiles(jsonDir, jsonFile="construction.json")

    return loadedJson


def loadJsonFiles(jsonDir, jsonFile="", subDir=""):
    f="" # This is for error handling
    # If neither is specified or both are specified that's an error
    if jsonFile == subDir:
        raise TypeError("loadJsonFiles called with wrong number of args")

    result = []

    try:
        # TODO: Rewrite this without conditionals, ie using a list
        # If the json is contained in a single file
        if jsonFile:
            with open(jsonDir + "/" + jsonFile, "r", encoding="utf8") as openedJsonFile:
                result.append(json.load(openedJsonFile))

        # If there is a subdirectory with more files (or even with more subdirectories)
        if subDir:
            jsonFiles = glob.glob(jsonDir + "/" + subDir + "/**/*.json", recursive=True)
            for f in jsonFiles:
                with open(f, "r", encoding="utf8") as openedJsonFile:
                    result.append(json.load(openedJsonFile))

    # In the improbable event one of the files is missing, or wrong directory got through the checks
    except FileNotFoundError:
            print("Failed to open file {0}{1}.".format(jsonFile, f))
            raise FileNotFoundError

    return result


# This is the command prompt the user interacts with
def startPrompt(jsonDir):
    loadedJson = loadJson(jsonDir)
    print("What would you like to do? Type 'help' for some options. ")

    while True:
        command = input("> ")

        try:
            doAction, args = interpretCommand(command)
        except (NameError, KeyError, IndexError):
            invalidCommand(command)
            continue
        doAction(args, loadedJson)


### FUNCTIONS FOR ITEM COMMAND

def findItem(args, loadedJson):
    if not checkArgsNumber(args, 2):
        # Required to make multi-word names work
        command, itemName = separateArgs(args)
        item = findJsonEntry(loadedJson["items"], ["name", "str"], itemName, [])

        if not checkEntry(item, itemName, "item"):
            return

        if command == "description":
            outputItemDesc(item[0], loadedJson)
        elif command == "recipes":
            outputItemRecipes(item[0], loadedJson)
        elif command == "craft":
            outputItemCrafting(item[0], loadedJson)
        else:
            invalidCommand(command)


def outputItemDesc(item, loadedJson):
    readableItem = filterJson(item, "item")

    for i in readableItem:
        # If the value was not set
        if not readableItem[i]:
            continue
        print(prettifyString(i) + ": " + prettifyString(readableItem[i]))


# I really cannot find a way to print efficiently hundreds of recipes in a terminal
def outputItemRecipes(item, loadedJson):
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
            item = findJsonEntry(loadedJson["items"], ["id"], r["result"], [])

            if item == None:
                # TODO: Investigate results of rock item
                # Without this conditional
                continue

            name = findJsonEntry(item, ["name", "str"], entries = [])[0]
            name = setStringLength(name)

            # counterStr = setStringLength(str(counter), 3) # TODO: Make this line work

            print(str(counter) + ". " + prettifyString(name))
            counter+=1
    else:
        for r in recipes:
            item = findJsonEntry(loadedJson["items"], ["id"], r["result"], [])[0]
            name = findJsonEntry(item, ["name", "str"], entries = [])[0]

            if item == None:
                continue

            name = findJsonEntry(item, ["name", "str"], entries = [])
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
                    for replacements in components:
                        componentName = replacements[0]
                        if componentName == itemId:
                            matchingRecipes.append(recipe)
    return matchingRecipes


def outputItemCrafting(item, loadedJson):
    itemID = item["id"]
    matchingRecipes = []

    for recipes in loadedJson["recipes"]:
        for recipe in recipes:
            result = recipe.get("result")
            if result == itemID:
                matchingRecipes.append(recipe)

    for i in matchingRecipes:
        values = filterJson(i, "item")
        for i in values:
            fullString = i + ": " + str(values[i])
            print(prettifyString(fullString))
        print("-----------------")


### MISC COMMANDS

def outputMonsters(args, loadedJson):
    monsterName = separateArgs(args, False)
    monster = findJsonEntry(loadedJson["monsters"], ["name", "str"], monsterName, [])

    if not checkEntry(monster, monsterName, "monster"):
        return

    prettyPrint(monster[0], "monster")


# TODO: This function looks awfully similar to outputMonsters
# outputItemDesc. Do I really need a separate function for all 3?
def outputMutation(args, loadedJson):
    mutationName = separateArgs(args, False)
    mutation = findJsonEntry(loadedJson["mutations"], ["name", "str"], mutationName, [])

    if not checkEntry(mutation, mutationName, "mutation"):
        return

    prettyPrint(mutation[0], "mutation")

    # Traits like stylish or glass jaw, for example have no
    # effect in json. I think they are defined in the source


def outputBionics(args, loadedJson):
    bionicName = separateArgs(args, False)
    bionic = findJsonEntry(loadedJson["bionics"], ["name", "str"], bionicName, [])

    if not checkEntry(bionic, bionicName, "bionic"):
        return

    prettyPrint(bionic[0], "bionic")


def outputMaterial(args, loadedJson):
    materialName = separateArgs(args, False)
    material = findJsonEntry(loadedJson["materials"], ["name", "str"], materialName, [])

    if not checkEntry(material, materialName, "material"):
        return

    prettyPrint(material[0], "material")


def outputMartialArt(args, loadedJson):
    subcommand, martialArtName = separateArgs(args)
    martialArt = findJsonEntry(loadedJson["martialArts"], ["name", "str"], martialArtName, [])

    if subcommand == "overview":
        if not checkEntry(martialArt, martialArtName, "martialArt"):
            return

        prettyPrint(martialArt[0], "martialArt")
    elif subcommand == "buffs":
       printMartialBuffs(martialArt[0])
    else:
        print("Subcommand not found: {0}".format(subcommand))


def printMartialBuffs(martialArt):
    buffs = ["static_buffs", "onmiss_buffs",
             "onmove_buffs", "ondodge_buffs",
             "onhit_buffs",  "oncrit_buffs",
             "onblock_buffs"]
    for buff in buffs:
        for entry in martialArt:
            if entry == buff:
                effect = martialArt[entry]
                print("\n" + buff + "\n----------------")
                prettyPrint(effect[0], "all")


def getVehicleParts(loadedJson, args):
    subcommand, partName = separateArgs(args)

    part = findJsonEntry(loadedJson["parts"], ["name", "str"], partName, [])

    if subcommand == "overview":
        if not checkEntry(part, partName, "part"):
            return

        prettyPrint(part[0], "part")

    elif subcommand == "requirements":
        getPartRequirements(part)

    else:
        print("Subcommand not found: {0}".format(subcommand))


def getPartRequirements(part):
    for entry in part:
        if entry == "requirements":
            pass


# Searches through all json files for the entry specified
def outputJson(args, loadedJson):
    # TODO Currently does not support nested dicts like str:name
    key = args[0]
    finalEntries = []

    if len(args) < 2:
        value = ' '.join(args[1:])
    else:
        value = ""

    for f in loadedJson:
        json = findJsonEntry(loadedJson[f], [key], value, [])
        finalEntries.append(json)

    for j in finalEntries:
        print(j)


### PRETTY-PRINTING FUNCTIONS

def prettifyString(string):
    string = string.capitalize()
    string = string.replace("_", " ")
    string = string.replace("],", " ")
    string = string.replace("\",", " ")
    string = string.replace("},", " ")
    string = string.replace("[", "")
    string = string.replace("{", "")
    string = string.replace("]", "")
    string = string.replace("}", "")
    string = string.replace("'", "")
    string = string.replace(",", ":")

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


def prettyPrint(output, kind):
    output = filterJson(output, kind)

    for i in output:
        printableString = str(i + ": " + output[i])
        print (prettifyString(printableString))


# Pads string with spaces so it is easier to pretty-print
def padString(string, length=20):
    strlen = len(string)
    if strlen < length:
        padNum = length - len(string)
        string += " " * padNum
    return string


### UTILITY FUNCTIONS

""" findJsonEntry - Recursive function to retrieve values from JSON
                    Use this if you need to retrieve a JSON entry or
                    a particular value from JSON entries.
        Arguments:
            objs  - The object which we will parse for info. Either string, dict, or list.
            keys  - What key we are looking for. Is an array to accomodate nested dictionaries.
            value - What value the key should be equal to. It is optional, and if not specified
                    the function will return a list of all values corresponding to key in object.
            top   - Indicates whether this is at the top or not. This is to prevent recursiveness
                    from returning the function too early.
            entries - A list of all the matching JSON entries in object. Note: despite the fact
                      that it has a default value, you should still specify []. This is because
                      otherwise the entries will remain saved from the last time the function was used
        Returns:
            If value is specified, returns a list of JSON entries that match the keys and value
            If value is not specified, returns a list of all values corresponding to key
        TODO: If given an entire json category with multiple files (i.e. loadedJson["items"]) it will only return one value per file right now
"""
def findJsonEntry(objs, keys, value="", entries = [], top=True):
    objtype = str(type(objs))
    # Only dicts will contain what we are looking for
    # so only info from dicts gets returned by the function
    if "dict" in objtype:
        for obj in objs:
            # Note that keys is an array because of nested
            # dictionaries (namely name) which would throw
            # the function out of whack
            if obj in keys:
                j = findJsonEntry(objs[obj], keys, value, entries, False)
                # Only appends it if it's from the JSON entry because
                # otherwise nested dicts would get incorrectly returned
                if not value:
                    entries.append(j)
                elif j and obj == keys[0]:
                    entries.append(objs)
                return j
    elif "list" in objtype:
        for obj in objs:
            j = findJsonEntry(obj, keys, value, entries, False)
            # If it returns not at top, it will only return one result
            if j and not top:
                return j
    elif "str" in objtype:
        if objs.lower() == value.lower() or not value:
            return objs
    if top:
        # Note that it always returns a list, so if you're looking
        # for only on value you have to use findJsonEntry[0]
        return entries


# Removes any extra information, handles missing information,
# and returns it in a dictionary
def filterJson(entry, entryType):
    # Buffer for the returned values
    values = {}
    # All the values we do not want to see
    unwantedValues = {
        "all":  ["id", "type", "//", "//2"],
        "item": ["color", "use_action", "category", "subcategory",
                 "id_suffix", "result"],
        "monster":   ["harvest", "revert_to_itype", "vision_day",
                      "color", "weight", "default_faction"],
        "mutation":  ["starting_trait", "valid"],
        "bionic"  :  ["flags", "fake_item", "time"],
        "martialArt":["initiate", "static_buffs", "onmiss_buffs",
                      "onmove_buffs", "ondodge_buffs", "onhit_buffs",
                      "oncrit_buffs", "onblock_buffs"],
        "material":  ["dmg_adj", "bash_dmg_verb", "cut_dmg_verb",
                      "ident"],
        "part": ["item", "location", "requirements", "size"]
    }
    # TODO Add option to display these; probably with arguments

    # itemMat = item["material"] # TODO: Add something to handle materials

    # The values for this specific operation
    try:
        ignoredValues = unwantedValues["all"] + unwantedValues[entryType]
    except KeyError:
        print ("filterJson() called with invalid entry type!")
        raise

    for i in entry:
        if i not in ignoredValues:
            values[i] = str(entry[i])
    return values


### GENERAL FUNCTIONS
def endPrompt(*argv):
    quit()


def checkEntry(entry, name, entryType):
    if not entry:
        print("Could not find {0} {1}.".format(entryType, name))
        return None
    return entry


# Attempts to expand the abbreviation; if the abbreviation is not valid,
# assumes command has been typed out in full and returns whatever was passed
def expandAbbreviation(abbr):
    try:
        return abbreviations[abbr]
    except KeyError:
        return abbr

# Separates an array of args into first arg,
# and space-separated string of the rest
def separateArgs(args, cmd=True):
    if args:
        if cmd:
            command = args[0]
            name = " ".join(args[1:])
            return command, name
        else:
            name = " ".join(args)
            return name
    return


def printHelpMessage(*argv):
    print("A list of commands:\n")
    for command in commandHelp:
        for subcommand in commandHelp[command]:
            if subcommand == "main":
                print("{0}: {1}".format(command, commandHelp[command][subcommand]))
            else:
                print("\t {0}: {1}".format(subcommand, commandHelp[command][subcommand]))

def invalidCommand(command):
    print("Command not found: {0}".format(command))


def checkArgsNumber(args, necessary):
    try:
        args[necessary - 1]
        return 0
    except IndexError:
        print("Not enough arguments for command.", end=' ')
        print("You need at least {0}".format(necessary))
        return 1


def printVersion():
    print("Version: {0}".format(version))


def interpretCommand(command):
    command = command.split()
    cmd = command[0]
    args = command[1:]
    cmd = expandAbbreviation(cmd)

    return commands[cmd], args


commands = {
    "help" : printHelpMessage,
    "quit" : endPrompt,
    "item" : findItem,
    "monster" : outputMonsters,
    "mutation": outputMutation,
    "bionic"  : outputBionics,
    "martialart": outputMartialArt,
    "material": outputMaterial,
    "json" : outputJson
}
abbreviations = {
    "i" : "item",
    "v" : "vehicle",
    "p" : "part",
    "b" : "bionic",
    "m" : "material",
    "mo": "monster",
    "ma": "martialart",
    "mu": "mutation",
    "c" : "construction",
    "j" : "json",
    "q" : "quit"
}
commandHelp = {
    "help"     : {"main": "Prints out this help message."},
    "quit/q"   : {"main": "Exits the program."},
    "item/i"   : {"main": "Outputs selected value of an item.",
                  "description":"Prints out the properties of an item",
                  "craft": "Outputs all recipes to craftor disassemble an item",
                  "recipes": "Outputs all recipes using an item (warning: may be long)"},
    "vehicle/v": {"main": "Outputs selected value of a vehicle."},
    "part/p"   : {"main": "Outputs selected value of a vehicle part."},
    "bionic/b" : {"main": "Outputs the effect of a bionic."},
    "monster/mo": {"main": "Outputs information on specified monster"},
    "material/m": {"main": "Outputs selected value of a material."},
    "martialart/ma" : {"main": "Outputs the effects of a martial art.",
                       "overview": "Prints a brief overview of the martial art",
                       "buffs": "Prints all the buffs the martial art gives."},
    "mutation/mu"   : {"main": "Outputs the effects of a mutation."},
    "construction/c": {"main": "Outputs selected value of a construction interaction."},
    "json/j"   : {"main": "Display raw json value of values with attribute equal to second attribute.",
                  "WARNING": "Currently very bugged!"}
}


if __name__ == "__main__":
    main()
