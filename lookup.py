import re
from os import listdir
#import argparse TODO
import json

version = "0.0 - In developemnt"

def main():
    JsonDir = readJsonDir()

    # If no valid JSON dir has been found, set one
    if JsonDir == 1:
        JsonDir = getJsonDir()

    startPrompt(JsonDir)


# Get the Json directory from file
# Returns 1 on error, directory name on success
def readJsonDir():
    # Creates the file if it does not exist already
    with open("jsondir.txt", "a+") as JsonDirFile:
        directory = JsonDir.readline()

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


def getWelcomeBanner():
    return "Welcome to Dellon's CDDA json browser!"


def startPrompt(JsonDir):
    print("What would you like to do? Type 'help' for some options. ")

    while True:
        command = input("> ")
        doAction, args = parseCommand(command)
        doAction(args)


def printHelpMessage():


def endPrompt():
    print("Goodbye!")
    break

commands = {
    "help" : printHelpMessage,
    "quit" : endPrompt
}


if __name__ == "__main__":
    main()
