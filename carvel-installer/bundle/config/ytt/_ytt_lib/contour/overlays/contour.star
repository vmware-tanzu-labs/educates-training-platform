load("@ytt:data", "data")

def should_add_externaldns_annotation():
  return hasattr(data.values, "externaldns") and hasattr(data.values.externaldns, "domains")
end


def external_dns_annotation():
   dns_domains = []
   for domain in data.values.externaldns.domains:
     dns_domains.append("*.{}.".format(domain))
   end
   return ",".join(dns_domains)
end