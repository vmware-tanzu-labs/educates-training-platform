load("@ytt:data", "data")

def get_default_aws_args():
  args = [
    "--provider=aws",
    "--source=service",
    "--source=ingress",
    "--source=contour-httpproxy",
    "--aws-prefer-cname",
    "--registry=txt",
    "--txt-prefix=txt",
  ]

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
