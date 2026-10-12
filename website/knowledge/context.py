import json
from django.conf import settings

def site_version(request):
    version=json.loads((settings.CONTENT_DIR/'site-version.json').read_text())
    return {'site_version':version['version'],'site_revision':version['revision'][:7],'site_dirty':version['dirty'],'site_revision_url':'https://github.com/lightningspore/shieldsigner-dev/commit/'+version['revision']}
