load("@ytt:data", "data")
load("@ytt:base64", "base64")
load("@ytt:json", "json")

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

def image_reference(name):
  registry = data.values.imageRegistry.host
  if not registry:
    registry = "registry.default.svc.cluster.local"
  end
  if data.values.imageRegistry.namespace:
    registry = "{}/{}".format(registry, data.values.imageRegistry.namespace)
  end
  image = "{}/educates-{}:{}".format(registry, name, data.values.version)
  for item in data.values.imageVersions:
    if item.name == name:
      image = item.image
      break
    end
  end
  return image
end

def image_pull_policy(image):
  tag = image.split(":")
  always = len(tag) <= 1 or tag[-1] in ["latest", "main", "master", "develop"]
  return always and "Always" or "IfNotPresent"
end

def image_pull_secrets():
  return [item["name"] for item in data.values.clusterSecrets.pullSecretRefs]
end

def docker_config_json(host, username, password):
  return json.encode({
    "auths": {
      host: {
        "auth": base64.encode("{}:{}".format(username, password))
      }
    }
  })
end
