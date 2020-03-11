import re
import json
from os import listdir
#import argparse TODO

version = "0.0 - In developemnt"

def main():
    print(getWelcome())
    jsonDir = readJsonDir()

    # If no valid JSON dir has been found, set one
    if jsonDir == 1:
        jsonDir = getJsonDir()

    startPrompt(jsonDir)


# Get the Json directory from file
# Returns 1 on error, directory name on success
def readJsonDir():
    # Creates the file if it does not exist already
    with open("jsondir.txt", "r") as jsonDirFile:
        directory = jsonDirFile.readline()

        if checkDirValidity(directory):
            return 1

        return directory


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
            if not any(".json" in f for f in listdir(directory)):
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


def startPrompt(JsonDir):
    # json = loadJson()
    print("What would you like to do? Type 'help' for some options. ")

    while True:
        command = input("> ")

        try:
            doAction, args = interpretCommand(command)
            doAction(args)
        except NameError:
            incorrectCommand(command)


def endPrompt(_):
    quit()
    print("Goodbye!")


def printHelpMessage(_):
    print("A list of commands:\n")
    for e in commandHelp:
        print("{0}:  {1}".format(e, commandHelp[e]))


def incorrectCommand(command):
    print("Command not found: {0}".format(command))


# Attempts to expand the abbreviation; if the abbreviation is not valid,
# assumes command has been typed out in full and returns whatever was passed
def expandAbbreviation(abbr):
    try:
        return abbreviations[abbr]
    except NameError:
        return abbr


commands = {
    "help" : printHelpMessage,
    "quit" : endPrompt
}
abbreviations = {
    "f" : "find",
    "i" : "description",
    "c" : "crafting",
    "r" : "recipes",
    "d" : "disassembly",
    "j" : "json",
    "q" : "quit"
}
commandHelp = {
    "help" : "  Prints out this help message.",
    "quit/q" : "Exits the program.",
    "find/f" : "Searches for entry ids matching the argument.",
    "description/i" : "Displays the description of the argument.",
    "crafting/c" : "   Displays information on how to craft specified item.",
    "recipes/r" : "    Displays recipes using specified item.",
    "disassembly/d" : "Displays what the specified item disassembles to.",
    "json/j" : "Display the raw json value of all values with attribute equal to second attribute."
}

if __name__ == "__main__":
    main()
