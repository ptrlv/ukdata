from django.db import models

SRMTYPE = (
            ('dpm', 'DPM'),
            ('dcache', 'DCACHE'),
          )
TOKENS = (
            ('ATLASRALFARM', 'ATLASRALFARM'),
            ('ATLASDATADISK', 'ATLASDATADISK'),
            ('ATLASMCDISK', 'ATLASMCDISK'),
            ('ATLASMCTAPE', 'ATLASMCTAPE'),
            ('ATLASHOTDISK', 'ATLASHOTDISK'),
            ('ATLASPRODDISK', 'ATLASPRODDISK'),
            ('ATLASSCRATCHDISK', 'ATLASSCRATCHDISK'),
            ('ATLASGROUPDISK', 'ATLASGROUPDISK'),
            ('ATLASLOCALGROUPDISK', 'ATLASLOCALGROUPDISK'),
        )

class Tag(models.Model):
    """
    tag string, used to select subset of sites
    """
    name = models.CharField(max_length=40)
    def __unicode__(self):
        return self.name

class CE(models.Model):
    """
    Represents a ComputingElement
    """
    pass

class Site(models.Model):
    """
    Site name and federation
    """ 
    name = models.CharField(max_length=128, unique=True)
    tags = models.ManyToManyField(Tag, blank=True)
    # update to DecimalField when moved to python > 2.4
    #    total = models.DecimalField(max_digits=5, decimal_places=2)
    #    unused = models.DecimalField(max_digits=5, decimal_places=2)
    total = models.FloatField()
    used = models.FloatField()
    unused = models.FloatField()
    gocid = models.PositiveIntegerField()
    slots = models.PositiveIntegerField()
    # pledge numbers from https://www.gridpp.ac.uk/deployment/status/reports/reports.html
    pledge = models.FloatField()
    wlcg2010 = models.FloatField()
    wlcg2011 = models.FloatField()
    wlcg2012 = models.FloatField()
    wlcg2013 = models.FloatField()
    wlcg2014 = models.FloatField()
    wlcg2015 = models.FloatField()
    wlcg2016 = models.FloatField()
    wlcg2017 = models.FloatField()
    wlcg2018 = models.FloatField()
    wlcg2019 = models.FloatField()
    wlcg2020 = models.FloatField()
    last_modified = models.DateTimeField(auto_now=True, editable=False)
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

class Storage(models.Model):
    """
    Represents an ATLAS storage token
    """
    site = models.ForeignKey(Site)
    name = models.CharField(max_length=255)
#    token = models.CharField(max_length=32, choices=TOKENS)
    total = models.FloatField(default=0.0)
    used = models.FloatField(default=0.0)
    unused = models.FloatField(default=0.0)
    srmtype = models.CharField(max_length=16, choices=SRMTYPE, blank=True)
    last_modified = models.DateTimeField(auto_now=True, editable=False)
    def __unicode__(self):
        return self.name

class Token(models.Model):
    """
    Represents SRM space token
    """
    srm = models.ForeignKey(Storage)
    name = models.CharField(max_length=32, choices=TOKENS)
    total = models.FloatField(default=0.0)
    used = models.FloatField(default=0.0)
    unused = models.FloatField(default=0.0)
    last_modified = models.DateTimeField(auto_now=True, editable=False)
    fwdcheck = models.DateTimeField(auto_now=False, editable=True, blank=True)
    revcheck = models.DateTimeField(auto_now=False, editable=True, blank=True)
    def __unicode__(self):
        return self.srm.name + '_' + self.name

class DDMSource(models.Model):
    """
    Represents a DDM resource from the ToA
    """
    name = models.CharField(max_length=128)
    # ToA 'srm' == this token+url
    token = models.ForeignKey(Token)
    url = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=128, blank=True)
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

class Space(models.Model):
    """
    Space status for a token at a given datetime
    """
    token = models.ForeignKey(Token)
    datetime = models.DateTimeField(auto_now=True, editable=False)
    total = models.FloatField()
    used = models.FloatField()
    unused = models.FloatField()
    def __unicode__(self):
        return str(self.id)
    class Meta:
        get_latest_by = 'datetime'

class Pattern(models.Model):
    """
    Represents usage stats of a dataset pattern
    """
    name = models.CharField(max_length=40)
    datetime = models.DateTimeField(auto_now=True, editable=False)
    regex = models.CharField(max_length=128)
    ddmsource = models.ForeignKey(DDMSource)
    tb = models.FloatField()
    ndatasets = models.PositiveIntegerField()
    complete = models.PositiveIntegerField()
    nfiles = models.PositiveIntegerField()
    def __unicode__(self):
        return "%s-%s" % (str(self.token), self.name)
    class Meta:
        get_latest_by = 'datetime'

class Dataset(models.Model):
    """
    Represents a DQ2 dataset or container
    """
    name = models.CharField(max_length=128, unique=True)
    pattern = models.ForeignKey(Pattern)
    totalsize = models.PositiveIntegerField()
    nfiles = models.PositiveIntegerField()
    def __unicode__(self):
        return self.name

#def queryStorageUsage (self, key=None, value=None, site=None, metaDataAttributes={}, locations=[]):
# client.queryStorageUsage (metaDataAttributes={'pattern': mypattern_eff}, locations=list_sites)
