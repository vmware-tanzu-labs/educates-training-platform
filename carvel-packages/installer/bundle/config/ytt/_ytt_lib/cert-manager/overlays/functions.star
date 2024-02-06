load("@ytt:data", "data")
load("@ytt:struct", "struct")

def get_serviceaccount_annotations():
  annotations = {}

  if data.values.serviceaccount.annotations:
    annotations_kvs = struct.decode(data.values.serviceaccount.annotations)
    annotations.update(annotations_kvs)
  end

  return annotations
end

