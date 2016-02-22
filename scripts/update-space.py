#!/usr/bin/env python
import commands
import logging
import re
import sys
import pycurl
import StringIO
from optparse import OptionParser
from dq2.info import TiersOfATLAS

"""
TODO: query DB to get list of tokens to update, not ToA
use command lcg-stmd
"""

_buffer = StringIO.StringIO()
_curl = pycurl.Curl()
_curl.setopt(pycurl.WRITEFUNCTION, _buffer.write)
_UPDATEURL = 'http://www.hep.lancs.ac.uk/~love/ukdata/update/'
#_UPDATEURL = 'http://lapb.lancs.ac.uk:8888/ukdata/update/'
_SRMMATCH = re.compile('token:(\S+):(srm://(.*):.*)')
_TOKENMATCH = re.compile('Space Reservation Tokens:\n(\S+)', re.DOTALL)
#_TOKENMATCH = re.compile('.+Space Reservation Tokens:\n(\S+)', re.DOTALL)
_SPACEMATCH = re.compile('.+totalSize:(\S+).+guaranteedSize:(\S+).+unusedSize:(\S+)', re.DOTALL)

def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-q", action="store_true", default=False,
                      help="quiet mode", dest="quiet")
    parser.add_option("-d", action="store_true", default=False,
                      help="debug mode", dest="debug")
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("incorrect number of arguments")
        return 1
    loglevel = 'INFO'
    if options.quiet:
        loglevel = 'WARNING'
    if options.debug:
        loglevel = 'DEBUG'

    logger = logging.getLogger()
    logger.setLevel(logging._levelNames[loglevel])
    fmt = '[UKDATA:%(levelname)s %(asctime)s] %(message)s'
    formatter = logging.Formatter(fmt, '%d %b %T')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)

    proxy = 'X509_USER_PROXY=/home/d0/love/certs/prod.out'
    
    labels = TiersOfATLAS.getSites('UKSITES')
    
    #labels = ['UKI-NORTHGRID-MAN-HEP1_LOCALGROUPDISK', 'UKI-NORTHGRID-MAN-HEP1_LOCALGROUPDISK']
    #labels = ['UKI-SCOTGRID-GLASGOW_MCDISK']
    #labels= ['UKI-NORTHGRID-LIV-HEP_MCDISK']
    #labels= ['UKI-SOUTHGRID-BHAM-HEP_MCDISK']
    #labels = [
    #        'UKI-LT2-IC-HEP_PRODDISK',
    #        'UKI-LT2-IC-HEP_MCDISK',
    #        'UKI-LT2-IC-HEP_DATADISK',
    #        'UKI-LT2-IC-HEP_HOTDISK',
    #        ]
    
    #labels = ['UKI-SOUTHGRID-SUSX_PRODDISK']
    
    try:
      labels.remove('UKI-SCOTGRID-GLASGOW_PPSDATADISK')
    except:
      pass
    try:
      labels.remove('RAL-LCG2_PPSDATADISK')
    except:
      pass
    
    for label in labels:
#        if 'SUSX' not in label: continue
        srm = TiersOfATLAS.getSiteProperty(label, 'srm')
        domain = TiersOfATLAS.getSiteProperty(label, 'domain')
        srmmatch = _SRMMATCH.match(srm)
        srmtok = srmmatch.group(1)
        srmpath = srmmatch.group(2)
        srmhost = srmmatch.group(3)
    
        cmd = '%s srm-get-space-tokens -retry_num=2 %s -space_desc=%s' % (proxy, srmpath, srmtok)
        logging.debug(cmd)
        status, output = commands.getstatusoutput(cmd)
    
        if status == 0:
            tokmatch = _TOKENMATCH.match(output)
            if tokmatch:
                tokenid = tokmatch.group(1)
                msg = "Found token ID %s: %s" % (srmtok, tokenid)
                logging.debug(msg)
            else:
                msg = "Token ID not found for %s at %s" % (srmtok, label)
                logging.warn(msg)
                continue
        else:
            msg = "Cannot get token ID using cmd %s" % cmd
            logging.warn(msg)
            continue
    
    
        # replace this with lcg-stmd
        cmd = '%s srm-get-space-metadata -retry_num=1 -space_tokens=%s %s' % (proxy, tokenid, srmpath)
        logging.debug(cmd)
        status, output = commands.getstatusoutput(cmd)
    
        if status == 0:
            spacematch = _SPACEMATCH.match(output)
            if spacematch:
                totsize = spacematch.group(1)
                freesize = spacematch.group(3)
            else:
                msg = "Cannot parse output: %s" % cmd
                logging.warn(msg)
                continue
        else:
            msg = "Cannot get srm-get-space-metadata for tokenid: %s" % tokenid
            logging.warn(msg)
            continue
    
        msg = "%s totalsize: %s freesize: %s" % (label, totsize, freesize)
        logging.info(msg)
    
        vals = (label, totsize, freesize)
        fields = "label=%s&tsize=%s&usize=%s" % vals
        _curl.setopt(pycurl.URL, _UPDATEURL)
        _curl.setopt(pycurl.POST, 1) 
        _curl.setopt(pycurl.POSTFIELDS, fields) 
#        _curl.setopt(pycurl.VERBOSE, True) 
        try:
            _curl.perform()
            _buffer.seek(0)
            if _curl.getinfo(pycurl.HTTP_CODE) != 200:
                msg = "failed: %s%s" % (_UPDATEURL, fields)
                logging.debug(msg)
                # read from start of buffer
                _buffer.seek(0)
                logging.debug(_buffer.read())
    
                for row in _buffer:
                    print row
                sys.exit(1)
    
        except pycurl.error:
            msg = "Problem contacting server: %s" % _UPDATEURL
            logging.error(msg)
            raise
    
    # hack for RAL FARM area
    label= 'RAL-LCG2_RALFARM'
    totsize = '102000000000000.0'
    freesize = '0.0'
    
    vals = (label, totsize, freesize)
    fields = "label=%s&tsize=%s&usize=%s" % vals
    _curl.setopt(pycurl.URL, _UPDATEURL)
    _curl.setopt(pycurl.POST, 1) 
    _curl.setopt(pycurl.POSTFIELDS, fields) 
    try:
        _curl.perform()
        _buffer.seek(0)
        code = _curl.getinfo(pycurl.HTTP_CODE)
        if code == 500:
            for row in _buffer:
                print row
            sys.exit(1)
    
    except pycurl.error:
        msg = "Problem contacting server: %s" % _UPDATEURL
        logging.error(msg)
        raise



if __name__ == "__main__":
#    c = statsd.StatsClient(host='py-heimdallr', port=8125)
#    stat = 'apfmon.monexpire'
#    start = time()
    rc = main()
#    elapsed = time() - start
#    c.timing(stat,int(elapsed))
    sys.exit(rc)
