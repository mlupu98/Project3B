import csv
import sys


def readCSV(inputFile):
    print("BBB")
    csvFile = open(inputFile, "r")

    blockSize = 0
    inodeSize = 0

    # Use first string to determine type.
    for line in csvFile:
        currentLine = line.split(',')

        if currentLine[0] == "SUPERBLOCK":
            blockSize = currentLine[3]
            inodeSize = currentLine[4]
        elif currentLine[0] == "GROUP":
            return
        elif currentLine[0] == "BFREE":
            print("aAAA")
        elif currentLine[0] == "INODE":
            inodeNumber = currentLine[1]
            fileType = currentLine[2]
            checkInode(inodeNumber, fileType)
        elif currentLine[0] == "INDIRECT":
            checkIndirect()
    return


def checkGroup():
    return


def checkBfree():
    return


def addInode(inodeNumber, fileType):
    freeList = []
    if fileType == '0':
        freeList[inodeNumber] = 999999  # Random Number, please change.

    return


def checkIndirect():
    return


def parseInode(fileType):

    if fileType != "f" | | fileType != "d":


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Error: incorrect number of arguments \n")
        exit(1)

    readCSV(sys.argv[1])


if __name__ == '__main__':
    main()
