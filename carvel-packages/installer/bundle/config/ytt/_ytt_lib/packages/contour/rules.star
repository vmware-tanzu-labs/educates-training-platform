def check_infra(val):
  if val["infraProvider"] in ["minikube"]:
    return val["service"]["type"] in ["ClusterIP", "LoadBalancer"] or fail("{} infra provider requires service.type to be ClusterIP or LoadBalancer".format(val["infraProvider"]))
  end
  if val["infraProvider"] in ["aws", "gcp", "azure"]:
    return val["service"]["type"] == "LoadBalancer" or fail("{} infra provider requires service.type to be LoadBalancer".format(val["infraProvider"]))
  end
  if val["infraProvider"] in ["kind"]:
    return val["service"]["type"] == "ClusterIP" or fail("{} infra provider requires service.type to be ClusterIP".format(val["infraProvider"]))
  end
  return True
end

def check_host_ports(val):
  if val["infraProvider"] in ["kind", "aws", "gcp", "azure", "minikube"]:
    return val["service"]["useHostPorts"] == True or fail("{} infra provider requires service.useHostPorts to be True".format(val["infraProvider"]))
  end
  return True
end

def check_all(val):
  return check_infra(val) and check_host_ports(val)
end

def default_HTTP_Versions():
  return ["HTTP/1.1", "HTTP/2"]
end
