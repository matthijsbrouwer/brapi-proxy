# BrAPI proxy solution


A BRAPI server instance that functions as a proxy for endpoints from existing BRAPI services.

## Installation

```
pip install brapi_proxy
```

### Usage

- **Step 1: Create Configuration File**
  - Create a file named config.ini.
  - Populate this file with the necessary configuration settings.

- **Step 2: Start the Service**
  - Start the service by running the command:
    ``` sh
    brapi_proxy
    ```
  - If the config.ini file is located outside the working directory, use the --config option to specify its location. For example:

    ```sh
    brapi_proxy --config /path/to/config.ini
    ```


### Currently Supported

**BrAPI Versions**
- version 2.1

**Endpoints**

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

### Structure Configuration File

Include at least the `brapi` section:
```
[brapi]
port=8080
host=::
threads=4
debug=False
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



