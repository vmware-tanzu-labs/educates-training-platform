load("@ytt:assert", "assert")

def custom_requires_clusterPackages(val):
  if val["clusterPackages"] == None:
     return fail("clusterPackages must be defined when provider is custom")
  end
end

def custom_requires_one_enabled_Package(val):
   for package in val["clusterPackages"]:
      if val["clusterPackages"][package] != None and val["clusterPackages"][package]["enabled"] == True:
         return True
      end
   end
   fail("At least one package needs to be enabled for custom provider")
end

validation_custom = [
   custom_requires_clusterPackages,
   custom_requires_one_enabled_Package
]

def validate_custom(val):
   if val["clusterInfrastructure"]["provider"] == "custom":
      for function in validation_custom:
         function(val)
      end
   end
   return True
end

def validate_domain(val):
   #! Domain not validated for custom infrastructure provider
   if val["clusterInfrastructure"]["provider"] == "custom":
     return True
   end

   #! Domain provided at top level
   if val["clusterIngress"] != None and \
      val["clusterIngress"]["domain"] != None:
      return True
   end

   #! Domain provided at clusterPackage level
   val, err = assert.try_to(lambda: val["clusterPackages"]["educates"]["settings"]["clusterIngress"]["domain"])
   if val != None:
      return True
   end

   #! Domain is not required if educates is not enabled
   enabled, err = assert.try_to(lambda: val["clusterPackages"]["educates"]["enabled"])
   if not enabled:
      return True
   end

   fail("clusterIngress.domain for educates needs to be provided")
end

validation_functions = [
   validate_custom, 
   validate_domain
]

def validate_all(val):
   for function in validation_functions:
      function(val)
   end
   return True
end
