import csv
import pytz
import re
import sys
from datetime import datetime, timedelta
from ukdata.models import Site, Space, Pattern, Tag, Storage, DDMSource, Token
from django.core import serializers
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import Q
import json as json

_TOKMATCH = re.compile('(\S+)_(\S+)')
_RED = 'B94A48'
_GREEN = '99CC99'

atlaspledge2009 = {
        'londont2' : 130,
        'northgrid' : 501,
        'scotgrid' : 358,
        'southgrid' : 200,
        }

atlaspledge2010 = {
        'londont2' : 712,
        'northgrid' : 926,
        'scotgrid' : 854,
        'southgrid' : 295,
        }

# These from WLCG
# http://gstat-wlcg.cern.ch/apps/capacities/pledge_comparison/
atlaspledge2012 = {
        'londont2' : 1688,
        'northgrid' : 2169,
        'scotgrid' : 1290,
        'southgrid' : 728,
        }

atlaspledge2013 = {
        'londont2' : 1609,
        'northgrid' : 1841,
        'scotgrid' : 1120,
        'southgrid' : 729,
        }

atlaspledge2015 = {
        'londont2' : 1427,
        'northgrid' : 1874,
        'scotgrid' : 1111,
        'southgrid' : 888,
        }

atlaspledge2016 = {
        'londont2' : 2430,
        'northgrid' : 3182,
        'scotgrid' : 1845,
        'southgrid' : 1530,
        }

# https://www.gridpp.ac.uk/tier-2-gridpp-pledge-levels/
atlaspledge2018 = {
        'londont2' : 2993,
        'northgrid' : 3948,
        'scotgrid' : 2982,
        'southgrid' : 1027,
        }

latestpledge = atlaspledge2018

#    atlaspledge2011 = {
#            'londont2' : 898,
#            'northgrid' : 1168,
#            'scotgrid' : 1077,
#            'southgrid' : 371,
#            }

# These from WLCG pdf 
# http://lcg.web.cern.ch/LCG/Resources/
#    atlaspledge2011 = {
#            'londont2' : 1342,
#            'northgrid' : 1539,
#            'scotgrid' : 1237,
#            'southgrid' : 582,
#            }

def maint(request):
    """
    Rendered maintenance page
    """
    return render_to_response('ukdata/maint.html')

def cpu(request):
    context = {}
    return render_to_response('ukdata/cpu.html', context)

def step09(request):
    return redirect('https://twiki.cern.ch/twiki/bin/view/Atlas/Step09Feedback')

def index(request):
    """
    Rendered view of font page
    """

# These from GridPP spreadsheet

    t1 = Token.objects.filter(name__contains='RAL-LCG')
    t2 = Token.objects.filter(name__contains='UKI')
    tokens = t1 | t2
#    tokens.exclude(name='RAL-LCG2_PPSDATADISK')
    sites = Site.objects.all().order_by('name')
    t1sites = sites.filter(tags__name='tier1')
    t2sites = sites.filter(tags__name='tier2')

    srmtoks = [
                'ATLASDATADISK',
#                'ATLASGROUPDISK',
                'ATLASHOTDISK',
                'ATLASLOCALGROUPDISK',
#                'ATLASMCDISK',
#                'ATLASMCTAPE',
                'ATLASPRODDISK',
                'ATLASSCRATCHDISK',
                ]
    
    usageurl = "http://chart.apis.google.com/chart?cht=bhs&chd=t:%.1f|%.1f&" + \
               "chs=96x16&" + \
               "chco=%s,%s&" % (_RED, _GREEN) + \
               "chxt=x,y&chxs=0,990000,0,0,_|1,999900,0,0,_&chds=0,%.1f"

    t1pledge = []
    t1rows = []
    for site in t1sites:
        t1row = {}
        t1row['s'] = site
        if site.total > site.wlcg2018:
            t1row['p'] = 'pass'
        else:
            t1row['p'] = 'fail'
        if site.total > site.wlcg2018:
            t1pledge.append('pass')
        else:
            t1pledge.append('fail')

        t1row['url'] = usageurl % (site.used, site.unused, site.total)
        t1rows.append(t1row)

    t2tots = {}
    t2tots['pledge'] = 0
    t2tots['wpledge'] = 0
    t2tots['size'] = 0
    t2tots['wsize'] = 0
    t2tots['used'] = 0
    t2tots['unused'] = 0


    t2rows = []
    for site in t2sites:
        t2row = {}
        t2row['s'] = site
        t2row['wpledge'] = 1.00 * site.wlcg2018
        t2row['localtax'] = site.wlcg2018 + 0.20 * site.wlcg2018
        dtdead = datetime.now() - timedelta(days=10)
        try:
            localtoks = Token.objects.filter(srm__site=site, name='ATLASLOCALGROUPDISK', last_modified__gt=dtdead)
        except Token.DoesNotExist:
            print "No localgroupdisk for %s" % fedsite.name
        localdisk = 0
        for localtok in localtoks:
            localdisk +=  localtok.total
        t2row['wsize'] = site.total # include localgroupdisk
        if t2row['wsize'] > t2row['wpledge']:
            t2row['w'] = 'pass'
        else:
            t2row['w'] = 'fail'
        if site.total > site.wlcg2018:
            t2row['p'] = 'pass'
        else:
            t2row['p'] = 'fail'
        if site.total > t2row['localtax']:
            t2row['tax'] = 'softpass'
        else:
            t2row['tax'] = 'softfail'

        t2row['url'] = usageurl % (site.used, site.unused, site.total)

        t2tots['pledge'] += site.wlcg2018
        t2tots['wpledge'] += t2row['wpledge']
        t2tots['wsize'] += t2row['wsize']
        t2tots['size'] += site.total
        t2tots['used'] += site.used
        t2tots['unused'] += site.unused

        t2rows.append(t2row)


    fedrows = []
    fedtots = {}
    fedtots['total'] = 0
    fedtots['p'] = 0
    for fed in latestpledge.keys():
        fedrow = {}
        fedrow['name'] = fed
        fedrow['pledge'] = latestpledge[fed]
        fedrow['total'] = 0
        fedsites = sites.filter(tags__name=fed)
        dtdead = datetime.now() - timedelta(days=10)
        for fedsite in fedsites:
            try:
                localtoks = Token.objects.filter(srm__site=fedsite, name='ATLASLOCALGROUPDISK', last_modified__gt=dtdead)
            except Token.DoesNotExist:
                print "No localgroupdisk for %s" % fedsite.name
            nonlocal = fedsite.total
            for localtok in localtoks:
                nonlocal -=  localtok.total
            fedrow['total'] += nonlocal
        if fedrow['total'] > latestpledge[fed]:
            fedrow['p'] = 'pass'
        else:
            fedrow['p'] = 'fail'
        fedtots['total'] += fedrow['total']
        fedtots['p'] += latestpledge[fed]

        fedrows.append(fedrow)

    usageurl = "http://chart.apis.google.com/chart?cht=bhs&chd=t:%.1f|%.1f" + \
               "&chs=96x16&chco=%s,%s" % (_RED, _GREEN) + \
               "&chxt=x,y&chxs=0,990000,0,0,_|1,999900,0,0,_&chds=0,%s"

    context = {
                't2tots' : t2tots,
                't1pledge' : t1pledge,
                't1sites' : t1sites,
                't2sites' : t2sites,
                'srmtoks' : srmtoks,
                'url' : usageurl,
                'fedrows' : fedrows,
                'fedtots' : fedtots,
                't1rows' : t1rows,
                't2rows' : t2rows,
                'red' : _RED,
                'green' : _GREEN,
              }

    return render_to_response('ukdata/index.html', context)

def raw(request):
    """
    Rendered view of raw label data
    """

    labels = DDMSource.objects.all()

    context = {
                'labels' : labels,
              }

    return render_to_response('ukdata/raw.html', context)

def rawbysite(request):
    """
    Return data of site usage in json format
    """

    data = Site.objects.values('name', 'total', 'used', 'unused', 'wlcg2018')
    for d in data:
        if d['total'] > d['wlcg2018']:
            d['delivered'] = True
        else:
            d['delivered'] = False
        
    return HttpResponse(json.dumps(list(data), sort_keys=True, indent=2), mimetype="application/json")

def toa(request):
    """
    update the ToA information
    For each set of info received,
    1. ensure Site is defined
    2. add/get Storage object for each SRM
    3. add/get Token object for each Token
    4. add/get DDSource object for each label
    """
    
#    print request.POST.items()
    label = request.POST.get('label', None)
    sitename = request.POST.get('site', None)
    srm = request.POST.get('srm', None)
    srmtok = request.POST.get('srmtok', None)
    srmpath = request.POST.get('srmpath', None)
    srmhost = request.POST.get('srmhost', None)
    dom = request.POST.get('domain', None)

    try:
        s = Site.objects.get(name=sitename)
    except Site.DoesNotExist:
        content = "Site DoesNotExist: %s\n" % sitename
        return HttpResponseBadRequest(content, mimetype="text/plain")

    try:
        se = Storage.objects.get(site=s, name=srmhost)
    except Storage.DoesNotExist:
        se = Storage(site=s, name=srmhost)
        se.save()

    try:
        t = Token.objects.get(srm=se, name=srmtok)
    except Token.DoesNotExist:
        t = Token(srm=se, name=srmtok)
        t.save()
        
    if t.name != srmtok:
        t.name = srmtok
        t.save()

    try:
        ddmlabel = DDMSource.objects.get(name=label)
    except DDMSource.DoesNotExist:
        ddmlabel = DDMSource(name=label, token=t, url=srm, domain=dom)
        ddmlabel.save()

    if ddmlabel.token != t:
        ddmlabel.token = t
        ddmlabel.save()

    return HttpResponse("UPDATED OK %s" % t.name, mimetype="text/plain")


def update(request):
    """
    update the Token space information, assumes DB up-to-date
    """
    
    #print request.POST.items()
    label = request.POST.get('label', None)
    # receive these in bytes but store in terabytes as float
    tsize = request.POST.get('tsize', None)
    usize = request.POST.get('usize', None)

    try:
        ddm = DDMSource.objects.get(name=label)
    except DDMSource.DoesNotExist:
        content = "DDMSource DoesNotExist: %s\n" % label
        return HttpResponseBadRequest(content, mimetype="text/plain")
        
    t = ddm.token

    bytesperT = float(1000*1000*1000*1000)
    if tsize: totalT = float(tsize)/bytesperT
    else: totalT = 0.0
    if usize: unusedT = float(usize)/bytesperT
    else: unusedT = 0.0
    usedT = (float(tsize)-float(usize))/bytesperT
    # historic sizes
    s = Space(token=t)
    s.total = totalT
    s.used = usedT
    s.unused = unusedT
    try:
        s.save()
    except:
        print 'PROBLEM saving Space()'
        raise

    # add latest sizes to Token
    t.total = s.total
    t.unused = s.unused
    t.used = s.total - s.unused
    try:
        t.save()
    except:
        print 'PROBLEM updating token:', t
        #raise
    
    srm = t.srm
    srm.total = 0
    srm.used = 0
    srm.unused = 0
    srmtoks = Token.objects.filter(srm=srm)
    srmtoks = srmtoks.exclude(name='ATLASMCDISK')
    dtdead = datetime.now() - timedelta(days=10)
    srmtoks = srmtoks.filter(last_modified__gt=dtdead)
    for token in srmtoks:
        srm.total += token.total
        srm.used += token.used
        srm.unused += token.unused
    srm.save()

    site = srm.site
    site.total = 0
    site.used = 0
    site.unused = 0
    sitesrms = Storage.objects.filter(site=site)
    for srm in sitesrms:
        site.total += srm.total
        site.used += srm.used
        site.unused += srm.unused

    site.save()

    return HttpResponse("UPDATED OK %s" % t.name, mimetype="text/plain")

def dsusage(request):
    """
    update dataset usage
    """

    tok = request.POST.get('token', None)
    pat = request.POST.get('name', None)
    regex = request.POST.get('regex', None)
    # receive these in bytes but store in terabytes as float
    bytes = request.POST.get('bytes', None)
    nfiles = request.POST.get('nfiles', None)
    ndatasets = request.POST.get('ndatasets', None)
    complete = request.POST.get('complete', None)
    analy = request.POST.get('analy', None)
    
    try:
        t = Token.objects.get(name=tok)
    except Token.DoesNotExist:
        content = "Token DoesNotExist: %s\n" % tok
        return HttpResponseBadRequest(content, mimetype="text/plain")

    p = Pattern(token=t)
    bytesperT = float(1000*1000*1000*1000)
    if bytes: p.tb = float(bytes)/bytesperT
    else: p.tb = 0.0
    if regex: p.regex = regex
    if nfiles: p.nfiles = int(nfiles)
    if ndatasets: p.ndatasets = int(ndatasets)
    if complete: p.complete = int(complete)
    p.name = pat
    try:
        p.save()
    except:
        print 'PROBLEM saving Pattern()'
        raise

    return HttpResponse("UPDATED OK %s" % p.name, mimetype="text/plain")


def token(request, t):
    """
    Rendered summary of space token
    """

    atlas = Tag.objects.get(name='atlas')
    t1site = Site.objects.get(name='RAL-LCG2')
    tokens = Token.objects.filter(name=t)
    tokens = tokens.filter(srm__site__tags__name='tier2')
    tokens = tokens.exclude(name__contains='PPS').order_by('srm__site__name')
    dtdead = datetime.now() - timedelta(days=10)
    tokens = tokens.filter(last_modified__gt=dtdead)

    if not tokens:
        raise Http404

    rows = []
    tots = {}
    tots['sizetot'] = 0
    tots['freetot'] = 0
    tots['usedtot'] = 0
    # Used|Unused
    url = "http://chart.apis.google.com/chart?cht=bhs&chd=t:%.2f|%.2f&chs=96x16" + \
          "&chco=%s,%s" % (_RED, _GREEN) + \
          "&chxt=x,y&chxs=0,990000,0,0,_|1,999900,0,0,_&chds=0,%s"
    for token in tokens:
        state = 'pass'
        freestate = 'pass'
        warnat = 2.0
        failat = 1.0
        if t == 'ATLASHOTDISK':
          warnat = 0.2
          failat = 0.1
        if token.unused <= warnat: freestate = 'warn'
        if token.unused <= failat: freestate = 'fail'

        try:
            percentused = 100 * (token.total - token.unused)/token.total
        except ZeroDivisionError:
            percentused = 0

        try:
          tokenfrac = 100 * token.total / token.srm.site.wlcg2018
        except ZeroDivisionError, e:
          tokenfrac = 0

        tab = {
            'site' : token.srm.site,
            'srm' : token.srm,
            'size' : token.total,
            'used' : token.total - token.unused,
            'percentused' : percentused,
            'tokenfrac' : tokenfrac,
            'free' : token.unused,
            'state' : state,
            'freestate' : freestate,
            'stamp' : token.last_modified,
            'usageurl' : url % (token.total - token.unused, token.unused, '%.2f'),
            }
        tots['sizetot'] += tab['size']
        tots['usedtot'] += tab['used']
        tots['freetot'] += tab['free']
        rows.append(tab)

    for tab in rows:
    # rescale bar chart with grand total
    #    tab['usageurl'] = tab['usageurl'] % tots['sizetot']
    # rescale with token total
        tab['usageurl'] = tab['usageurl'] % tab['size']

    try:
        pused = 100 * tots['usedtot'] / tots['sizetot']
        pfree = 100 * tots['freetot'] / tots['sizetot']
    except ZeroDivisionError, e:
        print e
        pused = 100
        pfree = 0
    tots['usageurl'] = url % (tots['usedtot'], tots['freetot'], tots['sizetot'])

    aux = {
           'tots' : tots,
           'warnat' : warnat,
           'failat' : failat,
           'thistok' : t,
           't1site' : t1site,
        }

    context = {
                'aux' : aux,
                'rows' : rows,
            }

    return render_to_response('ukdata/token.html', context)

def site(request, sid):
    """
    Rendered summary of site
    """

    atlas = Tag.objects.get(name='atlas')
    tier1 = Tag.objects.get(name='tier1')
    site = get_object_or_404(Site, id=sid)
    srms = Storage.objects.filter(site=site)
    tokens = Token.objects.filter(srm__site=site)
    tokens = tokens.exclude(name='ATLASMCDISK')
    dtdead = datetime.now() - timedelta(days=10)
    tokens = tokens.filter(last_modified__gt=dtdead)
    istier1 = False
    if tier1 in site.tags.all(): istier1 = True

    rows = []
    tots = {}
    tots['sizetot'] = 0
    tots['freetot'] = 0
    tots['usedtot'] = 0
    # Used|Unused
    url = "http://chart.apis.google.com/chart?cht=bhs&chd=t:%.1f|%.1f&chs=96x16" + \
          "&chco=%s,%s" % (_RED, _GREEN) + \
          "&chxt=x,y&chxs=0,990000,0,0,_|1,999900,0,0,_&chds=0,%s"
    for srm in srms:
        tots['sizetot'] += srm.total
        tots['freetot'] += srm.unused

    used = tots['sizetot'] - tots['freetot']
    tots['usageurl'] = url % (used, tots['freetot'], tots['sizetot'])

    aux = {
           'tots' : tots,
           'thissite' : site,
        }

    tokurls = []
    tokfrac = []
    for srm in srms:
        frac = ""
        legend = ""
        for t in Token.objects.filter(srm=srm):
            try:
                val = int(100*(t.total/t.srm.total))
            except ZeroDivisionError:
                val = 0
            frac += "%s," % val
            legend += "%s|" % t.name[5:]
        legend = legend[:-1]
        frac = frac[:-1]
        tokfrac.append(frac)
        url = "http://chart.apis.google.com/chart?cht=p&chd=t:%s&chs=450x130&chl=%s" 
        tokurl = url % (frac, legend)
        tokurls.append(tokurl)
    
    context = {
                'tokurl' : tokurl,
                'tokurls' : tokurls,
                'tokfrac' : tokfrac,
                'tokens' : tokens,
                'srms' : srms,
                'aux' : aux,
                'istier1' : istier1,
                'red' : _RED,
                'green' : _GREEN,
            }

    return render_to_response('ukdata/site.html', context)

def fwd(request, label):
    """
    Modify the Forward check date to be 'now'
    """

    try:
        ddm = DDMSource.objects.get(name=label)
    except:
        content = "Bad request"
        return HttpResponseBadRequest(content, mimetype="text/plain")

    token = ddm.token

    token.fwdcheck=datetime.now()
    token.save()

    return HttpResponse("OK", mimetype="text/plain")

def rev(request, label):
    """
    Modify the Forward check date to be 'now'
    """

    print request, label
    try:
        ddm = DDMSource.objects.get(name=label)
    except:
        content = "Bad request"
        return HttpResponseBadRequest(content, mimetype="text/plain")

    token = ddm.token

    token.revcheck=datetime.now()
    token.save()

    return HttpResponse("OK", mimetype="text/plain")


def localgroup(request, token='LOCALGROUPDISK'):
    """
    LOCALGROUPDISK
    """

    rows = {'key' : 'val',
            }

    context = {
              'rows' : rows,
               }

    return HttpResponse(json.dumps(rows, sort_keys=True, indent=2), mimetype="application/json")

