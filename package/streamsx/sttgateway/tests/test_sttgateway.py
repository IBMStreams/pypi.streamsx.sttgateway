import streamsx.sttgateway as stt

from streamsx.topology.topology import Topology
from streamsx.topology.tester import Tester
from streamsx.topology.schema import CommonSchema, StreamSchema
import streamsx.spl.op as op
from streamsx.spl import toolkit
from streamsx.topology import context
import streamsx.rest as sr
import streamsx.rest_primitives
import unittest
import datetime
import os
import json
from subprocess import call, Popen, PIPE
from streamsx.sttgateway.schema import GatewaySchema


def _get_test_tk_path():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return script_dir+'/test.source'

def _run_shell_command_line(command):
    process = Popen(command, universal_newlines=True, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def _streams_install_env_var():
    result = True
    try:
        os.environ['STREAMS_INSTALL']
    except KeyError: 
        result = False
    return result

def cp4d_url_env_var():
    result = True
    try:
        os.environ['CP4D_URL']
    except KeyError: 
        result = False
    return result

class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print (str(self))
        self.sttgateway_toolkit_home = os.environ["STREAMS_STTGATEWAY_TOOLKIT"]
        self.sttgateway_audio_dir = os.environ["STREAMS_STTGATEWAY_AUDIO_DIR"]
        
    def _index_toolkit(self, tk):
        if _streams_install_env_var():
            cmd = os.environ['STREAMS_INSTALL']+'/bin/spl-make-toolkit -i .'
            _run_shell_command_line('cd '+tk+'; '+cmd)

    def _build_only(self, name, topo):
        # build with c++11
        build_config = {}
        build_config[context.ConfigParams.SC_OPTIONS] = '--c++std=c++11'

        result = context.submit("TOOLKIT", topo.graph) # creates tk* directory
        print(name + ' (TOOLKIT):' + str(result))
        assert(result.return_code == 0)
        result = context.submit("BUNDLE", topo.graph, build_config)  # creates sab file
        print(name + ' (BUNDLE):' + str(result))
        assert(result.return_code == 0)


    def test_app_config(self):
        print ('\n---------'+str(self))
        name = 'test_app_config'
        topo = Topology(name)
        toolkit.add_toolkit(topo, self.sttgateway_toolkit_home)
        self._index_toolkit(_get_test_tk_path())
        toolkit.add_toolkit(topo, _get_test_tk_path())

        app_config = 'stt'
        cred_file = os.environ['STT_CREDENTIALS']
        print("STT credentials file:" + cred_file)
        with open(cred_file) as data_file:
            creds = json.load(data_file)

        if ("TestDistributed" in str(self) and cp4d_url_env_var() is True):
            instance = streamsx.rest_primitives.Instance.of_endpoint(verify=False)
            res = stt.configure_connection(instance, credentials=creds, name=app_config)
            print (str(res))
        else: 
            if _streams_install_env_var():        
                _run_shell_command_line('streamtool rmappconfig --noprompt '+app_config)
                print ('create appConfig with streamtool: ' + app_config)
                if 'access_token' in creds:
                    cmd = os.environ['STREAMS_INSTALL']+'/bin/streamtool mkappconfig --property \"accessToken='+creds.get('access_token')+'\" --property \"url='+creds.get('url')+'\" '+app_config
                else:
                    cmd = os.environ['STREAMS_INSTALL']+'/bin/streamtool mkappconfig --property \"apiKey='+creds.get('api_key')+'\" --property \"iamTokenURL='+creds.get('iam_token_url')+'\" --property \"url='+creds.get('url')+'\" '+app_config
                stdout, stderr, rc = _run_shell_command_line(cmd)
                print (str(rc))
            else:
                print ('Application configuration not created')
     
        dirname = 'etc'
        topo.add_file_dependency(self.sttgateway_audio_dir, dirname) 
        if os.path.isdir(self.sttgateway_audio_dir):
            # add_file_dependency adds it to sub directory having last part of the dir as name
            # retrieve the name here and use it later in the parameter
            dirname = dirname + '/' + os.path.basename(self.sttgateway_audio_dir) 

        files = op.Invoke(topo, kind='test::FilesReader', schemas=[GatewaySchema.STTInput])
        files.params['audioApplDir'] = dirname
        files = files.outputs[0]
       
        res = files.map(stt.WatsonSTT(credentials=app_config, base_language_model='en-US_NarrowbandModel'))

        res.print()

        if (("TestDistributed" in str(self)) or ("TestStreamingAnalytics" in str(self))):
            tester = Tester(topo)
            tester.tuple_count(res, 1, exact=False)
            self.test_config[context.ConfigParams.SC_OPTIONS] = '--c++std=c++11'
            tester.test(self.test_ctxtype, self.test_config, always_collect_logs=True)
        else:
            # build only
            self._build_only(name, topo)

    @unittest.skipUnless(_streams_install_env_var(), "STREAMS_INSTALL required")
    def test_properties(self):
        print ('\n---------'+str(self))
        name = 'test_properties'
        topo = Topology(name)
        toolkit.add_toolkit(topo, self.sttgateway_toolkit_home)
        self._index_toolkit(_get_test_tk_path())
        toolkit.add_toolkit(topo, _get_test_tk_path())

        files = op.Invoke(topo, kind='test::FilesReader', schemas=[GatewaySchema.STTInput])
        files.params['pattern'] = "\\.mp3$"
        files = files.outputs[0]
       
        creds = {
            'url': 'wss://hostplaceholder/speech-to-text/ibm-wc/instances/1188888444444/api/v1/recognize',
            'access_token': 'sample-access-token'
        }
        gateway = stt.WatsonSTT(credentials=creds, base_language_model='en-US_NarrowbandModel', partial_result=True)
        gateway.content_type = 'audio/mp3'
        gateway.filter_profanity = True
        gateway.keywords_spotting_threshold = 0.5
        gateway.keywords_to_be_spotted = ['sample','test']
        #gateway.keywords_to_be_spotted = "['sample','test']"
        gateway.max_utterance_alternatives = 5
        gateway.non_final_utterances_needed = True

        res = files.map(gateway)
        res.print()
        # build only
        self._build_only(name, topo)


    def test_schema_named_tuple(self):
        print ('\n---------'+str(self))
        name = 'test_schema_named_tuple'
        topo = Topology(name)
        toolkit.add_toolkit(topo, self.sttgateway_toolkit_home)
        self._index_toolkit(_get_test_tk_path())
        toolkit.add_toolkit(topo, _get_test_tk_path())

        cred_file = os.environ['STT_CREDENTIALS']
        print("STT credentials file:" + cred_file)
        with open(cred_file) as data_file:
            creds = json.load(data_file)
    
        dirname = 'etc'
        topo.add_file_dependency(self.sttgateway_audio_dir, dirname) 
        if os.path.isdir(self.sttgateway_audio_dir):
            # add_file_dependency adds it to sub directory having last part of the dir as name
            # retrieve the name here and use it later in the parameter
            dirname = dirname + '/' + os.path.basename(self.sttgateway_audio_dir) 

        dirname = op.Expression.expression('getApplicationDir()+"/'+dirname+'"')
        print(dirname)

        import streamsx.standard.files as stdfiles
        import typing
        SttResult = typing.NamedTuple('SttResult', [('conversationId', str), ('utteranceText', str)])

        s = topo.source(stdfiles.DirectoryScan(directory=dirname, pattern='.*call-center.*\.wav$'))

        low1 = s.low_latency()
        files = low1.map(stdfiles.BlockFilesReader(block_size=512, file_name='conversationId'), schema=StreamSchema('tuple<blob speech, rstring conversationId>'))

        res = files.map(stt.WatsonSTT(credentials=creds, base_language_model='en-US_NarrowbandModel'), schema=SttResult)
        elow1 = res.end_low_latency()

        elow1.print()

        if (("TestDistributed" in str(self)) or ("TestStreamingAnalytics" in str(self))):
            tester = Tester(topo)
            tester.run_for(60)
            tester.tuple_count(elow1, 3, exact=False)
            self.test_config[context.ConfigParams.SC_OPTIONS] = '--c++std=c++11'
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

