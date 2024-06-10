load("@ytt:data", "data")

def get_domains():
   domains = []
   for domain in data.values.domains:
     domains.append("*.{}".format(domain))
   end
   return domains
end