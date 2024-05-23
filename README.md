# BrAPI proxy solution


A BrAPI server instance that functions as a proxy for endpoints from existing BrAPI services.

## Installation

- **Step 1: Install BrAPI Proxy**
  - To install the BrAPI Proxy, run the following command:
    ```sh
    pip install brapi_proxy
    ```
- **Step 2: Test the Installation (Optional)**
  - To ensure that the installation was successful, you can run the BrAPI Proxy in demo mode with the following command:
    ```sh
    brapi_proxy --demo
    ```
    This will start a [service on port 8080](http://localhost:8080/) from a configuration based on the [BrAPI Test Server](https://test-server.brapi.org/brapi/v2/)

## Usage

- **Step 1: Create Configuration File**
  - Create a file named config.ini.
  - Populate this file with the necessary configuration settings.

- **Step 2: Start the Service**
  - Start the service by running the command:
    ```sh
    brapi_proxy
    ```
  - If the config.ini file is located outside the working directory, use the --config option to specify its location. For example:
    ```sh
    brapi_proxy --config /path/to/config.ini
    ```
    
---

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
  
### ToDo

- Implement additional endpoints
- Enable authentication for underlying servers
  
---

### Structure Configuration File

Create a `config.ini` file with the necessary configuration settings.

**Basic Configuration**

Include at least the `brapi` section:

```config
[brapi]
port=8080
host=::
threads=4
debug=False
version=2.1
```

**Optional: Authorization**

Optionally, provide authentication tokens to restrict access in the `authorization` section:

```
[authorization]
john=tokenjohn123abc
mary=tokenmary456def
```

**Server Definitions**

Within sections prefixed with `server.`, define the underlying servers:

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



