#! /usr/local/cs/bin/python3

import csv
import sys

from collections import defaultdict

# Using default dictionary to store references.
blockReference = defaultdict(list)

# List of various items,

freeBlocks = set()
allocatedInodes = []
freeInodes = []
inodes = {}  # Save pointers to inodes.
indirects = []
dirents = set()

# Global Variables

blockSize = 0
inodeSize = 0
numBlocks = 0
numInodes = 0
blockSize = 0
inodeSize = 0
freeInodeBeginning = 0
blocksPerGroup = 0
blocksPerInode = 0
firstFreeNode = 0
firstValidBlock = 0


def readCSV(inputFile):
    csvFile = open(inputFile, "r")
    global blockSize, inodeSize, numInodes, blockSize, inodeSize, blocksPerGroup, blocksPerGroup, numBlocks, firstFreeNode, firstValidBlock, freeInodeBeginning

    # Use first string to determine type.
    for line in csvFile:
        # currentLine references each field.
        currentLine = line.split(',')
        #freeInodeBeginning
        if currentLine[0] == "SUPERBLOCK":
            # FORMAT: superblock, numBlocks, numInodes, blockSize,
            #         inodeSize, blocksPerGroup, blocksPerInode, firstFreeNode
            freeInodeBeginning = int(currentLine[7])
            blockSize = int(currentLine[3])
            inodeSize = int(currentLine[4])  # Do we need to convert to int?
        elif currentLine[0] == "GROUP":
            # FORMAT: group, groupNum, numBlocks, numInodes, numFreeBlocks,
            # numFreeInodes, freeBitmap, freeInodeBitmap, firstFreeNode
            numBlocks = int(currentLine[2])
            numInodes = int(currentLine[3])
            firstFreeNode = int(currentLine[8])
            # First Valid Block, crosscheck with block allocations
            firstValidBlock = int(firstFreeNode) + \
                inodeSize * numInodes / blockSize
        elif currentLine[0] == "BFREE":
            # FORMAT: bfree, numFreeBlocks
            freeBlocks.add(currentLine[1])
        elif currentLine[0] == "IFREE":
            freeInodes.append(int(currentLine[1]))
            #freeInodes.append(currentLine[1])
            # FORMAT: ifree, numFreeInodes
            #freeInodes.add(currentLine[1])
        elif currentLine[0] == "INODE":
            # FORMAT: inodes, inodeNum, fileType, mode, owner, group, linkCount,
            #         timeOfLastChange, timeOfModTime, timeOfLastAccess,
            #         fileSize, blockSize
            inodes[currentLine[1]] = currentLine
            # inodeNumber = currentLine[1]
            # fileType = currentLine[2]
            # checkInodes(inodeNumber, fileType)
        elif currentLine[0] == "DIRENT":
            dirents.add(currentLine[1])
        elif currentLine[0] == "INDIRECT":
            # All of these may need type conversions.
            indirects.append(currentLine)
    return


def checkGroup():
    return


def checkBfree():
    return


def check_block(indirection, block_number, inode_number, offset):
    status = ''
    if (int(block_number) < 0 or int(block_number) > numBlocks - 1):
        status = 'INVALID'
    elif (int(block_number) < firstFreeNode):
        status = 'RESERVED'
    else:
        # br = BlockRef(indirection, block_number, inode_number, offset)
        #blockReference[int(block_number)].append(
            #[indirection, inode_number, offset])
        return


    if indirection != "":
        print(status, indirection, 'BLOCK', block_number, 'IN INODE', inode_number, 'AT OFFSET', offset)
    else:
        print(status, 'BLOCK', block_number, 'IN INODE', inode_number, 'AT OFFSET', offset)


def checkInodes():
    freeInodeBeginning
    for line in inodes.values():
        for i in range(12, 24):
            if (int(line[i]) != 0):
                check_block('', line[i], line[1], i - 12)
        if (int(line[24]) != 0):
            check_block(       'INDIRECT', line[24], line[1], 12)
        if (int(line[25]) != 0):
            check_block('DOUBLE INDIRECT', line[25], line[1], 256 + 12)
        if (int(line[26]) != 0):
            check_block('TRIPLE INDIRECT', int(line[26]), line[1], (256 * 256) + 256 + 12)

        for entry in freeInodes:
            if int(line[1]) == int(entry):
                print("ALLOCATED INODE", int(line[1]), "ON FREELIST")

        allocatedInodes.append(int(line[1]))

    for i in range(freeInodeBeginning, numInodes+1):
        if i not in freeInodes and i not in allocatedInodes:
            print("UNALLOCATED INODE", i, "NOT ON FREELIST")

    return


def checkIndirects():
    indirectionType = ['', 'INDIRECT', 'DOUBLE INDIRECT', 'TRIPLE INDIRECT']
    for line in indirects:
        check_block(indirectionType[int(line[2])], line[5], line[1], line[3])
    #blockReference[int(line[5])].append(line[5], line[1], line[3])
    # Add block reference.


def checkAllocation():
    num = firstValidBlock
    for block in numBlocks:
        while num != block and num < 64:  # Why 64?
            print("UNREFERENCED BLOCK", num)


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Error: incorrect number of arguments \n")
        exit(1)

    readCSV(sys.argv[1])
    checkInodes()
    checkIndirects()


if __name__ == '__main__':
    main()
