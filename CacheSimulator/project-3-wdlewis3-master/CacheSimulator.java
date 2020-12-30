import java.util.*;

public class CacheSimulator {
    public static void main(String args[]) {

        if (args.length < 1) {
            System.out.println("\n********Error*******\n Input file and/or Output file not specified\n" + 
                "Terminating Program\n");
            return;
        }

        Functions Cache = new Functions(args[0]);

        // get size, set_size, line_size
        Cache.parseHeader();

        // get # of sets for cache array of linked lists
        int rows = Cache.getSets();

        // declare cache array of linked lists 
        ArrayList<LinkedList<Integer>> cacheSim = new ArrayList<>();
        for (int i=0; i<rows; i++) {
            LinkedList<Integer> row = new LinkedList<Integer>();
            cacheSim.add(row);
        }

        // set offset
        Cache.setOffset();

        // set index
        Cache.setIndex();

        // get rest of file
        Cache.readFile();
        
        // print header info
        Cache.writeHeader();

        // print main data
        Cache.writeData(cacheSim);

        // print summary data
        Cache.writeSummary();
    }
}