load("@ytt:struct", "struct")

def removeNulls(data):
   # Iterate over a struct of scalar values and return only those where value is not null
   filtered_data = {}
   for key in struct.decode(data):
      value = getattr(data, key, None)
      if type(value) == "struct":
         value = removeNulls(value)
      end
      if value: #! This means that value is not an empty string, dict, struct, ...
         filtered_data[key] = value
      end
   end
   return struct.encode(filtered_data)
end

