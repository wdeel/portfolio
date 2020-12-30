import sys

def main():
    outstr = "sets:16\nset_size:4\nline_size:4\n"
    with open(sys.argv[1], 'w+') as of:
        for i in range(512):
            outstr = outstr + "R:" + hex(i)[2:] + "\n"
        of.write(outstr)

main()