# Scenarios

There's some scenarios we want to cover and test. We can print the list of scenarios and the
test file by executing:

```
./test-scenarios.sh --help
```

We can run the scenarios by executing:

```
./test-scenarios.sh
```

If you want to see the results generated vi the scenario, run (on the `installer` dir or adjust paths accordingly):

```
ytt --data-values-file scenarios/<SCENARIO> -f bundle/config
```

If we want to test the scenarios on a cluster, we need to output the result of the scenarios an pipe it
to `kapp`. e.g. command (on the `installer` dir or adjust paths accordingly)

```
ytt --data-values-file scenarios/<SCENARIO> -f bundle/config | kapp deploy -a educates -f - -c -y
```

**NOTE** Take into account that values are mock, so if you really want to test these scenarios into a cluster
make a copy and alter the values to your needs.

**NOTE** You will need to have a cluster to test on the cluster
