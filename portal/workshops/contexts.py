import os

portal_title = os.environ.get("PORTAL_TITLE")

portal_logo = None

google_tracking_id = os.environ.get("GOOGLE_TRACKING_ID")

training_portal = os.environ.get("TRAINING_PORTAL")
ingress_domain = os.environ.get("INGRESS_DOMAIN")
ingress_protocol = os.environ.get("INGRESS_PROTOCOL")

if os.path.exists("/opt/app-root/config/logo"):
    with open("/opt/app-root/config/logo") as fp:
        portal_logo = fp.read()

def portal(request):
    context = {}
    context["portal_title"] = portal_title or "Workshops"
    context["portal_logo"] = portal_logo
    context["google_tracking_id"] = google_tracking_id
    context["training_portal"] = training_portal
    context["ingress_domain"] = ingress_domain
    context["ingress_protocol"] = ingress_protocol
    return context
