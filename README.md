# Python streamsx.sttgateway package

This exposes SPL operators in the `com.ibm.streamsx.sttgateway` toolkit as Python methods.

Package is organized using standard packaging to upload to PyPi.

The package is uploaded to PyPi in the standard way:
```
cd package
python setup.py sdist bdist_wheel upload -r pypi
```
Note: This is done using the `ibmstreams` account at pypi.org and requires `.pypirc` file containing the credentials in your home directory.

Package details: https://pypi.python.org/pypi/streamsx.sttgateway

Documentation is using Sphinx and can be built locally using:
```
cd package/docs
make html
```

or

    ant doc

and viewed using
```
firefox package/docs/build/html/index.html
```

The documentation is also setup at `readthedocs.io`.

Documentation links:
* http://streamsxsttgateway.readthedocs.io

## Version update

To change the version information of the Python package, edit following files:

- ./package/docs/source/conf.py
- ./package/streamsx/sttgateway/\_\_init\_\_.py

When the development status changes, edit the *classifiers* in

- ./package/setup.py

When the documented sample must be changed, change it here:

- ./package/streamsx/sttgateway/\_\_init\_\_.py
- ./package/DESC.txt

## Environment

You need the streamsx package in version 1.14.7 or later to use and test the streamsx.sttgateway package. Install it like this:

    pip install streamsx==1.14.7

In addition you should unset the PYTHONPATH variable to not use the streams package included in your local Streams installation:

    unset PYTHONPATH
    
## Test

When using local build (e.g. not forcing remote build), then you need to specifiy the toolkit location, for example:

    export STREAMS_STTGATEWAY_TOOLKIT=<PATH_TO_STTGATEWAY_TOOLKIT>/com.ibm.streamsx.sttgateway

Specify the directory of sample audio files, used by test applications:

    export STREAMS_STTGATEWAY_AUDIO_DIR=<PATH_TO_STTGATEWAY_TOOLKIT>/samples/audio-files

Specify the STT credentials, used by test applications, for example:

    export STT_CREDENTIALS=<PATH_TO_CREDENTIALS_FILE>/watson_stt_public_cloud.json

Example, content of JSON file given with STT_CREDENTIALS:

```
{
  "url": "wss://xxx/instances/xxx/v1/recognize",
  "api_key": "xxxx",
  "iam_token_url": "https://iam.cloud.ibm.com/identity/token"
}
```


### Test build-only

Required environment variables:

* STREAMS_INSTALL
* STREAMS_STTGATEWAY_TOOLKIT

Run the (build-only) test with:

    ant test

or 

```
cd package
python3 -u -m unittest streamsx.sttgateway.tests.test_sttgateway.Test
```

### Test distributed

Required environment variables for tests with local Streams instance:

* STREAMS_STTGATEWAY_TOOLKIT
* STREAMS_STTGATEWAY_AUDIO_DIR
* STT_CREDENTIALS
* STREAMS_INSTALL
* STREAMS_INSTANCE_ID
* STREAMS_DOMAIN_ID
* STREAMS_USERNAME
* STREAMS_PASSWORD

Start the Streams instance before running the test.

Run the distributed test with:

    ant test-distributed

or

```
cd package
python3 -u -m unittest streamsx.sttgateway.tests.test_sttgateway.TestDistributed
```

### Test distributed with remote build (Cloud Pak for Data)

This test uses the toolkit from the build service.

Required environment variables for tests with local Streams instance:

* STREAMS_STTGATEWAY_AUDIO_DIR
* STT_CREDENTIALS
* CP4D_URL
* STREAMS_INSTANCE_ID
* STREAMS_USERNAME
* STREAMS_PASSWORD

Start the Streams instance before running the test.

Run the distributed test with:

    ant test-icp

or

```
unset STREAMS_INSTALL
unset STREAMS_DOMAIN_ID
cd package
python3 -u -m unittest streamsx.sttgateway.tests.test_sttgateway.TestICPRemote
```

