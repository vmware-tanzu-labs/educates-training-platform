load("@ytt:data", "data")

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