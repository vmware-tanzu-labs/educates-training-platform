import os

portal_title = os.environ.get("PORTAL_TITLE")

portal_logo = None

if os.path.exists("/opt/app-root/config/logo"):
    with open("/opt/app-root/config/logo") as fp:
        portal_logo = fp.read()

def portal(request):
    context = {}
    context["portal_title"] = portal_title or "Workshops"
    context["portal_logo"] = portal_logo
    return context
