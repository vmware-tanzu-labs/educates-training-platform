load("@ytt:data", "data")

def isWildcardCertEnabled():
  return (hasattr(data.values.clusterInfrastructure, "wildcardCertificate") and
          hasattr(data.values.clusterInfrastructure.wildcardCertificate, "key") and
          hasattr(data.values.clusterInfrastructure.wildcardCertificate, "cert"))
end

def isWildcardCAEnabled():
  return (hasattr(data.values.clusterInfrastructure, "wildcardCA") and
          hasattr(data.values.clusterInfrastructure.wildcardCA, "key") and
          hasattr(data.values.clusterInfrastructure.wildcardCA, "cert"))
end

def shouldEnableCerts():
  return (isWildcardCAEnabled() or isWildcardCertEnabled())
end