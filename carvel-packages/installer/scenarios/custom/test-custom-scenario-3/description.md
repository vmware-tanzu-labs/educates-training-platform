kind using provided domain with custom configuration
In this scenario we don't use any global educates config, but the one in the clusterPackages.
We do not provide config for `kapp-controller` and `certs` so these packages will be `disabled` in
generated config. All the other `clusterPackages` configuration will be respected.
