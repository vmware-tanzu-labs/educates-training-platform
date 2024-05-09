kind using provided domain with custom configuration
In this scenario we don't use any global educates config, but the one in the clusterPackages.
We do provide some custom config for `contour` that should be passed down to the clusterPackage, 
but none for `external-dns` so it'll inherit it's defaults.
