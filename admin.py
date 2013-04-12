from django.contrib import admin
from ukdata.models import Site, Tag, Space, Storage, Token
from ukdata.models import Pattern, Dataset, DDMSource

admin.site.register(Site)
admin.site.register(Storage)
admin.site.register(Token)
admin.site.register(Tag)
admin.site.register(Space)
admin.site.register(Pattern)
admin.site.register(Dataset)
admin.site.register(DDMSource)
