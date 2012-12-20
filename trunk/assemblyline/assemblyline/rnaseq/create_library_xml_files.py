'''
Created on Aug 7, 2011

@author: mkiyer
'''
import os
import sys
import argparse
import logging
import xml.etree.cElementTree as etree

import assemblyline.rnaseq.lib.config as config 
from assemblyline.rnaseq.lib.base import indent_xml
from assemblyline.rnaseq.lib.libtable import read_library_table_xls, FRAGMENT_LAYOUT_PAIRED

def find_library_sequence_files(library, server):
    if library.seq_repo not in server.seq_dirs:
        logging.error("Library %s seq_repo '%s' not found" % (library.library_id, library.seq_repo))
        return None,None,None
    seq_dirs = server.seq_dirs[library.seq_repo]
    for seq_dir in seq_dirs:
        read1_files = []
        read2_files = []
        bam_files = []   
        found_files = True
        for filename in library.read1_files:
            fullpath = os.path.join(seq_dir, filename)
            if os.path.exists(fullpath) and os.path.isfile(fullpath):
                read1_files.append(fullpath)
            else:
                found_files = False
                break
        if library.fragment_layout == FRAGMENT_LAYOUT_PAIRED:
            for filename in library.read2_files:
                fullpath = os.path.join(seq_dir, filename)
                if os.path.exists(fullpath) and os.path.isfile(fullpath):
                    read2_files.append(fullpath)
                else:
                    found_files = False
                    break
        for filename in library.bam_files:
            fullpath = os.path.join(seq_dir, filename)
            if os.path.exists(fullpath) and os.path.isfile(fullpath):
                bam_files.append(fullpath)
            else:
                found_files = False
                break
        if found_files:
            return read1_files,read2_files,bam_files
    return None,None,None

def main():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("config_xml_file")
    parser.add_argument("server_name")    
    parser.add_argument("library_xls_file")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    # read configuration file
    logging.info("Reading pipeline configuration file '%s'" % (args.config_xml_file))
    pipeline = config.PipelineConfig.from_xml(args.config_xml_file)
    # get server information
    if args.server_name not in pipeline.servers:
        logging.error("Server %s not found" % (args.server_name))
    server = pipeline.servers[args.server_name]
    # read library file
    logging.info("Reading library table '%s'" % (args.library_xls_file))
    libraries = read_library_table_xls(args.library_xls_file)
    logging.info("Generating XML files at output directory '%s'" % (args.output_dir))
    for library in libraries.itervalues():
        # search for library sequence files
        read1_files, read2_files, bam_files = find_library_sequence_files(library, server)
        if read1_files is None:
            logging.error("Library %s sequence files not found" % (library.library_id))
            continue
        # update library sequence files
        library.read1_files = read1_files
        library.read2_files = read2_files
        library.bam_files = bam_files
        # check for valid data structure
        if not library.is_valid():
            logging.error("Library %s not valid" % (library.library_id))
            continue
        # add patient        
        root = etree.Element("library")
        library.to_xml(root)
        # indent for pretty printing
        indent_xml(root)
        # write to file
        output_file = os.path.join(args.output_dir, "%s.xml" % (library.library_id))        
        f = open(output_file, "w")
        print >>f, etree.tostring(root)
        f.close()  
    logging.info("Done")
    
if __name__ == '__main__': 
    sys.exit(main())
    