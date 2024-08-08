load("@ytt:data", "data")
load("defaults.star", "enabledByDefaultPackagesList")

def isClusterPackageEnableByDefault(package):
  return package in enabledByDefaultPackagesList
end

def isClusterPackageEnabled(package):
  if hasattr(data.values, "clusterPackages") and hasattr(data.values.clusterPackages, package) and hasattr(data.values.clusterPackages[package], "enabled"):
    return data.values.clusterPackages[package].enabled
  else:
    return package in enabledByDefaultPackagesList
  end
end

def isClusterPackageExplicitDisabled(package):
  return not isClusterPackageEnabled(package)
end

def isGlobalCaCertificateRefEnabled():
  return (hasattr(data.values.clusterInfrastructure, "caCertificateRef") and
          hasattr(data.values.clusterInfrastructure.caCertificateRef, "namespace") and
          hasattr(data.values.clusterInfrastructure.caCertificateRef, "name"))
end

def isEducatesTLSCertRefEnabled():
  return (hasattr(data.values.clusterPackages.educates.settings, "clusterIngress") and
          hasattr(data.values.clusterPackages.educates.settings.clusterIngress, "tlsCertificateRef") and
          hasattr(data.values.clusterPackages.educates.settings.clusterIngress.tlsCertificateRef, "namespace") and
          hasattr(data.values.clusterPackages.educates.settings.clusterIngress.tlsCertificateRef, "name"))
end

def isEducatesCARefEnabled():
  return (hasattr(data.values.clusterPackages.educates.settings, "clusterIngress") and
          hasattr(data.values.clusterPackages.educates.settings.clusterIngress, "caCertificateRef") and
          hasattr(data.values.clusterPackages.educates.settings.clusterIngress.caCertificateRef, "namespace") and
          hasattr(data.values.clusterPackages.educates.settings.clusterIngress.caCertificateRef, "name"))
end

def xgetattr(object, path, default=None):
  def _lookup(object, key, default=None):
    keys = key.split(".")
    value = default
    for key in keys:
      value = getattr(object, key, None)
      if value == None:
        return default
      end
      object = value
    end
    return value
  end

  return _lookup(object, path, default)
end