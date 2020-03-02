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

You need the streamsx package in version 1.14.7 to use and test the streamsx.sttgateway package. Install it like this:

    pip install streamsx==1.14.7

In addition you should unset the PYTHONPATH variable to not use the streams package included in your local Streams installation:

    unset PYTHONPATH
    
## Test

When using local build (e.g. not forcing remote build), then you need to specifiy the toolkit location, for example:

    export STREAMS_STTGATEWAY_TOOLKIT=<PATH_TO_STTGATEWAY_TOOLKIT>/com.ibm.streamsx.sttgateway


### Test

Run the (build-only) test with:

    ant test


```
cd package
python3 -u -m unittest streamsx.sttgateway.tests.test_sttgateway.Test
```


