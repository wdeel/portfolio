import java.io.*;
import java.util.*;
import java.nio.*;

public class Functions {

    // private variables
    private int sets;
    private int sets_size;
    private int line_size;
    private int index;
    private int offset;
    private int accesses;
    private int totalHits;
    private int totalMisses;
    private String stat;
    private int memRefs;
    private List<String>address;
    private List<String>readWrite;
    private BufferedReader reader;

    // constructor
    Functions(String inFile) {
        sets = 0;
        sets_size = 0;
        line_size = 0;
        index = 0;
        offset = 0;
        accesses = 0;
        totalHits = 0;
        totalMisses = 0;
        memRefs = -1;
        stat = "";
        address = new ArrayList<String>();
        readWrite = new ArrayList<String>();

        // opens a reader and writer for reading the input file and writing the output file
        try { reader = new BufferedReader(new FileReader(inFile)); }
        catch (Exception e) {
            System.err.format("Exception occured");
            e.printStackTrace();
        }
    }

    // pulls sets, sets_size, and line_size from beginning of file
    public void parseHeader() {
        String line;

        try {
            // get sets 
            line = reader.readLine();
            line = line.substring(line.indexOf(":") + 1).trim();
            sets = Integer.parseInt(line);

            // get sets_size
            line = reader.readLine();
            line = line.substring(line.indexOf(":") + 1).trim();
            sets_size = Integer.parseInt(line);

            // get line_size
            line = reader.readLine();
            line = line.substring(line.indexOf(":") + 1).trim();
            line_size = Integer.parseInt(line);
        }
        catch (Exception e) {
            System.err.format("Exception occured"); 
            e.printStackTrace();
        }
    }

    // reads rest of info from file
    public void readFile() {
        String line;
        String addr;
        String read;

        try {
            // get reads and addresses and adds them to lists
            while ((line = reader.readLine()) != null) {
                read = line.replaceAll("[:a-z0-9]", "");
                addr = line.substring(line.indexOf(":") + 1).trim();
                if (read.equals("R")) {
                    address.add(addr);
                    readWrite.add("read");
                    accesses++;
                }
                else if (read.equals("W")) {
                    address.add(addr);
                    readWrite.add("write");
                    accesses++;
                }
            }
            reader.close();
        }
        catch (Exception e) {
            System.err.format("Exception occured"); 
            e.printStackTrace();
        }
    }

    // writes header info at top of file
    public void writeHeader() {
        System.out.println("Cache Configuration\n");
        System.out.println("       " + sets + " " + sets_size + "-way set associative entries");
        System.out.println("       of line size " + line_size + " bytes\n");
        System.out.println("Access Address    Tag   Index Offset Status Memrefs");
        System.out.println("------ ------- ------- ------ ------ ------ -------");
    }

    // simulates cache hits and misses with an array of linked lists
    // I went with an array of linked lists because I thought it would be the easiest way
    // to maintain LRU cache accesses by keeping them at the tail of the linked list and just using .removeLast()
    // to evict them when their associated block is full
    public void writeData(ArrayList<LinkedList<Integer>> cache) {
        // get offset mask
        int offsetMask = getMask(offset);
        // get index mask
        int indexMask = getMask(index);

        // iterates through all hex addresses and simulates cache hits/misses
        for (int i=0; i<address.size(); i++) {
            // get decimal representation of hex address
            int decNum = Integer.parseInt(address.get(i), 16);
            // get cache index
            int cacheIndex = getIndex(decNum, indexMask);
            // get tag 
            int tag = getTag(decNum);

            // check if cache index is empty (miss)
            if (cache.get(cacheIndex).size() == 0) {
                cache.get(cacheIndex).addFirst(tag);
                setStatus("miss");
                setMemRefs(1);
                totalMisses++;
            }
            // check if it's there (hit)
            else if (cache.get(cacheIndex).contains(tag)) {
                // remove it and add it to the front (for LRU sim)
                cache.get(cacheIndex).addFirst(tag);
                cache.get(cacheIndex).removeLastOccurrence(tag);
                setStatus("hit");
                setMemRefs(0);
                totalHits++;
            }
            // check if it's not in the cache and there's an available set
            else if ((!cache.get(cacheIndex).contains(tag)) && cache.get(cacheIndex).size() < sets_size) { 
                cache.get(cacheIndex).addFirst(tag);
                setStatus("miss");
                setMemRefs(1);
                totalMisses++;
            }
            // otherwise the cache is full and LRU needs to be evicted
            // and new tag should be added to the front
            else {
                cache.get(cacheIndex).removeLast();
                cache.get(cacheIndex).addFirst(tag);
                setStatus("miss");
                setMemRefs(1);
                totalMisses++;
            } 

            // prints info for each memory address
            String line = String.format("%1$6s %2$7s %3$7s %4$6s %5$6s %6$6s %7$7s", 
                readWrite.get(i), address.get(i), getTag(decNum), getIndex(decNum, indexMask), 
                getOffset(decNum, offsetMask), getStatus(), getMemRefs());

            System.out.println(line);
        }
        System.out.println();
    }

    // sets status (hit or miss)
    public void setStatus(String status) {
        stat = status;
    }

    // sets memRefs (1 or 0)
    public void setMemRefs(int num) {
        memRefs = num;
    }

    // takes log2 of line_size to get offset size (number of bits)
    public void setOffset() {
        offset = (int) (Math.log(line_size) / Math.log(2));        
    }

    // takes log2 of sets to get index size (number of bits)
    public void setIndex() {
        index = (int) (Math.log(sets) / Math.log(2));
    }

    // gets the tag portion of the address (decimal representation)
    public Integer getTag(int decNum) {
        decNum >>= offset;
        return decNum >> index;
    }

    // returns # of sets
    public int getSets() {
        return sets;
    }

    // returns sets_size
    public int getsetSize() {
        return sets_size;
    }

    // returns line_size
    public int getlineSize() {
        return line_size;
    }

    // gets index of address
    public Integer getIndex(int decNum, int indexMask) {
        indexMask <<= offset;
        decNum &= indexMask;
        return decNum >>= offset;
    }

    // gets offset of addrsess
    public Integer getOffset(int decNum, int offsetMask) {
        return decNum & offsetMask;
    }

    // gets mask used for getting tag and offset of address
    public Integer getMask(int num) {
        int sum = 0;
        for (int i=0; i<num; i++)
            sum += Math.pow(2, i);
        return sum;
    }

    // returns status (hit or miss) when doing cache lookup
    public String getStatus() {
        return stat;
    }

    // returns whether a memory reference was needed (miss)
    public Integer getMemRefs() {
        return memRefs;
    }

    // writes summary info at end of file and closes file writer
    public void writeSummary() {
        System.out.println("Simulation Summary Statistics\n-----------------------------");
        System.out.println("Total hits       : " + totalHits);
        System.out.println("Total misses     : " + totalMisses);
        System.out.println("Total accesses   : " + accesses);
        System.out.println("Hit ratio        : " + (float) totalHits/accesses);
        System.out.println("Miss ratio       : " + (float) totalMisses/accesses);
    }
}