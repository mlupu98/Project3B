#! /usr/local/cs/bin/python3

import sys
from collections import defaultdict
from collections import namedtuple

BlockRef = namedtuple(
    'BlockRef', ['indirection', 'block_num', 'inode_num', 'offset'])

lines = []                              # list of pre-split lines from the csv file
# maps block numbers to a set of BlockRef tuples
block_references = defaultdict(set)
free_blocks = set()                     # set of free block numbers
inodes = {}                             # maps inodes to line arrays
free_inodes = set()                     # set of free inode numbers
indirects = []                          # list of pre-split indirect lines
total_blocks = None
first_non_reserved_block = None
first_non_reserved_inode = None
total_inodes = None
dirents = []                            # list of pre-split dirent lines


def parse_csv():
    global lines, block_references, free_blocks, inodes, indirects, free_inodes
    global first_non_reserved_inode, total_inodes, total_blocks, first_non_reserved_block
    for line in lines:
        if line.startswith('SUPERBLOCK'):
            sb_fields = line.split(',')
            total_blocks, block_size, inode_size, first_non_reserved_inode, total_inodes = map(int,
                                                                                               (sb_fields[1], sb_fields[3], sb_fields[4], sb_fields[7], sb_fields[2]))
        elif line.startswith('INODE'):
            i_fields = line.split(',')
            inodes[i_fields[1]] = i_fields
        elif line.startswith('GROUP'):
            g_fields = line.split(',')
            num_inodes, inode_table_offset = map(
                int, (g_fields[3], g_fields[8]))
            first_non_reserved_block = inode_table_offset + \
                ((inode_size * num_inodes) / block_size)
        elif line.startswith('INDIRECT'):
            ind_fields = line.split(',')
            indirects.append(ind_fields)
        elif line.startswith('BFREE'):
            free_blocks.add(int(line.split(',')[1]))
        elif line.startswith('IFREE'):
            free_inodes.add(int(line.split(',')[1]))
        elif line.startswith('DIRENT'):
            dirent_fields = line.split(',')
            dirents.append(dirent_fields)


def block_consistency_audit():
    # Takes an int block number and returns its status
    # Either INVALID, RESERVED, or VALID
    def check_block(indirection, block_number, inode_number, offset):
        status = ''
        if (int(block_number) < 0 or int(block_number) > total_blocks - 1):
            status = 'INVALID'
        elif (int(block_number) < first_non_reserved_block):
            status = 'RESERVED'
        else:
            br = BlockRef(indirection, block_number, inode_number, offset)
            block_references[int(block_number)].add(br)
            return
        if (indirection):
            print('{} {} BLOCK {} IN INODE {} AT OFFSET {}'
                  .format(status, indirection, block_number, inode_number, offset))
        else:
            print('{} BLOCK {} IN INODE {} AT OFFSET {}'
                  .format(status, block_number, inode_number, offset))

    # Examine every inode pointer in every inode
    # This includes all direct pointers as well as the
    # single variable indirect pointer for each level.
    for inode_line in inodes.values():
        for i in range(12, 24):
            if (int(inode_line[i]) != 0):
                check_block('', inode_line[i], inode_line[1], i - 12)
        if (int(inode_line[24]) != 0):
            check_block('INDIRECT', inode_line[24], inode_line[1], 12)
        if (int(inode_line[25]) != 0):
            check_block('DOUBLE INDIRECT',
                        inode_line[25], inode_line[1], 256 + 12)
        if (int(inode_line[26]) != 0):
            check_block('TRIPLE INDIRECT',
                        inode_line[26], inode_line[1], (256 * 256) + 256 + 12)

    # Process the indirect lines by checking them
    # Then insert them into block_references
    for indir_line in indirects:
        indirection_map = ['', 'INDIRECT',
                           'DOUBLE INDIRECT', 'TRIPLE INDIRECT']
        check_block(indirection_map[int(indir_line[2])],
                    indir_line[5], indir_line[1], indir_line[3])
        br = BlockRef(indirection_map[int(indir_line[2])],
                      indir_line[5], indir_line[1], indir_line[3])
        block_references[int(indir_line[5])].add(br)

    # Manage block consistency
    # UNREFERENCED - A block is not in the free list and not referenced by inode
    # ALLOCATED - A block is referenced by an inode but also on the free list
    # DUPLICATE - A block is referenced by more than one inode
    for block_num in range(8, total_blocks):
        if (block_num not in free_blocks) and (block_num not in block_references):
            print("UNREFERENCED BLOCK {}".format(block_num))
        elif block_num in free_blocks and block_num in block_references:
            print("ALLOCATED BLOCK {} ON FREELIST".format(block_num))
        elif len(block_references[block_num]) > 1:
            for br in block_references[block_num]:
                if (br.indirection):
                    print("DUPLICATE {} BLOCK {} IN INODE {} AT OFFSET {}"
                          .format(br.indirection, br.block_num, br.inode_num, br.offset))
                else:
                    print("DUPLICATE BLOCK {} IN INODE {} AT OFFSET {}"
                          .format(br.block_num, br.inode_num, br.offset))


def inode_allocation_audit():
    # Build unallocated and allocated lists
    temp_unallocated, temp_allocated = set(), set()
    for inode_line in inodes.values():
        inode_number, inode_file_type = inode_line[1], inode_line[2]
        if inode_file_type == '0':
            temp_unallocated.add(int(inode_number))
        else:
            temp_allocated.add(int(inode_number))

    # Compare unallocated list to free list
    for inode_number in temp_unallocated:
        if (int(inode_number) not in free_inodes):
            print("UNALLOCATED INODE {} NOT ON FREELIST".format(inode_number))

    # Compare allocated list to free list
    for inode_number in temp_allocated:
        if (int(inode_number) in free_inodes):
            print("ALLOCATED INODE {} ON FREELIST".format(inode_number))

    # Compare unallocated non-reserved inodes to the free list
    for inode_number in range(first_non_reserved_inode, total_inodes):
        if inode_number not in temp_allocated and inode_number not in free_inodes:
            print("UNALLOCATED INODE {} NOT ON FREELIST".format(inode_number))


def directory_consistency_audits():
    # Check consistency between link counts in inodes
    # and link counts when traversing directories
    # maps inode number to its reference count
    inode_reference_counts = defaultdict(int)
    for dirent_line in dirents:
        inode_reference_counts[int(dirent_line[3])] += 1
    for inode_number, inode_line in inodes.items():
        record_inode_link_count = int(inode_line[6])
        discovered_inode_link_count = inode_reference_counts[int(inode_number)]
        if (record_inode_link_count != discovered_inode_link_count):
            print("INODE {} HAS {} LINKS BUT LINKCOUNT IS {}".format(inode_number,
                                                                     str(discovered_inode_link_count), str(record_inode_link_count)))

    # Directory entries should only refer to valid and allocated I-nodes.
        # INVALID - inode number is less than 1 or greater than inode number of last inode in system
        # UNALLOCATED - inode number exists in free inode list

    childToParent = {}  # maps child inode to parent inode

    # check validity and allocation status of each referenced inode
    # create mapping of valid and allocated child inode to parent inode
    for dirent_line in dirents:
        inode_number, ref_inode_number, dirent_name = int(
            dirent_line[1]), int(dirent_line[3]), str(dirent_line[6])
        if ref_inode_number in free_inodes and str(ref_inode_number) not in inodes:
            print("DIRECTORY INODE {} NAME {} UNALLOCATED INODE {}".format(
                inode_number, dirent_name, ref_inode_number))
        elif ref_inode_number < 1 or ref_inode_number > total_inodes:
            print("DIRECTORY INODE {} NAME {} INVALID INODE {}".format(
                inode_number, dirent_name, ref_inode_number))
        elif (dirent_name != "'.'" and dirent_name != "'..'"):
            childToParent[ref_inode_number] = inode_number

    # check correctness of '.' and '..' links
    # on linux, inode 2 is root directory so '.' and '..' both point to itself
    childToParent[2] = 2
    for dirent_line in dirents:
        inode_number, ref_inode_number, dirent_name = int(
            dirent_line[1]), int(dirent_line[3]), str(dirent_line[6])
        if (dirent_name == "'.'" and ref_inode_number != inode_number):
            print("DIRECTORY INODE {} NAME '.' LINK TO INODE {} SHOULD BE {}"
                  .format(inode_number, ref_inode_number, inode_number))
        elif (dirent_name == "'..'" and (inode_number not in childToParent.keys() or ref_inode_number != childToParent[inode_number])):
            print("DIRECTORY INODE {} NAME '..' LINK TO INODE {} SHOULD BE {}"
                  .format(inode_number, ref_inode_number, childToParent[inode_number]))


def main():
    global lines

    # Check for correct argument
    if len(sys.argv) != 2:
        sys.stderr.write('Error: incorrect args!')
        sys.exit()

    # Parse in lines from file
    with open(sys.argv[1], 'r') as f:
        lines = [x.strip() for x in f.readlines()]

    parse_csv()
    block_consistency_audit()
    inode_allocation_audit()
    directory_consistency_audits()


if __name__ == "__main__":
    main()
