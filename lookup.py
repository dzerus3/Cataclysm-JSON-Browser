import re
import json
import glob
import struct
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
    except FileNotFoundError:
        if jsonFile:
            print("Failed to open file {0}. Some commands may be unavailable.".format(jsonFile))
            print("Are you sure " + jsonDir + jsonFile + " is the right location?")
        else:
            print("Failed to open file {0}. Some commands may be unavailable.".format(f))
            print("Are you sure " + jsonDir + f + " is the right location?")

    return result


def startPrompt(jsonDir):
    loadedJson = loadJson(jsonDir)
    print("What would you like to do? Type 'help' for some options. ")

    while True:
        command = input("> ")

        try:
            doAction, args = interpretCommand(command)
            doAction(args, loadedJson)
        except NameError:
            incorrectCommand(command)


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
    item = findJsonEntry(args[1], loadedJson)


    if args[0] == "description":
        readableItem = getItemDesc(item)
        for i in readableItem:
            print(readableItem[i])

    elif args[0] == "recipes":
        pass


# Removes any extra information, handles missing information,
# and returns it in a dictionary
def getItemDesc(item):
    values = {
        "name"  : 0,
        "volume": 0,
        "weight": 0,
        "bash_protec": 0,
        "cut_protec" : 0,
        "tohit_bonus": 0,
        "attackmoves": 0,
        "category": 0,
        "material": 0,
        "price": 0,
        "flags": 0,
        "description": 0
    }
    # Name declared separately because it has 2 keys
    values["name"] = item["name"]["str"]

    for i in values:
        try:
            values[i] = str(item[i])
        except:
            values[i] = 0

    return values


def findJsonEntry(name, loadedJson):
    for i in loadedJson:
        if i["name"]["str"] == name:
            return i
    print("Could not find item {0}".format(name))


def endPrompt(_):
    quit()


def printHelpMessage(_):
    print("A list of commands:\n")
    for e in commandHelp:
        print("{0}:  {1}".format(e, commandHelp[e]))


def incorrectCommand(command):
    print("Command not found: {0}".format(command))


# def getItem(name, prop):
#     itemDir = items

#     # Finds the json values assigned to that item
#     item = findItem(name)


# def findItem(name):



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
