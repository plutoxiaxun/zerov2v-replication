# Data Access Statement

## Public data

The public release contains deidentified per-run CSV files, summary JSON,
selection/exclusion fields, analysis scripts, and SHA-256 hashes. Direct
identifiers are removed or replaced by stable public record identifiers.

## Controlled data

The following materials are retained but are not suitable for unrestricted
publication:

- application and batch SQLite databases;
- complete systemd journals and migration logs;
- vCenter, ZStack, Ceph, VM, volume, RBD, mapping, checkpoint, and snapshot
  identifiers;
- private network addresses, credentials, tokens, and endpoint configuration;
- console captures that may contain workload-specific information;
- journal-linked per-run records behind the descriptive historical TCG/KVM
  distribution.

Researchers who need to verify a result not covered by the public tables may
contact the corresponding author. A request should identify the question,
required fields, storage and deletion arrangements, and any institutional
approval. Where access is possible, only the necessary subset will be shared
under a written data-use agreement. Credentials and authentication material
are not available.

Controlled-access enquiries should be sent to the corresponding author, Xun
Xia, at `xiaxun@lzy.edu.cn`. A repository issue route may be used for public
questions that do not disclose controlled identifiers or infrastructure
details.

## Implementation availability

The ZeroV2V migration-controller source is not distributed with this public
release. The public package is intended for numerical reproduction and review
of the reported protocol evidence. Infrastructure re-execution would also
require a separately maintained implementation and a compatible
VMware/VDDK/Ceph/KVM environment.
