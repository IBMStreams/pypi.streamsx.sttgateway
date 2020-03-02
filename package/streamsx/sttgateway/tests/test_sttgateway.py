import streamsx.sttgateway as geo

from streamsx.topology.topology import Topology
from streamsx.topology.tester import Tester
from streamsx.topology.schema import CommonSchema, StreamSchema
import streamsx.spl.op as op
from streamsx.spl import toolkit
from streamsx.topology import context
import streamsx.rest as sr
import unittest
import datetime
import os
import json
from streamsx.sttgateway.schema import GatewaySchema


def _streams_install_env_var():
    result = True
    try:
        os.environ['STREAMS_INSTALL']
    except KeyError: 
        result = False
    return result

class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print (str(self))
        self.sttgateway_toolkit_home = os.environ["STREAMS_STTGATEWAY_TOOLKIT"]
        
    def _build_only(self, name, topo):
        result = context.submit("TOOLKIT", topo.graph) # creates tk* directory
        print(name + ' (TOOLKIT):' + str(result))
        assert(result.return_code == 0)
        result = context.submit("BUNDLE", topo.graph)  # creates sab file
        print(name + ' (BUNDLE):' + str(result))
        assert(result.return_code == 0)


    def test_basic(self):
        print ('\n---------'+str(self))
        name = 'test_basic'
        topo = Topology(name)
        toolkit.add_toolkit(topo, self.sttgateway_toolkit_home)

        if (("TestDistributed" in str(self)) or ("TestStreamingAnalytics" in str(self))):
            tester = Tester(topo)
            tester.tuple_count(res, 1, exact=True)
            tester.test(self.test_ctxtype, self.test_config, always_collect_logs=True)
        else:
            # build only
            self._build_only(name, topo)


class TestDistributed(Test):
    def setUp(self):
        Tester.setup_distributed(self)
        # setup test config
        self.test_config = {}
        job_config = context.JobConfig(tracing='info')
        job_config.add(self.test_config)
        self.test_config[context.ConfigParams.SSL_VERIFY] = False  

    def _launch(self, topo):
        rc = context.submit('DISTRIBUTED', topo, self.test_config)
        print(str(rc))
        if rc is not None:
            if (rc.return_code == 0):
                rc.job.cancel()


class TestStreamingAnalytics(Test):
    def setUp(self):
        # setup test config
        #self.test_config = {}
        #job_config = context.JobConfig(tracing='info')
        #job_config.add(self.test_config)
        Tester.setup_streaming_analytics(self, force_remote_build=False)

    def _launch(self, topo):
        rc = context.submit('STREAMING_ANALYTICS_SERVICE', topo, self.test_config)
        print(str(rc))
        if rc is not None:
            if (rc.return_code == 0):
                rc.job.cancel()

    @classmethod
    def setUpClass(self):
        # start streams service
        connection = sr.StreamingAnalyticsConnection()
        service = connection.get_streaming_analytics()
        result = service.start_instance()
        super().setUpClass()

