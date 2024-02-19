load("@ytt:data", "data")

def isWildcardCertEnabled():
  return (hasattr(data.values.clusterInfrastructure, "wildcardCertificate") and
          hasattr(data.values.clusterInfrastructure.wildcardCertificate, "tls.crt") and
          hasattr(data.values.clusterInfrastructure.wildcardCertificate, "tls.key"))
end

def isWildcardCAEnabled():
  return (hasattr(data.values.clusterInfrastructure, "wildcardCA") and
          hasattr(data.values.clusterInfrastructure.wildcardCA, "ca.crt"))
end

def shouldEnableCerts():
  return (isWildcardCAEnabled() or isWildcardCertEnabled())
end