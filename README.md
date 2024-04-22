# BrAPI proxy solution

Create a file `config.ini` (see `config_demo.ini` for an example) with the required configuration.

Start the service with `python service.py` or use the `service.sh` script.

### Supported

- BrAPI-Core
  - /commoncropnames
  - /studies
  - /studies/{studyDbId}
- BrAPI-Genotyping
  - /callsets
  - /callsets/{callSetDbId}
  - /variants
  - /variants/{variantDbId}
  - /variantsets
  - /variantsets/{variantSetDbId}
  - /plates
  - /plates/{plateDbId}
  - /samples
  - /samples/{sampleDbId}
  - /references
  - /references/{referenceDbId}
  - /referencesets
  - /referencesets/{referenceSetDbId}
  - /allelematrix

### Configuration

Include at least the `brapi` section:
```
[brapi]
port=5000
host=0.0.0.0
threads=10
debug=True
version=2.1
```

Optionally provide authentication tokens to restrict access in the `authorization` section:
```
[authorization]
john=tokenjohn123abc
mary=tokenmary456def
```

Within sections prefixed with `server.` the underlying servers can be defined:
```
[server.test1]
url=https://test-server.brapi.org/brapi/v2
calls=commoncropnames,variants,allelematrix
prefix.variants=barley:
prefix.variantsets=barley:
prefix.references=barley:
prefix.referencesets=barley:
prefix.callsets=barley:

[server.test2]
url=https://test-server.brapi.org/brapi/v2
calls=commoncropnames,variants,allelematrix
prefix.variants=wheat:
prefix.variantsets=wheat:
prefix.references=wheat:
prefix.referencesets=wheat:
prefix.callsets=wheat:

[server.test3]
url=https://test-server.brapi.org/brapi/v2
calls=samples,studies,plates,callsets,variantsets,referencesets,references
```

---
This software has been developed for the [AGENT](https://www.agent-project.eu/) project



