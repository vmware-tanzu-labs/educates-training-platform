load("@ytt:data", "data")

def get_default_aws_args():
  args = [
    "--provider=aws",
    "--source=service",
    "--aws-prefer-cname",
    "--aws-zone-match-parent",
    "--registry=txt",
    "--txt-prefix=txt",
  ]
  #! These are removed as in AWS we just need the wildcard for the envoy service
  #!  "--source=ingress",
  #!  "--source=contour-httpproxy",

  if hasattr(data.values.aws, "args"):
    if data.values.aws.args.zone_type:
      args.append("--aws-zone-type={}".format(data.values.aws.args.zone_type))
    end

    if data.values.aws.args.policy:
      args.append("--policy={}".format(data.values.aws.args.policy))
    end

    if data.values.aws.args.domain_filter:
      args.append("--domain-filter={}".format(data.values.aws.args.domain_filter))
    end

    if data.values.aws.args.txt_owner_id:
      args.append("--txt-owner-id={}".format(data.values.aws.args.txt_owner_id))
    end
  end

  return args
end

def get_default_google_args():
  args = [
    "--provider=google",
    "--source=service",
    "--log-format=json",
    "--registry=txt",
    "--txt-prefix=txt",
  ]
  #! These are removed as in GCP we just need the wildcard for the envoy service
  #!  "--source=ingress",
  #!  "--source=contour-httpproxy",

  if hasattr(data.values.gcp, "args"):
    if data.values.gcp.args.zone_visibility:
      args.append("--google-zone-visibility={}".format(data.values.gcp.args.zone_visibility))
    end

    if data.values.gcp.args.policy:
      args.append("--policy={}".format(data.values.gcp.args.policy))
    end

    if data.values.gcp.args.domain_filter:
      args.append("--domain-filter={}".format(data.values.gcp.args.domain_filter))
    end

    if data.values.gcp.args.txt_owner_id:
      args.append("--txt-owner-id={}".format(data.values.gcp.args.txt_owner_id))
    end

    if data.values.gcp.args.project:
      args.append("--google-project={}".format(data.values.gcp.args.project))
    end
  end

  return args
end
