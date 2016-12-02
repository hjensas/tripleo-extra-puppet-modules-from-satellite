# tripleo-extra-puppet-modules-from-satellite

### Example: NodeExtraConfig environment file
```
resource_registry:
   OS::TripleO::NodeExtraConfig: /home/stack/templates/extraconfig/pre_deploy/extra-puppet-modules-from-satellite/extra-puppet-modules-from-satellite.yaml

parameter_defaults:
  ExtraPuppetModulesFromSatellite:
    server: satellite.example.com
    protocol: https
    organization: Org
    environment: Production
    content_view: OSP
    modules:
      - puppetlabs-motd
      - saz-rsyslog
```


### Example: Extraconfig Environment file
```
parameter_defaults:
  #
  # All nodes, ExtraConfig
  #
  ExtraConfig:
    compute_classes:
      - ::motd
      - ::rsyslog::client
    controller_classes:
      - ::motd
      - ::rsyslog::client

    rsyslog::client::spool_size: 2g
    rsyslog::client::remote_servers:
      - host: logs.foo.example.com
        port: 55514
        protocol: udp
      - host: logs.bar.example.com
        port: 555
        pattern: '*.log'
        protocol: tcp
        format: RFC3164fmt

